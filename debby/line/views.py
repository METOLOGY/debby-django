import datetime
import json

from django.conf import settings
from django.core.cache import cache
from django.http.response import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError)
from linebot.models import ImageMessage
from linebot.models import (
    MessageEvent, TextMessage, PostbackEvent
)

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
            UserInit(line_id)

            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        return HttpResponse()
    else:
        return HttpResponseNotAllowed(['POST'])


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    line_id = event.source.sender_id
    text = event.message.text
    # print(text)

    input_handler = InputHandler(line_id, event.message)
    send_message = input_handler.handle()

    # Save to log model.
    UserLogModel.objects.save_to_log(line_id=line_id, input_text=text, send_message=send_message)

    # return to Line Server
    line_bot_api.reply_message(
        event.reply_token,
        send_message)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event: MessageEvent):
    line_id = event.source.sender_id

    input_handler = InputHandler(line_id, event.message)
    send_message = input_handler.handle()

    # Save to log model.
    # TODO: input_text should be provided as image saved path. ex '/media/XXX.jpg'
    # food = FoodModel.objects.last(line_id=line_id)
    UserLogModel.objects.save_to_log(line_id=line_id, input_text='images', send_message=send_message)

    # return to Line Server
    line_bot_api.reply_message(
        event.reply_token,
        send_message)


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


def UserInit(line_id: str):
    if CustomUserModel.objects.filter(line_id=line_id).exists() is False:
        user = CustomUserModel.objects.create_user(line_id=line_id)

        # init reminder
        for reminder_type in ['bg', 'insulin', 'drug']:
            for time in [datetime.time(7, 00), datetime.time(8, 00), datetime.time(12, 00), datetime.time(18, 00), datetime.time(22, 00)]:
                UserReminder.objects.create(user=user, type=reminder_type, time=time, status=False)
