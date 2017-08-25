from django.core.cache import cache
from linebot.models import TemplateSendMessage, ButtonsTemplate, TextSendMessage, PostbackTemplateAction, \
    URITemplateAction, CarouselTemplate, CarouselColumn

from line.callback import DrugAskCallback, ConsultFoodCallback, MyDiaryCallback
from line.callback import LineCallback, BGRecordCallback, FoodRecordCallback
from line.constant import DrugAskAction, ConsultFoodAction
from line.constant import LineAction, BGRecordAction, FoodRecordAction, MyDiaryAction


class LineManager(object):
    def __init__(self, callback: LineCallback):
        self.callback = callback
        self.registered_callback = {
            LineAction.MAIN_START: self.main_start,
            LineAction.CONSULT_START: self.consult_start,
            LineAction.RECORD_START: self.record_start,
            LineAction.REPLY_INTRO: self.reply_intro,
            LineAction.OPEN_FUTURE_MODE: self.open_future_mode,
        }

    def main_start(self):
        carousels = list()

        # the search part
        carousels.append(CarouselColumn(
            title="搜尋相關資訊",
            text="請選擇要搜尋的項目",
            thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/search.png',
            actions=[
                PostbackTemplateAction(
                    label='我想了解食物營養成分🍲',
                    data=ConsultFoodCallback(
                        line_id=self.callback.line_id,
                        action=ConsultFoodAction.READ_FROM_MENU
                    ).url
                ),
                PostbackTemplateAction(
                    label='我想要查藥物💊',
                    data=DrugAskCallback(
                        line_id=self.callback.line_id,
                        action=DrugAskAction.READ_FROM_MENU
                    ).url
                )
            ]
        ))

        # the record part
        carousels.append(CarouselColumn(
            title="記錄生活",
            text="請選擇要記錄的項目",
            thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/record.png',
            actions=[
                PostbackTemplateAction(
                    label='幫我記錄血糖',
                    data=BGRecordCallback(
                        line_id=self.callback.line_id,
                        action=BGRecordAction.CREATE_FROM_MENU,
                        text=self.callback.text
                    ).url
                ),
                PostbackTemplateAction(
                    label='幫我記錄飲食',
                    data=FoodRecordCallback(
                        line_id=self.callback.line_id,
                        action=FoodRecordAction.CREATE_FROM_MENU,
                    ).url
                ),
                # PostbackTemplateAction(
                #     label='服用藥物',
                #     data=BGRecordCallback(
                #         line_id=self.callback.line_id,
                #         action=BGRecordAction.CREATE_DRUG_RECORD
                #     ).url
                # ),
                # PostbackTemplateAction(
                #     label='注射胰島素',
                #     data=BGRecordCallback(
                #         line_id=self.callback.line_id,
                #         action=BGRecordAction.CREATE_INSULIN_RECORD
                #     ).url
                # ),
            ]
        ))

        # the diary part
        carousels.append(CarouselColumn(
            title="我的日記",
            text="請選擇要檢視的記錄項目",
            thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/summary.png',
            actions=[
                PostbackTemplateAction(
                    label="我的飲食記錄",
                    data=MyDiaryCallback(line_id=self.callback.line_id,
                                         action=MyDiaryAction.FOOD_HISTORY).url
                ),
                PostbackTemplateAction(
                    label="我的血糖記錄",
                    data=MyDiaryCallback(line_id=self.callback.line_id,
                                         action=MyDiaryAction.BG_HISTORY).url
                ),
            ]
        ))

        # future mode beta part
        carousels.append(CarouselColumn(
            title="人工智慧營養師Beta!",
            text="快來上傳你的食物照片試試看~",
            thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/beta.png',
            actions=[
                PostbackTemplateAction(
                    label="來嘗鮮!",
                    data=LineCallback(line_id=self.callback.line_id,
                                      action=LineAction.OPEN_FUTURE_MODE).url
                ),
                PostbackTemplateAction(
                    label="去玩玩!",
                    data=LineCallback(line_id=self.callback.line_id,
                                      action=LineAction.OPEN_FUTURE_MODE).url
                )
            ]
        ))

        # the reminder part

        ### temporarily remove reminder: 8/5
        # carousels.append(CarouselColumn(
        #     title="用藥提醒",
        #     text="請選擇要設定的提醒項目",
        #     thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/reminder.png',
        #     actions=[
        #         PostbackTemplateAction(
        #             label='服用藥物',
        #             data=UserSettingsCallback(line_id=self.callback.line_id, action=UserSettingsAction.SET_REMINDER,
        #                                       choice='drug').url
        #         ),
        #         PostbackTemplateAction(
        #             label='量測血糖',
        #             data=UserSettingsCallback(line_id=self.callback.line_id, action=UserSettingsAction.SET_REMINDER,
        #                                       choice='bg').url
        #         ),
        #     ]
        # ))

        # the reminder part

        carousels.append(CarouselColumn(
            title="其他",
            text="看看 Debby 會甚麼? 有空幫 Debby 填個問券嗎~?",
            thumbnail_image_url='https://debby.metology.com.tw/media/carousel-thumb/else.png',
            actions=[
                PostbackTemplateAction(
                    label='如何使用Debby?',
                    data=LineCallback(
                        line_id=self.callback.line_id,
                        action=LineAction.REPLY_INTRO,
                    ).url
                ),
                URITemplateAction(
                    label='給 Debby 一點回饋吧~',
                    uri='https://www.surveycake.com/s/Mv3Dl'
                ),
            ]
        ))

        # noinspection PyTypeChecker
        reply = [TemplateSendMessage(
            alt_text='Debby 說...',
            template=CarouselTemplate(
                columns=carousels
            )
        )]
        return reply

    def record_start(self):
        reply = TemplateSendMessage(
            alt_text='請問您要紀錄的是？',
            template=ButtonsTemplate(
                text='請問您要紀錄的是？',
                actions=[
                    PostbackTemplateAction(
                        label='記錄血糖',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=BGRecordAction.CREATE_FROM_MENU,
                            text=self.callback.text
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='記錄飲食',
                        data=FoodRecordCallback(
                            line_id=self.callback.line_id,
                            action=FoodRecordAction.CREATE_FROM_MENU,
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='服用藥物',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=BGRecordAction.CREATE_DRUG_RECORD
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='注射胰島素',
                        data=BGRecordCallback(
                            line_id=self.callback.line_id,
                            action=BGRecordAction.CREATE_INSULIN_RECORD
                        ).url
                    ),

                ]
            )
        )
        return reply

    def consult_start(self):
        reply = TemplateSendMessage(
            alt_text='請問您要查詢的是？',
            template=ButtonsTemplate(
                text='請問您要查詢的是？',
                actions=[
                    PostbackTemplateAction(
                        label='藥物查詢',
                        data=DrugAskCallback(
                            line_id=self.callback.line_id,
                            action=DrugAskAction.READ_FROM_MENU
                        ).url
                    ),
                    PostbackTemplateAction(
                        label='食物營養成分查詢',
                        data=ConsultFoodCallback(
                            line_id=self.callback.line_id,
                            action=ConsultFoodAction.READ_FROM_MENU
                        ).url
                    )
                ]
            )
        )
        return reply

    def reply_intro(self):
        # emoji list: https://emojipedia.org
        text = "您好~~我的名字是Debby！😃 我是一位線上虛擬營養衛教師，希望可以幫助您管理日常生活中的大小事哦！👍先看一下如何和Debby溝通的影片吧:\n\n" \
               "https://youtu.be/oOI2y-TlLN8 \n\n" \
               "您可於下方主選單內選擇: \n\n" \
               "(1) 搜尋相關資訊🔍: 如果您想瞭解食物的營養組成成分，我會依據六大類均衡原則，建議最適合您的攝取量哦！您也可以搜尋糖尿病用藥哦！\n\n" \
               "(2) 記錄生活📝: 可快速記錄血糖值或飲食內容，跟著Debby我的步驟來完成吧！\n\n" \
               "(3) 我的日記📓: 您還可即時查詢最近五筆血糖或飲食的紀錄情形，也可以再修改喔!\n" \
               "(詳細報表: http://m.metology.com.tw/ )\n\n" \
               "(4) 人工智慧營養師🤖:上傳你的食物照片吧!Debby幫你評估熱量~\n" \
               "(如何使用: https://youtu.be/RFol2-MrxmU)\n\n" \
               "(5) 其他❔:您點進來這裡就是啦！記得幫Debby填一下回饋喔~\n" \
               "(回饋連結: https://www.surveycake.com/s/Mv3Dl )\n\n" \
               "您也可以在訊息欄內直接輸入您想跟我說的話哦！😚(例如數字,食物名稱,藥物名稱,或直接上傳照片)，會發現意想不到的驚喜喔❤❤^^"

        # temp remove reminder
        # "(4) 用藥提醒🔔:不要害怕忘記自己要吃藥或量血糖～由我來提醒您時間吧，請放心！\n\n" \

        reply = TextSendMessage(text=text)
        return reply

    def open_future_mode(self):
        text = "體驗開始，請上傳您的食物照片"

        cache.set(self.callback.line_id + '_future', True, 300)

        reply = TextSendMessage(text=text)
        return reply

    def handle(self):
        reply = self.registered_callback[self.callback.action]()
        return reply
