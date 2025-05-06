from django.urls import path
from . import views

app_name = 'patient_records'

urlpatterns = [
    # 病历列表页
    path('', views.patient_list, name='patient_list'),
    
    # 新增病历
    path('add/', views.patient_add, name='patient_add'),
    
    # 病历详情页
    path('<int:patient_id>/', views.patient_detail, name='patient_detail'),
    
    # 编辑病历
    path('<int:patient_id>/edit/', views.patient_edit, name='patient_edit'),
    
    # 删除病历
    path('<int:patient_id>/delete/', views.patient_delete, name='patient_delete'),
    
    # 添加就诊记录
    path('<int:patient_id>/add-record/', views.add_medical_record, name='add_medical_record'),
] 