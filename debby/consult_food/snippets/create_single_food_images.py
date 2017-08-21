import os

import django
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'debby.settings'
django.setup()

from consult_food.models import SynonymModel, NutritionTuple, ImageType

def run():
    nutrition = NutritionTuple(name='蛋沙拉潛艇堡',
                               gram=0.0, calories=307, protein=11.16, fat=8.36, carbohydrates=48,
                               fruit_amount=0.0, vegetable_amount=0.42, grain_amount=2.79,
                               protein_food_amount=0.385, diary_amount=0.179, oil_amount=0.525
                               ).functions()
    calories_image = nutrition.make_calories_image()
    six_group_image = nutrition.make_six_group_image()
    nutrition.save_img(calories_image, 'demo', ImageType.CALORIES)
    nutrition.save_img(six_group_image, 'demo', ImageType.SIX_GROUP)

if __name__ == '__main__':
    run()
