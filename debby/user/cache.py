from abc import ABCMeta
from enum import Enum, auto

from django.core.cache import cache
from django.db.models import QuerySet
from typing import TypeVar


class AppCache(object):
    def __init__(self, line_id: str, app: str = '', action: str = ''):
        self.line_id = line_id
        self.app = app
        self.action = action
        self.expired_time = 120  # in seconds
        self.data = None

        # update itself from cache
        user_cache = cache.get(line_id)  # type: AppCache
        if user_cache and type(user_cache) is AppCache:
            self.__dict__.update(user_cache.__dict__)

    def is_app_running(self, app: str = '') -> bool:
        if app:
            return bool(app)
        return bool(self.app)

    def set_app(self, app: str):
        self.app = app

    def set_action(self, action: str = ''):
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


class App(metaclass=ABCMeta):
    pass


class FoodRecord(App):
    class Action(Enum):
        CREATE = auto()
        CREATE_FROM_MENU = auto()
        UPDATE = auto()


class DrugAsk(App):
    class Action(Enum):
        READ = auto()
        READ_FROM_MENU = auto()
        WAIT_DRUG_TYPE_CHOICE = auto()
        READ_DRUG_DETAIL = auto()


class CacheData(metaclass=ABCMeta):
    pass


C = TypeVar("C", bound=CacheData)


class FoodData(CacheData):
    food_record_pk = ''  # type: str
    keep_recording = False  # type: bool


class DrugAskData(CacheData):
    drug_types = None  # type: QuerySet
    drug_detail_pk = ''  # type: str

class BGData(CacheData):
    text = ''  # type: str

class ReminderData(CacheData):
    reminder_id = 0 #type: int