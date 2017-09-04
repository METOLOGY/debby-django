import csv
import os

import django

from debby import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'debby.settings'
django.setup()


def run():
    from consult_food.models import FoodModel, NutritionModel, NutritionTuple
    from debby import utils
    chat_table_dir = os.path.join(settings.PROJECT_DIR, 'chat_table')
    file_path = os.path.join(chat_table_dir, 'fast_food.csv')

    with open(file_path, encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(row['name'])
            nutrition = NutritionTuple(name=row['name'],
                                       gram=utils.to_number(row['gram']),
                                       calories=utils.to_number(row['calories']),
                                       protein=utils.to_number(row['protein']),
                                       fat=utils.to_number(row['fat']),
                                       carbohydrates=utils.to_number(row['carbohydrates']))
            nutrition_model = NutritionModel.objects.create(**nutrition._asdict())
            nutrition_model.make_and_save_calories_image()

            food_model = FoodModel()
            food_model.name = row['name']
            food_model.count_word = row['count_word']
            food_model.source = row['source']
            food_model.nutrition = nutrition_model
            food_model.synonyms.create(synonym=food_model.name)
            food_model.save()


if __name__ == '__main__':
    run()
