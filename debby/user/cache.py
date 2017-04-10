from abc import ABCMeta
from typing import Type, TypeVar

from django.core.cache import cache




class AppCache(object):
    def __init__(self, line_id: str):
        self.line_id = line_id
        self.app = ''
        self.action = ''
        self.expired_time = 120  # in seconds
        self.data = None

        # update itself from cache
        user_cache = cache.get(line_id)  # type: AppCache
        if user_cache and type(user_cache) is AppCache:
            self.__dict__.update(user_cache.__dict__)

    def is_app_running(self) -> bool:
        return bool(self.app)

    def set_app(self, app: str, action: str = ''):
        self.app = app
        self.action = action

    def set_data(self, data: "C"):
        self.data = data

    def delete(self):
        cache.delete(self.line_id)

    def commit(self):
        cache.set(self.line_id, self, self.expired_time)

    def save_data(self, app: str, action: str, data: "C"):
        self.set_app(app, action)
        self.set_data(data)
        self.commit()


class CacheData(metaclass=ABCMeta):
    pass


class FoodData(CacheData):
    food_record_pk = ''
    keep_recording = False


C = TypeVar("C", bound=CacheData)
