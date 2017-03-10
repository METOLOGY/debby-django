from __future__ import absolute_import, unicode_literals
from celery import shared_task
from bg_record.manager import BGRecordManager
from linebot import LineBotApi, WebhookHandler
from debby.bot_settings import webhook_secret, webhook_token

line_bot_api = LineBotApi(webhook_token)
handler = WebhookHandler(webhook_secret)


@shared_task
def ask_record_bg():
    bg_manager = BGRecordManager()
    bg_manager.record_reminder(line_bot_api)
