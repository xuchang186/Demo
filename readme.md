# 肺炎诊断系统

## 项目概述

肺炎诊断系统是一个医疗辅助工具，面向医生使用，用于管理患者病历、辅助肺炎诊断以及进行感染区域分割分析。系统采用了现代Web技术栈，提供直观、专业的用户界面，帮助医生提高工作效率和诊断准确率。

## UI设计与用户体验

系统采用了专业的医疗界面设计原则，主要特点包括：

1. **色彩方案**
   - 使用蓝色系主色调 (#2B5DE0)，传达专业、可靠的医疗形象
   - 辅助色包括医疗绿 (#41B883)，用于表示健康状态
   - 功能色彩设计：成功/正常(绿色)、警告/轻度(橙色)、危险/重度(红色)
   - 文字颜色采用多层次设计，提升可读性

2. **界面布局**
   - 二栏布局：左侧固定导航栏 + 右侧内容区
   - 清晰的视觉层次和信息架构
   - 卡片式设计，强调内容边界
   - 响应式设计，支持各种屏幕尺寸

3. **交互设计**
   - 图标化操作按钮，提升可识别性
   - 工具提示增强可用性
   - 状态反馈系统（操作确认、成功通知）
   - 表单优化和搜索体验改进

## 功能特点

1. **患者管理系统**
   - 患者基础信息管理（ID、姓名、性别、年龄等）
   - 临床特征记录（128项临床指标，含血常规、生化指标等）
   - 就诊记录管理

2. **智能肺炎诊断系统**
   - CT图像上传与分析
   - 结合临床特征的肺炎等级诊断（无肺炎、轻度肺炎、重度肺炎）

3. **肺炎感染区域分割系统**
   - X光图像上传与处理
   - 肺炎感染区域自动分割

## 技术栈

- 前端：HTML、CSS、JavaScript、Bootstrap 5
- 后端：Python 3.9、Django 4.2
- 数据库：MySQL
- 缓存：Redis
- 任务队列：Celery

## 项目安装和运行

### 环境要求

- Python 3.9
- Django 4.2
- 其他依赖见`requirements.txt`

### 安装步骤

1. 克隆项目
```
git clone <项目地址>
cd <项目目录>
```

2. 创建虚拟环境
```
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. 安装依赖
```
pip install -r requirements.txt
```

4. 应用数据库迁移
```
python manage.py migrate
```

5. 创建超级用户
```
python manage.py createsuperuser
```

6. 运行开发服务器
```
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 查看应用。

## 目录结构

```
肺炎诊断系统/
├── Demo/                     # Django项目配置目录
│   ├── __init__.py           # Python包标识文件
│   ├── settings.py           # Django设置文件
│   ├── urls.py               # URL路由配置
│   ├── asgi.py               # ASGI服务器配置
│   └── wsgi.py               # WSGI服务器配置
├── patient_records/          # 患者管理应用
│   ├── __init__.py           # Python包标识文件
│   ├── models.py             # 数据模型定义（Doctor, Patient, ClinicalFeature）
│   ├── views.py              # 视图函数
│   ├── urls.py               # URL配置
│   ├── settings.py           # 应用特定设置
│   ├── migrations/           # 数据库迁移文件目录
│   └── templates/            # 应用模板目录
│       └── patient_records/  # 患者相关模板
│           └── patient_list.html # 患者列表页面模板
├── diagnosis/                # 肺炎诊断应用
│   ├── __init__.py           # Python包标识文件
│   ├── views.py              # 视图函数
│   ├── urls.py               # URL配置
│   └── templates/            # 应用模板目录
├── segmentation/             # 感染区域分割应用
│   ├── __init__.py           # Python包标识文件
│   ├── views.py              # 视图函数
│   ├── urls.py               # URL配置
│   └── templates/            # 应用模板目录
├── manage.py                 # Django项目管理脚本
├── static/                   # 静态文件目录
│   ├── css/                  # CSS样式文件
│   │   ├── main.css          # 主样式文件
│   │   ├── common.css        # 通用样式
│   │   ├── patient_list.css  # 患者列表页面样式
│   │   ├── diagnosis_home.css # 诊断首页样式
│   │   ├── upload_ct.css     # CT上传页面样式
│   │   ├── diagnosis_history.css # 诊断历史样式
│   │   ├── patient_diagnosis_history.css # 患者诊断历史样式
│   │   └── segmentation_home.css # 分割首页样式
│   ├── js/                   # JavaScript文件
│   │   ├── main.js           # 主JS文件，负责导入和初始化
│   │   ├── common.js         # 通用JS函数
│   │   ├── notifications.js  # 通知系统
│   │   ├── forms.js          # 表单处理
│   │   ├── modal.js          # 模态框处理
│   │   └── upload.js         # 文件上传处理
│   └── images/               # 图像资源目录
├── templates/                # HTML模板目录
│   ├── index.html            # 主布局模板文件
│   ├── login.html            # 登录页面
│   └── logout.html           # 登出页面
├── media/                    # 用户上传的文件目录
│   ├── ct_images/            # CT图像存储目录
│   └── xray_images/          # X光图像存储目录
├── color.txt                 # 系统色彩方案定义文件
├── requirements.txt          # 项目依赖列表
└── README.md                 # 项目说明文档
```

## 模块说明

### 患者管理模块 (patient_records)
- 患者列表：浏览、搜索和管理患者记录
- 新增患者：添加新患者的基本信息和临床数据
- 编辑患者：修改已有患者的信息
- 查看详情：查看患者的详细信息和历史记录

### 肺炎诊断模块 (diagnosis)
- 诊断主页：系统功能介绍和快速入口
- CT图像上传：上传患者CT图像进行肺炎诊断
- 诊断结果：展示AI诊断分析结果，包括肺炎类型预测、严重程度评估等
- 诊断历史：浏览和管理历史诊断记录
- 患者诊断历史：查看指定患者的所有诊断记录和趋势分析

### 感染区域分割模块 (segmentation)
- 分割主页：功能介绍和快速入口
- X光图像上传：上传患者X光胸片进行感染区域分割
- 分割结果：展示分割结果，标记感染区域
- 历史分割结果：浏览和管理历史分割记录

### 前端

#### 静态文件

CSS结构：
- **css/main.css**: 集中导入所有CSS模块
- **css/common.css**: 公共样式和变量定义
- **css/patient_list.css**: 患者列表页面样式
- **css/diagnosis_home.css**: 诊断首页样式
- **css/upload_ct.css**: CT上传页面样式
- **css/diagnosis_history.css**: 诊断历史页面样式
- **css/patient_diagnosis_history.css**: 患者诊断历史页面样式
- **css/segmentation_home.css**: 分割首页样式

JavaScript结构：
- **js/main.js**: 主JS文件，导入和初始化其他模块
- **js/common.js**: 通用功能，如导航激活、移动端适配等
- **js/notifications.js**: 通知系统实现
- **js/forms.js**: 表单验证和处理
- **js/modal.js**: 模态框和确认对话框功能
- **js/upload.js**: 文件上传处理

#### 模板

- **templates/index.html**: 
  - 主布局模板，定义整体页面结构
  - 左侧导航栏实现
  - 右侧内容区框架
  - 自适应移动端视图

### 后端

#### URL配置

- **Demo/urls.py**: 
  - 主URL配置文件
  - 连接各个应用的URL配置
  - 处理静态和媒体文件URL

- **patient_records/urls.py**:
  - 患者管理相关的URL配置
  - 包含患者列表、详情、编辑等路径

- **diagnosis/urls.py**:
  - 肺炎诊断相关的URL配置
  - 包含诊断操作、结果显示等路径

- **segmentation/urls.py**:
  - 感染区域分割相关的URL配置
  - 包含图像上传、分割结果等路径

### 色彩方案

- **color.txt**:
  - 定义系统全局色彩变量
  - 包含主题色、文本色、背景色和功能色
  - 为医疗系统设计的专业配色方案

## 页面结构

- 首页: `/` - 系统主页和功能导航
- 登录页: `/login/` - 用户登录界面
- 退出登录: `/logout/` - 退出登录

### 患者管理
- 患者列表: `/patient-records/` - 患者管理列表
- 新增患者: `/patient-records/add/` - 添加新患者
- 编辑患者: `/patient-records/edit/<id>/` - 编辑患者信息
- 患者详情: `/patient-records/detail/<id>/` - 查看患者详细信息

### 肺炎诊断
- 诊断主页: `/diagnosis/` - 肺炎诊断功能主页
- CT图像上传: `/diagnosis/upload-ct/` - 上传CT图像页面
- 诊断结果: `/diagnosis/result/<id>/` - 查看诊断结果
- 诊断历史: `/diagnosis/history/` - 浏览诊断历史记录
- 患者诊断历史: `/diagnosis/history/<patient_id>/` - 查看指定患者的诊断历史

### 感染区域分割
- 分割主页: `/segmentation/` - 感染区域分割功能主页
- 图像上传: `/segmentation/upload-xray/` - 上传X光图像页面
- 分割结果: `/segmentation/result/<id>/` - 查看分割结果
- 历史分割结果: `/segmentation/history/` - 浏览历史分割结果
- 分割结果详情: `/segmentation/result/<id>/` - 查看分割结果详情

## URL路径结构

```
/                           # 首页
/login/                     # 登录页面
/logout/                    # 登出操作

/patient-records/           # 患者列表页
/patient-records/add/       # 新增患者
/patient-records/<id>/      # 患者详情页
/patient-records/<id>/edit/ # 编辑患者
/patient-records/<id>/delete/     # 删除患者
/patient-records/<id>/add-record/ # 添加就诊记录

/diagnosis/                 # 诊断首页
/diagnosis/upload-ct/       # 上传CT图像
/diagnosis/result/<id>/     # 诊断结果页面
/diagnosis/history/         # 诊断历史记录
/diagnosis/history/<id>/    # 指定患者的诊断历史

/segmentation/              # 分割首页
/segmentation/upload-xray/  # 上传X光图像
/segmentation/result/<id>/  # 分割结果页面
/segmentation/history/      # 分割历史记录
/segmentation/history/<id>/ # 指定患者的分割历史

/admin/                     # 管理员界面
```
### 技术栈

- **前端**：HTML, CSS, JavaScript, Bootstrap
- **后端**：Python, Django
- **数据库**：MySQL
- **AI模型**：深度学习模型用于图像分析和多模态诊断

### 系统页面

1. **诊断首页**：展示患者列表，可按姓名或ID搜索患者，选择患者进行诊断。
2. **CT上传页面**：显示患者基本信息和临床特征，上传CT图像并启动诊断流程。
3. **诊断结果页面**：展示诊断结果、概率分布、CT图像分析和临床建议。
4. **诊断历史页面**：查看历史诊断记录，支持按患者和诊断结果筛选。

### 使用流程

1. 在诊断首页选择患者或搜索特定患者。
2. 点击"开始诊断"进入CT上传页面。
3. 上传患者的CT图像，点击"开始诊断"。
4. 系统分析数据并生成诊断结果。
5. 查看诊断详情，包括肺炎类型、置信度和医疗建议。

### 注意事项

- 系统诊断结果仅供医生参考，最终诊断应由专业医生根据患者实际情况决定。
- CT图像应清晰完整，以确保AI模型分析准确度。
- 临床特征数据应准确无误，尤其是炎症指标和免疫相关指标。
