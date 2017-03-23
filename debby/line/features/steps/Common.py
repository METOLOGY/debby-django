from urllib.parse import parse_qsl

from behave import *
from django.apps import apps
from hamcrest import *
from linebot.models import ConfirmTemplate
from linebot.models import TemplateSendMessage
from linebot.models import TextSendMessage

from line.callback import Callback
from line.handler import CallbackHandler
from user.models import CustomUserModel
from user.models import UserLogModel


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
    message_template = context.given_template if hasattr(context, 'given_template') else context.reply_template
    action = next((x for x in message_template.template.actions
                   if x.label == text), None)
    data = action.data

    data_dict = dict(parse_qsl(data))
    callback = Callback(**data_dict)
    ch = CallbackHandler(callback)
    if ch.is_callback_from_food_record():
        assert_that(ch.callback.action, equal_to('CREATE'))
        ch.setup_for_record_food_image(context.image_content)
    context.send_message = ch.handle()
    UserLogModel.objects.save_to_log(line_id=context.line_id, input_text=action.label,
                                     send_message=context.send_message)


@then('debby會回我 "{text}"')
def step_impl(context, text: str):
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


@then('debby在Log裡面記錄了剛剛我打的句子 "{request}", 跟回覆 "{response}"')
def step_impl(context, request, response):
    latest_log = UserLogModel.objects.filter(user=CustomUserModel.objects.get(line_id=context.line_id)).last()
    assert_that(request, equal_to(latest_log.request_text))
    assert_that(response, equal_to(latest_log.response))


@given('DB "{model_name}" 和 "{event_model_name}" 裡面有些data')
def step_impl(context, model_name, event_model_name):
    model = apps.get_model(*model_name.split('.'))
    event_model = apps.get_model(*event_model_name.split('.'))
    for row in context.table:
        model.objects.create(phrase=row['phrase'], answer=row['answer'])
        event_model.objects.create(phrase=row['phrase'], callback=row['callback'], action=row['action'])


@then('debby會回我以下裡面其中一樣')
def step_impl(context):
    answers = [row['answer'] for row in context.table]

    assert_that(context.send_message, instance_of(TextSendMessage))
    message = context.send_message.text
    assert_that(message, is_in(answers))



