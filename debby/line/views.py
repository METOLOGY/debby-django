from urllib.parse import parse_qsl

from django.core.cache import cache
from django.http.response import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from linebot.models import ImageMessage
from line.callback import FoodRecordCallback, Callback
from line.handler import InputHandler, CallbackHandler
from user.models import CustomUserModel
from user.models import UserLogModel
from food_record.models import FoodModel
import json

from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError)
from linebot.models import (
    MessageEvent, TextMessage, PostbackEvent
)

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
        try:
            line_id = data['events'][0]['source']['userId']

            ## create a new user in database.
            if CustomUserModel.objects.filter(line_id=line_id).exists() is False:
                CustomUserModel.objects.create_user(line_id=line_id)

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
    print(text)

    ### no need to query here, right?
    # current_user = CustomUserModel.objects.get(line_id=line_id)
    # print(current_user)

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
    print(line_id)
    c = FoodRecordCallback(line_id, action='CONFIRM_RECORD')
    ch = CallbackHandler(c)
    send_message = ch.handle()

    user_cache = {'event': 'record_food', 'message_id': event.message.id}
    cache.set(line_id, user_cache, 120)  # cache for 2 min

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
    data = event.postback.data
    data_dict = dict(parse_qsl(data))
    c = Callback(**data_dict)
    ch = CallbackHandler(c)
    if ch.is_callback_from_food_record():
        user_cache = cache.get(line_id)
        if user_cache:
            message_id = user_cache['message_id']
            image_content = line_bot_api.get_message_content(message_id=message_id)
            ch.setup_for_record_food_image(image_content.content)

    send_message = ch.handle()

    # Save to log model.
    UserLogModel.objects.save_to_log(line_id=line_id, input_text=data, send_message=send_message)

    # return to Line Server
    line_bot_api.reply_message(
        event.reply_token,
        send_message
    )
