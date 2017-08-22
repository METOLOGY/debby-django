import os
from enum import Enum
from pathlib import Path
from typing import NamedTuple, Union

from PIL import Image
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Create your models here.
from consult_food.image_maker import CaloriesParameters, CaloriesMaker, SixGroupParameters, SixGroupPortionMaker
from debby import settings


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

    content_type = models.ForeignKey(ContentType,
                                     limit_choices_to={
                                         "model__in": ("FoodModel",
                                                       "TaiwanSnackModel",
                                                       "ICookIngredientModel",
                                                       "ICookDishModel")
                                     })
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = SynonymModelManager()

    def __str__(self):
        return "id: {}, synonym: {}".format(self.id, self.synonym)


class ImageType(Enum):
    CALORIES = 'nutrition_amount'
    SIX_GROUP = 'six_group_portion'


NutritionExtended = Union['NutritionTuple', 'NutritionModel']


class NutritionMixin:
    def is_valid(self: NutritionExtended):
        return self.gram is not None and \
               self.calories is not None and \
               self.protein is not None and \
               self.fat is not None and \
               self.carbohydrates is not None

    def is_six_group_valid(self: NutritionExtended):
        return self.fruit_amount + self.vegetable_amount + self.grain_amount + self.protein_food_amount \
               + self.diary_amount + self.oil_amount > 0

    @staticmethod
    def save_img(img: Image, nutrition_id: int, image_type: ImageType):
        media_dir = os.path.join(settings.PROJECT_DIR, 'media')
        directory = os.path.join(media_dir, "ConsultFood")
        if not os.path.exists(directory):
            os.makedirs(directory)
        directory = os.path.join(media_dir, "ConsultFood", image_type.value)
        if not os.path.exists(directory):
            os.makedirs(directory)
        img2 = img.convert('RGB')
        img2.save('{}/{}.jpeg'.format(directory, nutrition_id), quality=95)

        directory = os.path.join(media_dir, "ConsultFood", image_type.value + "_preview")
        if not os.path.exists(directory):
            os.makedirs(directory)

        img2.thumbnail((240, 240), Image.ANTIALIAS)
        img2.save('{}/{}.jpeg'.format(directory, nutrition_id), quality=95)

    def make_calories_image(self: NutritionExtended):
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
        return maker.img

    def make_six_group_image(self: NutritionExtended):
        if self.is_six_group_valid():
            parameters = SixGroupParameters(grains=self.grain_amount,
                                            fruits=self.fruit_amount,
                                            vegetables=self.vegetable_amount,
                                            protein_foods=self.protein_food_amount,
                                            diaries=self.diary_amount,
                                            oil=self.oil_amount)
            maker = SixGroupPortionMaker()
            maker.make_img(parameters)
            return maker.img


class NutritionTuple(NamedTuple):
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

    def functions(self):
        return NutritionFunctions(self)


class NutritionFunctions(NutritionMixin):
    def __init__(self, nutrition_data: NutritionTuple):
        super().__init__()
        self.name = nutrition_data.name
        self.gram = nutrition_data.gram
        self.calories = nutrition_data.calories
        self.carbohydrates = nutrition_data.carbohydrates
        self.fat = nutrition_data.fat
        self.protein = nutrition_data.protein
        self.grain_amount = nutrition_data.grain_amount
        self.fruit_amount = nutrition_data.fruit_amount
        self.vegetable_amount = nutrition_data.vegetable_amount
        self.protein_food_amount = nutrition_data.protein_food_amount
        self.diary_amount = nutrition_data.diary_amount
        self.oil_amount = nutrition_data.oil_amount


class NutritionModel(NutritionMixin, models.Model):
    # six groups
    name = models.CharField(max_length=30, verbose_name="名稱", default="")
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

    def is_calories_image_created(self):
        directory = "../media/ConsultFood/" + ImageType.CALORIES.value
        file = Path('{}/{}.jpeg'.format(directory, self.id))
        return file.is_file()

    def is_six_group_image_created(self):
        directory = "../media/ConsultFood/" + ImageType.SIX_GROUP.value
        file = Path('{}/{}.jpeg'.format(directory, self.id))
        return file.is_file()

    def delete_six_group_image(self):
        directory = "../media/ConsultFood/" + ImageType.SIX_GROUP.value
        file = Path('{}/{}.jpeg'.format(directory, self.id))
        if file.is_file():
            file.unlink()
            self.six_group_portion_image = ''
            self.six_group_portion_image_preview = ''

    def make_and_save_calories_image(self):
        img = self.make_calories_image()
        self.save_img(img, self.id, ImageType.CALORIES)
        self.nutrition_amount_image = os.path.join('ConsultFood',
                                                   ImageType.CALORIES.value,
                                                   '{}.jpeg'.format(self.id))
        self.nutrition_amount_image_preview = os.path.join('ConsultFood',
                                                           ImageType.CALORIES.value + '_preview',
                                                           '{}.jpeg'.format(self.id))

    def make_and_save_six_group_image(self):
        img = self.make_six_group_image()
        self.save_img(img, self.id, ImageType.SIX_GROUP)

        self.six_group_portion_image = os.path.join('ConsultFood',
                                                    ImageType.SIX_GROUP.value,
                                                    '{}.jpeg'.format(self.id))
        self.six_group_portion_image_preview = os.path.join('ConsultFood',
                                                            ImageType.SIX_GROUP.value + '_preview',
                                                            '{}.jpeg'.format(self.id))

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

    def is_in_db_already(self, name: str, gram: float):
        return self.filter(name=name, gram=gram).count()


class ICookIngredientModel(models.Model):
    name = models.CharField(verbose_name="食材名稱", max_length=100)
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


class ICookDishModelManager(models.Manager):
    def is_in_db_already(self, source_url: str):
        return self.filter(source_url=source_url).count()

    def search_by_name(self, name: str):
        return self.filter(name=name)

    def search_by_synonym(self, name: str):
        return self.filter(synonyms__synonym=name)


class ICookDishModel(models.Model):
    name = models.CharField(verbose_name="菜餚名稱", max_length=50)
    source_url = models.TextField()
    count_word = models.CharField(max_length=20, blank=False)

    nutrition = models.OneToOneField(NutritionModel, blank=False)

    synonyms = GenericRelation(SynonymModel)

    objects = ICookDishModelManager()


class ICookDishIngredientModel(models.Model):
    name = models.CharField(verbose_name="食材名稱", max_length=20)
    gram = models.FloatField(verbose_name='克')
    dish = models.ForeignKey('ICookDishModel', blank=False)


class WikiFoodTranslateModel(models.Model):
    english = models.CharField(verbose_name='en', max_length=100)
    chinese = models.CharField(verbose_name='zh-tw', max_length=100, blank=True, default=True)
