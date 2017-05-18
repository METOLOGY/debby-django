import datetime
from abc import ABCMeta
from typing import TypeVar

from django.core.cache import cache
from django.db.models import QuerySet


class AppCache(object):
    def __init__(self, line_id: str):
        self.line_id = line_id

        self.app = ''
        self.action = ''
        self.expired_time = 120  # in seconds
        self.data = None

        # if there is any cache inside user's cache, it will overwrite any information here
        user_cache = cache.get(self.line_id)  # type: AppCache
        if user_cache and type(user_cache) is AppCache:
            self._update(user_cache)

    def _update(self, user_cache):
        self.__dict__.update(user_cache.__dict__)

    def is_app_running(self, app: str = '') -> bool:
        if app:
            return bool(app)
        return bool(self.app)

    def set_app(self, app: str):
        self.app = app

    def set_next_action(self, app: str, action: str):
        self.app = app
        self.action = action

    def set_data(self, data: "C"):
        self.data = data

    def delete(self):
        cache.delete(self.line_id)

    def commit(self):
        cache.set(self.line_id, self, self.expired_time)

    def save_data(self, data: "C"):
        self.set_data(data)
        self.commit()

    def set_expired_time(self, seconds: int):
        self.expired_time = seconds


class CacheData(metaclass=ABCMeta):
    def setup_data(self, data: "C"):
        self.__dict__.update(data.__dict__)


C = TypeVar("C", bound=CacheData)


class ConsultFoodData(CacheData):
    pass


class FoodData(CacheData):
    food_record_pk = ''  # type: str
    keep_recording = False  # type: bool
    extra_info = ''  # type: str
    image_id = ''  # type: str


class DrugAskData(CacheData):
    drug_types = None  # type: QuerySet
    drug_detail_pk = ''  # type: str


class BGData(CacheData):
    text = ''  # type: str
    record_time = '' # type: datetime.datetime


class ReminderData(CacheData):
    reminder_id = 0  # type: int


class UserSettingData(CacheData):
    reminder_id = 0  # type: int


class MyDiaryData(CacheData):
    record_id = 0  # type: int
    record_type = ''  # type: str
    new_datetime = ''  # type: datetime.datetime
    new_value = 0  # type: int
    new_type = ''  # type: str
    text = '' # type: text
