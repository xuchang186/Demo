from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from patient_records.models import Patient, ClinicalFeature, Doctor
from .models import DiagnosisResult
import os
import json
from datetime import datetime, timedelta
import random
import time
import paramiko  # 用于SSH连接
import base64
import socket
from django.db.models import Q

# 添加一个全局变量，用于跟踪正在进行的远程命令执行
# 格式: {patient_id: (timestamp, status, result)}
# status: 'running', 'completed', 'error'
# result: 远程执行结果，如果有
_remote_executions = {}

# 添加一个等待远程结果的函数
def wait_for_remote_result(patient_id, timeout=60, polling_interval=1):
    """
    等待远程执行结果返回
    
    参数:
    - patient_id: 患者ID
    - timeout: 最大等待时间（秒），默认60秒
    - polling_interval: 轮询间隔（秒），默认1秒
    
    返回:
    - 远程执行结果字典或None
    """
    global _remote_executions
    start_time = datetime.now()
    elapsed_time = 0
    
    print(f"开始等待患者 {patient_id} 的远程执行结果，最长等待 {timeout} 秒")
    
    while elapsed_time < timeout:
        # 检查患者的远程执行状态
        if patient_id in _remote_executions:
            timestamp, status, result = _remote_executions[patient_id]
            
            # 如果执行已完成且有结果，返回结果
            if status == 'completed' and result is not None:
                print(f"患者 {patient_id} 的远程执行结果已返回，等待时间: {elapsed_time} 秒")
                return result
            
            # 如果执行已完成但没有结果，或者执行出错，停止等待
            if status == 'completed' or status == 'error':
                print(f"患者 {patient_id} 的远程执行已结束，但未返回有效结果，状态: {status}")
                return None
        
        # 等待一段时间后再次检查
        time.sleep(polling_interval)
        elapsed_time = (datetime.now() - start_time).total_seconds()
    
    print(f"等待患者 {patient_id} 的远程执行结果超时，已等待 {timeout} 秒")
    return None

# 诊断首页视图
def diagnosis_home(request):
    # 获取搜索参数
    search_id = request.GET.get('search_id', '')
    search_name = request.GET.get('search_name', '')
    search_date = request.GET.get('search_date', '')
    
    # 初始查询：获取所有患者
    patients = Patient.objects.all()
    
    # 应用搜索过滤
    if search_id:
        patients = patients.filter(patient_id=search_id)
    
    if search_name:
        patients = patients.filter(name__icontains=search_name)
    
    if search_date:
        # 按创建日期过滤
        try:
            from datetime import datetime
            search_date_obj = datetime.strptime(search_date, '%Y-%m-%d').date()
            patients = patients.filter(created_at__date=search_date_obj)
        except (ValueError, TypeError):
            # 如果日期格式不正确，忽略该过滤条件
            pass
    
    # 按创建时间倒序排序，并限制最多显示10条记录
    patients = patients.order_by('-created_at')[:10]
    
    return render(request, 'diagnosis/diagnosis_home.html', {
        'patients': patients,
        'search_id': search_id,
        'search_name': search_name,
        'search_date': search_date
    })

# 上传CT图像视图
def upload_ct(request, patient_id=None):
    """上传CT图像页面"""
    try:
        if patient_id:
            # 获取特定患者信息
            patient = get_object_or_404(Patient, patient_id=patient_id)
            
            # 获取患者的临床特征
            try:
                clinical_features = ClinicalFeature.objects.get(patient=patient)
            except ClinicalFeature.DoesNotExist:
                clinical_features = None
                
            context = {
                'patient': patient,
                'clinical_features': clinical_features,
            }
            
            return render(request, 'diagnosis/upload_ct.html', context)
        else:
            # 如果没有提供patient_id，重定向到诊断首页
            messages.warning(request, "请先选择一位患者进行诊断")
            return redirect('diagnosis:home')
    except Exception as e:
        messages.error(request, f"获取患者信息时出错: {str(e)}")
        return redirect('diagnosis:home')

# 远程执行HUST-19模型
def run_remote_model(temp_image_path=None, patient=None, clinical_features=None, form_data=None, from_api=False):
    """
    在远程服务器上运行HUST-19模型
    
    参数:
    - patient: 患者对象（用于创建诊断结果记录）
    - from_api: 是否来自API调用
    
    返回:
    - 解析后的结果概率字典或None
    """
    global _remote_executions
    result_probabilities = None
    client = None
    
    try:
        # 如果未提供患者信息且提供了表单数据，则从表单获取患者ID
        if patient is None and form_data:
            patient_id = form_data.get('patient')
            try:
                patient = Patient.objects.get(patient_id=patient_id)
                clinical_features = patient.clinical_features
            except:
                print(f"无法获取患者信息，ID: {patient_id}")
                return None
        
        if patient is None:
            print("错误：未提供患者信息")
            return None
            
        patient_id = patient.patient_id
        
        # 检查是否有正在进行的相同患者命令执行
        current_time = datetime.now()
        execution_id = f"run_remote_model_{patient_id}_{current_time.strftime('%Y%m%d%H%M%S')}"
        print(f"开始执行ID: {execution_id} 的远程模型")
        
        if patient_id in _remote_executions:
            timestamp, status, cached_result = _remote_executions[patient_id]
            
            # 如果有已完成的结果且不超过10分钟，直接返回缓存的结果
            if status == 'completed' and cached_result is not None and (current_time - timestamp).total_seconds() < 600:
                print(f"患者 {patient_id} 已有缓存的远程执行结果，将直接返回")
                return cached_result
        
        # 标记此患者的远程执行为进行中
        print(f"标记患者 {patient_id} 的远程执行状态为进行中")
        _remote_executions[patient_id] = (current_time, 'running', None)
        
        # 远程服务器连接信息
        hostname = "202.197.33.114"
        port = 223
        username = "xuchang"
        password = "1"
        
        # HUST-19项目路径和python环境
        remote_project_path = "/data8t/xuchang/PycharmProjects/HUST-19"
        python_env = "source /data8t/xuchang/anaconda3/etc/profile.d/conda.sh && conda activate hust19"
        
        # 创建SSH客户端
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 连接到远程服务器
            print(f"正在连接到远程服务器 {hostname}:{port}")
            client.connect(
                hostname=hostname, 
                port=port, 
                username=username, 
                password=password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 构建命令（使用patient_id替代id）
            command = f"{python_env} && cd {remote_project_path} && python run.py --patient_id={patient.patient_id}"
            print(f"执行远程命令: {command}")
            
            # 执行命令
            stdin, stdout, stderr = client.exec_command(command, timeout=120)  # 增加超时时间到120秒
            
            # 读取输出
            stdout_str = stdout.read().decode('utf-8', errors='ignore')
            stderr_str = stderr.read().decode('utf-8', errors='ignore')
            exit_status = stdout.channel.recv_exit_status()
            
            print(f"远程执行命令完成，退出状态: {exit_status}")
            print(f"标准输出: {stdout_str}")
            if stderr_str:
                print(f"标准错误: {stderr_str}")
            
            # 尝试从标准输出中解析结果，改进正则表达式匹配
            import re
            
            # 先尝试匹配标准格式：三个浮点数以加号分隔
            result_match = re.search(r"(\d+\.\d+)\+(\d+\.\d+)\+(\d+\.\d+)", stdout_str)
            if result_match:
                probability_normal = float(result_match.group(1))
                probability_mild = float(result_match.group(2))
                probability_severe = float(result_match.group(3))
                
                print(f"从远程输出中解析到概率: 正常({probability_normal:.4f}), 轻度({probability_mild:.4f}), 重度({probability_severe:.4f})")
                
                # 创建结果概率字典
                result_probabilities = {
                    'normal': probability_normal,
                    'mild': probability_mild,
                    'severe': probability_severe
                }
                
                # 更新此患者的远程执行状态为完成，同时缓存结果
                _remote_executions[patient_id] = (current_time, 'completed', result_probabilities)
                
                print(f"执行ID: {execution_id} 的远程模型完成，结果: {result_probabilities}")
                
                # 立即关闭SSH连接
                if client:
                    client.close()
                    client = None
                    
                return result_probabilities
            else:
                # 尝试其他格式匹配，查找包含概率信息的行
                print("无法通过标准格式解析结果，尝试其他方式...")
                
                # 查找结果类型和概率
                for line in stdout_str.splitlines():
                    if "result_str" in line and "该患者" in line:
                        print(f"找到结果行: {line}")
                        # 查找下一行是否包含概率
                        break
                
                # 如果上面的方法都失败，尝试直接在整个输出中查找三个浮点数
                numbers = re.findall(r"(\d+\.\d+)", stdout_str)
                if len(numbers) >= 3:
                    print(f"在输出中找到浮点数: {numbers}")
                    probability_normal = float(numbers[0])
                    probability_mild = float(numbers[1])
                    probability_severe = float(numbers[2])
                    
                    # 检查概率和是否接近1
                    prob_sum = probability_normal + probability_mild + probability_severe
                    if 0.99 <= prob_sum <= 1.01:
                        print(f"找到有效概率值: 正常({probability_normal:.4f}), 轻度({probability_mild:.4f}), 重度({probability_severe:.4f})")
                        
                        # 创建结果概率字典
                        result_probabilities = {
                            'normal': probability_normal,
                            'mild': probability_mild,
                            'severe': probability_severe
                        }
                        
                        # 更新此患者的远程执行状态为完成，同时缓存结果
                        _remote_executions[patient_id] = (current_time, 'completed', result_probabilities)
                        
                        print(f"执行ID: {execution_id} 的远程模型完成，结果: {result_probabilities}")
                        
                        # 立即关闭SSH连接
                        if client:
                            client.close()
                            client = None
                        
                        return result_probabilities
                
                print("无法从远程输出中解析出结果概率")
                # 更新此患者的远程执行状态为完成，但没有有效结果
                _remote_executions[patient_id] = (current_time, 'completed', None)
            
        except paramiko.AuthenticationException:
            print("SSH认证失败: 用户名或密码错误")
            _remote_executions[patient_id] = (current_time, 'error', None)
        except paramiko.SSHException as e:
            print(f"SSH连接错误: {str(e)}")
            _remote_executions[patient_id] = (current_time, 'error', None)
        except socket.timeout:
            print("SSH连接超时，请检查网络或服务器状态")
            _remote_executions[patient_id] = (current_time, 'error', None)
        except socket.error as e:
            print(f"Socket错误: {str(e)}")
            _remote_executions[patient_id] = (current_time, 'error', None)
        except Exception as e:
            print(f"远程执行过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            _remote_executions[patient_id] = (current_time, 'error', None)
        
    except Exception as e:
        print(f"运行远程模型时发生错误: {str(e)}")
        # 更新状态为错误
        if patient and hasattr(patient, 'patient_id'):
            _remote_executions[patient.patient_id] = (current_time, 'error', None)
    finally:
        # 确保连接被关闭
        if client:
            try:
                client.close()
                print("SSH连接已关闭")
            except:
                pass
    
    return result_probabilities

# 解析模型输出结果
def parse_model_results(patient_id, remote_result=None):
    """
    解析模型输出的结果，优先使用远程运行的结果
    
    参数:
    - patient_id: 患者ID
    - remote_result: 远程运行得到的结果，如果提供则优先使用
    
    返回:
    - 概率字典 {'normal': x, 'mild': y, 'severe': z}
    """
    # 如果提供了远程运行结果，直接使用
    if remote_result is not None:
        print(f"使用远程运行得到的结果: {remote_result}")
        return remote_result
    
    # 尝试从多个可能的位置查找结果文件
    possible_paths = [
        f'Demo_result_{patient_id}.txt',  # 项目根目录
    ]
    
    for result_file in possible_paths:
        try:
            if os.path.exists(result_file):
                print(f"找到结果文件: {result_file}")
                import pandas as pd
                df = pd.read_csv(result_file, sep='\t')
                if len(df) > 0:
                    # 读取三个概率值
                    probability_normal = float(df['Control'].iloc[0])     # 对照组/无肺炎
                    probability_mild = float(df['Regular or Mild'].iloc[0])  # 轻度肺炎
                    probability_severe = float(df['Critically ill or Severe'].iloc[0])  # 重度肺炎
                    
                    print(f"读取到患者{patient_id}的预测结果: 正常({probability_normal:.4f}), 轻度({probability_mild:.4f}), 重度({probability_severe:.4f})")
                    
                    return {
                        'normal': probability_normal,
                        'mild': probability_mild,
                        'severe': probability_severe
                    }
        except Exception as e:
            print(f"尝试读取{result_file}时出错: {str(e)}")
    
    print(f"未找到患者{patient_id}的预测结果文件，将使用默认值")
    
    # 如果无法读取结果文件，则返回默认值（以对照组为主）
    return {
        'normal': 0.9781,  # 对照组/无肺炎
        'mild': 0.0208,    # 轻度肺炎
        'severe': 0.0011   # 重度肺炎
    }

# 检查是否已经存在最近创建的诊断记录
def check_recent_diagnosis(patient_id, time_threshold_seconds=30):
    """
    检查是否在最近时间内已经为该患者创建了诊断记录
    
    参数:
    - patient_id: 患者ID
    - time_threshold_seconds: 时间阈值（秒），默认30秒
    
    返回:
    - 如果存在返回记录对象，否则返回None
    """
    try:
        from django.utils import timezone
        import pytz
        
        # 获取当前时间，确保使用时区感知的datetime
        now = timezone.now()
        
        # 查询最近的诊断记录
        recent_diagnoses = DiagnosisResult.objects.filter(
            patient_id=patient_id,
            created_at__gte=now - timedelta(seconds=time_threshold_seconds)
        ).order_by('-created_at')
        
        if recent_diagnoses.exists():
            return recent_diagnoses.first()
        
    except Exception as e:
        print(f"检查最近诊断记录时出错: {str(e)}")
    
    return None

# 处理CT图像上传视图
def process_ct(request):
    if request.method == 'POST':
        # 获取表单数据
        patient_id = request.POST.get('patient_id')
        
        if not patient_id:
            print("请求中未提供患者ID")
            return JsonResponse({
                'success': False,
                'error': '请选择患者'
            })
        
        print(f"接收到患者 {patient_id} 的诊断请求")
        
        try:
            from django.db import transaction
            
            # 检查最近120秒内是否已经创建了诊断记录
            recent_diagnosis = check_recent_diagnosis(patient_id, 120)
            if recent_diagnosis:
                # 如果存在最近的诊断记录，使用该记录的结果
                print(f"发现患者 {patient_id} 最近的诊断记录（ID: {recent_diagnosis.id}），直接返回")
                return JsonResponse({
                    'success': True,
                    'diagnosis_id': recent_diagnosis.id,
                    'message': '使用现有的诊断结果',
                    'result_type': recent_diagnosis.result_type,
                    'confidence': recent_diagnosis.confidence * 100,
                    'probabilities': {
                        'normal': recent_diagnosis.probability_normal * 100,
                        'mild': recent_diagnosis.probability_mild * 100,
                        'severe': recent_diagnosis.probability_severe * 100
                    }
                })
            
            # 获取患者信息
            patient = get_object_or_404(Patient, patient_id=patient_id)
            
            # 上传的CT图像（可选）
            ct_image = None
            if 'ct_image' in request.FILES:
                ct_image = request.FILES['ct_image']
                print(f"成功获取CT图像: {ct_image.name}, 大小: {ct_image.size} 字节")
            else:
                print("未上传CT图像")
            
            # 检查是否有正在进行的远程执行
            global _remote_executions
            current_time = datetime.now()
            
            # 如果有进行中的执行，不要开始新的执行
            if patient_id in _remote_executions:
                timestamp, status, _ = _remote_executions[patient_id]
                if status == 'running' and (current_time - timestamp).total_seconds() < 180:  # 3分钟内
                    print(f"患者 {patient_id} 有正在进行的远程执行，将等待结果")
                    
                    # 使用一个更长的超时时间等待结果
                    print(f"等待患者 {patient_id} 的远程执行结果，最多等待180秒...")
                    probabilities = wait_for_remote_result(patient_id, timeout=180, polling_interval=3)
                    
                    if probabilities:
                        print(f"成功获取到患者 {patient_id} 的远程执行结果: {probabilities}")
                    else:
                        print(f"等待超时，未能获取患者 {patient_id} 的远程执行结果")
                        return JsonResponse({
                            'success': False,
                            'message': '远程执行超时，请稍后重试',
                            'status': 'timeout'
                        })
                else:
                    # 如果状态不是running或者已经超过3分钟，重置执行状态
                    print(f"重置患者 {patient_id} 的远程执行状态")
            
            # 如果没有获取到结果，启动新的远程执行
            if 'probabilities' not in locals() or probabilities is None:
                print(f"为患者 {patient_id} 启动新的远程执行")
                
                # 标记执行状态为running
                _remote_executions[patient_id] = (current_time, 'running', None)
                
                # 执行远程模型并等待结果
                probabilities = run_remote_model(None, patient, patient.clinical_features, None, False)
                
                # 如果仍然没有结果，再等待一次
                if probabilities is None:
                    print(f"首次执行未获取结果，再次等待患者 {patient_id} 的远程执行结果...")
                    probabilities = wait_for_remote_result(patient_id, timeout=120, polling_interval=3)
                
                # 最终验证是否有结果
                if probabilities is None:
                    print(f"多次尝试后仍未获取到患者 {patient_id} 的远程执行结果，返回错误")
                    return JsonResponse({
                        'success': False,
                        'message': '无法获取远程执行结果，请稍后重试',
                        'status': 'failed'
                    })
            
            # 确定最大概率所对应的类型
            max_prob_type = max(probabilities, key=probabilities.get)
            max_prob = probabilities[max_prob_type]
            
            # 映射回前端使用的类型
            result_type_map = {
                'normal': 'Normal',
                'mild': 'Mild',
                'severe': 'Severe'
            }
            result_type = result_type_map[max_prob_type]
            
            # 使用事务创建诊断结果记录
            with transaction.atomic():
                # 再次检查最近的诊断记录（可能在等待期间由其他请求创建）
                recent_check = check_recent_diagnosis(patient_id, 10)
                if recent_check:
                    print(f"发现患者 {patient_id} 在等待期间创建的诊断记录（ID: {recent_check.id}），直接返回")
                    return JsonResponse({
                        'success': True,
                        'diagnosis_id': recent_check.id,
                        'message': '使用等待期间创建的诊断结果',
                        'result_type': recent_check.result_type,
                        'confidence': recent_check.confidence * 100,
                        'probabilities': {
                            'normal': recent_check.probability_normal * 100,
                            'mild': recent_check.probability_mild * 100,
                            'severe': recent_check.probability_severe * 100
                        }
                    })
                
                # 创建诊断结果记录，使用真实的远程执行结果
                # 添加用户身份调试信息
                print(f"当前用户: {request.user}, 是否匿名: {request.user.is_anonymous}")
                if not request.user.is_anonymous:
                    print(f"用户ID: {request.user.id}, 用户名: {request.user.username}")
                    if hasattr(request.user, 'doctor'):
                        print(f"关联的医生ID: {request.user.doctor.doctor_id}")
                
                # 获取当前登录的医生信息
                doctor = None
                if not request.user.is_anonymous and hasattr(request.user, 'doctor'):
                    doctor = request.user.doctor
                else:
                    # 尝试从会话中获取医生ID
                    doctor_id = request.session.get('doctor_id')
                    if doctor_id:
                        try:
                            doctor = Doctor.objects.get(doctor_id=doctor_id)
                            print(f"从会话中恢复医生信息，ID: {doctor_id}")
                        except Doctor.DoesNotExist:
                            print(f"无法找到ID为{doctor_id}的医生")
                    
                    # 如果仍然无法获取医生信息，使用ID为1的医生
                    if not doctor:
                        doctor = get_object_or_404(Doctor, doctor_id=1)
                        print(f"使用默认医生，ID: 1")
                
                diagnosis_result = DiagnosisResult.objects.create(
                    patient=patient,
                    result_type=result_type,
                    confidence=max_prob,
                    probability_normal=probabilities['normal'],
                    probability_mild=probabilities['mild'],
                    probability_severe=probabilities['severe'],
                    ct_image=ct_image,
                    notes=request.POST.get('notes', ''),
                    created_by=doctor
                )
                
                print(f"成功创建患者 {patient_id} 的诊断结果记录，ID: {diagnosis_result.id}，结果: {result_type}")
            
            # 返回统一格式的响应
            return JsonResponse({
                'success': True,
                'diagnosis_id': diagnosis_result.id,
                'result_type': result_type,
                'confidence': max_prob * 100,
                'probabilities': {
                    'normal': probabilities['normal'] * 100,
                    'mild': probabilities['mild'] * 100,
                    'severe': probabilities['severe'] * 100
                },
                'message': '诊断完成'
            })
        
        except Exception as e:
            print(f"处理CT图像过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'诊断过程发生错误: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': '仅支持POST请求'
    })

# 诊断结果视图
def diagnosis_result(request, diagnosis_id):
    # 获取诊断结果记录
    diagnosis = get_object_or_404(DiagnosisResult, id=diagnosis_id)
    
    return render(request, 'diagnosis/diagnosis_result.html', {
        'diagnosis': diagnosis,
    })

# 诊断历史记录视图
def diagnosis_history(request):
    # 获取搜索参数
    search_query = request.GET.get('search_query', '')
    result_type = request.GET.get('result_type', '')
    date_range = request.GET.get('date_range', '')
    
    # 初始查询：获取所有诊断记录
    diagnosis_results = DiagnosisResult.objects.all()
    
    # 应用搜索过滤
    if search_query:
        # 搜索患者ID或姓名
        diagnosis_results = diagnosis_results.filter(
            Q(patient__patient_id__icontains=search_query) | 
            Q(patient__name__icontains=search_query)
        )
    
    if result_type:
        # 按诊断结果类型过滤
        diagnosis_results = diagnosis_results.filter(result_type=result_type)
    
    if date_range:
        # 按日期范围过滤
        from datetime import datetime, timedelta
        now = datetime.now()
        
        if date_range == 'today':
            # 今天
            diagnosis_results = diagnosis_results.filter(created_at__date=now.date())
        elif date_range == 'week':
            # 最近一周
            one_week_ago = now - timedelta(days=7)
            diagnosis_results = diagnosis_results.filter(created_at__gte=one_week_ago)
        elif date_range == 'month':
            # 最近一个月
            one_month_ago = now - timedelta(days=30)
            diagnosis_results = diagnosis_results.filter(created_at__gte=one_month_ago)
    
    # 按创建时间倒序排序
    diagnosis_results = diagnosis_results.order_by('-created_at')
    
    # 统计各类型诊断结果的数量
    total_count = diagnosis_results.count()
    normal_count = diagnosis_results.filter(result_type='Normal').count()
    mild_count = diagnosis_results.filter(result_type='Mild').count()
    severe_count = diagnosis_results.filter(result_type='Severe').count()
    
    return render(request, 'diagnosis/diagnosis_history.html', {
        'diagnosis_results': diagnosis_results,
        'total_count': total_count,
        'normal_count': normal_count,
        'mild_count': mild_count,
        'severe_count': severe_count,
        'search_query': search_query,
        'result_type': result_type,
        'date_range': date_range
    })

# AJAX接口：获取患者信息
def get_patient_info(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    # 获取患者的临床特征数据
    clinical_features = None
    if hasattr(patient, 'clinical_features') and patient.clinical_features:
        cf = patient.clinical_features
        clinical_features = {
            # 血液常规
            'wbc': cf.WBC,
            'rbc': cf.RBC,
            'hgb': cf.HGB,
            'hct': cf.HCT,
            'plt': cf.PLT,
            # 炎症指标
            'crp': cf.CRP,
            'esr': cf.ESR,
            'pct': cf.PCT,
            # 肝肾功能
            'alt': cf.ALT,
            'ast': cf.AST,
            'crea': cf.CREA,
            # 免疫相关
            'cd4': cf.CD4,
            'cd8': cf.CD8,
            'il6': cf.IL_6,
        }
    
    # 构建响应数据
    data = {
        'id': patient.patient_id,
        'name': patient.name,
        'gender': patient.gender,
        'age': patient.get_age(),
        'contact': patient.phone,
        'clinical_features': clinical_features,
    }
    
    return JsonResponse(data)

# AJAX接口：执行诊断
@csrf_exempt
def ajax_diagnose(request):
    """AJAX接口：执行诊断"""
    if request.method == 'POST':
        try:
            import threading
            from django.db import transaction
            
            data = json.loads(request.body)
            patient_id = data.get('patient_id')

            if not patient_id:
                return JsonResponse({'success': False, 'error': '缺少患者ID'})
            
            print(f"接收到患者 {patient_id} 的AJAX诊断请求")

            # 检查最近的诊断记录
            recent_diagnosis = check_recent_diagnosis(patient_id, 120)
            if recent_diagnosis:
                # 如果存在最近的诊断记录，使用该记录的结果
                print(f"发现患者 {patient_id} 的最近诊断记录，ID: {recent_diagnosis.id}，跳过重复创建")
                return JsonResponse({
                    'success': True,
                    'diagnosis_id': recent_diagnosis.id,
                    'result_type': recent_diagnosis.result_type,
                    'confidence': recent_diagnosis.confidence * 100,  # 转换为百分比
                    'probabilities': {
                        'normal': recent_diagnosis.probability_normal * 100,
                        'mild': recent_diagnosis.probability_mild * 100,
                        'severe': recent_diagnosis.probability_severe * 100
                    },
                    'message': '使用现有的诊断结果'
                })
            
            # 获取患者信息
            try:
                patient = Patient.objects.get(patient_id=patient_id)
                clinical_features = patient.clinical_features
            except Patient.DoesNotExist:
                print(f"找不到ID为{patient_id}的患者")
                return JsonResponse({'success': False, 'error': f'找不到ID为{patient_id}的患者'})
            except Exception as e:
                print(f"获取患者数据失败: {str(e)}")
                return JsonResponse({'success': False, 'error': f'获取患者数据失败: {str(e)}'})
            
            # 检查此患者是否正在执行远程诊断
            global _remote_executions
            current_time = datetime.now()
            
            if patient_id in _remote_executions:
                timestamp, status, cached_result = _remote_executions[patient_id]
                
                # 如果已有已完成的结果且不超过10分钟，直接使用缓存的结果
                if status == 'completed' and cached_result is not None and (current_time - timestamp).total_seconds() < 600:
                    print(f"患者 {patient_id} 已有缓存的远程执行结果，将直接使用")
                    probabilities = cached_result
                    
                    # 确定最大概率所对应的类型
                    max_prob_type = max(probabilities, key=probabilities.get)
                    max_prob = probabilities[max_prob_type]
                    
                    # 映射回前端使用的类型
                    result_type_map = {
                        'normal': 'Normal',
                        'mild': 'Mild',
                        'severe': 'Severe'
                    }
                    result_type = result_type_map[max_prob_type]
                    
                    # 使用事务创建诊断结果记录
                    with transaction.atomic():
                        # 再次检查最近的诊断记录（防止并发）
                        recent_check = check_recent_diagnosis(patient_id, 5)
                        if recent_check:
                            print(f"发现患者 {patient_id} 的最近诊断记录，ID: {recent_check.id}，使用该记录")
                            return JsonResponse({
                                'success': True,
                                'diagnosis_id': recent_check.id,
                                'result_type': recent_check.result_type,
                                'confidence': recent_check.confidence * 100,
                                'probabilities': {
                                    'normal': recent_check.probability_normal * 100,
                                    'mild': recent_check.probability_mild * 100,
                                    'severe': recent_check.probability_severe * 100
                                },
                                'message': '使用已创建的诊断结果'
                            })
                        
                        # 创建诊断结果
                        diagnosis_result = DiagnosisResult.objects.create(
                            patient=patient,
                            result_type=result_type,
                            confidence=max_prob,
                            probability_normal=probabilities['normal'],
                            probability_mild=probabilities['mild'],
                            probability_severe=probabilities['severe'],
                            notes=data.get('notes', ''),
                            created_by=request.user.doctor if not request.user.is_anonymous else get_object_or_404(Doctor, doctor_id=1)  # 未登录时使用ID为1的医生
                        )
                        
                        print(f"成功从缓存创建患者 {patient_id} 的诊断结果记录，ID: {diagnosis_result.id}")
                        
                        return JsonResponse({
                            'success': True,
                            'diagnosis_id': diagnosis_result.id,
                            'result_type': result_type,
                            'confidence': max_prob * 100,
                            'probabilities': {
                                'normal': probabilities['normal'] * 100,
                                'mild': probabilities['mild'] * 100,
                                'severe': probabilities['severe'] * 100
                            },
                            'message': '诊断完成（使用缓存结果）'
                        })
                
                # 如果正在执行中且不超过3分钟，等待结果
                elif status == 'running' and (current_time - timestamp).total_seconds() < 180:
                    print(f"患者 {patient_id} 已有正在进行的远程执行任务，将等待结果")
                    
                    # 等待结果最多60秒
                    probabilities = wait_for_remote_result(patient_id, timeout=60, polling_interval=3)
                    
                    if probabilities:
                        print(f"成功获取到患者 {patient_id} 的远程执行结果: {probabilities}")
                    else:
                        print(f"等待超时，未能获取患者 {patient_id} 的远程执行结果")
                        return JsonResponse({
                            'success': False,
                            'message': '远程执行超时，请稍后重试',
                            'status': 'timeout'
                        })
            
            # 如果没有获取到结果，或者没有正在执行的任务，启动新的远程执行
            if 'probabilities' not in locals() or probabilities is None:
                print(f"为患者 {patient_id} 启动新的远程执行")
                
                # 标记执行状态为running
                _remote_executions[patient_id] = (current_time, 'running', None)
                
                # 执行远程模型并等待结果
                probabilities = run_remote_model(None, patient, clinical_features, None, False)
                
                # 如果仍然没有结果，再等待一次
                if probabilities is None:
                    print(f"首次执行未获取结果，再次等待患者 {patient_id} 的远程执行结果...")
                    probabilities = wait_for_remote_result(patient_id, timeout=90, polling_interval=3)
                
                # 最终验证是否有结果
                if probabilities is None:
                    print(f"多次尝试后仍未获取到患者 {patient_id} 的远程执行结果，返回错误")
                    return JsonResponse({
                        'success': False,
                        'message': '无法获取远程执行结果，请稍后重试',
                        'status': 'failed'
                    })
            
            # 确定最大概率所对应的类型
            max_prob_type = max(probabilities, key=probabilities.get)
            max_prob = probabilities[max_prob_type]
            
            # 映射回前端使用的类型
            result_type_map = {
                'normal': 'Normal',
                'mild': 'Mild',
                'severe': 'Severe'
            }
            result_type = result_type_map[max_prob_type]
            
            # 使用事务创建诊断结果记录
            with transaction.atomic():
                # 再次检查最近的诊断记录（可能在等待期间由其他请求创建）
                recent_check = check_recent_diagnosis(patient_id, 10)
                if recent_check:
                    print(f"发现患者 {patient_id} 在等待期间创建的诊断记录（ID: {recent_check.id}），直接返回")
                    return JsonResponse({
                        'success': True,
                        'diagnosis_id': recent_check.id,
                        'message': '使用等待期间创建的诊断结果',
                        'result_type': recent_check.result_type,
                        'confidence': recent_check.confidence * 100,
                        'probabilities': {
                            'normal': recent_check.probability_normal * 100,
                            'mild': recent_check.probability_mild * 100,
                            'severe': recent_check.probability_severe * 100
                        }
                    })
                
                # 创建诊断结果记录，使用真实的远程执行结果
                # 添加用户身份调试信息
                print(f"当前用户: {request.user}, 是否匿名: {request.user.is_anonymous}")
                if not request.user.is_anonymous:
                    print(f"用户ID: {request.user.id}, 用户名: {request.user.username}")
                    if hasattr(request.user, 'doctor'):
                        print(f"关联的医生ID: {request.user.doctor.doctor_id}")
                
                # 获取当前登录的医生信息
                doctor = None
                if not request.user.is_anonymous and hasattr(request.user, 'doctor'):
                    doctor = request.user.doctor
                else:
                    # 尝试从会话中获取医生ID
                    doctor_id = request.session.get('doctor_id')
                    if doctor_id:
                        try:
                            doctor = Doctor.objects.get(doctor_id=doctor_id)
                            print(f"从会话中恢复医生信息，ID: {doctor_id}")
                        except Doctor.DoesNotExist:
                            print(f"无法找到ID为{doctor_id}的医生")
                    
                    # 如果仍然无法获取医生信息，使用ID为1的医生
                    if not doctor:
                        doctor = get_object_or_404(Doctor, doctor_id=1)
                        print(f"使用默认医生，ID: 1")
                
                # 创建诊断结果
                diagnosis_result = DiagnosisResult.objects.create(
                    patient=patient,
                    result_type=result_type,
                    confidence=max_prob,
                    probability_normal=probabilities['normal'],
                    probability_mild=probabilities['mild'],
                    probability_severe=probabilities['severe'],
                    notes=data.get('notes', ''),
                    created_by=doctor
                )
                
                print(f"成功创建患者 {patient_id} 的诊断结果记录，ID: {diagnosis_result.id}")
                
                return JsonResponse({
                    'success': True,
                    'diagnosis_id': diagnosis_result.id,
                    'result_type': result_type,
                    'confidence': max_prob * 100,
                    'probabilities': {
                        'normal': probabilities['normal'] * 100,
                        'mild': probabilities['mild'] * 100,
                        'severe': probabilities['severe'] * 100
                    },
                    'message': '诊断完成'
                })

        except Exception as e:
            print(f"诊断过程发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': '仅支持POST请求'})

# 直接运行远程模型（不需要上传CT图像）
@csrf_exempt
def run_remote_diagnosis(request):
    """运行远程模型诊断，可直接从前端调用"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '仅支持POST请求'}, status=405)
    
    try:
        # 解析请求体
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return JsonResponse({'status': 'error', 'message': '未提供患者ID'}, status=400)
        
        # 获取患者对象
        try:
            patient = Patient.objects.get(patient_id=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'未找到ID为{patient_id}的患者'}, status=404)
        
        # 直接运行远程模型
        run_remote_model(patient=patient, from_api=True)
        
        # 直接返回成功响应
        return JsonResponse({
            'status': 'success',
            'message': '模型诊断请求已提交',
            'data': {
                'patient_id': patient_id,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': '无效的JSON数据'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500) 