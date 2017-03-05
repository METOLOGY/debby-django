from behave import *
from hamcrest import *
from line.handler import InputHandler


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
    context.template = input_handler.find_best_answer().as_json_dict()


@then('debby會回我 "{answer}"')
def step_impl(context, answer):
    """
    :type context: behave.runner.Context
    """

    message = context.template['template']['text']
    assert_that(message, equal_to(answer))


@step('會有個選單問我是要 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """

    message = context.template['template']['actions'][0]['label']
    assert_that(message, equal_to(text))


@step('還是 "{text}"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    """
    message = context.template['template']['actions'][1]['label']
    assert_that(message, equal_to(text))
