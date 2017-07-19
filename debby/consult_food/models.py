from django.db import models


# Create your models here.
class ConsultFoodModel(models.Model):
    sample_name = models.CharField(verbose_name="樣品名稱", max_length=100, blank=False, unique=True)
    modified_calorie = models.FloatField(verbose_name="修正熱量-成分值(kcal)", blank=True, null=True)  # kcal
    carbohydrates = models.FloatField(verbose_name="總碳水化合物-成分值(g)", blank=True, null=True)  # g
    dietary_fiber = models.FloatField(verbose_name="膳食纖維-成分值(g)", blank=True, null=True)  # g
    metabolic_carbohydrates = models.FloatField(verbose_name="可代謝醣量", blank=True, null=True)
    carbohydrates_equivalent = models.FloatField(verbose_name="醣類份數當量", blank=True, null=True)
    white_rice_equivalent = models.FloatField(verbose_name="幾碗白飯當量", blank=True, null=True)


class FoodModel(models.Model):
    integration_number = models.CharField(verbose_name="整合編號", max_length=20)
    food_type = models.CharField(verbose_name="食物分類", max_length=20)
    sample_name = models.CharField(verbose_name="樣品名稱", max_length=100, unique=True)
    modified_calorie = models.FloatField(verbose_name="修正熱量-成分值(kcal)")
    crude_protein = models.FloatField(verbose_name="粗蛋白-成分值(g)")
    crude_fat = models.FloatField(verbose_name="粗脂肪-成分值(g)")
    carbohydrates = models.FloatField(verbose_name="總碳水化合物-成分值(g)", blank=True, null=True)
    dietary_fiber = models.FloatField(verbose_name="膳食纖維-成分值(g)", blank=True, null=True)
    metabolic_carbohydrates = models.FloatField(verbose_name="可代謝醣類(g)")


class FoodNameModel(models.Model):
    known_as_name = models.CharField(verbose_name="代稱", max_length=100)
    food = models.ForeignKey(FoodModel)


class NutritionModel(models.Model):
    # six groups
    fruit_amount = models.FloatField(verbose_name="水果類")
    vegetable_amount = models.FloatField(verbose_name="蔬菜類")
    grain_amount = models.FloatField(verbose_name="全榖根莖類")
    protein_food_amount = models.FloatField(verbose_name="蛋豆魚肉類")
    diary_amount = models.FloatField(verbose_name="低脂乳品類")
    oil_amount = models.FloatField(verbose_name="油脂與堅果種子類")
    # nutrition
    gram = models.FloatField(verbose_name="重量")
    calories = models.FloatField(verbose_name="熱量")
    protein = models.FloatField(verbose_name="蛋白質")
    fat = models.FloatField(verbose_name="脂質")
    carbohydrates = models.FloatField(verbose_name="碳水化合物")
    six_group_portion_image = models.ImageField(verbose_name="六大類份數圖表", upload_to="six_group_portion/", blank=True)
    nutrition_amount_image = models.ImageField(verbose_name="營養含量圖表", upload_to="nutrition_amount/", blank=True)


class TaiwanSnackModel(models.Model):
    name = models.CharField(verbose_name="名稱", max_length=100)
    nutrition = models.OneToOneField(NutritionModel)


class TaiwanSnackNameSynonymModel(models.Model):
    synonym = models.CharField(verbose_name="代稱", max_length=100)
    snack = models.ForeignKey(TaiwanSnackModel)

