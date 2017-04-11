from django.db import models


# Create your models here.
class DrugModel(models.Model):
    chinese_name = models.CharField(max_length=100)
    eng_name = models.CharField(max_length=100)
    permission_type = models.CharField(max_length=20)
    main_ingredient = models.CharField(max_length=20)


class DrugTypeModel(models.Model):
    question = models.CharField(max_length=100)
    user_choice = models.CharField(max_length=100, blank=True, null=True)
    answer = models.CharField(max_length=100)
    type = models.CharField(max_length=100)


class DrugDetailModel(models.Model):
    type = models.CharField(max_length=100, unique=True)
    mechanism = models.CharField(max_length=200)
    side_effect = models.CharField(max_length=200)
    taboo = models.CharField(max_length=200)
    awareness = models.CharField(max_length=200)
