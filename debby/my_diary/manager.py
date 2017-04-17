from linebot.models import TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, TextSendMessage, \
    CarouselTemplate, CarouselColumn

from bg_record.models import BGModel
from line.callback import MyDiaryCallback
from user.cache import AppCache


class MyDiaryManager(object):
    def __init__(self, callback: MyDiaryCallback):
        self.callback = callback


    def handle(self):
        reply = TextSendMessage(text="ERROR!")
        app_cache = AppCache(self.callback.line_id, app=self.callback.app)

        if self.callback.action == "START":
            app_cache.commit()
            reply = TemplateSendMessage(
                alt_text="請選擇想要檢視的紀錄",
                template=ButtonsTemplate(
                    text="請選擇想要檢視的紀錄",
                    actions=[
                        PostbackTemplateAction(
                            label="血糖紀錄",
                            data="app=MyDiary&action=BGHistory"
                        )
                    ]
                )

            )
        elif self.callback.action == "BGHistory":
            records = BGModel.objects.filter(user__line_id=self.callback.line_id).order_by('-time')[:6]
            carousels = []
            for record in records:
                time = record.time.strftime("%H:%M, %x")
                type_ = "飯後" if record.type == "after" else "飯前"
                val = record.glucose_val
                message = "紀錄時間: {}\n血糖值: {} {}".format(time, type_, val)
                carousels.append(CarouselColumn(
                            text=message,
                            actions=[
                                PostbackTemplateAction(
                                    label='太好了!',
                                    data='app=MyDiary&action=YOKATTA'
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
        elif self.callback.action == "YOKATTA":
            reply = TextSendMessage(text="謝謝你的讚美>///<")

        return reply
