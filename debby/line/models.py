from typing import Union

from django.db import models


class EventModelManager(models.Manager):
    def get_or_none(self, **kwargs) -> Union['EventModel', None]:
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def get_unique_or_none(self, *args, **kwargs)-> Union['EventModel', None]:
        try:
            return self.get(*args, **kwargs)
        except (self.model.DoesNotExist, self.model.MultipleObjectsReturned):
            return None


class EventModel(models.Model):
    phrase = models.CharField(max_length=30, blank=False)
    callback = models.CharField(max_length=30, blank=False)
    action = models.CharField(max_length=30, blank=False)

    objects = EventModelManager()


class ReservedKeywordsModelManager(models.Manager):
    def is_reserved_keywords(self, text: str) -> bool:
        return self.filter(keyword=text)


class ReservedKeywordsModel(models.Model):
    keyword = models.CharField(max_length=30)
    callback = models.CharField(max_length=30)
    action = models.CharField(max_length=30)

    objects = ReservedKeywordsModelManager()
