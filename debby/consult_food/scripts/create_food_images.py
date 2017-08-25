import os

from PIL import Image

from consult_food.image_maker import SixGroupPortionMaker, SixGroupParameters, CaloriesParameters, CaloriesMaker
from consult_food.models import TaiwanSnackModel, NutritionModel, TFDAModel


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


def create_six_group(nutrition):
    if nutrition.is_six_group_valid():
        parameters = SixGroupParameters(grains=nutrition.grain_amount,
                                        fruits=nutrition.fruit_amount,
                                        vegetables=nutrition.vegetable_amount,
                                        protein_foods=nutrition.protein_food_amount,
                                        diaries=nutrition.diary_amount,
                                        oil=nutrition.oil_amount)
        maker = SixGroupPortionMaker()
        maker.make_img(parameters)
        save_img(maker.img, nutrition.id, 'six_group_portion')


def create_calories(nutrition):
    carbohydrates_calories = nutrition.carbohydrates * 4
    fat_calories = nutrition.fat * 9
    protein_calories = nutrition.protein * 4
    total = carbohydrates_calories + fat_calories + protein_calories
    carbohydrates_percentages = carbohydrates_calories / total * 100
    fat_percentages = fat_calories / total * 100
    protein_percentages = protein_calories / total * 100

    parameters = CaloriesParameters(sample_name=nutrition.name,
                                    calories=nutrition.calories,
                                    carbohydrates_grams=nutrition.carbohydrates,
                                    carbohydrates_percentages=carbohydrates_percentages,
                                    fat_grams=nutrition.fat,
                                    fat_percentages=fat_percentages,
                                    protein_grams=nutrition.protein,
                                    protein_percentages=protein_percentages)
    maker = CaloriesMaker()
    maker.make_img(parameters)
    save_img(maker.img, nutrition.id, 'nutrition_amount')


def save_to_nutrition(nutrition: NutritionModel):
    if nutrition.is_six_group_valid():
        nutrition.six_group_portion_image = os.path.join('ConsultFood',
                                                         'six_group_portion',
                                                         '{}.jpeg'.format(nutrition.id))
        nutrition.six_group_portion_image_preview = os.path.join('ConsultFood',
                                                                 'six_group_portion_preview',
                                                                 '{}.jpeg'.format(nutrition.id))

    else:
        nutrition.six_group_portion_image = None
        nutrition.six_group_portion_image_preview = None

    nutrition.nutrition_amount_image = os.path.join('ConsultFood',
                                                    'nutrition_amount',
                                                    '{}.jpeg'.format(nutrition.id))
    nutrition.nutrition_amount_image_preview = os.path.join('ConsultFood',
                                                            'nutrition_amount_preview',
                                                            '{}.jpeg'.format(nutrition.id))

    nutrition.save()


def run():
    queries = TaiwanSnackModel.objects.all()
    for food in queries:
        print("food id:{}, ".format(food.id))
        if food.nutrition:
            nutrition = food.nutrition
            print("nutrition id:{}".format(nutrition.id))

            create_six_group(nutrition)
            create_calories(nutrition)

            save_to_nutrition(nutrition)

        else:
            print('no nutrition')

    queries = TFDAModel.objects.all()
    for food in queries:
        print("food id:{}, ".format(food.id))
        if food.nutrition:
            nutrition = food.nutrition
            print("nutrition id:{}".format(nutrition.id))

            create_six_group(nutrition)
            create_calories(nutrition)

            save_to_nutrition(nutrition)

        else:
            print('no nutrition')


if __name__ == '__main__':
    run()
