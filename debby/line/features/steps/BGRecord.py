from urllib.parse import parse_qsl

from behave import *
from hamcrest import *
from django.apps import apps
from linebot.models import MessageEvent
from linebot.models import TextMessage

from bg_record.manager import BGRecordManager
from line.handler import InputHandler, CallbackHandler
from user.models import CustomUserModel


@given("我打開 debby 對話框")
def step_impl(context):
    pass


@when('我輸入 "{input_text}"')
def step_impl(context, input_text):
    # {'altText': 'Confirm template',
    #  'template': {'actions': [{'data': 'action=record_bg&choice=true',
    #                            'label': '好啊',
    #                            'text': None,
    #                            'type': 'postback'},
    #                           {'data': 'action=record_bg&choice=false',
    #                            'label': '等等再說',
    #                            'text': None,
    #                            'type': 'postback'}],
    #               'text': '嗨，現在要記錄血糖嗎？',
    #               'type': 'confirm'},
    #  'type': 'template'}
    tm = TextMessage(text=input_text)
    event = MessageEvent(message=tm)
    input_handler = InputHandler(context.current_user, event.message)
    context.send_message = input_handler.handle()


@given('選單 "嗨，現在要記錄血糖嗎？"')
def step_impl(context):
    bg_manager = BGRecordManager()
    context.given_template = bg_manager.reply_does_user_want_to_record().as_json_dict()


@when('我選選項 "{text}"')
def step_impl(context, text):
    action = next((x for x in context.given_template['template']['actions']
                   if x['label'] == text), {'data': ''})
    data = action['data']

    ih = CallbackHandler(data)
    context.send_message = ih.handle()


@then('debby會回我 "{text}"')
def step_impl(context, text):
    message = context.send_message.text
    assert_that(message, equal_to(text))


@given("有個DB")
def step_impl(context):
    pass


@step("在DB {model_name} 中有這筆資料使用者 {line_id} 血糖 {value:n}")
def step_impl(context, model_name, line_id, value):
    model = apps.get_model(*model_name.split('.'))
    user = CustomUserModel.objects.get(line_id=line_id)
    obj = model.objects.get(user=user)
    assert_that(obj.glucose_val, equal_to(value))
