from django.urls import path
from . import views

app_name = 'segmentation'

urlpatterns = [
    # 分割首页
    path('', views.segmentation_home, name='segmentation_home'),
    
    # 上传X光图像
    path('upload-xray/', views.upload_xray, name='upload_xray'),
    
    # 带患者ID的上传X光图像
    path('upload-xray/<int:patient_id>/', views.upload_xray, name='upload_xray_with_patient'),
    
    # X光图像上传API端点
    path('api/upload-xray/', views.api_upload_xray, name='api_upload_xray'),
    
    # 分割结果页面
    path('result/<int:segmentation_id>/', views.segmentation_result, name='segmentation_result'),
    
    # 分割历史记录
    path('history/', views.segmentation_history, name='segmentation_history'),
    
    # 指定患者的分割历史
    path('history/<int:patient_id>/', views.patient_segmentation_history, name='patient_segmentation_history'),
    
    # DeepSeek API聊天接口
    path('api/deepseek-chat/', views.deepseek_chat, name='deepseek_chat'),
] 