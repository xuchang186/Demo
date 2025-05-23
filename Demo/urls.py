"""
URL configuration for Demo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from patient_records import views as auth_views
from django.shortcuts import redirect

# 创建需要登录的首页视图
def home_view(request):
    if not request.session.get('doctor_id'):
        return redirect('login')
    return TemplateView.as_view(template_name='home.html')(request)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 用户认证相关
    path('', auth_views.login_view, name='index'),  # 默认首页为登录页面
    path('home/', home_view, name='home'),
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.doctor_profile, name='doctor_profile'),
    path('forget-password/', auth_views.forget_password, name='forget_password'),
    path('verify-code/', auth_views.verify_code, name='verify_code'),
    path('reset-password/', auth_views.reset_password, name='reset_password'),
    
    # 功能模块路径
    path('patient-records/', include('patient_records.urls')),
    path('diagnosis/', include('diagnosis.urls')),
    path('segmentation/', include('segmentation.urls')),
]

# 添加媒体文件的处理
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
