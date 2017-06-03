import os
from datetime import datetime
from io import BytesIO

from PIL import Image
from django.core.files import File
from django.core.files.storage import default_storage as storage
from django.db import models

# Create your models here.
from user.models import CustomUserModel


def user_id_path(instance, filename):
    date = datetime.today().date()
    file_type = filename.split('.')[1]
    today_image_count = len(FoodModel.objects.filter(time__date=date)) + 1  # add one for the new one
    return '{}/{}'.format(instance.user.line_id,
                          instance.user.line_id + '_' + str(date) + '_' + str(today_image_count) + '.' + file_type)


class FoodModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    calories = models.IntegerField(null=True, blank=True)
    gi_value = models.IntegerField(null=True, blank=True)
    food_name = models.CharField(max_length=50)
    note = models.CharField(max_length=200)
    time = models.DateTimeField(auto_now_add=True)
    food_image_upload = models.ImageField(upload_to=user_id_path)
    carousel = models.ImageField()

    # def save(self, *args, **kwargs):
    #     super(FoodModel, self).save(*args, **kwargs)

    def make_carousel(self):
        """
        Create and save the thumbnail for the photo (simple resize with PIL).
        """
        fh = storage.open(self.food_image_upload.name)
        try:
            image = Image.open(fh)
        except:
            raise Exception()

        size = (512, 339)
        image.thumbnail(size, Image.ANTIALIAS)
        carousel = Image.new('RGBA', size, (255, 255, 255, 255))
        carousel.paste(
            image, (int((size[0] - image.size[0]) // 2), int((size[1] - image.size[1]) // 2))
        )
        fh.close()

        # Path to save to, name, and extension
        carousel_name, carousel_extension = os.path.splitext(self.food_image_upload.name)
        carousel_extension = carousel_extension.lower()

        carousel_filename = carousel_name + '_carousel' + carousel_extension

        if carousel_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif carousel_extension == '.gif':
            FTYPE = 'GIF'
        elif carousel_extension == '.png':
            FTYPE = 'PNG'
        else:
            return False  # Unrecognized file type

        # Save thumbnail to in-memory file as StringIO
        temp_file = BytesIO()
        carousel.save(temp_file, FTYPE)

        # Load a ContentFile into the thumbnail field so it gets saved
        self.carousel.save(carousel_filename, File(temp_file), save=True)


class TempImageModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    image_upload = models.ImageField(upload_to='Temp')
    time = models.DateTimeField(auto_now_add=True)

    def remove_on_image_update(self):
        try:
            # is the object in the database yet?
            obj = TempImageModel.objects.get(id=self.id)
        except TempImageModel.DoesNotExist:
            # object is not in db, nothing to worry about
            return
        # is the save due to an update of the actual image file?
        if obj.image_upload and self.image_upload and obj.image_upload != self.image_upload:
            # delete the old image file from the storage in favor of the new file
            obj.image_upload.delete()

    def delete(self, *args, **kwargs):
        # object is being removed from db, remove the file from storage first
        self.image_upload.delete()
        return super(TempImageModel, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # object is possibly being updated, if so, clean up.
        self.remove_on_image_update()
        return super(TempImageModel, self).save(*args, **kwargs)
