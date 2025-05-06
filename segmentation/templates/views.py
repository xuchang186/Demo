from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import uuid
from django.conf import settings
from diagnosis.models import DiagnosisResult
from django.db.models import Q
from .models import SegmentationResult
import paramiko
import tempfile
from pathlib import Path
import time
import shutil
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
import requests
from patient_records.models import Patient, Doctor

# 分割首页
def segmentation_home(request):
    # 查询诊断结果为重度肺炎(Severe)的患者
    # 获取搜索参数
    search_id = request.GET.get('search_id', '')
    search_name = request.GET.get('search_name', '')
    search_date = request.GET.get('search_date', '')
    
    # 构建基本查询：只查询结果为重度肺炎的记录
    severe_diagnoses = DiagnosisResult.objects.filter(result_type='Severe')
    
    # 应用搜索过滤
    if search_id:
        severe_diagnoses = severe_diagnoses.filter(patient__patient_id=search_id)
    if search_name:
        severe_diagnoses = severe_diagnoses.filter(patient__name__icontains=search_name)
    if search_date:
        severe_diagnoses = severe_diagnoses.filter(created_at__date=search_date)
    
    # 按创建时间倒序排序，限制最多显示10条记录
    severe_diagnoses = severe_diagnoses.order_by('-created_at')[:10]
    
    # 传递给模板
    return render(request, 'segmentation/segmentation_home.html', {
        'title': '感染区域分割',
        'severe_diagnoses': severe_diagnoses,
        'patients_count': severe_diagnoses.count(),
    })

# 上传X光图像
def upload_xray(request, patient_id=None):
    # 如果指定了患者ID，获取该患者信息
    patient = None
    diagnosis = None
    if patient_id:
        from patient_records.models import Patient
        patient = get_object_or_404(Patient, patient_id=patient_id)
        
        # 获取患者最新的重度肺炎诊断结果
        diagnosis = DiagnosisResult.objects.filter(
            patient=patient,
            result_type='Severe'
        ).order_by('-created_at').first()
    
    return render(request, 'segmentation/upload_xray.html', {
        'title': '上传X光图像',
        'patient': patient,
        'diagnosis': diagnosis,
    })

# 远程执行分割任务
def execute_remote_segmentation(xray_image_path, prompt_text, image_filename):
    """
    通过SSH连接远程服务器，执行run.py脚本进行图像分割
    
    Args:
        xray_image_path: 本地X光图像路径
        prompt_text: 医生输入的分割提示文本
        image_filename: 图像文件名
        
    Returns:
        tuple: (成功与否, 结果消息, 结果图像本地路径)
    """
    try:
        # 远程服务器信息
        hostname = "202.197.33.114"
        port = 223
        username = "xuchang"
        password = "1"
        
        # 远程工作目录和结果目录
        remote_work_dir = "/data8t/xuchang/PycharmProjects/LanGuideMedSeg-MICCAI2023"
        remote_image_path = f"{remote_work_dir}/{image_filename}"
        
        # 指定Python环境激活命令，与diagnosis/views.py中的方法相同
        python_env = "source /data8t/xuchang/anaconda3/etc/profile.d/conda.sh && conda activate lgms"
        
        # 创建SSH客户端
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 连接到远程服务器
        ssh_client.connect(
            hostname=hostname, 
            port=port, 
            username=username, 
            password=password,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        
        # 创建SFTP客户端
        sftp_client = ssh_client.open_sftp()
        
        # 上传X光图像到远程服务器
        sftp_client.put(xray_image_path, remote_image_path)
        
        # 执行分割命令
        # 注意：转义提示文本中的引号，防止命令解析错误
        escaped_prompt_text = prompt_text.replace('"', '\\"')
        command = f'{python_env} && cd {remote_work_dir} && python run.py --image {image_filename} --prompt "{escaped_prompt_text}"'
        
        print(f"执行远程命令: {command}")
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=180)  # 增加超时时间到180秒
        
        # 读取输出流和错误流，以便记录日志
        stdout_str = stdout.read().decode('utf-8', errors='ignore')
        stderr_str = stderr.read().decode('utf-8', errors='ignore')
        exit_status = stdout.channel.recv_exit_status()  # 等待命令执行完成
        
        print(f"远程执行命令完成，退出状态: {exit_status}")
        print(f"标准输出: {stdout_str}")
        if stderr_str:
            print(f"标准错误: {stderr_str}")
        
        if exit_status != 0:
            return False, f"远程执行失败: {stderr_str}", None
        
        # 等待结果生成（增加等待时间）
        time.sleep(10)
        
        # 使用正确的分割结果图像命名规则：在文件名前添加segmentation_前缀
        result_filename = f"segmentation_{image_filename}"
        remote_result_path = f"{remote_work_dir}/{result_filename}"
        
        # 创建临时目录保存结果
        temp_dir = tempfile.mkdtemp()
        local_result_path = os.path.join(temp_dir, result_filename)
        
        # 从远程服务器下载结果图像
        try:
            sftp_client.get(remote_result_path, local_result_path)
            print(f"成功下载分割结果图像: {local_result_path}")
        except FileNotFoundError:
            # 如果找不到结果文件，尝试查找其他可能的格式
            print(f"远程服务器上未找到默认格式的结果图像 {result_filename}，尝试其他格式...")
            
            # 列出远程工作目录中的文件
            try:
                remote_files = sftp_client.listdir(remote_work_dir)
                # 尝试不同的命名规则匹配
                potential_patterns = [
                    f"segmentation_{image_filename}",  # segmentation_前缀
                    f"segmentation_{image_filename.split('.')[0]}.png",  # segmentation_前缀,固定png扩展名
                    f"{image_filename.split('.')[0]}_result.png",  # _result后缀,固定png扩展名
                    f"{image_filename.split('.')[0]}_segmentation.png",  # _segmentation后缀
                ]
                
                potential_results = []
                for pattern in potential_patterns:
                    if pattern in remote_files:
                        potential_results.append(pattern)
                
                # 如果没找到，尝试更宽松的匹配
                if not potential_results:
                    for file in remote_files:
                        # 检查文件名是否包含原图像名(不含扩展名)，以及是否包含segmentation或result关键词
                        base_name = image_filename.split('.')[0]
                        if base_name in file and ('segmentation' in file.lower() or 'result' in file.lower()):
                            potential_results.append(file)
                
                if potential_results:
                    # 找到可能的结果文件，下载第一个
                    result_filename = potential_results[0]
                    remote_result_path = f"{remote_work_dir}/{result_filename}"
                    local_result_path = os.path.join(temp_dir, result_filename)
                    
                    print(f"找到可能的结果文件: {result_filename}，尝试下载...")
                    sftp_client.get(remote_result_path, local_result_path)
                    print(f"成功下载可能的结果图像: {local_result_path}")
                else:
                    print("未找到任何可能的结果图像文件")
                    return False, "远程服务器上未找到任何结果图像文件", None
            except Exception as e:
                print(f"尝试查找其他结果格式时出错: {str(e)}")
                return False, f"查找结果图像失败: {str(e)}", None
        
        # 关闭连接
        sftp_client.close()
        ssh_client.close()
        
        return True, "分割成功", local_result_path
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"SSH连接或命令执行出错: {str(e)}", None

# 处理X光图像上传的API
@csrf_exempt
def api_upload_xray(request):
    if request.method == 'POST':
        # 检查是否有文件上传
        if 'xray_image' not in request.FILES:
            return JsonResponse({'error': '未找到上传的文件'}, status=400)
        
        # 获取上传的文件和参数
        xray_image = request.FILES['xray_image']
        patient_id = request.POST.get('patient_id')
        prompt_text = request.POST.get('prompt_text', '')
        
        # 检查文件类型
        if not xray_image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            return JsonResponse({'error': '只支持PNG和JPG格式的图像文件'}, status=400)
        
        if not patient_id:
            return JsonResponse({'error': '缺少患者ID参数'}, status=400)
        
        try:
            # 获取患者信息
            patient = get_object_or_404(Patient, patient_id=patient_id)
            
            # 查找患者的重度肺炎诊断结果
            diagnosis = DiagnosisResult.objects.filter(
                patient=patient,
                result_type='Severe'
            ).order_by('-created_at').first()
            
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
            
            # 创建分割结果记录
            segmentation_result = SegmentationResult.objects.create(
                patient=patient,
                diagnosis=diagnosis,
                xray_image=xray_image,
                prompt_text=prompt_text,
                created_by=doctor
            )
            
            # 保存X光图像到本地临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(xray_image.name)[1]) as temp_file:
                for chunk in xray_image.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            print(f"正在处理图像: {xray_image.name}, 临时文件路径: {temp_file_path}")
            
            # 远程执行分割
            success, message, result_image_path = execute_remote_segmentation(
                temp_file_path, 
                prompt_text, 
                os.path.basename(xray_image.name)
            )
            
            print(f"分割执行结果: 成功={success}, 消息={message}, 结果路径={result_image_path}")
            
            if success and result_image_path:
                # 将结果图像保存到数据库
                result_filename = os.path.basename(result_image_path)
                result_path = os.path.join('segmentation_results', result_filename)
                
                # 确保media目录下有segmentation_results文件夹
                media_path = os.path.join(settings.MEDIA_ROOT, 'segmentation_results')
                os.makedirs(media_path, exist_ok=True)
                
                # 复制结果图像到media目录
                destination_path = os.path.join(media_path, result_filename)
                shutil.copy2(result_image_path, destination_path)
                
                print(f"成功将结果图像复制到: {destination_path}")
                
                # 更新分割结果记录
                from django.core.files.base import ContentFile
                from django.core.files.storage import default_storage
                
                with open(result_image_path, 'rb') as f:
                    content = f.read()
                    rel_path = os.path.join('segmentation_results', time.strftime('%Y/%m/%d'), result_filename)
                    segmentation_result.segmentation_image.save(rel_path, ContentFile(content), save=True)
                
                # 清理临时文件
                os.unlink(temp_file_path)
                shutil.rmtree(os.path.dirname(result_image_path))
                
                # 检查是否是AJAX请求
                is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                
                if is_ajax:
                    # 对于AJAX请求返回JSON响应
                    return JsonResponse({
                        'success': True,
                        'message': '图像上传和分割成功',
                        'filename': xray_image.name,
                        'segmentation_id': segmentation_result.id,
                        'redirect_url': reverse('segmentation:segmentation_result', args=[segmentation_result.id])
                    })
                else:
                    # 对于非AJAX请求直接重定向到结果页面
                    return redirect('segmentation:segmentation_result', segmentation_id=segmentation_result.id)
            else:
                # 分割失败，但仍保留上传记录
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': message,
                        'filename': xray_image.name,
                        'segmentation_id': segmentation_result.id
                    })
                else:
                    from django.contrib import messages
                    messages.error(request, f"分割失败: {message}")
                    return redirect('segmentation:upload_xray')
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'上传过程中出错: {str(e)}'}, status=500)
    
    return JsonResponse({'error': '不支持的请求方法'}, status=405)

# 分割结果页面
def segmentation_result(request, segmentation_id):
    # 从数据库获取分割结果
    segmentation = get_object_or_404(SegmentationResult, id=segmentation_id)
    
    context = {
        'title': '分割结果',
        'segmentation_id': segmentation_id,
        'segmentation': segmentation,
        'patient': segmentation.patient,
        'diagnosis': segmentation.diagnosis
    }
    return render(request, 'segmentation/segmentation_result.html', context)

# 分割历史记录
def segmentation_history(request):
    # 获取查询参数
    patient_id = request.GET.get('patient_id', '')
    date_range = request.GET.get('date_range', '')
    
    # 获取所有分割结果记录，按时间倒序排列
    segmentation_results = SegmentationResult.objects.all().order_by('-created_at')
    
    # 应用过滤条件
    if patient_id:
        segmentation_results = segmentation_results.filter(patient__patient_id=patient_id)
    
    if date_range:
        from datetime import datetime, timedelta
        now = datetime.now()
        if date_range == 'week':
            start_date = now - timedelta(days=7)
            segmentation_results = segmentation_results.filter(created_at__gte=start_date)
        elif date_range == 'month':
            start_date = now - timedelta(days=30)
            segmentation_results = segmentation_results.filter(created_at__gte=start_date)
        elif date_range == 'three_months':
            start_date = now - timedelta(days=90)
            segmentation_results = segmentation_results.filter(created_at__gte=start_date)
    
    # 分页处理
    paginator = Paginator(segmentation_results, 9)  # 每页显示9条记录
    page = request.GET.get('page')
    
    try:
        segmentation_results = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码不是整数，则返回第一页
        segmentation_results = paginator.page(1)
    except EmptyPage:
        # 如果页码超出范围，则返回最后一页
        segmentation_results = paginator.page(paginator.num_pages)
    
    return render(request, 'segmentation/segmentation_history.html', {
        'title': '分割历史记录',
        'segmentation_results': segmentation_results,
        'patient_id': patient_id,
        'date_range': date_range
    })

# 指定患者的分割历史
def patient_segmentation_history(request, patient_id):
    # 获取指定患者
    from patient_records.models import Patient
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    # 获取该患者的所有分割结果记录
    segmentation_results = SegmentationResult.objects.filter(
        patient=patient
    ).order_by('-created_at')
    
    return render(request, 'segmentation/patient_segmentation_history.html', {
        'title': f'患者 {patient.name} 分割历史',
        'patient': patient,
        'segmentation_results': segmentation_results
    })

@csrf_exempt
@require_POST
def deepseek_chat(request):
    """
    与DeepSeek API进行通信的视图函数，处理用户与AI的对话
    """
    try:
        # 解析请求数据
        data = json.loads(request.body)
        system_message = data.get('systemMessage', '')
        user_message = data.get('userMessage', '')
        xray_image_url = data.get('xrayImageUrl', '')
        segmentation_image_url = data.get('segmentationImageUrl', '')
        
        print(f"接收到DeepSeek API请求 - 系统消息长度: {len(system_message)}, 用户消息: {user_message[:50]}...")
        
        # 如果提供了图像URL，将其添加到用户消息中
        if xray_image_url and segmentation_image_url:
            enhanced_user_message = f"""
{user_message}

参考X光原图: {xray_image_url}
参考分割结果图: {segmentation_image_url}
"""
        else:
            enhanced_user_message = user_message
        
        # 设置DeepSeek API的配置
        api_key = "sk-a814e6bb77e24d8ba7a7fd8fc79dcf74"  # 使用提供的API密钥
        endpoint = "https://api.deepseek.com/chat/completions"
        
        # 构建请求数据
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": enhanced_user_message}
            ],
            "stream": False
        }
        
        print(f"发送请求到DeepSeek API: {endpoint}")
        print(f"系统消息: {system_message[:150]}...")
        print(f"增强后的用户消息: {enhanced_user_message[:150]}...")
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 发送请求到DeepSeek API
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        print(f"DeepSeek API响应状态码: {response.status_code}")
        
        # 检查请求是否成功
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return JsonResponse({"response": ai_response})
        else:
            # 请求失败，返回错误信息
            error_detail = response.text
            print(f"DeepSeek API请求失败 - 状态码: {response.status_code}, 详情: {error_detail}")
            return JsonResponse({
                "error": f"API请求失败，状态码: {response.status_code}",
                "detail": error_detail
            }, status=500)
            
    except requests.exceptions.Timeout:
        print("DeepSeek API请求超时")
        return JsonResponse({"error": "请求超时，请稍后再试"}, status=504)
    except requests.exceptions.ConnectionError:
        print("DeepSeek API连接错误")
        return JsonResponse({"error": "无法连接到DeepSeek API服务"}, status=502)
    except Exception as e:
        # 捕获并返回任何异常
        import traceback
        error_trace = traceback.format_exc()
        print(f"DeepSeek API请求异常: {str(e)}\n{error_trace}")
        return JsonResponse({"error": str(e)}, status=500) 