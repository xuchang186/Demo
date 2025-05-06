from django.db import models
from patient_records.models import Patient, Doctor

# 诊断结果模型
class DiagnosisResult(models.Model):
    RESULT_TYPES = [
        ('Normal', '无肺炎'),
        ('Mild', '轻度肺炎'),
        ('Severe', '重度肺炎'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diagnosis_results')
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES, verbose_name='诊断结果')
    confidence = models.FloatField(verbose_name='置信度') # 保留置信度字段用于兼容性
    
    # 新增三种类型的概率字段
    probability_normal = models.FloatField(verbose_name='无肺炎概率', default=0.0)
    probability_mild = models.FloatField(verbose_name='轻度肺炎概率', default=0.0)
    probability_severe = models.FloatField(verbose_name='重度肺炎概率', default=0.0)
    
    # CT图像存储路径
    ct_image = models.ImageField(upload_to='ct_images/%Y/%m/%d/', verbose_name='CT图像')
    
    notes = models.TextField(blank=True, null=True, verbose_name='临床备注') # 仅此字段可为空
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='诊断时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name='创建医生') # 添加创建医生字段
    
    class Meta:
        verbose_name = '诊断结果'
        verbose_name_plural = '诊断结果'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.name} - {self.result_type} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_confidence_percentage(self):
        """返回置信度百分比"""
        return f"{self.confidence * 100:.1f}%"
    
    def get_probability_percentage(self, prob_type):
        """根据类型返回概率百分比"""
        if prob_type == 'normal':
            return self.probability_normal * 100
        elif prob_type == 'mild':
            return self.probability_mild * 100
        elif prob_type == 'severe':
            return self.probability_severe * 100
        return 0.0
    
    def get_formatted_probability(self, prob_type):
        """根据类型返回格式化的概率百分比字符串"""
        percentage = self.get_probability_percentage(prob_type)
        return f"{percentage:.1f}%"
        
    # 添加属性访问方法，方便模板调用
    @property
    def normal_probability(self):
        """返回无肺炎概率的百分比形式（0-100）"""
        return self.probability_normal * 100
        
    @property
    def mild_probability(self):
        """返回轻度肺炎概率的百分比形式（0-100）"""
        return self.probability_mild * 100
        
    @property
    def severe_probability(self):
        """返回重度肺炎概率的百分比形式（0-100）"""
        return self.probability_severe * 100 