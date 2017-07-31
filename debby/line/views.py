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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    line_id = event.source.sender_id
    text = event.message.text
    # print(text)
    send_message = None
    """
    trick start
    """
    if text == ':demo:':
        cache.set(line_id + '_demo', 240)
        text = TextSendMessage(text="準備好了 丟圖來吧!")
        reply_message(event, line_id, text)
    else:

        """
        future mode setting
        """
        future_mode = cache.get(line_id + '_future')

        if text == ':future:' and not future_mode:
            cache.set(line_id + '_future', True, 1200)
            send_message = TextSendMessage(text="開啟未來模式，開始計時20分鐘")
        elif text == ':future:' and future_mode:
            cache.set(line_id + '_future', True, 1200)
            send_message = TextSendMessage(text="延長未來模式，重新開始計時20分鐘")
        elif text == ':close:' and future_mode:
            cache.delete(line_id + '_future')
            send_message = TextSendMessage(text="關閉未來模式")
        elif future_mode:
            ai = apiai.ApiAI(settings.CLIENT_ACCESS_TOKEN)
            request = ai.text_request()
            request.session_id = line_id
            request.query = text
            response = request.getresponse()
            js = json.loads(response.read().decode('utf-8'))

            if js['result']['action'] == "input.welcome":
                text = js['result']['fulfillment']['messages'][0]['speech']
                send_message = TextSendMessage(text=text)
            else:
                input_handler = InputHandler(line_id, event.message)
                send_message = input_handler.handle()
        else:
            input_handler = InputHandler(line_id, event.message)
            send_message = input_handler.handle()

        # Save to log model.
        UserLogModel.objects.save_to_log(line_id=line_id, input_text=text, send_message=send_message)

        # return to Line Server
        reply_message(event, line_id, send_message)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event: MessageEvent):
    line_id = event.source.sender_id

    """
    trick start
    """
    demo_mode = cache.get(line_id + '_demo')
    if demo_mode:
        message = '請問是下面其中某一項食物嗎?'
        postbacks = [
            PostbackTemplateAction(
                label="(1) 豬腳麵線",
                data=Callback(line_id, app='demo').url,
            ),
            PostbackTemplateAction(
                label="(2) 炒麵",
                data=Callback(line_id, app='demo').url,
            ),
            PostbackTemplateAction(
                label="(3) 鴨肉羹",
                data=Callback(line_id, app='demo').url,
            ),
            PostbackTemplateAction(
                label="(4) 都不是嗎?",
                data=Callback(line_id, app='demo').url,
            ),
        ]

        send_message = TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=postbacks,
            )
        )

        reply_message(event, line_id, send_message)

    # trick end
    else:
        input_handler = InputHandler(line_id, event.message)
        send_message = input_handler.handle()

        # Save to log model.
        # TODO: input_text should be provided as image saved path. ex '/media/XXX.jpg'
        # food = FoodModel.objects.last(line_id=line_id)
        UserLogModel.objects.save_to_log(line_id=line_id, input_text='images', send_message=send_message)

        # return to Line Server
        reply_message(event, line_id, send_message)


@handler.add(PostbackEvent)
def postback(event: PostbackEvent):
    line_id = event.source.sender_id

    """
    trick start
    """
    demo_mode = cache.get(line_id + '_demo')
    if demo_mode:
        host = cache.get("host_name")
        url = '/media/ConsultFood/demo/1.jpg'
        preview_url = '/media/ConsultFood/demo/1_preview.jpg'
        photo = "https://{}{}".format(host, url)
        preview_photo = "https://{}{}".format(host, preview_url)

        message = ImageSendMessage(original_content_url=photo,
                                   preview_image_url=preview_photo)

        url = '/media/ConsultFood/demo/2.jpg'
        preview_url = '/media/ConsultFood/demo/2_preview.jpg'
        photo = "https://{}{}".format(host, url)
        preview_photo = "https://{}{}".format(host, preview_url)

        message2 = ImageSendMessage(original_content_url=photo,
                                    preview_image_url=preview_photo)
        reply_message(event, line_id, [message, message2])
        cache.delete(line_id + '_demo')
    else:

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
