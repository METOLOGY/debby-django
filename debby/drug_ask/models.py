from django.db import models

# Create your models here.
class DrugModel(models.Model):
    chinese_name = models.CharField(max_length=30)
    eng_name = models.CharField(max_length=50)
    permission_type = models.CharField(max_length=20)
    main_ingredient = models.CharField(max_length=20)
