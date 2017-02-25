from django.http.response import HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from user.models import CustomUserModel
from bg_record.models import BGModel
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
def handle_message(event):
    bg_manager = BGRecordManager(line_bot_api, event)

    text = event.message.text

    print(text)
    current_user = CustomUserModel.objects.get(line_id=event.source.sender_id)
    print(current_user)

    # template for recording glucose
    if text.isdigit():
        bg_value = int(text)
        bg_manager.record_bg_record(current_user, bg_value)

        bg_manager.reply_record_success()
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

    data = event.postback.data
    query_string_dict = parse_qs(data)  # e.g.: {'action': ['record_bg'], 'choice': ['true']}
    if query_string_dict['action'][0] == 'record_bg':
        bg_manager.reply_to_input(query_string_dict)

