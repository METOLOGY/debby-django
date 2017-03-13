from typing import Type, TypeVar
from urllib.parse import urlencode, parse_qsl


class Callback(object):
    def __init__(self, line_id: str = '', **kwargs):
        self.data = kwargs
        self.data['line_id'] = line_id

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

    def transfer_to(self, callback_cls: Type['Callback']):
        return callback_cls(**self.data)


class DerivedAppCallback(Callback):
    app = ''

    def __init__(self, line_id: str, action: str, **kwargs):
        super().__init__(line_id, action=action, **kwargs)
        self.data['app'] = self.app


class FoodRecordCallback(DerivedAppCallback):
    app = 'FoodRecord'

    @property
    def text(self):
        return self.data.get('text')

    @property
    def choice(self):
        return self.data.get('choice')


class BGRecordCallback(DerivedAppCallback):
    app = 'BGRecord'


class FoodQueryCallback(DerivedAppCallback):
    app = 'FoodQuery'


class DrugQueryCallback(DerivedAppCallback):
    app = 'DrugQuery'
