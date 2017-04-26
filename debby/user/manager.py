from linebot.models import ButtonsTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import TextSendMessage, TemplateSendMessage
from linebot.models import CarouselColumn, CarouselTemplate
from .models import UserSettingModel
from reminder.models import UserReminder
from user.models import CustomUserModel

from user.cache import AppCache
from line.callback import UserSettingsCallback

class UserSettingManager(object):

    def __init__(self, callback: UserSettingsCallback):
        self.callback = callback


    setting_message = TemplateSendMessage(
        alt_text='請選擇要設定的項目',
        template=ButtonsTemplate(
            text='請選擇要設定的項目',
            actions=[
                PostbackTemplateAction(
                    label='血糖單位',
                    data=UserSettingsCallback(
                        action='SELECT_UNIT'
                    ).url
                ),
                PostbackTemplateAction(
                    label='提醒時間',
                    data=UserSettingsCallback(
                        action='SELECT_REMINDED_TYPE'
                    ).url
                ),
                PostbackTemplateAction(
                    label='離開設定',
                    data=UserSettingsCallback(
                        action='' #TODO: set leave action
                    ).url
                )
            ]
        )
    )

    set_unit_message = TemplateSendMessage(
        alt_text='請選擇單位',
        template=ButtonsTemplate(
            text='請選擇單位',
            actions=[
                PostbackTemplateAction(
                    label='mg/dL',
                    data=UserSettingsCallback(
                        action='SET_UNIT',
                        choice='mg/dL'
                    ).url
                ),
                PostbackTemplateAction(
                    label='mmol/L',
                    data=UserSettingsCallback(
                        action='SET_UNIT',
                        choice='mmol/L'
                    ).url
                )
            ]
        )
    )

    select_reminder_type_message = TemplateSendMessage(
        alt_text='請選擇您要調整的提醒項目',
        template=ButtonsTemplate(
            text='請選擇您要調整的提醒項目',
            actions=[
                PostbackTemplateAction(
                    label='量測血糖',
                    data=UserSettingsCallback(
                        action='SET_REMINDER',
                        choice='bg'
                    ).url
                ),
                PostbackTemplateAction(
                    label='注射胰島素',
                    data=UserSettingsCallback(
                        action='SET_REMINDER',
                        choice='insulin'
                    ).url
                ),
                PostbackTemplateAction(
                    label='服用藥物',
                    data=UserSettingsCallback(
                        action='SET_REMINDER',
                        choice='drug'
                    ).url
                ),
                PostbackTemplateAction(
                    label='離開設定',
                    data=UserSettingsCallback(
                        action=''   #TODO: set leave action
                    ).url
                ),
            ]
        )
    )




    conversation_closed_message = TextSendMessage(text='您可以隨時回來調整哦！')


    def reminder_select_carousel(self, carousels):
        return TemplateSendMessage(
            alt_text="請選擇要更改的提醒項目",
            tempalte=CarouselTemplate(
                columns=carousels
            )
        )

    def confirm_reminder_turn_off(self, reminder_id):
        return TemplateSendMessage(
            alt_text='確定要關閉提醒嗎?',
            template=ButtonsTemplate(
                text='確定要關閉提醒嗎?',
                actions=[
                    PostbackTemplateAction(
                        label='確定',
                        data='app=UserSetting&action=TURN_OFF_REMINDER&reminder_id={}'.format(reminder_id)
                    ),
                    PostbackTemplateAction(
                        label='取消',
                        data='app=UserSetting&action=CANCEL_TURN_OFF_REMINDER'
                    )
                ]
            )
        )


    def handle(self):
        reply = TextSendMessage(text='ERROR!')
        app_cache = AppCache(self.callback.line_id, app='UserSetting')

        if self.callback.action == 'CREATE_FROM_MENU':
            reply = self.setting_message
        elif self.callback.action == 'SELECT_UNIT':
            reply = self.set_unit_message
        elif self.callback.action == 'SET_UNIT':
            unit = self.callback.choice
            user_setting = UserSettingModel.objects.get(line_id=self.callback.line_id)
            user_setting.unit = unit
            user_setting.save()
            reply = TextSendMessage(text='設定完成！')

        elif self.callback.action == 'SELECT_REMINDED_TYPE':
            reply = self.select_reminder_type_message

        elif self.callback.action == 'SET_REMINDER':
            type = self.callback.choice
            user_reminders = UserReminder.objects.fileter(
                user=CustomUserModel.objects.get(line_id=self.callback.line_id),
                type=type
            )

            carousels = []
            for reminder in user_reminders:
                message = '提醒時間：{}\n提醒是否開啟：{}'.format(reminder.time, '是' if reminder.status else '否')
                carousels.append(CarouselColumn(
                    text=message,
                    actions=[
                        PostbackTemplateAction(
                            label='設定時間',
                            data='app=UserSetting&action=SET_REMINDER_TIME&reminder_id={}'.format(reminder.id)
                        ),
                        PostbackTemplateAction(
                            label='關閉提醒',
                            data='app=UserSetting&action=CONFIRM_TURN_OFF_REMINDER&reminder_id={}'.format(reminder.id)
                        ),
                    ]
                ))

            reply = self.reminder_select_carousel(carousels=carousels)


        elif self.callback.action == 'CONFIRM_TURN_OFF_REMINDER':
            reminder_id = self.action.reminder_id
            reply = self.confirm_reminder_turn_off(reminder_id=reminder_id)

        elif self.callback.action == 'TURN_OFF_REMINDER':
            reminder_id = self.action.reminder_id
            reminder = UserReminder.objects.get(id=reminder_id)
            reminder.status = False
            reminder.save()
            reply = TextSendMessage(text='設定完成，已關閉提醒！')

        elif self.callback.action == 'CANCEL_TURN_OFF_REMINDER':
            reply = self.conversation_closed_message


        elif self.callback.action == 'SET_REMINDER_TIME':
            reminder_id = self.callback.reminder_id
            pass # TODO: bookmark here, contiune here later

        return reply
