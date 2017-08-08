from typing import NamedTuple

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models


# Create your models here.
from django.utils.safestring import mark_safe


class SynonymModelManager(models.Manager):
    def search_by_synonym(self, name: str):
        return self.filter(synonym=name)


class SynonymModel(models.Model):
    synonym = models.CharField(verbose_name="代稱", max_length=100)

    # Generic

    content_type = models.ForeignKey(ContentType, limit_choices_to={"model__in": ("FoodModel", "TaiwanSnackModel")})
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = SynonymModelManager()

    def __str__(self):
        return "id: {}, synonym: {}".format(self.id, self.synonym)


class Nutrition(NamedTuple):
    name: str
    # nutrition
    gram: float
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    # six groups
    fruit_amount: float = 0.0
    vegetable_amount: float = 0.0
    grain_amount: float = 0.0
    protein_food_amount: float = 0.0
    diary_amount: float = 0.0
    oil_amount: float = 0.0


class NutritionModelManager(models.Manager):
    #  TODO: Experimental. It seems nonsense
    def is_nutrition_already_exist(self, nutrition: Nutrition):
        q = self.filter(
            name=nutrition.name,
            gram=nutrition.gram,
            calories=nutrition.calories,
            protein=nutrition.protein,
            fat=nutrition.fat,
            carbohydrates=nutrition.carbohydrates,
            fruit_amount=nutrition.fruit_amount,
            vegetable_amount=nutrition.vegetable_amount,
            grain_amount=nutrition.grain_amount,
            protein_food_amount=nutrition.protein_food_amount,
            diary_amount=nutrition.diary_amount,
            oil_amount=nutrition.oil_amount
        )
        return q.count() > 0


class NutritionModel(models.Model):
    # six groups
    name = models.CharField(max_length=30, verbose_name="名稱", default="")
    fruit_amount = models.FloatField(verbose_name="水果類", default=0.0)
    vegetable_amount = models.FloatField(verbose_name="蔬菜類", default=0.0)
    grain_amount = models.FloatField(verbose_name="全榖根莖類", default=0.0)
    protein_food_amount = models.FloatField(verbose_name="蛋豆魚肉類", default=0.0)
    diary_amount = models.FloatField(verbose_name="低脂乳品類", default=0.0)
    oil_amount = models.FloatField(verbose_name="油脂與堅果種子類", default=0.0)
    # nutrition
    gram = models.FloatField(verbose_name="重量", blank=True)
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

    def is_six_group_exist(self):
        return self.fruit_amount + self.vegetable_amount + self.grain_amount + self.protein_food_amount \
               + self.diary_amount + self.oil_amount > 0

    objects = NutritionModelManager()

    def __str__(self):
        return "id: {}, name: {}".format(self.id, self.name)

class FoodModelManager(models.Manager):
    def search_by_name(self, name: str):
        return self.filter(sample_name=name)

    def search_by_synonyms(self, name: str):
        return self.filter(synonyms__synonym=name)


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
    nutrition = models.OneToOneField(NutritionModel, blank=True, null=True)
    synonyms = GenericRelation(SynonymModel)

    objects = FoodModelManager()

    def list_synonyms(self):
        synonyms = self.synonyms.all()
        synonym_list = [s.synonym for s in synonyms]
        return ', '.join(synonym_list)

    list_synonyms.short_description = "代稱"


class TaiwanSnackModelManager(models.Manager):
    def search_by_name(self, name: str):
        return self.filter(name=name)

    def search_by_synonym(self, name: str):
        return self.filter(synonyms__synonym=name)


class TaiwanSnackModel(models.Model):
    name = models.CharField(verbose_name="名稱", max_length=100)
    place = models.CharField(verbose_name="地方", max_length=20, default="")
    count_word = models.CharField(verbose_name="量詞", max_length=20, default="")
    nutrition = models.OneToOneField(NutritionModel)
    synonyms = GenericRelation(SynonymModel)

    objects = TaiwanSnackModelManager()

    def list_synonyms(self):
        synonyms = self.synonyms.all()
        synonym_list = [s.synonym for s in synonyms]
        return ', '.join(synonym_list)

    def __str__(self):
        return self.name


class ICookIngredientModelManager(models.Manager):
    def search_by_name(self, name: str):
        return self.filter(name=name)


class ICookIngredientModel(models.Model):
    name = models.CharField(verbose_name="食材名稱", max_length=100, unique=True)
    nutrition = models.ForeignKey(NutritionModel)

    objects = ICookIngredientModelManager()
