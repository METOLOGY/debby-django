import os

from PIL import Image, ImageDraw, ImageFont

# python manage.py runscript add_image_to_nutrition_model --traceback
from consult_food.models import FoodModel, NutritionModel


def create_img(food: FoodModel):
    img = Image.open('../nutrition/calories.png')

    fnt = ImageFont.truetype('../nutrition/wt004.ttf', 70)
    fnt2 = ImageFont.truetype('../nutrition/wt004.ttf', 60)

    d = ImageDraw.Draw(img)

    d.text((370, 100), "{} 大卡".format(food.modified_calorie), font=fnt, fill=(255, 0, 0))
    d.text((60, 810), "{:.2f} g".format(food.crude_protein), font=fnt2, fill=(0, 0, 0))
    d.text((450, 910), "{:.2f} g".format(food.crude_fat), font=fnt2, fill=(0, 0, 0))
    d.text((800, 820), "{:.2f} g".format(food.carbohydrates), font=fnt2, fill=(0, 0, 0))
    return img


def save_img(img: Image.Image, nutrition_id):
    print(nutrition_id)
    directory = "../media/ConsultFood"
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory = "../media/ConsultFood/nutrition_amount"
    if not os.path.exists(directory):
        os.makedirs(directory)
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img)
    bg.save('{}/{}.jpeg'.format(directory, nutrition_id))

    directory = "../media/ConsultFood/nutrition_amount_preview"
    if not os.path.exists(directory):
        os.makedirs(directory)
    bg.thumbnail((240, 240), Image.ANTIALIAS)
    bg.save('{}/{}.jpeg'.format(directory, nutrition_id))


def run():
    queries = FoodModel.objects.all()
    for food in queries:
        if not food.nutrition:
            nutrition = NutritionModel.objects.create(gram=100,
                                                      calories=food.modified_calorie,
                                                      protein=food.crude_protein,
                                                      fat=food.crude_fat,
                                                      carbohydrates=food.carbohydrates,
                                                      )
        else:
            nutrition = food.nutrition

        nutrition.nutrition_amount_image = os.path.join('ConsultFood', 'nutrition_amount',
                                                        '{}.jpeg'.format(nutrition.id))
        nutrition.nutrition_amount_image_preview = os.path.join('ConsultFood',
                                                                'nutrition_amount_preview',
                                                                '{}.jpeg'.format(nutrition.id))
        nutrition.save()

        food.nutrition = nutrition
        food.save()

        img = create_img(food)
        save_img(img, nutrition.id)
