import os

from PIL import Image, ImageDraw, ImageFont

from consult_food.models import TaiwanSnackModel


# python manage.py runscript add_image_to_nutrition_model --traceback

def create_img(snack: TaiwanSnackModel):
    img = Image.open('../nutrition/calories.png')

    fnt = ImageFont.truetype('../nutrition/wt004.ttf', 70)
    fnt2 = ImageFont.truetype('../nutrition/wt004.ttf', 60)

    d = ImageDraw.Draw(img)

    d.text((370, 100), "{} 大卡".format(snack.nutrition.calories), font=fnt, fill=(255, 0, 0))
    d.text((60, 810), "{} g".format(snack.nutrition.protein), font=fnt2, fill=(0, 0, 0))
    d.text((450, 910), "{} g".format(snack.nutrition.fat), font=fnt2, fill=(0, 0, 0))
    d.text((800, 820), "{} g".format(snack.nutrition.carbohydrates), font=fnt2, fill=(0, 0, 0))
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
    queries = TaiwanSnackModel.objects.all()
    for snack in queries:
        img = create_img(snack)
        save_img(img, snack.nutrition_id)
        snack.nutrition.nutrition_amount_image = os.path.join('ConsultFood', 'nutrition_amount',
                                                              '{}.jpeg'.format(snack.nutrition_id))
        snack.nutrition.nutrition_amount_image_preview = os.path.join('ConsultFood',
                                                                      'nutrition_amount_preview',
                                                                      '{}.jpeg'.format(snack.nutrition_id))
        snack.nutrition.save()
