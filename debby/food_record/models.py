from django.db import models

# Create your models here.
from user.models import CustomUserModel


class FoodModel(models.Model):
    user = models.ForeignKey(CustomUserModel)
    calories = models.IntegerField(null=True, blank=True)
    gi_value = models.IntegerField(null=True, blank=True)
    food_name = models.CharField(max_length=50)
    food_image_upload = models.ImageField(upload_to='FoodRecord')
    note = models.CharField(max_length=200)
    time = models.DateTimeField(auto_now_add=True)


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

