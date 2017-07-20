import os

from PIL import Image, ImageDraw, ImageFont

from consult_food.models import TaiwanSnackModel


# python manage.py runscript add_image_to_nutrition_model --traceback

def create_img(snack: TaiwanSnackModel):
    img = Image.open('../nutrition/bg.jpg')
    fnt = ImageFont.truetype('../nutrition/wt014.ttf', 55)
    fnt2 = ImageFont.truetype('../nutrition/wt014.ttf', 50)

    d = ImageDraw.Draw(img)

    d.text((80, 530), "熱量：{:.0f}大卡".format(snack.nutrition.calories), font=fnt, fill=(237, 111, 5))
    d.text((870, 100), "醣類：{:.1f}克".format(snack.nutrition.protein), font=fnt2, fill=(0, 103, 170))
    d.text((870, 340), "蛋白質：{:.1f}克".format(snack.nutrition.fat), font=fnt2, fill=(0, 103, 170))
    d.text((870, 570), "脂肪：{:.1f}克".format(snack.nutrition.carbohydrates), font=fnt2, fill=(0, 103, 170))
    return img


def save_img(img: Image.Image, nutrition_id):
    print(nutrition_id)
    directory = "../media/ConsultFood"
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory = "../media/ConsultFood/nutrition_amount"
    if not os.path.exists(directory):
        os.makedirs(directory)

    ratio = 1024 / img.size[0]
    img2 = img.resize((1024, int(img.size[1] * ratio)), resample=Image.BICUBIC)
    img2.save('{}/{}.jpeg'.format(directory, nutrition_id))

    directory = "../media/ConsultFood/nutrition_amount_preview"
    if not os.path.exists(directory):
        os.makedirs(directory)

    ratio = 240 / img.size[0]
    img.thumbnail((240, int(img.size[1] * ratio)), Image.ANTIALIAS)
    img.save('{}/{}.jpeg'.format(directory, nutrition_id))


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
