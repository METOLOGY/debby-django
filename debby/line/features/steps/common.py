from behave import *
from hamcrest import *
from user.models import CustomUserModel


@given("我的line_id是 {line_id}")
def step_impl(context, line_id):
    context.current_user, _ = CustomUserModel.objects.get_or_create(line_id=line_id)


@then('debby會有個選單回我 "{answer}"')
def step_impl(context, answer):
    message = context.send_message['template']['text']
    assert_that(message, equal_to(answer))


@step('並問我是要選項 "{text}"')
def step_impl(context, text):
    message = ''
    for action in context.send_message['template']['actions']:
        if action['label'] == text:
            message = action['label']
    assert_that(message, equal_to(text))


@step('還是選項 "{text}"')
def step_impl(context, text):
    message = ''
    for action in context.send_message['template']['actions']:
        if action['label'] == text:
            message = action['label']
    assert_that(message, equal_to(text))
