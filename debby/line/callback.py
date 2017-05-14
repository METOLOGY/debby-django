import datetime
from typing import Type, Union
from urllib.parse import urlencode, parse_qsl

from line.constant import App


class Callback(object):
    def __init__(self, line_id: str = '', app='', action='', **kwargs):
        self.data = kwargs
        self.data['line_id'] = line_id
        self.data['app'] = app
        self.data['action'] = action

    @property
    def line_id(self):
        return self.data['line_id']

    @property
    def app(self):
        return self.data.get('app')

    @property
    def action(self):
        return self.data.get('action')

    @action.setter
    def action(self, val):
        self.data["action"] = val

    @property
    def url(self):
        return urlencode(self.data)

    @staticmethod
    def decode(url: str) -> 'Callback':
        url_dict = dict(parse_qsl(url))

        return Callback(**url_dict)

    def __eq__(self, other):
        return self.data.get('app') == other.app

    def convert_to(self, callback_cls: Type['Callback']):
        return callback_cls(**self.data)


class DerivedAppCallback(Callback):
    app = ''

    def __init__(self, line_id: str, **kwargs):
        super().__init__(line_id, **kwargs)
        self.data['app'] = self.app


class FoodRecordCallback(DerivedAppCallback):
    app = App.FOOD_RECORD

    @property
    def image_id(self) -> str:
        return self.data.get('image_id')

    @property
    def text(self) -> str:
        return self.data.get('text')

    @property
    def choice(self):
        return self.data.get('choice')


class BGRecordCallback(DerivedAppCallback):
    app = App.BG_RECORD

    @property
    def choice(self):
        return self.data.get('choice')

    @property
    def text(self):
        return self.data.get('text')


class ConsultFoodCallback(DerivedAppCallback):
    app = App.CONSULT_FOOD

    @property
    def text(self) -> str:
        return self.data.get('text')


class DrugAskCallback(DerivedAppCallback):
    app = App.DRUG_ASK

    @property
    def text(self) -> str:
        return self.data.get('text')

    @property
    def choice(self) -> str:
        return self.data.get('choice')

    @property
    def fuzzy_drug_name(self) -> str:
        return self.data.get('fuzzy_drug_name')

    @property
    def drug_detail_id(self) -> str:
        return self.data.get('drug_detail_id')


class ChatCallback(DerivedAppCallback):
    app = App.CHAT

    @property
    def text(self) -> str:
        return self.data.get('text')


class ReminderCallback(DerivedAppCallback):
    app = App.REMINDER

    @property
    def choice(self) -> str:
        return self.data.get('choice')

    @property
    def reminder_id(self) -> str:
        return self.data.get('reminder_id')


class MyDiaryCallback(DerivedAppCallback):
    app = App.MY_DIARY

    @property
    def record_id(self) -> int:
        return self.data.get('record_id')

    @property
    def record_type(self) -> str:
        return self.data.get('record_type')

    @property
    def new_value(self) -> Union[str, datetime.datetime]:
        return self.data.get('new_value')

    @property
    def text(self) -> str:
        return self.data.get('text')


class UserSettingsCallback(DerivedAppCallback):
    app = 'UserSetting'

    @property
    def reminder_id(self) -> str:
        return self.data.get('reminder_id')

    @property
    def choice(self) -> str:
        return self.data.get('choice')

    @property
    def text(self) -> str:
        return self.data.get('text')
