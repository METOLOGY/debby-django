from behave import *
from django.apps import apps
from linebot.models import ImageMessage
from linebot.models import MessageEvent

from line.handler import InputHandler


@when("我上傳了一張照片")
def step_impl(context):
    # https://devdocs.line.me/en/#webhook-event-object
    im = ImageMessage(id='55669487')
    event = MessageEvent(message=im)

    ih = InputHandler(context.current_user, event.message)
    context.send_message = ih.handle()
