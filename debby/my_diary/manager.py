from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, TextSendMessage, \
    CarouselTemplate, CarouselColumn

from bg_record.models import BGModel, InsulinIntakeModel, DrugIntakeModel
from line.callback import MyDiaryCallback
from line.constant import MyDiaryAction as Action
from user.cache import AppCache, MyDiaryData
from datetime import datetime, time


class MyDiaryManager(object):


    def isDate(self, val: str):
        year = val[0:4]
        month = val[4:6]
        day = val[6:]

        today = datetime.now().date()

        try:
            new_date = datetime(year=year, month=month, day=day)
            if new_date > today:
                return False
            else:
                return new_date
        except ValueError:
            return False

    def isTime(self, val: str):
        hour = val[0:2]
        minute = val[2:]

        try:
            new_time = time(hour=hour, minute=minute)
            return new_time
        except ValueError:
            return False


    def __init__(self, callback: MyDiaryCallback):
        self.callback = callback

    def handle(self):
        reply = TextSendMessage(text="ERROR!")
        app_cache = AppCache(self.callback.line_id, app=self.callback.app)

        if self.callback.action == Action.CREATE_FROM_MENU:
            app_cache.commit()
            reply = TemplateSendMessage(
                alt_text="請選擇想要檢視的紀錄",
                template=ButtonsTemplate(
                    text="請選擇想要檢視的紀錄",
                    actions=[
                        PostbackTemplateAction(
                            label="血糖紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.BG_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="胰島素注射紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.INSULIN_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="用藥紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.DRUG_HISTORY).url
                        )
                    ]
                )

            )
        elif self.callback.action == Action.BG_HISTORY:
            records = BGModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:6]
            carousels = []
            type='bg'

            if len(records) == 0:
                reply = TextSendMessage(text="目前您沒有任何記錄哦～")
            else:
                for record in records:
                    time = record.time.strftime("%H:%M, %x")
                    type_ = "飯後" if record.type == "after" else "飯前"
                    val = record.glucose_val
                    message = "血糖值: {} {}".format(type_, val)
                    carousels.append(CarouselColumn(
                        title="紀錄時間: {}".format(time),
                        text=message,
                        actions=[
                            PostbackTemplateAction(
                                label='修改記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.BG_UPDATE,
                                    type=type,
                                    record_id=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    type=type,
                                    record_id=record.id).url
                            )
                        ]
                    ))

                # noinspection PyTypeChecker
                reply = TemplateSendMessage(
                    alt_text="最近的五筆血糖紀錄",
                    template=CarouselTemplate(
                        columns=carousels
                    )
                )

        elif self.callback.action == Action.DELETE:
            type = self.callback.type
            print(dir(self.callback))
            print(self.callback.record_id, type)

            reply = TemplateSendMessage(
                alt_text='確定要刪除這筆紀錄？',
                template=ButtonsTemplate(
                    text='您確定要刪除這筆紀錄？',
                    actions=[
                        PostbackTemplateAction(
                            label='確定',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE_CONFIRM,
                                type=type,
                                record_id=self.callback.record_id).url
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE_CANCEL,
                                type=type,
                                record_id=self.callback.record_id).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.DELETE_CANCEL:

            action = ''
            if self.callback.type == 'bg':
                action = Action.BG_HISTORY

            elif self.callback.type == 'insulin':
                action = Action.INSULIN_HISTORY

            elif self.callback.type == 'drug':
                action = Action.DRUG_HISTORY

            self.callback.action = action

            reply = [
                TextSendMessage(text="紀錄仍保留,請選擇欲修改項目"),
                self.handle()
                ]

        elif self.callback.action == Action.DELETE_CONFIRM:
            record_id = self.callback.record_id
            print(record_id)

            if self.callback.type == 'bg':
                record = BGModel.objects.get(id=record_id)
                record.delete()

            elif self.callback.type == 'insulin':
                record = InsulinIntakeModel.objects.get(id=record_id)
                record.delete()

            elif self.callback.type == 'drug':
                record = DrugIntakeModel.objects.get(id=record_id)
                record.delete()

            reply = TextSendMessage(text='刪除成功!')

        elif self.callback.action == Action.BG_UPDATE:
            reply = TemplateSendMessage(
                alt_text="請選擇欲修改的項目",
                template=ButtonsTemplate(
                    text="請選擇欲修改的項目",
                    actions=[
                        PostbackTemplateAction(
                            label="日期",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.BG_UPDATE_DATE,
                                type='bg',
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="時間",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.BG_UPDATE_TIME,
                                type='bg',
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="血糖",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.BG_UPDATE_VALUE,
                                type='bg',
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="餐前或飯後",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.BG_UPDATE_TYPE,
                                type='bg',
                                record_id=self.callback.record_id
                            ).url
                        ),
                    ]
                )
            )
        elif self.callback.action == Action.BG_UPDATE_DATE:
            app_cache.set_next_action("BG_UPDATE_DATE_CHECK")
            data = MyDiaryData()
            data.record_id = self.callback.record_id
            data.record_type = self.callback.record_type
            app_cache.save_data(data)

            reply = TemplateSendMessage(
                alt_text="請輸入西元年月日共8碼,例如: 20170225",
                template=ButtonsTemplate(
                    text="請輸入西元年月日共8碼,例如: 20170225",
                    actions=[
                        PostbackTemplateAction(
                            label="取消修改",
                            data=MyDiaryCallback(
                                action=Action.UPDATE_CANCEL
                            ).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.UPDATE_DATE_CHECK:
            text = self.callback.text
            record_type = app_cache.data.record_type
            record_id = app_cache.data.record_id
            if self.isDate(text):
                pass
            else:
                reply_action = record_type.upper() + '_UPDATE_DATE_CHECK'

                reply = TemplateSendMessage(
                    alt_text="哎呀！您如果要修改日期的話請依照格式輸入喔！",
                    template=ButtonsTemplate(
                        text="哎呀！您如果要修改日期的話請依照格式輸入喔！",
                        actions=[
                            PostbackTemplateAction(
                                label="重新輸入",
                                date=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=reply_action,
                                    type=record_type,
                                    record_id=record_id
                                ).url
                            ),
                            PostbackTemplateAction(
                                label="取消修改",
                                data=MyDiaryCallback(
                                    action=Action.UPDATE_CANCEL
                                ).url
                            ),
                        ]
                    )
                )

        elif self.callback.action == Action.UPDATE_CANCEL:
            reply = TextSendMessage(text="好的！那就不更動您原始的紀錄囉！")
            app_cache.delete()

        return reply
