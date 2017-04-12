from typing import Type, TypeVar
from urllib.parse import urlencode, parse_qsl


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
    app = 'FoodRecord'

    @property
    def text(self) -> str:
        return self.data.get('text')

    @property
    def choice(self):
        return self.data.get('choice')


class BGRecordCallback(DerivedAppCallback):
    app = 'BGRecord'

    @property
    def choice(self):
        return self.data.get('choice')


class ConsultFoodCallback(DerivedAppCallback):
    app = 'ConsultFood'

    @property
    def text(self) -> str:
        return self.data.get('text')


class DrugAskCallback(DerivedAppCallback):
    app = 'DrugAsk'

    @property
    def text(self) -> str:
        return self.data.get('text')

    @property
    def choice(self) -> str:
        return self.data.get('choice')


class ChatCallback(DerivedAppCallback):
    app = 'Chat'

    @property
    def text(self) -> str:
        return self.data.get('text')

class ReminderCallback(DerivedAppCallback):
    app = 'Reminder'

    @property
    def choice(self) -> str:
        return self.data.get('choice')