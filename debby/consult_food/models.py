import os
from typing import NamedTuple

from PIL import Image
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Create your models here.
from consult_food.image_maker import CaloriesParameters, CaloriesMaker, SixGroupParameters, SixGroupPortionMaker


class SynonymModelManager(models.Manager):
    def search_by_synonym(self, name: str):
        return self.filter(synonym=name)

    # Generic
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


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

    def is_valid(self):
        return self.gram is not None and \
               self.calories is not None and \
               self.protein is not None and \
               self.fat is not None and \
               self.carbohydrates is not None


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

    @staticmethod
    def save_img(img: Image, nutrition_id: int, type_name: str):
        directory = "../media/ConsultFood"
        if not os.path.exists(directory):
            os.makedirs(directory)
        directory = "../media/ConsultFood/" + type_name
        if not os.path.exists(directory):
            os.makedirs(directory)
        img2 = img.convert('RGB')
        img2.save('{}/{}.jpeg'.format(directory, nutrition_id), quality=95)

        directory = "../media/ConsultFood/" + type_name + "_preview"
        if not os.path.exists(directory):
            os.makedirs(directory)

        img2.thumbnail((240, 240), Image.ANTIALIAS)
        img2.save('{}/{}.jpeg'.format(directory, nutrition_id), quality=95)

    def make_calories_image(self):
        carbohydrates_calories = self.carbohydrates * 4
        fat_calories = self.fat * 9
        protein_calories = self.protein * 4
        total = carbohydrates_calories + fat_calories + protein_calories
        if total != 0:
            carbohydrates_percentages = carbohydrates_calories / total * 100
            fat_percentages = fat_calories / total * 100
            protein_percentages = protein_calories / total * 100
        else:
            carbohydrates_percentages = 0
            fat_percentages = 0
            protein_percentages = 0
        parameters = CaloriesParameters(sample_name=self.name,
                                        calories=self.calories,
                                        carbohydrates_grams=self.carbohydrates,
                                        carbohydrates_percentages=carbohydrates_percentages,
                                        fat_grams=self.fat,
                                        fat_percentages=fat_percentages,
                                        protein_grams=self.protein,
                                        protein_percentages=protein_percentages)
        maker = CaloriesMaker()
        maker.make_img(parameters)
        self.save_img(maker.img, self.id, 'nutrition_amount')
        self.nutrition_amount_image = os.path.join('ConsultFood',
                                                   'nutrition_amount',
                                                   '{}.jpeg'.format(self.id))
        self.nutrition_amount_image_preview = os.path.join('ConsultFood',
                                                           'nutrition_amount_preview',
                                                           '{}.jpeg'.format(self.id))

    def create_six_group(self):
        if self.is_six_group_exist():
            parameters = SixGroupParameters(grains=self.grain_amount,
                                            fruits=self.fruit_amount,
                                            vegetables=self.vegetable_amount,
                                            protein_foods=self.protein_food_amount,
                                            diaries=self.diary_amount,
                                            oil=self.oil_amount)
            maker = SixGroupPortionMaker()
            maker.make_img(parameters)
            self.save_img(maker.img, self.id, 'six_group_portion')

            self.six_group_portion_image = os.path.join('ConsultFood',
                                                        'six_group_portion',
                                                        '{}.jpeg'.format(self.id))
            self.six_group_portion_image_preview = os.path.join('ConsultFood',
                                                                'six_group_portion_preview',
                                                                '{}.jpeg'.format(self.id))

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

    def search_by_synonym(self, name: str):
        return self.filter(synonyms__synonym=name)


class ICookIngredientModel(models.Model):
    name = models.CharField(verbose_name="食材名稱", max_length=100, unique=True)
    nutrition = models.ForeignKey(NutritionModel, null=True, blank=True)
    synonyms = GenericRelation(SynonymModel)
    source = models.TextField(default="TFDA")

    gram = models.FloatField(verbose_name="重量", null=True, blank=True, default=0.0)
    calories = models.FloatField(verbose_name="熱量", null=True, blank=True, default=0.0)
    protein = models.FloatField(verbose_name="蛋白質", null=True, blank=True, default=0.0)
    fat = models.FloatField(verbose_name="脂質", null=True, blank=True, default=0.0)
    carbohydrates = models.FloatField(verbose_name="碳水化合物", null=True, blank=True, default=0.0)
    sodium = models.FloatField(verbose_name="鈉", null=True, blank=True, default=0.0)

    objects = ICookIngredientModelManager()
