from django.db import models

# Create your models here.
class QAModel(models.Model):
    category = models.CharField(max_length=20,
                                choices=(
                                    ('bg', '血糖'),
                                    ('sports', '運動'),
                                    ('diet', '飲食'),
                                    ('greeting', '招呼詞'),
                                    ('other', '其他'),
                                ),
                                blank=False
                                )
    keyword = models.CharField(max_length=30, blank=False)
    answer = models.CharField(max_length=120, blank=True)