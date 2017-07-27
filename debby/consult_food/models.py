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


class FoodModelManager(models.Manager):
    def search_by_known_as_name(self, name: str):
        return self.filter(food_names__known_as_name=name)


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
    nutrition = models.OneToOneField('NutritionModel', blank=True, null=True)

    objects = FoodModelManager()


class FoodNameModelManager(models.Manager):
    def search_by_known_as_name(self, name: str):
        return self.filter(known_as_name=name)


class FoodNameModel(models.Model):
    known_as_name = models.CharField(verbose_name="代稱", max_length=100)
    food = models.ForeignKey(FoodModel, related_name='food_names')

    objects = FoodNameModelManager()


class NutritionModel(models.Model):
    # six groups
    fruit_amount = models.FloatField(verbose_name="水果類", default=0.0)
    vegetable_amount = models.FloatField(verbose_name="蔬菜類", default=0.0)
    grain_amount = models.FloatField(verbose_name="全榖根莖類", default=0.0)
    protein_food_amount = models.FloatField(verbose_name="蛋豆魚肉類", default=0.0)
    diary_amount = models.FloatField(verbose_name="低脂乳品類", default=0.0)
    oil_amount = models.FloatField(verbose_name="油脂與堅果種子類", default=0.0)
    # nutrition
    gram = models.FloatField(verbose_name="重量")
    calories = models.FloatField(verbose_name="熱量")
    protein = models.FloatField(verbose_name="蛋白質")
    fat = models.FloatField(verbose_name="脂質")
    carbohydrates = models.FloatField(verbose_name="碳水化合物")
    six_group_portion_image = models.ImageField(verbose_name="六大類份數圖表",
                                                upload_to="ConsultFood/six_group_portion/",
                                                blank=True)
    six_group_portion_image_preview = models.ImageField(verbose_name="六大類份數圖表(preview)",
                                                        upload_to="ConsultFood/six_group_portion_preview/",
                                                        blank=True)
    nutrition_amount_image = models.ImageField(verbose_name="營養含量圖表",
                                               upload_to="ConsultFood/nutrition_amount/",
                                               blank=True)
    nutrition_amount_image_preview = models.ImageField(verbose_name="營養含量圖表(preview)",
                                                       upload_to="ConsultFood/nutrition_amount/",
                                                       blank=True)


class TaiwanSnackModelManager(models.Manager):
    def search_by_name(self, name: str):
        return self.filter(name=name)

    def search_by_synonym(self, name: str):
        return self.filter(synonyms__synonym=name)


class TaiwanSnackModel(models.Model):
    name = models.CharField(verbose_name="名稱", max_length=100)
    nutrition = models.OneToOneField(NutritionModel)

    objects = TaiwanSnackModelManager()


class TaiwanSnackNameSynonymModelManager(models.Manager):
    def search_by_name(self, name: str):
        return self.filter(synonym=name)


class TaiwanSnackNameSynonymModel(models.Model):
    synonym = models.CharField(verbose_name="代稱", max_length=100)
    snack = models.ForeignKey(TaiwanSnackModel, related_name='synonyms')

    objects = TaiwanSnackNameSynonymModelManager()


class ICookIngredientModel(models.Model):
    name = models.CharField(verbose_name="食材名稱", max_length=100, unique=True)
    nutrition = models.ForeignKey(NutritionModel)
