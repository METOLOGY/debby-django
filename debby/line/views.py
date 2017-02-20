from django.shortcuts import Http404
from django.http.response import HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from user.models import CustomUserModel
from bg_record.models import BGModel
import json

from debby.bot_settings import webhook_secret, webhook_token

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ConfirmTemplate, PostbackTemplateAction, MessageTemplateAction, PostbackEvent
)

line_bot_api = LineBotApi(webhook_token)
handler = WebhookHandler(webhook_secret)

CurrentUser = ''

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        # the header field on tutorial of python-sdk is original, django middleware add 'HTTP_' to it.
        signature = request.META['HTTP_X_LINE_SIGNATURE']

        # get request body as text
        body = request.body.decode('utf-8') # this is a string
        print(body)
        data = json.loads(body)
        # {'events': [{'replyToken': '7c43c1d1d46d49d0ba9293685eaa4306', 'source': {'type': 'user', 'userId': 'U60d5ecd2f4700b6310cee793e3c55ca0'}, 'type': 'message', 'message': {'type': 'text', 'text': '次', 'id': '5636084685569'}, 'timestamp': 1486886979585}]}

        # handle webhook body
        try:
            lineID = data['events'][0]['source']['userId']
            if CustomUserModel.objects.filter(line_id=lineID).exists() is False:
                print('create a new user')
                CustomUserModel.objects.create_user(line_id=lineID)
            global CurrentUser
            CurrentUser = CustomUserModel.objects.get(line_id=lineID)
            handler.handle(body, signature)
        except InvalidSignatureError:
            return Http404

        return 'OK'
    else:
        return HttpResponseNotAllowed


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text
    print(text)
    print(CurrentUser)
    # bg_value = int(text)
    # BG = BGModel(user=CurrentUser, glucose=bg_value)

    # template for recoring glucose
    confirm_template_message = TemplateSendMessage(
        alt_text='Confirm template',
        template=ConfirmTemplate(
            text='嗨，現在要記錄血糖嗎？',
            actions=[
                PostbackTemplateAction(
                    label='好啊',
                    text='好啊',
                    # data='action=buy&itemid=1'
                    data='action=record_bg'
                ),
                MessageTemplateAction(
                    label='等等再說',
                    text='等等再說'
                )
            ]
        )
    )

    if check_is_number(text):
        bg_value = int(text)
        BG = BGModel(user=CurrentUser, glucose_val=bg_value)
        BG.save()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='紀錄成功！'))
    elif text == '好啊':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='那們，輸入血糖～'))
    elif text == '等等再說':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='好，要隨時注意自己的血糖狀況哦！'))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            confirm_template_message
        )



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


# @handler.add(PostbackEvent)
# def postback(event):
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text="123")
#     )


def check_is_number(string):
    try:
        int(string)
        return True
    except:
        return False
