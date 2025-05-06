                                                                                                                                              # 肺炎智能诊断系统数据库表结构

## 医生表(Doctor)

| 字段名 | 数据类型 | 说明 | 约束 |
|--------|----------|------|------|
| doctor_id | BigAutoField | 医生ID | 主键 |
| password | CharField(128) | 密码 | 非空 |
| email | EmailField(100) | 邮箱 | 可空 |
| full_name | CharField(50) | 全名 | 非空 |
| created_at | DateTimeField | 创建时间 | 自动添加 |
| last_login | DateTimeField | 最后登录时间 | 可空 |

## 患者表(Patient)

| 字段名 | 数据类型 | 说明 | 约束 |
|--------|----------|------|------|
| patient_id | BigAutoField | 患者ID | 主键 |
| name | CharField(50) | 姓名 | 非空 |
| gender | CharField(10) | 性别 | 非空 |
| birth_date | DateField | 出生日期 | 非空 |
| id_card | CharField(18) | 身份证号 | 可空 |
| phone | CharField(15) | 联系电话 | 可空 |
| emergency_contact | CharField(50) | 紧急联系人 | 可空 |
| emergency_phone | CharField(15) | 紧急联系电话 | 可空 |
| created_at | DateTimeField | 创建时间 | 自动添加 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |
| created_by | ForeignKey | 创建人 | 外键(Doctor) |

## 临床特征表(ClinicalFeature) - 核心字段

| 字段名 | 数据类型 | 说明 | 约束 |
|--------|----------|------|------|
| patient | OneToOneField | 患者 | 主键/外键(Patient) |
| age | CharField(10) | 年龄 | 非空 |
| gender | CharField(10) | 性别 | 非空 |
| body_temperature | CharField(10) | 体温 | 非空 |
| underlying_diseases | TextField | 基础疾病 | 可空 |
| ... | ... | ... | ... |
| created_at | DateTimeField | 创建时间 | 自动添加 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |
| created_by | ForeignKey | 创建人 | 外键(Doctor) |

### 临床特征表 - 临床指标分类

| 指标类别 | 字段数量 | 包含指标示例 |
|--------|----------|------------|
| 常规血液检查 | 21项 | MCHC(平均红细胞血红蛋白浓度), MCH(平均红细胞血红蛋白), MCV(平均红细胞体积), WBC(白细胞计数)等 |
| 凝血功能检查 | 6项 | DD(D-二聚体), TT(凝血酶时间), FIB(纤维蛋白原), PT(凝血酶原时间)等 |
| 炎症指标 | 3项 | ESR(红细胞沉降率), CRP(C反应蛋白), PCT(降钙素原) |
| 生化指标 | 42项 | ALB(白蛋白), ALT(丙氨酸氨基转移酶), AST(天冬氨酸氨基转移酶), TBIL(总胆红素)等 |
| 免疫细胞分型 | 6项 | CD3(CD3+ T细胞), CD4(CD4+ T细胞), CD8(CD8+ T细胞), CD4_CD8(CD4/CD8比值)等 |
| 细胞因子 | 6项 | IL_2(白介素-2), IL_4(白介素-4), IL_6(白介素-6), TNF(肿瘤坏死因子-α)等 |
| 尿常规指标 | 13项 | URBC(尿红细胞计数), UWBC(尿白细胞计数), SG(比重), PH(pH值)等 |
| 其他生化指标 | 31项 | IBIL(间接胆红素), AT_III(抗凝血酶III), LAC(乳酸)等 |

## 诊断结果表(DiagnosisResult)

| 字段名 | 数据类型 | 说明 | 约束 |
|--------|----------|------|------|
| id | AutoField | 诊断结果ID | 主键 |
| patient | ForeignKey | 患者 | 外键(Patient) |
| result_type | CharField(20) | 诊断结果类型 | 非空(选项) |
| confidence | FloatField | 置信度 | 非空 |
| probability_normal | FloatField | 无肺炎概率 | 默认0.0 |
| probability_mild | FloatField | 轻度肺炎概率 | 默认0.0 |
| probability_severe | FloatField | 重度肺炎概率 | 默认0.0 |
| ct_image | ImageField | CT图像 | 可空 |
| notes | TextField | 临床备注 | 可空 |
| created_at | DateTimeField | 诊断时间 | 自动添加 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |

## 分割结果表(SegmentationResult)

| 字段名 | 数据类型 | 说明 | 约束 |
|--------|----------|------|------|
| id | AutoField | 分割结果ID | 主键 |
| patient | ForeignKey | 患者 | 外键(Patient) |
| diagnosis | ForeignKey | 关联诊断结果 | 外键(DiagnosisResult)可空 |
| xray_image | ImageField | X光图像 | 可空 |
| segmentation_image | ImageField | 分割结果图像 | 可空 |
| prompt_text | TextField | 分割提示文本 | 可空 |
| created_at | DateTimeField | 创建时间 | 自动添加 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |

## 数据库表间关系描述

| 关系类型 | 相关表 | 关系描述 |
|--------|----------|------------|
| 一对多 | Doctor → Patient | 一个医生可以创建多个患者记录 |
| 一对一 | Patient → ClinicalFeature | 一个患者对应一份临床特征数据 |
| 一对多 | Patient → DiagnosisResult | 一个患者可以有多次诊断记录 |
| 一对多 | Patient → SegmentationResult | 一个患者可以有多次分割记录 |
| 一对多 | DiagnosisResult → SegmentationResult | 一次诊断可以对应多次分割(可选关联) |
| 一对多 | Doctor → ClinicalFeature | 一个医生可以创建多份临床特征记录 |

## 表结构说明

上述表格描述了肺炎智能诊断系统中的五个主要数据表及其关系:

1. **医生表(Doctor)**: 存储系统用户(医生)的基本信息。
2. **患者表(Patient)**: 存储患者的基本信息，并关联创建该患者记录的医生。
3. **临床特征表(ClinicalFeature)**: 与患者表一对一关联，存储128项临床指标，为AI模型提供诊断依据。
4. **诊断结果表(DiagnosisResult)**: 存储肺炎诊断结果，包含CT图像和预测概率。
5. **分割结果表(SegmentationResult)**: 存储肺部感染区域分割结果，包含X光图像和分割结果图像。

临床特征表中的128项临床指标按照医学分类进行了组织，涵盖了常规血液检查、凝血功能、炎症指标、生化指标等多个方面，为多模态肺炎诊断提供了全面的数据支持。
