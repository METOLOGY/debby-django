import os
from datetime import datetime
from io import BytesIO

from PIL import Image
from django.core.files import File
from django.core.files.storage import default_storage as storage
from django.db import models
from django.contrib.postgres.fields import JSONField
from google.cloud import vision
import io
import json


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
    webEntities = JSONField()


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


    # clone from GCP example: https://cloud.google.com/vision/docs/detecting-web?hl=zh-tw#vision-web-detection-gcs-python
    # modify to fit food_record model.
    def detect_web(self):
        """Detects web annotations given an image."""
        vision_client = vision.Client()

        with io.open(self.food_image_upload.url, 'rb') as image_file:
            content = image_file.read()

        image = vision_client.image(content=content)

        notes = image.detect_web()

        # TODO: discuss whether we have to save these results.
        # if notes.pages_with_matching_images:
        #     print('\n{} Pages with matching images retrieved')
        #
        #     for page in notes.pages_with_matching_images:
        #         print('Score : {}'.format(page.score))
        #         print('Url   : {}'.format(page.url))
        #
        # if notes.full_matching_images:
        #     print('\n{} Full Matches found: '.format(
        #         len(notes.full_matching_images)))
        #
        #     for image in notes.full_matching_images:
        #         print('Score:  {}'.format(image.score))
        #         print('Url  : {}'.format(image.url))
        #
        # if notes.partial_matching_images:
        #     print('\n{} Partial Matches found: '.format(
        #         len(notes.partial_matching_images)))
        #
        #     for image in notes.partial_matching_images:
        #         print('Score: {}'.format(image.score))
        #         print('Url  : {}'.format(image.url))

        if notes.web_entities:
            # print('\n{} Web entities found: '.format(len(notes.web_entities)))
            entities = {}
            for entity in notes.web_entities:
                entities[entity.description] = entity.score
                # print('Score      : {}'.format(entity.score))
                # print('Description: {}'.format(entity.description))

            self.webEntities.save(json.dumps(entities))

class TempImageModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    food_image_upload = models.ImageField(upload_to=user_id_path)
    time = models.DateTimeField(auto_now_add=True)  # may be modified from my_diary
    create_time = models.DateTimeField(auto_now_add=True, editable=False)  # temp create time won't be modified
    note = models.CharField(max_length=200)
    carousel = models.ImageField()

    def delete(self, *args, **kwargs):
        # object is being removed from db, remove the file from storage first
        self.food_image_upload.delete()
        return super(TempImageModel, self).delete(*args, **kwargs)

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
