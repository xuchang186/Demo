from django.urls import path
from . import views

app_name = 'diagnosis'

urlpatterns = [
    # 诊断首页
    path('', views.diagnosis_home, name='home'),
    
    # 上传CT图像
    path('upload-ct/', views.upload_ct, name='upload_ct'),
    path('upload-ct/<int:patient_id>/', views.upload_ct, name='upload_ct'),
    
    # 处理CT图像上传
    path('process-ct/', views.process_ct, name='process_ct'),
    
    # 诊断结果
    path('result/<int:diagnosis_id>/', views.diagnosis_result, name='diagnosis_result'),
    
    # 诊断历史
    path('history/', views.diagnosis_history, name='diagnosis_history'),
    
    # AJAX接口
    path('api/patient-info/<int:patient_id>/', views.get_patient_info, name='patient_info'),
    path('api/diagnose/', views.ajax_diagnose, name='ajax_diagnose'),
    path('api/remote-diagnose/', views.run_remote_diagnosis, name='remote_diagnose'),
] 