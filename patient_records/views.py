from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
import re
from .models import Patient, Doctor, ClinicalFeature
import os
import csv
import logging
from django.contrib.auth.decorators import login_required
import random
import string
from django.conf import settings

# 获取logger
logger = logging.getLogger(__name__)

# 登录视图
def login_view(request):
    # 如果用户已登录，重定向到首页
    if request.session.get('doctor_id'):
        return redirect('home')
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        password = request.POST.get('password')
        
        # 验证输入
        if not doctor_id or not password:
            messages.error(request, '请输入医生ID和密码')
            return render(request, 'login.html')
        
        try:
            doctor = Doctor.objects.get(doctor_id=doctor_id)
            
            # 验证密码
            if check_password(password, doctor.password):
                # 更新最后登录时间
                doctor.last_login = timezone.now()
                doctor.save()
                
                # 保存登录状态到session
                request.session['doctor_id'] = str(doctor.doctor_id)
                request.session['doctor_name'] = doctor.full_name
                
                # 重定向到首页
                return redirect('home')
            else:
                messages.error(request, '密码错误')
        except Doctor.DoesNotExist:
            messages.error(request, '医生ID不存在')
        
    return render(request, 'login.html')

# 注册视图
def register(request):
    # 如果用户已登录，重定向到首页
    if request.session.get('doctor_id'):
        return redirect('home')
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # 验证输入
        errors = []
        
        # 验证ID
        if not re.match(r'^\d{10}$', doctor_id):
            errors.append('医生ID必须是10位数字')
        else:
            # 检查ID是否已存在
            if Doctor.objects.filter(doctor_id=doctor_id).exists():
                errors.append('此医生ID已被注册')
        
        # 验证全名
        if not full_name or len(full_name) < 2:
            errors.append('请输入有效的全名')
        
        # 验证邮箱
        try:
            validate_email(email)
            # 检查邮箱是否已存在
            if Doctor.objects.filter(email=email).exists():
                errors.append('此邮箱已被注册')
        except ValidationError:
            errors.append('请输入有效的邮箱地址')
        
        # 验证密码
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{10,}$', password):
            errors.append('密码必须至少10位，且包含大小写字母和数字')
        
        # 验证密码一致性
        if password != confirm_password:
            errors.append('两次输入的密码不一致')
        
        # 如果有错误，显示错误信息
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register.html')
        
        try:
            # 创建医生账号
            doctor = Doctor(
                doctor_id=doctor_id,
                full_name=full_name,
                email=email,
                password=make_password(password),  # 使用Django的密码哈希函数
                created_at=timezone.now()
            )
            doctor.save()
            
            # 保存登录状态到session
            request.session['doctor_id'] = str(doctor.doctor_id)
            request.session['doctor_name'] = doctor.full_name
            
            # 注册成功，重定向到首页
            messages.success(request, '注册成功！')
            return redirect('home')
            
        except Exception as e:
            logger.error(f"注册时出错: {str(e)}", exc_info=True)
            messages.error(request, f'注册过程中发生错误: {str(e)}')
    
    return render(request, 'register.html')

# 注销视图
def logout_view(request):
    # 清除session
    if 'doctor_id' in request.session:
        del request.session['doctor_id']
    if 'doctor_name' in request.session:
        del request.session['doctor_name']
    
    # 重定向到登录页
    return redirect('login')

# 定义登录检查装饰器
def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('doctor_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# 病历列表页
@login_required_custom
def patient_list(request):
    # 获取搜索参数
    search_id = request.GET.get('search_id', '')
    search_name = request.GET.get('search_name', '')
    search_contact = request.GET.get('search_contact', '')
    
    # 初始查询
    patients = Patient.objects.all()
    
    # 应用搜索过滤
    if search_id:
        patients = patients.filter(patient_id=search_id)
    
    if search_name:
        patients = patients.filter(name__icontains=search_name)
    
    if search_contact:
        patients = patients.filter(phone__icontains=search_contact)
    
    # 按创建时间排序
    patients = patients.order_by('-created_at')
    
    return render(request, 'patient_records/patient_list.html', {
        'title': '病历列表', 
        'patients': patients,
        'search_id': search_id,
        'search_name': search_name,
        'search_contact': search_contact
    })

# 新增病历
@login_required_custom
@transaction.atomic
def patient_add(request):
    if request.method == 'POST':
        # 使用事务处理确保数据一致性
        try:
            with transaction.atomic():
                # 获取当前登录的医生
                doctor_id = request.session.get('doctor_id')
                doctor = get_object_or_404(Doctor, doctor_id=doctor_id)
                
                # 获取身份证号，如果为空字符串则设为None
                id_card = request.POST.get('id_card')
                if not id_card or not id_card.strip():
                    id_card = None
                
                # 解析出生日期
                birth_date_str = request.POST.get('birth_date')
                birth_date = None
                try:
                    from datetime import datetime
                    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    messages.error(request, f'无效的出生日期格式: {birth_date_str}')
                    return render(request, 'patient_records/patient_add.html', {'title': '新增患者'})
                
                # 临床特征基本数据
                gender = None
                body_temperature = None
                underlying_diseases = None
                patient_id_from_file = None
                age_from_file = None
                
                # 处理上传的临床特征文件
                if 'clinical_file' in request.FILES:
                    file = request.FILES['clinical_file']
                    logger.debug(f"处理上传的文件: {file.name}")
                    
                    # 检查文件类型
                    if file.name.endswith('.txt') or file.name.endswith('.csv'):
                        # 解析文件内容
                        clinical_data, extracted_data = parse_clinical_file(file)
                        
                        # 记录解析结果
                        logger.debug(f"解析结果: {extracted_data}")
                        
                        # 提取基本数据
                        gender = extracted_data.get('gender')
                        body_temperature = extracted_data.get('body_temperature')
                        underlying_diseases = extracted_data.get('underlying_diseases')
                        patient_id_from_file = extracted_data.get('patient_id')
                        age_from_file = extracted_data.get('age')
                        
                        # 如果没有提取到必要数据，返回错误
                        if not gender or not body_temperature:
                            messages.error(request, '上传的文件缺少必要的临床数据(性别、体温)')
                            return render(request, 'patient_records/patient_add.html', {'title': '新增患者'})
                    else:
                        messages.error(request, '请上传.txt或.csv格式的文件')
                        return render(request, 'patient_records/patient_add.html', {'title': '新增患者'})
                else:
                    messages.error(request, '请上传临床特征文件')
                    return render(request, 'patient_records/patient_add.html', {'title': '新增患者'})
                
                # 创建患者记录
                # 如果从文件中提取到了有效的患者ID，优先使用该ID
                if patient_id_from_file:
                    # 检查该ID是否已存在
                    try:
                        if Patient.objects.filter(patient_id=patient_id_from_file).exists():
                            messages.error(request, f'患者ID {patient_id_from_file} 已存在，请确认后重试')
                            return render(request, 'patient_records/patient_add.html', {'title': '新增患者'})
                        patient = Patient(
                            patient_id=patient_id_from_file,
                            name=request.POST.get('name'),
                            gender=gender,  # 从临床特征文件中获取
                            birth_date=birth_date,
                            id_card=id_card,
                            phone=request.POST.get('phone'),
                            emergency_contact=request.POST.get('emergency_contact'),
                            emergency_phone=request.POST.get('emergency_phone'),
                            created_by=doctor
                        )
                    except ValueError:
                        logger.warning(f"无法使用文件中的ID: {patient_id_from_file}, 将使用自动生成的ID")
                        patient = Patient(
                            name=request.POST.get('name'),
                            gender=gender,  # 从临床特征文件中获取
                            birth_date=birth_date,
                            id_card=id_card,
                            phone=request.POST.get('phone'),
                            emergency_contact=request.POST.get('emergency_contact'),
                            emergency_phone=request.POST.get('emergency_phone'),
                            created_by=doctor
                        )
                else:
                    # 使用自动生成的ID
                    patient = Patient(
                        name=request.POST.get('name'),
                        gender=gender,  # 从临床特征文件中获取
                        birth_date=birth_date,
                        id_card=id_card,
                        phone=request.POST.get('phone'),
                        emergency_contact=request.POST.get('emergency_contact'),
                        emergency_phone=request.POST.get('emergency_phone'),
                        created_by=doctor
                    )
                
                # 保存患者记录
                # 添加时间戳，避免created_at为NULL
                now = timezone.now()
                patient.created_at = now
                patient.updated_at = now
                patient.save()
                logger.debug(f"保存患者记录: ID={patient.patient_id}, 姓名={patient.name}")
                
                # 创建临床特征记录
                clinical_feature = ClinicalFeature(
                    patient=patient,
                    age=str(age_from_file) if age_from_file is not None else calculate_age(patient.birth_date),  # 优先使用文件中的年龄
                    gender=gender,
                    body_temperature=body_temperature,
                    underlying_diseases=underlying_diseases,
                    created_by=doctor,
                    created_at=now,
                    updated_at=now
                )
                
                # 更新其他临床特征
                if clinical_data:
                    for key, value in clinical_data.items():
                        if hasattr(clinical_feature, key) and value is not None:
                            setattr(clinical_feature, key, value)
                
                # 保存临床特征
                clinical_feature.save()
                logger.debug(f"保存临床特征记录: 患者ID={patient.patient_id}")
                
                # 添加成功消息
                messages.success(request, f'患者 {patient.name} 添加成功！')
                
                # 重定向到患者详情页面
                return redirect('patient_records:patient_detail', patient_id=patient.patient_id)
                
        except Exception as e:
            logger.error(f"添加患者时出错: {str(e)}", exc_info=True)
            messages.error(request, f'保存过程中发生错误: {str(e)}')
    
    # GET请求，显示表单
    return render(request, 'patient_records/patient_add.html', {'title': '新增患者'})

# 病历详情页
@login_required_custom
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    return render(request, 'patient_records/patient_detail.html', {
        'title': '病历详情', 
        'patient': patient
    })

# 编辑病历
@login_required_custom
@transaction.atomic
def patient_edit(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 更新患者基本信息
                patient.name = request.POST.get('name', patient.name)
                patient.gender = request.POST.get('gender', patient.gender)
                
                birth_date_str = request.POST.get('birth_date')
                if birth_date_str:
                    try:
                        from datetime import datetime
                        patient.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        messages.error(request, f'无效的出生日期格式: {birth_date_str}')
                        return redirect('patient_records:patient_edit', patient_id=patient_id)
                
                patient.id_card = request.POST.get('id_card', patient.id_card)
                patient.phone = request.POST.get('phone', patient.phone)
                patient.emergency_contact = request.POST.get('emergency_contact', patient.emergency_contact)
                patient.emergency_phone = request.POST.get('emergency_phone', patient.emergency_phone)
                
                # 保存患者信息
                patient.save()
                
                # 更新或创建临床特征信息
                cf, created = ClinicalFeature.objects.get_or_create(patient=patient)
                
                # 更新基本临床特征信息
                cf.age = request.POST.get('age', cf.age)
                cf.body_temperature = request.POST.get('body_temperature', cf.body_temperature)
                cf.underlying_diseases = request.POST.get('underlying_diseases', cf.underlying_diseases)
                
                # 更新其他临床指标
                # 处理常规血液检查指标
                cf.MCHC = request.POST.get('MCHC', cf.MCHC)
                cf.MCH = request.POST.get('MCH', cf.MCH)
                cf.MCV = request.POST.get('MCV', cf.MCV)
                cf.HCT = request.POST.get('HCT', cf.HCT)
                cf.HGB = request.POST.get('HGB', cf.HGB)
                cf.RBC = request.POST.get('RBC', cf.RBC)
                cf.WBC = request.POST.get('WBC', cf.WBC)
                cf.PLT = request.POST.get('PLT', cf.PLT)
                
                # 凝血功能检查指标
                cf.DD = request.POST.get('DD', cf.DD)
                cf.TT = request.POST.get('TT', cf.TT)
                cf.FIB = request.POST.get('FIB', cf.FIB)
                
                # 炎症指标
                cf.ESR = request.POST.get('ESR', cf.ESR)
                cf.CRP = request.POST.get('CRP', cf.CRP)
                cf.PCT = request.POST.get('PCT', cf.PCT)
                
                # 生化检查指标
                cf.ALT = request.POST.get('ALT', cf.ALT)
                cf.AST = request.POST.get('AST', cf.AST)
                cf.ALB = request.POST.get('ALB', cf.ALB)
                cf.GLB = request.POST.get('GLB', cf.GLB)
                cf.TBIL = request.POST.get('TBIL', cf.TBIL)
                cf.BUN = request.POST.get('BUN', cf.BUN)
                cf.CREA = request.POST.get('CREA', cf.CREA)
                
                # 免疫细胞分型
                cf.CD3 = request.POST.get('CD3', cf.CD3)
                cf.CD4 = request.POST.get('CD4', cf.CD4)
                cf.CD8 = request.POST.get('CD8', cf.CD8)
                cf.CD4_CD8 = request.POST.get('CD4_CD8', cf.CD4_CD8)
                
                # 细胞因子
                cf.IL_2 = request.POST.get('IL_2', cf.IL_2)
                cf.IL_4 = request.POST.get('IL_4', cf.IL_4)
                cf.IL_6 = request.POST.get('IL_6', cf.IL_6)
                cf.IL_10 = request.POST.get('IL_10', cf.IL_10)
                cf.TNF = request.POST.get('TNF', cf.TNF)
                cf.IFN = request.POST.get('IFN', cf.IFN)
                
                # 尿常规指标
                cf.URBC = request.POST.get('URBC', cf.URBC)
                cf.UWBC = request.POST.get('UWBC', cf.UWBC)
                
                # 处理表单中的所有字段，这种方式可以处理模型中定义的所有指标
                for key, value in request.POST.items():
                    # 检查该字段是否是临床特征的字段
                    if hasattr(cf, key) and key not in ['patient', 'created_at', 'updated_at', 'created_by']:
                        # 设置字段值，即使value为空字符串也设置
                        setattr(cf, key, value)
                
                # 保存临床特征
                cf.save()
                
                messages.success(request, f'患者 {patient.name} 的信息已成功更新')
                return redirect('patient_records:patient_detail', patient_id=patient.patient_id)
        
        except Exception as e:
            logger.error(f"更新病历时出错: {str(e)}", exc_info=True)
            messages.error(request, f'更新病历时发生错误: {str(e)}')
            return redirect('patient_records:patient_edit', patient_id=patient_id)
    
    return render(request, 'patient_records/patient_edit.html', {
        'title': '编辑病历', 
        'patient': patient
    })

# 删除病历
@login_required_custom
def patient_delete(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    patient.delete()
    return redirect('patient_records:patient_list')

# 添加就诊记录
def add_medical_record(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    return render(request, 'patient_records/add_medical_record.html', {
        'title': '添加就诊记录', 
        'patient': patient
    })

# 计算年龄
def calculate_age(birth_date):
    """
    计算年龄，处理字符串或日期对象类型的birth_date
    """
    today = timezone.now().date()
    
    # 如果birth_date是字符串，尝试将其转换为日期对象
    if isinstance(birth_date, str):
        try:
            # 尝试以YYYY-MM-DD格式解析
            from datetime import datetime
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            # 如果解析失败，返回空字符串或默认值
            logger.error(f"无法解析出生日期: {birth_date}")
            return "未知"
    
    # 计算年龄
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return str(age)

# 解析临床特征文件
def parse_clinical_file(file):
    """
    解析上传的临床特征文件，提取各项指标的值
    支持TXT和CSV格式
    返回：(clinical_data, extracted_data)，其中
    clinical_data：用于数据库字段的数据
    extracted_data：包含性别、体温和基础疾病的原始数据
    """
    clinical_data = {}
    extracted_data = {
        'gender': None,
        'body_temperature': None,
        'underlying_diseases': None,
        'patient_id': None,
        'age': None
    }
    
    try:
        # 读取文件内容
        content = file.read().decode('utf-8')
        logger.debug(f"文件大小: {len(content)} 字节")
        
        # 按行分割
        lines = content.strip().split('\n')
        logger.debug(f"文件行数: {len(lines)}")
        
        # 如果文件行数少于3，无法解析（至少需要标题行、单位行和数据行）
        if len(lines) < 3:
            logger.warning(f"文件行数不足，无法解析: {len(lines)}")
            return clinical_data, extracted_data
        
        # 判断是tab分隔还是csv格式
        if '\t' in lines[0]:
            delimiter = '\t'
            logger.debug("检测到Tab分隔符格式")
        else:
            delimiter = ','
            logger.debug("检测到CSV格式")
        
        # 解析标题行，获取各列的标题
        headers = lines[0].split(delimiter)
        logger.debug(f"解析到的标题: {headers}")
        
        # 获取缩写行（第二行）
        abbreviations = []
        if len(lines) > 1:
            abbreviations = lines[1].split(delimiter)
            logger.debug(f"解析到的缩写: {abbreviations}")
        
        # 找到数据行（通常是第4行，索引为3）
        data_line = None
        for i in range(2, min(6, len(lines))):
            if 'Patient' in lines[i]:
                data_line = lines[i].split(delimiter)
                break
        
        if not data_line:
            logger.warning("未找到患者数据行")
            return clinical_data, extracted_data
        
        logger.debug(f"解析到的数据: {data_line}")
        
        # 将标题和数据映射为字典
        data_dict = {}
        for i, header in enumerate(headers):
            if i < len(data_line):
                data_dict[header.strip()] = data_line[i].strip()
        
        logger.debug(f"标题数据映射: {data_dict}")
        
        # 提取患者ID - 从第一列（通常是"Patient X"）
        if 'Patient' in data_dict:
            patient_id_match = re.search(r'Patient\s+(\d+)', data_dict.get('Patient', ''))
            if patient_id_match:
                try:
                    extracted_data['patient_id'] = int(patient_id_match.group(1))
                    logger.debug(f"提取的患者ID: {extracted_data['patient_id']}")
                except ValueError:
                    logger.warning(f"无法将患者ID转换为整数: {patient_id_match.group(1)}")
            else:
                # 尝试直接从值中提取数字
                numeric_id = re.search(r'(\d+)', data_dict.get('Patient', ''))
                if numeric_id:
                    try:
                        extracted_data['patient_id'] = int(numeric_id.group(1))
                        logger.debug(f"从值中提取的患者ID: {extracted_data['patient_id']}")
                    except ValueError:
                        logger.warning(f"无法将提取的值转换为整数: {numeric_id.group(1)}")
        
        # 直接从数据中提取年龄
        if 'Age' in data_dict:
            age_str = data_dict.get('Age')
            try:
                extracted_data['age'] = int(age_str)
                logger.debug(f"提取的年龄: {extracted_data['age']}")
            except (ValueError, TypeError):
                logger.warning(f"无法解析年龄: {age_str}")
        
        # 直接从映射中提取性别
        extracted_data['gender'] = data_dict.get('Gender', None)
        
        # 提取体温，只保留数值部分
        body_temp = data_dict.get('Body temperature', None)
        if body_temp:
            temp_match = re.search(r'(\d+\.?\d*)', body_temp)
            if temp_match:
                extracted_data['body_temperature'] = float(temp_match.group(1))
                logger.debug(f"提取的体温: {extracted_data['body_temperature']}")
        
        # 直接使用原始基础疾病信息（保持英文）
        extracted_data['underlying_diseases'] = data_dict.get('Underlying diseases', None)
        logger.debug(f"提取的基础疾病: {extracted_data['underlying_diseases']}")
        
        # 创建映射字典：数据表头 -> 模型字段名
        # 先从缩写获取映射关系，因为ClinicalFeature模型中的字段名与缩写相符
        field_mapping = {}
        
        # 基于模型中的字段和文件中的标题创建映射
        model_fields = {
            'MCHC': 'Mean corpuscular hemoglobin concentration',
            'MCH': 'Mean corpuscular hemoglobin',
            'MCV': 'Mean corpuscular volume',
            'HCT': 'Hematocrit',
            'HGB': 'Hemoglobin',
            'RBC': 'Red blood cell',
            'PDW': 'Platelet distribution width',
            'PLCT': 'Plateletcrit',
            'MPV': 'Mean platelet volume',
            'PLT': 'Platelet count',
            'BA': 'Basophil count',
            'EO': 'Eosinophil count',
            'MO': 'Monocyte count',
            'LY': 'Lymphocyte count',
            'NE': 'Neutrophil count',
            'BAP': 'Basophil percent',
            'EOP': 'Eosinophil percent',
            'MOP': 'Monocyte percent',
            'LYP': 'Lymphocyte percent',
            'NEP': 'Neutrophil percent',
            'WBC': 'White blood cell',
            'PLCR': 'Platelet larger cell ratio',
            'RDWSD': 'Standard deviation of red cell volume distribution width',
            'RDWCV': 'Coefficient variation of red cell volume distribution width',
            'DD': 'D-Dimer',
            'TT': 'Thrombin time',
            'FIB': 'Fibrinogen',
            'APTT': 'Activated partial thromboplastin time',
            'INR': 'International normalization ratio',
            'PT': 'Prothrombin time',
            'ESR': 'Erythrocyte sedimentation rate',
            'CRP': 'C-reactive protein',
            'PCT': 'Procalcitonin',
            'ALG': 'Albumin/Globulin ratio',
            'ALB': 'Albumin',
            'ALP': 'Alkaline phosphatase',
            'ALT': 'Alanine aminotransferase',
            'AST': 'Aspartate aminotransferase',
            'BUN': 'Urea nitrogen',
            'CA': 'Calcium',
            'CL': 'Chlorine',
            'CO2': 'Total carbon dioxide',
            'CREA': 'Creatinine',
            'GGT': 'γ-glutamyltransferase',
            'GLB': 'Globulin',
            'K': 'Potassium',
            'MG': 'Magnesium',
            'Na': 'Sodium',
            'PHOS': 'Phosphorus',
            'TBIL': 'Total bilirubin',
            'TP': 'Serum total protein',
            'URIC': 'Uric acid',
            'CHOL': 'Total cholesterol',
            'CK': 'Creatine kinase',
            'HDLC': 'High density lipoprotein cholesterol',
            'LDH': 'Lactate dehydrogenase',
            'TG': 'Triglyceride',
            'AnG': 'Anion gap',
            'DBIL': 'Direct bilirubin',
            'GLU': 'Glucose',
            'LDLC': 'Low density lipoprotein cholesterol',
            'OSM': 'Osmotic pressure',
            'PA': 'Prealbumin',
            'TBA': 'Total bile acids',
            'HBDH': 'α-hydroxybutyrate dehydrogenase',
            'CysC': 'Cystatin C',
            'LAP': 'Leucine aminopeptidase',
            'NT5': '5\'nucleotidase',
            'HC': 'Homocysteine',
            'SAA': 'Serum amyloid protein A',
            'SdLDL': 'Small density low density lipoprotein',
            'CD3': 'CD3+ T cell',
            'CD4': 'CD4+ T cell',
            'CD8': 'CD8+ T cell',
            'BC': 'B lymphocyte',
            'NKC': 'Natural killer cell',
            'IL_2': 'Interleukin-2',
            'IL_4': 'Interleukin-4',
            'IL_6': 'Interleukin-6',
            'IL_10': 'Interleukin-10',
            'TNF': 'TNF-α',
            'IFN': 'IFN-γ',
            'CD4_CD8': 'CD4/CD8 ratio',
            'CHE': 'Choline esterase',
            'SA': 'Sialic acid',
            'C1q': 'Complement C1q',
            'C3': 'Complement C3',
            'AFU': 'α-L-Fucosidase',
            'LPA': 'Lipoprotein A',
            'APOA1': 'Apolipoprotein A1',
            'BNP': 'B-type brain natriuretic peptide precursor',
            'IGM': 'Immunoglobulin M',
            'IGA': 'Immunoglobulin A',
            'IGG': 'Immunoglobulin G',
            'FDP': 'Fibrin/fibrinogen degradation products',
            'C4': 'Complement C4',
            'APOB': 'Apolipoprotein B',
            'HSCRP': 'High-sensitivity C-reactive protein',
            'URBC': 'Red blood cell count',
            'UWBC': 'White blood cell count',
            'WBCC': 'Leukocyte mass',
            'SQEP': 'Squamous epithelial cell',
            'NSEC': 'Non-squamous epithelial cell',
            'HYAL': 'Hyaline cast',
            'UNCC': 'Pathological cast',
            'BYST': 'Yeast',
            'MS_U': 'Viscose rayon',
            'UNCX': 'Unclassified crystal',
            'SG': 'Specific gravity',
            'PH': 'pH',
            'BACT': 'Bacterial count',
            'IBIL': 'Indirect bilirubin',
            'AT_III': 'Antithrombin III',
            'FDG': 'Fungi (1-3)-β-D-glucan',
            'LPS': 'Lipase',
            'U': 'Urea',
            'UALB': 'Urinary albumin',
            'BCF8': 'Blood coagulation factor VIII activity',
            'ASO': 'Anti-streptolysin O',
            'PS': 'Plasma protein S activity',
            'RF': 'Rheumatoid factor',
            'PC': 'Plasma protein C activity',
            'LAC': 'Lactic acid'
        }
        
        # 构建从标题到字段的映射
        for field_abbr, full_name in model_fields.items():
            if full_name in headers:
                field_mapping[full_name] = field_abbr
        
        # 处理所有临床特征数据
        for header, value in data_dict.items():
            # 跳过基本信息，这些已单独处理
            if header in ['Patient', 'Age', 'Gender', 'Body temperature', 'Underlying diseases']:
                continue
                
            if header in field_mapping and value and value.upper() != 'N/A':
                # 获取模型中的字段名
                field_name = field_mapping[header]
                
                # 提取数值部分
                try:
                    # 使用正则表达式提取数值，忽略单位
                    numeric_value = re.search(r'(\d+\.?\d*)', value)
                    if numeric_value:
                        clinical_data[field_name] = numeric_value.group(1)
                        logger.debug(f"提取的特征 {field_name}: {clinical_data[field_name]}")
                    else:
                        # 如果没有数值，直接使用原始值
                        clinical_data[field_name] = value
                        logger.debug(f"使用原始值 {field_name}: {value}")
                except Exception as e:
                    logger.warning(f"处理 {header}({field_name}): {value} 时出错: {str(e)}")
        
        # 性别转换为数据库格式
        if extracted_data['gender'] == 'Male':
            extracted_data['gender'] = 'Male'
        elif extracted_data['gender'] == 'Female':
            extracted_data['gender'] = 'Female'
        
        logger.debug(f"提取的基本数据: {extracted_data}")
        logger.debug(f"提取的临床数据: {clinical_data}")
        
        return clinical_data, extracted_data
    
    except Exception as e:
        logger.error(f"解析临床特征文件时出错: {str(e)}", exc_info=True)
        return clinical_data, extracted_data 

# 医生个人信息页面
@login_required_custom
def doctor_profile(request):
    # 获取当前登录医生信息
    doctor_id = request.session.get('doctor_id')
    doctor = get_object_or_404(Doctor, doctor_id=doctor_id)
    
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value')
        
        # 根据不同字段进行更新
        if field == 'password':
            # 验证密码强度
            if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{10,}$', value):
                messages.error(request, '密码必须至少10位，且包含大小写字母和数字')
                return redirect('doctor_profile')
            
            # 更新密码（使用哈希）
            doctor.password = make_password(value)
            doctor.save()
            messages.success(request, '密码已更新')
            
        elif field == 'email':
            # 验证邮箱格式
            try:
                validate_email(value)
            except ValidationError:
                messages.error(request, '请输入有效的邮箱地址')
                return redirect('doctor_profile')
            
            # 检查邮箱是否已被其他人使用
            if Doctor.objects.filter(email=value).exclude(doctor_id=doctor_id).exists():
                messages.error(request, '此邮箱已被注册')
                return redirect('doctor_profile')
            
            doctor.email = value
            doctor.save()
            messages.success(request, '邮箱已更新')
            
        elif field == 'full_name':
            # 验证全名格式
            if not value or len(value) < 2:
                messages.error(request, '请输入有效的全名')
                return redirect('doctor_profile')
            
            doctor.full_name = value
            doctor.save()
            
            # 更新session中的医生姓名
            request.session['doctor_name'] = doctor.full_name
            
            messages.success(request, '全名已更新')
            
        return redirect('doctor_profile')
    
    # GET请求，显示个人信息
    return render(request, 'doctor_profile.html', {
        'title': '个人信息',
        'doctor': doctor
    })

# 忘记密码 - 步骤1: 输入邮箱
def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # 验证邮箱
        try:
            validate_email(email)
            doctor = Doctor.objects.filter(email=email).first()
            
            if doctor:
                # 生成6位数字验证码
                verification_code = ''.join(random.choices(string.digits, k=6))
                
                # 存储验证码到session
                request.session['reset_email'] = email
                request.session['verification_code'] = verification_code
                request.session['code_generated_time'] = timezone.now().timestamp()
                
                # 记录验证码到日志
                logger.info(f"为邮箱 {email} 生成的验证码: {verification_code}")
                
                try:
                    # 发送邮件
                    subject = '肺炎诊断系统 - 密码重置验证码'
                    message = f'''尊敬的医生，您好：
                    
您正在重置肺炎诊断系统的登录密码，请使用以下验证码完成操作：

验证码: {verification_code}

验证码有效期为10分钟，请尽快完成操作。如果不是您本人操作，请忽略此邮件并及时修改密码。

肺炎诊断系统团队
'''
                    send_mail(
                        subject,
                        message,
                        'aa1472583690111@163.com',  # 发件人
                        [email],  # 收件人
                        fail_silently=False,
                    )
                    
                    messages.success(request, f'验证码已发送到 {email}，请查收')
                    return redirect('verify_code')
                except Exception as e:
                    logger.error(f"发送邮件时出错: {str(e)}", exc_info=True)
                    messages.error(request, f'发送验证码失败: {str(e)}')
            else:
                messages.error(request, '该邮箱未注册')
        except ValidationError:
            messages.error(request, '请输入有效的邮箱地址')
    
    return render(request, 'forget_password.html')

# 忘记密码 - 步骤2: 验证验证码
def verify_code(request):
    reset_email = request.session.get('reset_email')
    if not reset_email:
        messages.error(request, '请先提交邮箱')
        return redirect('forget_password')
    
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        stored_code = request.session.get('verification_code')
        generated_time = request.session.get('code_generated_time')
        
        # 验证码有效期为10分钟
        current_time = timezone.now().timestamp()
        if not stored_code or current_time - generated_time > 600:
            messages.error(request, '验证码已过期，请重新获取')
            return redirect('forget_password')
        
        if code == stored_code:
            # 验证通过，可以重置密码
            return redirect('reset_password')
        else:
            messages.error(request, '验证码错误')
    
    return render(request, 'verify_code.html', {
        'email': reset_email
    })

# 忘记密码 - 步骤3: 重置密码
def reset_password(request):
    reset_email = request.session.get('reset_email')
    if not reset_email or not request.session.get('verification_code'):
        messages.error(request, '未经验证，请重新开始')
        return redirect('forget_password')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # 验证密码
        errors = []
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{10,}$', password):
            errors.append('密码必须至少10位，且包含大小写字母和数字')
        
        if password != confirm_password:
            errors.append('两次输入的密码不一致')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'reset_password.html')
        
        try:
            # 更新密码
            doctor = Doctor.objects.get(email=reset_email)
            doctor.password = make_password(password)
            doctor.save()
            
            # 清除session中的验证信息
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'verification_code' in request.session:
                del request.session['verification_code']
            if 'code_generated_time' in request.session:
                del request.session['code_generated_time']
            
            messages.success(request, '密码重置成功，请使用新密码登录')
            return redirect('login')
        except Doctor.DoesNotExist:
            messages.error(request, '用户不存在')
        except Exception as e:
            logger.error(f"重置密码时出错: {str(e)}", exc_info=True)
            messages.error(request, '密码重置失败，请稍后再试')
    
    return render(request, 'reset_password.html') 