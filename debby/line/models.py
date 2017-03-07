from django.db import models

# Create your models here.
class QAModel(models.Model):
    phrase = models.CharField(max_length=30, blank=False)
    answer = models.TextField(max_length=200, blank=True)
    callback = models.CharField(max_length=20,
                                choices=(
                                    ('BGRecord', '紀錄血糖'),
                                    ('FoodRecord', '紀錄飲食'),
                                    ('FoodQuery', '查詢食物熱量'),
                                    ('DrugQuery', '查詢藥物'),
                                    ('Chat', '閒聊'),
                                ),
                                blank=False
                                )