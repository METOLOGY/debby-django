from django.core.cache import cache
from django.http.response import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from linebot.models import ImageMessage

from line.handler import InputHandler, CallbackHandler
from user.models import CustomUserModel
import json

from debby.bot_settings import webhook_secret, webhook_token

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError)
from linebot.models import (
    MessageEvent, TextMessage, PostbackEvent
)

line_bot_api = LineBotApi(webhook_token)
handler = WebhookHandler(webhook_secret)


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
            if CustomUserModel.objects.filter(line_id=line_id).exists() is False:
                print('create a new user')
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
    current_user = CustomUserModel.objects.get(line_id=line_id)
    print(current_user)

<<<<<<< Updated upstream
    input_handler = InputHandler(line_id, event.message)
    send_message = input_handler.handle()
    line_bot_api.reply_message(
        event.reply_token,
        send_message)
=======
    user_cache = cache.get(line_id)
    # template for recording glucose

    if text == '紀錄飲食':
        fr_manager.ask_user_upload_an_image()
        user_cache = {'event': 'record_food'}
        cache.set(line_id, user_cache)
    if text.isdigit():
        bg_value = int(text)
        bg_manager.record_bg_record(current_user, bg_value)
>>>>>>> Stashed changes


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event: MessageEvent):
    line_id = event.source.sender_id
    print(line_id)

    ih = InputHandler(line_id, event.message)
    send_message = ih.handle()
    line_bot_api.reply_message(
        event.reply_token,
        send_message)


@handler.add(PostbackEvent)
def postback(event: PostbackEvent):
    line_id = event.source.sender_id
    data = event.postback.data

<<<<<<< Updated upstream
    ch = CallbackHandler(line_id)
    ch.set_postback_data(input_data=data)
    if ch.is_callback_from_food_record():
        user_cache = cache.get(line_id)
        if user_cache:
            message_id = user_cache['message_id']
            image_content = line_bot_api.get_message_content(message_id=message_id)
            ch.setup_for_record_food_image(image_content.content)

    send_message = ch.handle()
    line_bot_api.reply_message(
        event.reply_token,
        send_message
    )
=======

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event: MessageEvent):
    line_id = event.source.sender_id
    user_cache = cache.get(line_id)

    fr_manager = FoodRecordManager(line_bot_api, event)
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)

    if image_content:
        if not user_cache:
            fr_manager.ask_if_want_to_record_food()
        user_cache = {'event': 'record_food', 'message_id': message_id}
        cache.set(line_id, user_cache, 120)  # cache for 2 min
>>>>>>> Stashed changes
