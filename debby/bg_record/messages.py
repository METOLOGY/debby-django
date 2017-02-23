from typing import Dict

from linebot import LineBotApi
from linebot.models import (ConfirmTemplate,
                            MessageTemplateAction,
                            PostbackEvent,
                            PostbackTemplateAction,
                            TextSendMessage,
                            TemplateSendMessage)


def handle_postback(event: PostbackEvent,
                    line_bot_api: LineBotApi,
                    query_string: Dict[str, list]):
    if query_string['action'][0] == 'record_bg':
        if query_string['choice'][0] == 'true':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='那們，輸入血糖～'))
        elif query_string['choice'][0] == 'false':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='好，要隨時注意自己的血糖狀況哦！'))


confirm_template_message = TemplateSendMessage(
    alt_text='Confirm template',
    template=ConfirmTemplate(
        text='嗨，現在要記錄血糖嗎？',
        actions=[
            PostbackTemplateAction(
                label='好啊',
                text='好啊',
                data='action=record_bg&choice=true'
            ),
            MessageTemplateAction(
                label='等等再說',
                text='等等再說',
                data='action=record_bg&choice=false'
            )
        ]
    )
)
