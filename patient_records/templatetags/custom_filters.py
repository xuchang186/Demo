from django import template
import re

register = template.Library()

@register.filter
def temp_status(value):
    """
    根据体温值返回对应的状态类名
    - 体温 < 37.3°C: 返回status-normal（正常）
    - 体温 37.3-38.0°C: 返回status-warning（低热）
    - 体温 > 38.0°C: 返回status-danger（高热）
    """
    try:
        # 正则匹配去除非数字字符，保留数字和小数点
        cleaned_value = re.sub(r'[^\d.]', '', str(value))
        temp = float(cleaned_value)
        
        if temp < 37.3:
            return 'status-normal'
        elif 37.3 <= temp <= 38.0:
            return 'status-warning'
        else:
            return 'status-danger'
    except (ValueError, TypeError):
        # 如果无法转换为浮点数，默认返回normal
        return 'status-normal' 