from django.shortcuts import Http404
from django.http.response import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from user.models import CustomUserModel
import json

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

line_bot_api = LineBotApi('o95VkDv5wNpJGzWHATn8oMscgxR24ovtcs0GnXd8b79TNAXF6CEEbipeJf247YVsnu+weRqCKFhPw4hSsXoPTO+UOFlYcv5cSiXdVaVkfePs2sWBXQU5J8pfJWkPSHNqwD04umCN9mmSHUUYmls8+gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('8800b2dbc38f81e3af174b9e3275eb1c')



@csrf_exempt
def callback(request):
    if request.method == 'POST':
        # the header field on tutorial of python-sdk is orignial, django middleware add 'HTTP_' to it.
        signature = request.META['HTTP_X_LINE_SIGNATURE']

        # get request body as text
        body = request.body.decode('utf-8') # this is a string
        data = json.loads(body)
        # {'events': [{'replyToken': '7c43c1d1d46d49d0ba9293685eaa4306', 'source': {'type': 'user', 'userId': 'U60d5ecd2f4700b6310cee793e3c55ca0'}, 'type': 'message', 'message': {'type': 'text', 'text': '次', 'id': '5636084685569'}, 'timestamp': 1486886979585}]}

        # handle webhook body
        try:
            lineID = data['events'][0]['source']['userId']
            if CustomUserModel.objects.filter(line_id=lineID).exists() is False:
                print('create a new user')
                CustomUserModel.object.create_user(line_id=lineID)
            handler.handle(body, signature)
        except InvalidSignatureError:
            return Http404

        return 'OK'
    else:
        return HttpResponseNotAllowed


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
