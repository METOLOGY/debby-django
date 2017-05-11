from django.core.cache import cache
from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, TextSendMessage, \
    CarouselTemplate, CarouselColumn

from bg_record.models import BGModel, InsulinIntakeModel, DrugIntakeModel
from line.callback import MyDiaryCallback
from line.constant import MyDiaryAction as Action, App
from line.constant import MyDiaryAction as Action
from line.constant import RecordType
from user.cache import AppCache, MyDiaryData
from datetime import datetime, time


class MyDiaryManager(object):

    @staticmethod
    def confirm_template(line_id, old, new):
        reply = TemplateSendMessage(
            alt_text='您確定要將原本紀錄 {} 修改成 {}?'.format(str(old.date()), str(new.date())),
            template=ButtonsTemplate(
                text='您確定要將原本紀錄 {} 修改成 {}?'.format(str(old.date()), str(new.date())),
                actions=[
                    PostbackTemplateAction(
                        label="是，請修改",
                        data=MyDiaryCallback(line_id=line_id,
                                             action=Action.UPDATE_CONFIRM).url
                    ),
                    PostbackTemplateAction(
                        label="否，取消修改",
                        data=MyDiaryCallback(line_id=line_id,
                                             action=Action.UPDATE_CANCEL).url
                    ),
                ]
            )

        )

        return reply

    @staticmethod
    def get_proper_record(record_type, record_id):
        print(record_type, record_id)
        if record_type == RecordType.BG:
            record = BGModel.objects.get(id=record_id)
        elif record_type == RecordType.INSULIN:
            record = InsulinIntakeModel.objects.get(id=record_id)
        else:
            record = DrugIntakeModel.objects.get(id=record_id)

        return record

    @staticmethod
    def is_date(val: str):
        year = int(val[0:4])
        month = int(val[4:6])
        day = int(val[6:])

        today = datetime.now()

        try:
            new_date = datetime(year=year, month=month, day=day)
            if new_date > today:
                return False
            else:
                return new_date
        except ValueError:
            return False

    @staticmethod
    def is_time(val: str):
        hour = val[0:2]
        minute = val[2:]

        try:
            new_time = time(hour=hour, minute=minute)
            return new_time
        except ValueError:
            return False

    def __init__(self, callback: MyDiaryCallback):
        self.callback = callback

    @staticmethod
    def no_record() -> TextSendMessage:
        return TextSendMessage(text="抱歉！沒有任何歷史紀錄耶~")

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
                                                 action=Action.FOOD_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="用藥紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.DRUG_HISTORY).url
                        ),
                        PostbackTemplateAction(
                            label="胰島素紀錄",
                            data=MyDiaryCallback(line_id=self.callback.line_id,
                                                 action=Action.INSULIN_HISTORY).url
                        ),
                    ]
                )

            )
        elif self.callback.action == Action.BG_HISTORY:
            records = BGModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:6]
            carousels = []
            record_type = RecordType.BG

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
                                    record_type=record_type,
                                    record_id=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    record_type=record_type,
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
            type_ = self.callback.record_type

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
                                record_type=type_,
                                record_id=self.callback.record_id).url
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE_CANCEL,
                                record_type=type_,
                                record_id=self.callback.record_id).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.DELETE_CANCEL:

            action = ''
            if self.callback.record_type == RecordType.BG:
                action = Action.BG_HISTORY

            elif self.callback.record_type == RecordType.INSULIN:
                action = Action.INSULIN_HISTORY

            elif self.callback.record_type == RecordType.DRUG:
                action = Action.DRUG_HISTORY

            self.callback.action = action

            reply = [
                TextSendMessage(text="紀錄仍保留,請選擇欲修改項目"),
                self.handle()
                ]

        elif self.callback.action == Action.DELETE_CONFIRM:
            record = self.get_proper_record(record_type=self.callback.record_type, record_id=self.callback.record_id)
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
                                action=Action.UPDATE_DATE,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="時間",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_TIME,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="血糖",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_VALUE,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                        PostbackTemplateAction(
                            label="餐前或飯後",
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.UPDATE_TYPE,
                                record_type=RecordType.BG,
                                record_id=self.callback.record_id
                            ).url
                        ),
                    ]
                )
            )
        elif self.callback.action == Action.UPDATE_DATE:
            app_cache.set_next_action("UPDATE_DATE_CHECK")
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
                                line_id=self.callback.line_id,
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

            if self.is_date(text):
                new_date = self.is_date(text)
                data = app_cache.data
                data.new_date = new_date
                app_cache.save_data(data)
                record = self.get_proper_record(record_id=record_id, record_type=record_type)
                reply = self.confirm_template(line_id=app_cache.line_id, old=record.time, new=new_date)

            else:
                reply = TemplateSendMessage(
                    alt_text="哎呀！您如果要修改日期的話請依照格式輸入喔！",
                    template=ButtonsTemplate(
                        text="哎呀！您如果要修改日期的話請依照格式輸入喔！",
                        actions=[
                            PostbackTemplateAction(
                                label="重新輸入",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_DATE,
                                    record_type=record_type,
                                    record_id=record_id
                                ).url
                            ),
                            PostbackTemplateAction(
                                label="取消修改",
                                data=MyDiaryCallback(
                                    line_id=app_cache.line_id,
                                    action=Action.UPDATE_CANCEL
                                ).url
                            ),
                        ]
                    )
                )

        elif self.callback.action == Action.UPDATE_CONFIRM:
            record_type = app_cache.data.record_type
            record_id = app_cache.data.record_id
            record = self.get_proper_record(record_id=record_id, record_type=record_type)
            record.time = app_cache.data.new_date
            record.save()

            reply = TextSendMessage(text="修改成功!")

        elif self.callback.action == Action.UPDATE_CANCEL:
            reply = TextSendMessage(text="好的！那就不更動您原始的紀錄囉！")
            app_cache.delete()

        return reply
