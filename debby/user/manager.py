from linebot.models import ButtonsTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import TextSendMessage, TemplateSendMessage
from .models import UserSettingModel

from user.cache import AppCache
from line.callback import UserSettingsCallback

class UserSettingManager:

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
            pass

        return reply
