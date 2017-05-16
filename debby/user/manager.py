import datetime
from typing import Union

from linebot.models import ButtonsTemplate
from linebot.models import CarouselColumn, CarouselTemplate
from linebot.models import PostbackTemplateAction
from linebot.models import TextSendMessage, TemplateSendMessage

from line.callback import UserSettingsCallback
from line.constant import UserSettingsAction as Action, App
from reminder.models import UserReminder
from user.cache import AppCache, UserSettingData
from user.models import CustomUserModel
from .models import UserSettingModel


class UserSettingManager(object):
    def __init__(self, callback: UserSettingsCallback):
        self.callback = callback

    @property
    def setting_message(self):

        return TemplateSendMessage(
            alt_text='請選擇要設定的項目',
            template=ButtonsTemplate(
                text='請選擇要設定的項目',
                actions=[
                    PostbackTemplateAction(
                        label='血糖單位',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SELECT_UNIT).url
                    ),
                    PostbackTemplateAction(
                        label='提醒時間',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SELECT_REMINDED_TYPE).url
                    ),
                    PostbackTemplateAction(
                        label='離開設定',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.END_CONVERSATION).url
                    )
                ]
            )
        )

    @property
    def set_unit_message(self):
        return TemplateSendMessage(
            alt_text='請選擇單位',
            template=ButtonsTemplate(
                text='請選擇單位',
                actions=[
                    PostbackTemplateAction(
                        label='mg/dL',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SET_UNIT,
                                                  choice='mg/dL').url
                    ),
                    PostbackTemplateAction(
                        label='mmol/L',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SET_UNIT,
                                                  choice='mmol/L').url
                    )
                ]
            )
        )

    @property
    def select_reminder_type_message(self):
        return TemplateSendMessage(
            alt_text='請選擇您要調整的提醒項目',
            template=ButtonsTemplate(
                text='請選擇您要調整的提醒項目',
                actions=[
                    PostbackTemplateAction(
                        label='量測血糖',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SET_REMINDER,
                                                  choice='bg').url
                    ),
                    PostbackTemplateAction(
                        label='注射胰島素',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SET_REMINDER,
                                                  choice='insulin').url
                    ),
                    PostbackTemplateAction(
                        label='服用藥物',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SET_REMINDER,
                                                  choice='drug').url
                    ),
                    PostbackTemplateAction(
                        label='離開設定',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.END_CONVERSATION).url
                    ),
                ]
            )
        )

    conversation_closed_message = TextSendMessage(text='您可以隨時回來調整哦！')

    def error_value_message(self, reminder_id):
        return TemplateSendMessage(
            alt_text='error value',
            template=ButtonsTemplate(
                text='格式好像有點錯誤... 再試一次嗎？',
                actions=[
                    PostbackTemplateAction(
                        label='繼續設定',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.SET_REMINDER_TIME,
                                                  reminder_id=reminder_id).url
                    ),
                    PostbackTemplateAction(
                        label='取消設定',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.END_CONVERSATION).url
                    )
                ]
            )
        )

    # noinspection PyTypeChecker
    @staticmethod
    def reminder_select_carousel(carousels):
        return TemplateSendMessage(
            alt_text="請選擇要更改的提醒項目",
            template=CarouselTemplate(
                columns=carousels
            )
        )

    def confirm_reminder_turn_on_or_off(self, reminder_id, status: bool):
        if status:
            status_zh = '開啟'
        else:
            status_zh = '關閉'

        return TemplateSendMessage(
            alt_text='確定要{}提醒嗎?'.format(status_zh),
            template=ButtonsTemplate(
                text='確定要{}提醒嗎?'.format(status_zh),
                actions=[
                    PostbackTemplateAction(
                        label='確定',
                        data='app=UserSetting&action=TURN_ON_OR_OFF_REMINDER&reminder_id={}'.format(reminder_id)
                    ),
                    PostbackTemplateAction(
                        label='取消',
                        data=UserSettingsCallback(line_id=self.callback.line_id, action=Action.END_CONVERSATION).url
                    )
                ]
            )
        )

    @staticmethod
    def check_input_is_time(text: str) -> Union[bool, datetime.time]:
        if len(text) == 4:
            for t in text:
                if not t.isdigit():
                    return False
                else:
                    pass

            if 0 <= int(text[0:2]) < 24 and 0 <= int(text[2:]) < 60:
                return datetime.time(hour=int(text[0:2]), minute=int(text[2:]))
            else:
                return False
        return False

    def handle(self):
        reply = TextSendMessage(text='USER SETTING ERROR!')  # default error message.
        app_cache = AppCache(self.callback.line_id)

        if self.callback.action == Action.CREATE_FROM_MENU:
            reply = self.setting_message
        elif self.callback.action == Action.SELECT_UNIT:
            reply = self.set_unit_message
        elif self.callback.action == Action.SET_UNIT:
            unit = self.callback.choice
            user = CustomUserModel.objects.get(line_id=self.callback.line_id)
            user_setting, created = UserSettingModel.objects.get_or_create(user=user)
            user_setting.unit = unit
            user_setting.save()
            reply = TextSendMessage(text='設定完成！')

        elif self.callback.action == 'SELECT_REMINDED_TYPE':
            reply = self.select_reminder_type_message

        elif self.callback.action == 'SET_REMINDER':
            user_reminders = UserReminder.objects.filter(
                user__line_id=self.callback.line_id,
                type=self.callback.choice
            )

            carousels = []
            for reminder in user_reminders:
                message = '提醒時間：{}\n提醒是否開啟：{}'.format(reminder.time, '是' if reminder.status else '否')

                set_time_action = PostbackTemplateAction(
                    label='設定時間',
                    data='app=UserSetting&action=SET_REMINDER_TIME&reminder_id={}'.format(reminder.id)
                )

                if reminder.status:
                    confirm_action = PostbackTemplateAction(
                            label='關閉提醒',
                            data='app=UserSetting&action=CONFIRM_TURN_OFF_REMINDER&reminder_id={}'.format(reminder.id)
                        )
                else:
                    confirm_action = PostbackTemplateAction(
                        label='開啟提醒',
                        data='app=UserSetting&action=CONFIRM_TURN_ON_REMINDER&reminder_id={}'.format(reminder.id)
                    )

                print(confirm_action)
                actions = [set_time_action, confirm_action]
                print(actions)

                carousels.append(CarouselColumn(
                    text=message,
                    actions=actions
                ))
            reply = self.reminder_select_carousel(carousels=carousels)

        elif self.callback.action == Action.CONFIRM_TURN_OFF_REMINDER:
            reminder_id = self.callback.reminder_id
            reply = self.confirm_reminder_turn_on_or_off(reminder_id=reminder_id, status=False)

        elif self.callback.action == 'CONFIRM_TURN_ON_REMINDER':
            reminder_id = self.callback.reminder_id
            reply = self.confirm_reminder_turn_on_or_off(reminder_id=reminder_id, status=True)

        elif self.callback.action == 'TURN_ON_OR_OFF_REMINDER':
            reminder_id = self.callback.reminder_id
            reminder = UserReminder.objects.get(id=reminder_id)
            reminder.status = not reminder.status
            reminder.save()
            reply = TextSendMessage(text='設定完成，已關閉提醒！')

        elif self.callback.action == 'SET_REMINDER_TIME':
            reminder_id = self.callback.reminder_id
            data = UserSettingData()
            data.reminder_id = reminder_id
            app_cache.set_next_action(self.callback.app, Action.CHECK_INPUT_REMINDER_TIME)
            app_cache.save_data(data)  # alias of set_data and commit

            reply = TextSendMessage(text='請輸入要設定的提醒時間共四碼，例如晚上七點半：1930')

        elif self.callback.action == Action.CHECK_INPUT_REMINDER_TIME:
            input_value = self.callback.text
            reminder_id = app_cache.data.reminder_id

            time = self.check_input_is_time(input_value)
            if not time:
                reply = self.error_value_message(
                    reminder_id=reminder_id
                )
            else:
                reminder = UserReminder.objects.get(id=reminder_id)
                reminder.time = time
                reminder.status = True
                reminder.save()
                reply = [TextSendMessage(text='設定成功！'), self.conversation_closed_message]

            app_cache.delete()

        elif self.callback.action == Action.END_CONVERSATION:
            reply = self.conversation_closed_message
            app_cache.delete()

        return reply
