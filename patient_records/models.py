from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Doctor(models.Model):
    """医生表"""
    doctor_id = models.BigAutoField(primary_key=True, verbose_name='医生ID')
    password = models.CharField(max_length=128, verbose_name='密码')
    email = models.EmailField(max_length=100, verbose_name='邮箱')
    full_name = models.CharField(max_length=30, verbose_name='全名')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_login = models.DateTimeField(auto_now=True, verbose_name='最后登录时间')
    
    class Meta:
        db_table = 'doctor'
        verbose_name = '医生'
        verbose_name_plural = '医生'
        
    def __str__(self):
        return self.full_name

class Patient(models.Model):
    """患者信息表"""
    GENDER_CHOICES = (
        ('Male', '男'),
        ('Female', '女'),
    )
    
    patient_id = models.BigAutoField(primary_key=True, verbose_name='患者ID')
    name = models.CharField(max_length=30, verbose_name='姓名')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='性别')
    birth_date = models.DateField(verbose_name='出生日期')
    id_card = models.CharField(max_length=18, verbose_name='身份证号')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    emergency_contact = models.CharField(max_length=30, verbose_name='紧急联系人')
    emergency_phone = models.CharField(max_length=11, verbose_name='紧急联系电话')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name='创建人')
    
    class Meta:
        db_table = 'patient'
        verbose_name = '患者'
        verbose_name_plural = '患者'
        
    def __str__(self):
        return f"{self.patient_id} - {self.name}"
    
    def get_age(self):
        """计算患者年龄"""
        today = timezone.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

class ClinicalFeature(models.Model):
    """临床特征表"""
    GENDER_CHOICES = (
        ('Male', '男'),
        ('Female', '女'),
    )
    
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, primary_key=True, related_name='clinical_features', verbose_name='患者')
    age = models.CharField(max_length=10, verbose_name='年龄')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='性别')
    body_temperature = models.CharField(max_length=10, verbose_name='体温', help_text='°C')
    underlying_diseases = models.TextField(verbose_name='基础疾病')
    
    # 常规血液检查
    MCHC = models.CharField(max_length=20, verbose_name='平均红细胞血红蛋白浓度', help_text='g/L', null=True, blank=True)
    MCH = models.CharField(max_length=20, verbose_name='平均红细胞血红蛋白', help_text='pg', null=True, blank=True)
    MCV = models.CharField(max_length=20, verbose_name='平均红细胞体积', help_text='fl', null=True, blank=True)
    HCT = models.CharField(max_length=20, verbose_name='血细胞比容', help_text='%', null=True, blank=True)
    HGB = models.CharField(max_length=20, verbose_name='血红蛋白', help_text='g/L', null=True, blank=True)
    RBC = models.CharField(max_length=20, verbose_name='红细胞计数', help_text='T/L', null=True, blank=True)
    PDW = models.CharField(max_length=20, verbose_name='血小板分布宽度', help_text='%', null=True, blank=True)
    PLCT = models.CharField(max_length=20, verbose_name='血小板比容', help_text='%', null=True, blank=True)
    MPV = models.CharField(max_length=20, verbose_name='平均血小板体积', help_text='fl', null=True, blank=True)
    PLT = models.CharField(max_length=20, verbose_name='血小板计数', help_text='G/L', null=True, blank=True)
    BA = models.CharField(max_length=20, verbose_name='嗜碱性粒细胞计数', help_text='G/L', null=True, blank=True)
    EO = models.CharField(max_length=20, verbose_name='嗜酸性粒细胞计数', help_text='G/L', null=True, blank=True)
    MO = models.CharField(max_length=20, verbose_name='单核细胞计数', help_text='G/L', null=True, blank=True)
    LY = models.CharField(max_length=20, verbose_name='淋巴细胞计数', help_text='G/L', null=True, blank=True)
    NE = models.CharField(max_length=20, verbose_name='中性粒细胞计数', help_text='G/L', null=True, blank=True)
    BAP = models.CharField(max_length=20, verbose_name='嗜碱性粒细胞百分比', help_text='%', null=True, blank=True)
    EOP = models.CharField(max_length=20, verbose_name='嗜酸性粒细胞百分比', help_text='%', null=True, blank=True)
    MOP = models.CharField(max_length=20, verbose_name='单核细胞百分比', help_text='%', null=True, blank=True)
    LYP = models.CharField(max_length=20, verbose_name='淋巴细胞百分比', help_text='%', null=True, blank=True)
    NEP = models.CharField(max_length=20, verbose_name='中性粒细胞百分比', help_text='%', null=True, blank=True)
    WBC = models.CharField(max_length=20, verbose_name='白细胞计数', help_text='G/L', null=True, blank=True)
    PLCR = models.CharField(max_length=20, verbose_name='大血小板比率', help_text='%', null=True, blank=True)
    RDWSD = models.CharField(max_length=20, verbose_name='红细胞分布宽度标准差', help_text='fl', null=True, blank=True)
    RDWCV = models.CharField(max_length=20, verbose_name='红细胞分布宽度变异系数', help_text='%', null=True, blank=True)
    
    # 凝血功能检查
    DD = models.CharField(max_length=20, verbose_name='D-二聚体', help_text='mg/L FEU', null=True, blank=True)
    TT = models.CharField(max_length=20, verbose_name='凝血酶时间', help_text='s', null=True, blank=True)
    FIB = models.CharField(max_length=20, verbose_name='纤维蛋白原', help_text='g/l', null=True, blank=True)
    APTT = models.CharField(max_length=20, verbose_name='活化部分凝血活酶时间', help_text='s', null=True, blank=True)
    INR = models.CharField(max_length=20, verbose_name='国际标准化比值', null=True, blank=True)
    PT = models.CharField(max_length=20, verbose_name='凝血酶原时间', help_text='s', null=True, blank=True)
    
    # 炎症指标
    ESR = models.CharField(max_length=20, verbose_name='红细胞沉降率', help_text='mm/h', null=True, blank=True)
    CRP = models.CharField(max_length=20, verbose_name='C反应蛋白', help_text='mg/L', null=True, blank=True)
    PCT = models.CharField(max_length=20, verbose_name='降钙素原', help_text='ng/ml', null=True, blank=True)
    
    # 生化指标
    ALG = models.CharField(max_length=20, verbose_name='白蛋白/球蛋白比值', null=True, blank=True)
    ALB = models.CharField(max_length=20, verbose_name='白蛋白', help_text='g/L', null=True, blank=True)
    ALP = models.CharField(max_length=20, verbose_name='碱性磷酸酶', help_text='U/L', null=True, blank=True)
    ALT = models.CharField(max_length=20, verbose_name='丙氨酸氨基转移酶', help_text='U/L', null=True, blank=True)
    AST = models.CharField(max_length=20, verbose_name='天冬氨酸氨基转移酶', help_text='U/L', null=True, blank=True)
    BUN = models.CharField(max_length=20, verbose_name='尿素氮', help_text='mmol/L', null=True, blank=True)
    CA = models.CharField(max_length=20, verbose_name='钙', help_text='mmol/L', null=True, blank=True)
    CL = models.CharField(max_length=20, verbose_name='氯', help_text='mmol/L', null=True, blank=True)
    CO2 = models.CharField(max_length=20, verbose_name='二氧化碳总量', help_text='mmol/L', null=True, blank=True)
    CREA = models.CharField(max_length=20, verbose_name='肌酐', help_text='μmol/L', null=True, blank=True)
    GGT = models.CharField(max_length=20, verbose_name='γ-谷氨酰转移酶', help_text='U/L', null=True, blank=True)
    GLB = models.CharField(max_length=20, verbose_name='球蛋白', help_text='g/L', null=True, blank=True)
    K = models.CharField(max_length=20, verbose_name='钾', help_text='mmol/L', null=True, blank=True)
    MG = models.CharField(max_length=20, verbose_name='镁', help_text='mmol/L', null=True, blank=True)
    Na = models.CharField(max_length=20, verbose_name='钠', help_text='mmol/L', null=True, blank=True)
    PHOS = models.CharField(max_length=20, verbose_name='磷', help_text='mmol/L', null=True, blank=True)
    TBIL = models.CharField(max_length=20, verbose_name='总胆红素', help_text='μmol/L', null=True, blank=True)
    TP = models.CharField(max_length=20, verbose_name='血清总蛋白', help_text='g/L', null=True, blank=True)
    URIC = models.CharField(max_length=20, verbose_name='尿酸', help_text='μmol/L', null=True, blank=True)
    CHOL = models.CharField(max_length=20, verbose_name='总胆固醇', help_text='mmol/L', null=True, blank=True)
    CK = models.CharField(max_length=20, verbose_name='肌酸激酶', help_text='U/L', null=True, blank=True)
    HDLC = models.CharField(max_length=20, verbose_name='高密度脂蛋白胆固醇', help_text='mmol/L', null=True, blank=True)
    LDH = models.CharField(max_length=20, verbose_name='乳酸脱氢酶', help_text='U/L', null=True, blank=True)
    TG = models.CharField(max_length=20, verbose_name='甘油三酯', help_text='mmol/L', null=True, blank=True)
    AnG = models.CharField(max_length=20, verbose_name='阴离子间隙', help_text='mmol/L', null=True, blank=True)
    DBIL = models.CharField(max_length=20, verbose_name='直接胆红素', help_text='μmol/L', null=True, blank=True)
    GLU = models.CharField(max_length=20, verbose_name='葡萄糖', help_text='mmol/L', null=True, blank=True)
    LDLC = models.CharField(max_length=20, verbose_name='低密度脂蛋白胆固醇', help_text='mmol/L', null=True, blank=True)
    OSM = models.CharField(max_length=20, verbose_name='渗透压', help_text='mOsm/L', null=True, blank=True)
    PA = models.CharField(max_length=20, verbose_name='前白蛋白', help_text='g/L', null=True, blank=True)
    TBA = models.CharField(max_length=20, verbose_name='总胆汁酸', help_text='μmol/L', null=True, blank=True)
    HBDH = models.CharField(max_length=20, verbose_name='α-羟丁酸脱氢酶', help_text='U/L', null=True, blank=True)
    CysC = models.CharField(max_length=20, verbose_name='胱抑素C', help_text='mg/L', null=True, blank=True)
    LAP = models.CharField(max_length=20, verbose_name='亮氨酸氨基肽酶', help_text='U/L', null=True, blank=True)
    NT5 = models.CharField(max_length=20, verbose_name='5-核苷酸酶', help_text='U/L', null=True, blank=True)
    HC = models.CharField(max_length=20, verbose_name='同型半胱氨酸', help_text='μmol/L', null=True, blank=True)
    SAA = models.CharField(max_length=20, verbose_name='血清淀粉样蛋白A', help_text='mg/L', null=True, blank=True)
    SdLDL = models.CharField(max_length=20, verbose_name='小密度低密度脂蛋白', help_text='mmol/L', null=True, blank=True)
    
    # 免疫细胞分型
    CD3 = models.CharField(max_length=20, verbose_name='CD3+ T细胞', help_text='%', null=True, blank=True)
    CD4 = models.CharField(max_length=20, verbose_name='CD4+ T细胞', help_text='%', null=True, blank=True)
    CD8 = models.CharField(max_length=20, verbose_name='CD8+ T细胞', help_text='%', null=True, blank=True)
    BC = models.CharField(max_length=20, verbose_name='B淋巴细胞', help_text='%', null=True, blank=True)
    NKC = models.CharField(max_length=20, verbose_name='自然杀伤细胞', help_text='%', null=True, blank=True)
    CD4_CD8 = models.CharField(max_length=20, verbose_name='CD4/CD8比值', null=True, blank=True)
    
    # 细胞因子
    IL_2 = models.CharField(max_length=20, verbose_name='白介素-2', help_text='pg/ml', null=True, blank=True)
    IL_4 = models.CharField(max_length=20, verbose_name='白介素-4', help_text='pg/ml', null=True, blank=True)
    IL_6 = models.CharField(max_length=20, verbose_name='白介素-6', help_text='pg/ml', null=True, blank=True)
    IL_10 = models.CharField(max_length=20, verbose_name='白介素-10', help_text='pg/ml', null=True, blank=True)
    TNF = models.CharField(max_length=20, verbose_name='肿瘤坏死因子-α', help_text='pg/ml', null=True, blank=True)
    IFN = models.CharField(max_length=20, verbose_name='干扰素-γ', help_text='pg/ml', null=True, blank=True)
    
    # 其他指标
    CHE = models.CharField(max_length=20, verbose_name='胆碱酯酶', null=True, blank=True)
    SA = models.CharField(max_length=20, verbose_name='唾液酸', help_text='mg/L', null=True, blank=True)
    C1q = models.CharField(max_length=20, verbose_name='补体C1q', help_text='mg/L', null=True, blank=True)
    C3 = models.CharField(max_length=20, verbose_name='补体C3', help_text='g/L', null=True, blank=True)
    AFU = models.CharField(max_length=20, verbose_name='α-L-岩藻糖苷酶', help_text='IU/L', null=True, blank=True)
    LPA = models.CharField(max_length=20, verbose_name='脂蛋白A', help_text='mg/L', null=True, blank=True)
    APOA1 = models.CharField(max_length=20, verbose_name='载脂蛋白A1', help_text='g/L', null=True, blank=True)
    BNP = models.CharField(max_length=20, verbose_name='B型脑钠肽前体', help_text='pg/ml', null=True, blank=True)
    IGM = models.CharField(max_length=20, verbose_name='免疫球蛋白M', help_text='g/L', null=True, blank=True)
    IGA = models.CharField(max_length=20, verbose_name='免疫球蛋白A', help_text='g/L', null=True, blank=True)
    IGG = models.CharField(max_length=20, verbose_name='免疫球蛋白G', help_text='g/L', null=True, blank=True)
    FDP = models.CharField(max_length=20, verbose_name='纤维蛋白/纤维蛋白原降解产物', help_text='ug/l', null=True, blank=True)
    C4 = models.CharField(max_length=20, verbose_name='补体C4', help_text='g/L', null=True, blank=True)
    APOB = models.CharField(max_length=20, verbose_name='载脂蛋白B', help_text='G/L', null=True, blank=True)
    HSCRP = models.CharField(max_length=20, verbose_name='高敏C反应蛋白', help_text='mg/L', null=True, blank=True)
    
    # 尿常规
    URBC = models.CharField(max_length=20, verbose_name='尿红细胞计数', help_text='/ul', null=True, blank=True)
    UWBC = models.CharField(max_length=20, verbose_name='尿白细胞计数', help_text='/ul', null=True, blank=True)
    WBCC = models.CharField(max_length=20, verbose_name='白细胞团', help_text='/ul', null=True, blank=True)
    SQEP = models.CharField(max_length=20, verbose_name='鳞状上皮细胞', help_text='/ul', null=True, blank=True)
    NSEC = models.CharField(max_length=20, verbose_name='非鳞状上皮细胞', help_text='/ul', null=True, blank=True)
    HYAL = models.CharField(max_length=20, verbose_name='透明管型', help_text='/LPF', null=True, blank=True)
    UNCC = models.CharField(max_length=20, verbose_name='病理性管型', help_text='/LPF', null=True, blank=True)
    BYST = models.CharField(max_length=20, verbose_name='酵母菌', help_text='/ul', null=True, blank=True)
    MS_U = models.CharField(max_length=20, verbose_name='粘液丝', help_text='/ul', null=True, blank=True)
    UNCX = models.CharField(max_length=20, verbose_name='未分类结晶', help_text='/ul', null=True, blank=True)
    SG = models.CharField(max_length=20, verbose_name='比重', null=True, blank=True)
    PH = models.CharField(max_length=20, verbose_name='pH值', null=True, blank=True)
    BACT = models.CharField(max_length=20, verbose_name='细菌计数', help_text='/ul', null=True, blank=True)
    
    # 其他生化指标
    IBIL = models.CharField(max_length=20, verbose_name='间接胆红素', help_text='umol/L', null=True, blank=True)
    AT_III = models.CharField(max_length=20, verbose_name='抗凝血酶III', help_text='%', null=True, blank=True)
    FDG = models.CharField(max_length=20, verbose_name='真菌(1-3)-β-D-葡聚糖', help_text='pg/ml', null=True, blank=True)
    LPS = models.CharField(max_length=20, verbose_name='脂肪酶', help_text='U/L', null=True, blank=True)
    U = models.CharField(max_length=20, verbose_name='尿素', help_text='mmol/L', null=True, blank=True)
    UALB = models.CharField(max_length=20, verbose_name='尿白蛋白', help_text='mg/L', null=True, blank=True)
    BCF8 = models.CharField(max_length=20, verbose_name='血凝因子VIII活性', help_text='%', null=True, blank=True)
    ASO = models.CharField(max_length=20, verbose_name='抗链球菌溶血素O', help_text='IU/ml', null=True, blank=True)
    PS = models.CharField(max_length=20, verbose_name='血浆蛋白S活性', help_text='%', null=True, blank=True)
    RF = models.CharField(max_length=20, verbose_name='类风湿因子', help_text='IU/ml', null=True, blank=True)
    PC = models.CharField(max_length=20, verbose_name='血浆蛋白C活性', help_text='%', null=True, blank=True)
    LAC = models.CharField(max_length=20, verbose_name='乳酸', help_text='mmol/L', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name='创建人')
    
    class Meta:
        db_table = 'clinical_feature'
        verbose_name = '临床特征'
        verbose_name_plural = '临床特征'
        
    def __str__(self):
        return f"{self.patient.name} - 临床特征 ({self.created_at.strftime('%Y-%m-%d')})" 