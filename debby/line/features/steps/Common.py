from PIL import Image
from behave import *
from hamcrest import *
from linebot.models import ConfirmTemplate
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from food_record.manager import FoodRecordManager
from line.handler import CallbackHandler
from user.models import CustomUserModel


@given("我的line_id是 {line_id}")
def step_impl(context, line_id):
    context.line_id = line_id
    context.current_user, _ = CustomUserModel.objects.get_or_create(line_id=line_id)


@then('debby會有個選單回我 "{answer}"')
def step_impl(context, answer):
    assert_that(context.send_message, instance_of(TemplateSendMessage))
    assert_that(context.send_message.template, instance_of(ConfirmTemplate))
    message = context.send_message.template.text
    context.reply_template = context.send_message

    assert_that(message, equal_to(answer))


@step('並問我是要選項 "{text}"')
def step_impl(context, text):
    assert_that(context.send_message, instance_of(TemplateSendMessage))
    assert_that(context.send_message.template, instance_of(ConfirmTemplate))
    message = ''
    for action in context.send_message.template.actions:
        if action.label == text:
            message = action.label
    assert_that(message, equal_to(text))


@step('還是選項 "{text}"')
def step_impl(context, text):
    assert_that(context.send_message, instance_of(TemplateSendMessage))
    assert_that(context.send_message.template, instance_of(ConfirmTemplate))

    message = ''
    for action in context.send_message.template.actions:
        if action.label == text:
            message = action.label
    assert_that(message, equal_to(text))


@when('我選選項 "{text}"')
def step_impl(context, text):
    message_template = context.given_template if context.__contains__('given_template') else context.reply_template
    action = next((x for x in message_template.template.actions
                   if x.label == text), None)
    data = action.data

    ch = CallbackHandler()
    ch.set_user_line_id(context.line_id)
    ch.set_postback_data(data)
    if ch.is_callback_from_food_record():
        ch.setup_for_record_food_image(context.current_user, context.image_content)
    context.send_message = ch.handle()


@then('debby會回我 "{text}"')
def step_impl(context, text):
    send_message = context.send_message
    assert_that(send_message, instance_of(TextSendMessage))
    message = context.send_message.text
    assert_that(message, equal_to(text))


@given('debby回了我 "{text}"')
def step_impl(context, text):
    send_message = TextSendMessage(text=text)

    assert_that(send_message, instance_of(TextSendMessage))
    message = send_message.text
    assert_that(message, equal_to(text))
