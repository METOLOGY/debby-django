import os

from PIL import Image

from consult_food.models import TaiwanSnackModel


# python manage.py runscript add_six_portion_image --traceback

def save_img(img: Image.Image, nutrition_id: int):
    print(nutrition_id)
    directory = "../media/ConsultFood"
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory = "../media/ConsultFood/six_group_portion"
    if not os.path.exists(directory):
        os.makedirs(directory)

    ratio = 1024 / img.size[0]
    img2: Image.Image = img.resize((1024, int(img.size[1] * ratio)), resample=Image.BICUBIC)
    img2.save('{}/{}.jpeg'.format(directory, nutrition_id))

    directory = "../media/ConsultFood/six_group_portion_preview"
    if not os.path.exists(directory):
        os.makedirs(directory)

    ratio = 240 / img.size[0]
    img.thumbnail((240, int(img.size[1] * ratio)), Image.ANTIALIAS)
    img.save('{}/{}.jpeg'.format(directory, nutrition_id))


def run():
    folder_path = '../nutrition/temp'
    file_names = os.listdir(folder_path)
    for f in file_names:
        file_path = os.path.join(folder_path, f)
        img = Image.open(file_path)

        id_ = int(f.rstrip('.jpg'))
        save_img(img, id_)

        snack = TaiwanSnackModel.objects.get(nutrition_id=id_)
        snack.nutrition.six_group_portion_image = os.path.join('ConsultFood',
                                                               'six_group_portion',
                                                               '{}.jpeg'.format(snack.nutrition_id))
        snack.nutrition.six_group_portion_image_preview = os.path.join('ConsultFood',
                                                                       'six_group_portion_preview',
                                                                       '{}.jpeg'.format(snack.nutrition_id))
        snack.nutrition.save()
