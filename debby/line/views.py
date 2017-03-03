from django.core.cache import cache
from django.http.response import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from linebot.models import ImageMessage

from user.models import CustomUserModel
from urllib.parse import parse_qs
import json

from debby.bot_settings import webhook_secret, webhook_token

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ConfirmTemplate, PostbackTemplateAction,
    MessageTemplateAction, PostbackEvent
)

from bg_record.manager import BGRecordManager
from food_record.manager import FoodRecordManager

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
    bg_manager = BGRecordManager(line_bot_api, event)
    fr_manager = FoodRecordManager(line_bot_api, event)

    text = event.message.text

    print(text)
    current_user = CustomUserModel.objects.get(line_id=line_id)
    print(current_user)

    user_cache = cache.get(line_id)
    # template for recording glucose
    if text.isdigit():
        bg_value = int(text)
        bg_manager.record_bg_record(current_user, bg_value)

        bg_manager.reply_record_success()
    elif user_cache and 'event' in user_cache.keys():
        if user_cache['event'] == 'record_food_detail':
            fr_manager.record_food_extra_info(text)
    else:
        bg_manager.ask_if_want_to_record_bg()

        # try:
        #     bg_value = int(text)
        #     BG = BGModel(user=CurrentUser, glucose_val=bg_value)
        #     BG.save()
        #     line_bot_api.reply_message(
        #         event.reply_token,
        #         TextSendMessage(text='紀錄成功！'))
        # except ValueError:
        #     line_bot_api.reply_message(
        #         event.reply_token,
        #         TextSendMessage(text='喂～ 要輸入數字才可以記錄血糖啦！'))


@handler.add(PostbackEvent)
def postback(event):
    bg_manager = BGRecordManager(line_bot_api, event)
    fr_manager = FoodRecordManager(line_bot_api, event)

    data = event.postback.data
    query_string_dict = parse_qs(data)  # e.g.: {'action': ['record_bg'], 'choice': ['true']}
    action = query_string_dict['action'][0]
    if action == 'record_bg':
        bg_manager.reply_to_input(query_string_dict)
    elif action == 'food_record':
        if len(query_string_dict['action']) > 1:
            if query_string_dict['action'][1] == 'write_other_notes':
                fr_manager.reply_if_want_to_record_detail(query_string_dict)

        fr_manager.handle_record(query_string_dict)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event: MessageEvent):
    line_id = event.source.sender_id
    current_user = CustomUserModel.objects.get(line_id=line_id)
    print(line_id)
    fr_manager = FoodRecordManager(line_bot_api, event)
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    if image_content:
        fr_manager.ask_if_want_to_record_food()
        user_cache = {'event': 'record_food', 'message_id': message_id}
        cache.set(line_id, user_cache, 120)  # cache for 2 min
