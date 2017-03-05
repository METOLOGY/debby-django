from urllib.parse import parse_qsl

from behave import *
from hamcrest import *

from bg_record.manager import BGRecordManager
from line.handler import InputHandler, CallbackHandler


@given("我打開 debby 對話框")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass


@when('我輸入 "{input_text}"')
def step_impl(context, input_text):
    """
    :type context: behave.runner.Context
    """
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
    input_handler = InputHandler(input_text)
    context.send_message = input_handler.find_best_answer_for_text().as_json_dict()


@then('debby會有個選單回我 "{answer}"')
def step_impl(context, answer):
    """
    :type context: behave.runner.Context
    """

    message = context.send_message['template']['text']
    assert_that(message, equal_to(answer))


@step('並問我是要選項 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """

    message = ''
    for action in context.send_message['template']['actions']:
        if action['label'] == text:
            message = action['label']
    assert_that(message, equal_to(text))


@step('還是選項 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """
    message = ''
    for action in context.send_message['template']['actions']:
        if action['label'] == text:
            message = action['label']
    assert_that(message, equal_to(text))


@given('選單 "嗨，現在要記錄血糖嗎？"')
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    bg_manager = BGRecordManager()
    context.given_template = bg_manager.reply_does_user_want_to_record().as_json_dict()


@when('我選選項 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """
    action = next((x for x in context.given_template['template']['actions']
                   if x['label'] == text), {'data': ''})
    data = dict(parse_qsl(action['data']))

    ih = CallbackHandler(data)
    context.send_message = ih.dispatch().as_json_dict()


@then('debby會回我 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """
    message = context.send_message['text']
    assert_that(message, equal_to(text))
