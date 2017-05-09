from django.core.cache import cache
from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, TextSendMessage, \
    CarouselTemplate, CarouselColumn

from bg_record.models import BGModel
from food_record.models import FoodModel
from line.callback import MyDiaryCallback
from line.constant import MyDiaryAction as Action, App
from user.cache import AppCache


class MyDiaryManager(object):
    def __init__(self, callback: MyDiaryCallback):
        self.callback = callback

    @staticmethod
    def no_record() -> TextSendMessage:
        return TextSendMessage(text="抱歉！沒有任何歷史紀錄耶~")

    def handle(self):
        reply = TextSendMessage(text="ERROR!")
        app_cache = AppCache(self.callback.line_id, app=self.callback.app)

        if self.callback.action == Action.START:
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
                            label="飲食紀錄",
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
            records = BGModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:5]
            if records:
                carousels = []
                for record in records:
                    time = record.time.strftime("%Y/%m/%d %H:%M:%S")
                    type_ = "飯後" if record.type == "after" else "飯前"
                    val = record.glucose_val
                    message = "血糖值: {} {}".format(type_, val)
                    carousels.append(CarouselColumn(
                        title=time,
                        text=message,
                        actions=[
                            PostbackTemplateAction(
                                label='修改記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.UPDATE,
                                    record_pk=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    record_pk=record.id).url
                            )
                        ]
                    ))
                # noinspection PyTypeChecker
                reply = TemplateSendMessage(
                    alt_text="最近的五筆血糖紀錄",
                    template=CarouselTemplate(
                        columns=carousels
                    ))
            else:
                reply = self.no_record()
        elif self.callback.action == Action.FOOD_HISTORY:
            print(App.MY_DIARY, Action.FOOD_HISTORY)
            records = FoodModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:5]
            if records:
                carousels = []
                for record in records:
                    time = record.time.strftime("%Y/%m/%d %H:%M:%S")
                    host = cache.get("host_name")
                    if record.food_image_upload:
                        url = record.food_image_upload.url
                    else:
                        url = '/media/FoodRecord/default.bmp'
                    photo = "https://{}{}".format(host, url)

                    text = record.note[:61].replace("\n", " ")
                    if not text:  # if text is empty
                        text = " "
                    carousels.append(CarouselColumn(
                        thumbnail_image_url=photo,
                        title=time,
                        text=text,
                        actions=[
                            PostbackTemplateAction(
                                label='修改記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.UPDATE,
                                    record_pk=record.id).url
                            ),
                            PostbackTemplateAction(
                                label='刪除記錄',
                                data=MyDiaryCallback(
                                    line_id=self.callback.line_id,
                                    action=Action.DELETE,
                                    record_pk=record.id).url
                            )
                        ]
                    ))

                # noinspection PyTypeChecker
                reply = TemplateSendMessage(
                    alt_text="最近的五筆飲食紀錄",
                    template=CarouselTemplate(
                        columns=carousels
                    ))

        elif self.callback.action == Action.DELETE:
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
                                record_id=self.callback.record_pk).url
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data=MyDiaryCallback(
                                line_id=self.callback.line_id,
                                action=Action.DELETE_CANCEL,
                                record_id=self.callback.record_pk).url
                        )
                    ]
                )
            )

        elif self.callback.action == Action.DELETE_CONFIRM:
            pass

        return reply
