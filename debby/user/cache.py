import warnings
from abc import ABCMeta
from typing import TypeVar

from django.core.cache import cache
from django.db.models import QuerySet


class AppCache(object):
    def __init__(self, line_id: str, app: str = '', action: str = ''):
        self.line_id = line_id
        self.app = app
        self.action = action
        self.expired_time = 120  # in seconds
        self.data = None

        self._update()

    def _update(self):
        # update itself from cache
        user_cache = cache.get(self.line_id)  # type: AppCache
        if user_cache and type(user_cache) is AppCache:
            self.__dict__.update(user_cache.__dict__)

    def is_app_running(self, app: str = '') -> bool:
        if app:
            return bool(app)
        return bool(self.app)

    def set_app(self, app: str):
        self.app = app

    def set_next_action(self, action: str = ''):
        self.action = action

    def set_action(self, action: str = ''):
        warnings.warn("Name changed, use set_next_action instead", DeprecationWarning)

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


class CacheData(metaclass=ABCMeta):
    def setup_data(self, data: "C"):
        self.__dict__.update(data.__dict__)


C = TypeVar("C", bound=CacheData)


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


class ReminderData(CacheData):
    reminder_id = 0  # type: int


class UserSettingData(CacheData):
    reminder_id = 0  # type: int
