from django.db import models
from patient_records.models import Patient, Doctor
from diagnosis.models import DiagnosisResult

# 分割结果模型
class SegmentationResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='segmentation_results', verbose_name='患者')
    diagnosis = models.ForeignKey(DiagnosisResult, on_delete=models.CASCADE, related_name='segmentation_results', verbose_name='关联诊断结果')
    
    # X光图像存储路径
    xray_image = models.ImageField(upload_to='xray_images/%Y/%m/%d/', verbose_name='X光图像')
    
    # 分割结果图像存储路径
    segmentation_image = models.ImageField(upload_to='segmentation_results/%Y/%m/%d/', verbose_name='分割结果图像')
    
    # 分割提示文本
    prompt_text = models.TextField(verbose_name='分割提示文本', 
                                  help_text='医生输入的分割提示文本，如"Bilateral pulmonary infection, two infected areas, all left lung and all right lung"')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name='创建医生')
    
    class Meta:
        verbose_name = '分割结果'
        verbose_name_plural = '分割结果'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.name} - 感染区域分割 ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_image_path(self):
        """返回X光图像路径"""
        if self.xray_image:
            return self.xray_image.url
        return None
    
    def get_result_path(self):
        """返回分割结果图像路径"""
        if self.segmentation_image:
            return self.segmentation_image.url
        return None 