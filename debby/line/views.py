import datetime
import json
from collections import deque

import apiai
from django.conf import settings
from django.core.cache import cache
from django.http.response import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError)
from linebot.models import ImageMessage, TextSendMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, \
    PostbackTemplateAction
from linebot.models import (
    MessageEvent, TextMessage, PostbackEvent
)

from line.callback import Callback
from line.handler import InputHandler
from reminder.models import UserReminder
from user.models import CustomUserModel
from user.models import UserLogModel

line_bot_api = settings.LINE_BOT_API
handler = settings.HANDLER


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        # the header field on tutorial of python-sdk is original, django middleware add 'HTTP_' to it.
        if 'HTTP_X_LINE_SIGNATURE' not in request.META.keys():
            return HttpResponseBadRequest()

        signature = request.META['HTTP_X_LINE_SIGNATURE']

        # get request body as text
        body = request.body.decode('utf-8')  # this is a string

        print(body)
        data = json.loads(body)
        # {'events': [{'replyToken': '7c43c1d1d46d49d0ba9293685eaa4306',
        #               'source': {'type': 'user', 'userId': 'U60d5ecd2f4700b6310cee793e3c55ca0'},
        #               'type': 'message', 'message': {'type': 'text', 'text': '次', 'id': '5636084685569'},
        #               'timestamp': 1486886979585}]}

        # handle webhook body

        # We need host name when returning pictures' url
        host_name = request.get_host()  # return like 'd3e42111.ngrok.io'
        cache.set("host_name", host_name, None)  # let this special cache never expire

        try:
            line_id = data['events'][0]['source']['userId']

            # create a new user in database.
            user_init(line_id)

            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        return HttpResponse()
    else:
        return HttpResponseNotAllowed(['POST'])


def is_using_api_ai_text_response(js: dict):
    return js['result']['fulfillment']['messages'][0]['type'] == 0 and \
           js['result']['fulfillment']['messages'][0]['speech']


def execute_command(line_id: str, text: str) -> str:
    future_mode = cache.get(line_id + '_future')
    reply = None
    if text == ':future:' and not future_mode:
        cache.set(line_id + '_future', True, 1200)
        reply = "開啟未來模式，開始計時20分鐘"
    elif text == ':future:' and future_mode:
        cache.set(line_id + '_future', True, 1200)
        reply = "延長未來模式，重新開始計時20分鐘"
    elif text == ':close:' and future_mode:
        cache.delete(line_id + '_future')
        reply = "關閉未來模式"
    elif text == ':demo:':
        cache.set(line_id + '_demo', True, 600)
        reply = "開始十分鐘的demo模式"
    return reply


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    line_id = event.source.sender_id
    text = event.message.text
    """
    future mode setting
    """
    cache.set(line_id + '_future', True, 1200)

    special_commands = [':future:', ':close:', ':demo:']
    if text in special_commands:
        reply = execute_command(line_id, text)
        send_message = TextSendMessage(text=reply)
    else:
        input_handler = InputHandler(line_id)
        send_message = input_handler.handle(event.message)

    # Save to log model.
    UserLogModel.objects.save_to_log(line_id=line_id, input_text=text, send_message=send_message)

    # return to Line Server
    reply_message(event, line_id, send_message)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event: MessageEvent):
    line_id = event.source.sender_id

    input_handler = InputHandler(line_id)
    send_message = input_handler.handle(event.message)

    # Save to log model.
    # TODO: input_text should be provided as image saved path. ex '/media/XXX.jpg'
    # food = FoodModel.objects.last(line_id=line_id)
    UserLogModel.objects.save_to_log(line_id=line_id, input_text='images', send_message=send_message)

    # return to Line Server
    reply_message(event, line_id, send_message)


@handler.add(PostbackEvent)
def postback(event: PostbackEvent):
    line_id = event.source.sender_id

    input_handler = InputHandler(line_id)
    send_message = input_handler.handle_postback(event.postback.data)

    if send_message:
        # Save to log model.
        UserLogModel.objects.save_to_log(line_id=line_id, input_text=event.postback.data, send_message=send_message)

        # return to Line Server
        line_bot_api.reply_message(
            event.reply_token,
            send_message
        )


def user_init(line_id: str):
    if CustomUserModel.objects.filter(line_id=line_id).exists() is False:
        user = CustomUserModel.objects.create_user(line_id=line_id)

        # init reminder
        for reminder_type in ['bg', 'insulin', 'drug']:
            for time in [datetime.time(7, 0), datetime.time(8, 0), datetime.time(12, 0), datetime.time(18, 0),
                         datetime.time(22, 0)]:
                if time == datetime.time(8, 0) and reminder_type == 'drug':
                    UserReminder.objects.get_or_create(user=user, type=reminder_type, time=time, status=True)
                else:
                    UserReminder.objects.get_or_create(user=user, type=reminder_type, time=time, status=False)


def reply_message(event, line_id, send_message):
    if type(send_message) is not list:
        line_bot_api.reply_message(
            event.reply_token,
            send_message
        )
    else:
        d = deque(send_message)
        i = 0
        s = []
        if len(d) > 5:
            while len(d) > 5:
                s.append(d.popleft())
                i += 1
                if i == 5:
                    print(i)
                    line_bot_api.reply_message(
                        event.reply_token,
                        s
                    )
                    i = 0
                    s = []
            try:
                while len(d) > 0:
                    s.append(d.popleft())
                    i += 1
                    if i == 5:
                        print(i)
                        line_bot_api.push_message(
                            to=line_id,
                            messages=s
                        )
                        i = 0
                        s = []
                else:
                    line_bot_api.push_message(
                        to=line_id,
                        messages=s
                    )

            except LineBotApiError as e:
                print(e)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                send_message
            )
