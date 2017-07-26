import math
from collections import deque
from typing import List, Union

from django.db.models import QuerySet
from linebot.models import SendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction
from linebot.models import TextSendMessage

from drug_ask.models import DrugTypeModel, DrugDetailModel
from line.callback import DrugAskCallback
from line.constant import DrugAskAction as Action, App
from user.cache import AppCache, DrugAskData


class DrugAskManager(object):
    def __init__(self, callback: DrugAskCallback):
        self.callback = callback

    @staticmethod
    def reply_choose_one(drug_types: QuerySet) -> TextSendMessage:
        choice_texts = ""
        for drug_type in drug_types:  # type: DrugTypeModel
            choice_texts += drug_type.user_choice + "\n"
        message = "請選擇符合的項目:\n"
        return TextSendMessage(text=message + choice_texts)

    def reply_want_which_content(self, fuzzy_drug_name: str, drug_detail_id: str) -> TemplateSendMessage:
        message = "請問您要查詢什麼項目呢?"
        if fuzzy_drug_name:
            message = "{}, 請問您要查詢什麼項目呢?".format(fuzzy_drug_name)
        reply = TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[
                    PostbackTemplateAction(
                        label='(1) 作用機轉和服用方式',
                        data=DrugAskCallback(
                            line_id=self.callback.line_id,
                            action=Action.READ_DRUG_DETAIL,
                            drug_detail_id=drug_detail_id,
                            choice=1).url
                    ),
                    PostbackTemplateAction(
                        label='(2) 不良反應,副作用',
                        data=DrugAskCallback(
                            line_id=self.callback.line_id,
                            action=Action.READ_DRUG_DETAIL,
                            drug_detail_id=drug_detail_id,
                            choice=2).url
                    ),
                    PostbackTemplateAction(
                        label='(3) 禁忌',
                        data=DrugAskCallback(
                            line_id=self.callback.line_id,
                            action=Action.READ_DRUG_DETAIL,
                            drug_detail_id=drug_detail_id,
                            choice=3).url
                    ),
                    PostbackTemplateAction(
                        label='(4) 注意事項',
                        data=DrugAskCallback(
                            line_id=self.callback.line_id,
                            action=Action.READ_DRUG_DETAIL,
                            drug_detail_id=drug_detail_id,
                            choice=4).url
                    )
                ]
            )
        )
        return reply

    def handle(self) -> Union[SendMessage, List[SendMessage]]:
        reply = TextSendMessage(text='DRUG_ASK ERROR!')
        app_cache = AppCache(self.callback.line_id)

        if self.callback.action == Action.READ_FROM_MENU:
            # init cache again to clean other app's status and data
            app_cache.set_next_action(self.callback.app, action=Action.READ)
            app_cache.commit()

            reply = TextSendMessage(text="請輸入藥品名稱(中英文皆可):")
        elif self.callback.action == Action.READ:
            drug_types = DrugTypeModel.objects.filter(question__icontains=self.callback.text)
            if len(drug_types) > 1:
                drug_types = [drug_type for drug_type in drug_types if drug_type.user_choice]
                drug_len = len(drug_types)
                data = DrugAskData()
                data.drug_types = drug_types

                # find how many template needed
                def get_each_card_num(choice_num: int) -> list:
                    def find_card_len(num):
                        return math.ceil(num / 4)

                    def find_button_num(num, _card_len):
                        return math.ceil(num / _card_len)

                    result = []
                    while choice_num > 0:
                        card_len = find_card_len(choice_num)
                        button_num = find_button_num(choice_num, card_len)
                        result.append(button_num)
                        choice_num -= button_num
                    return result

                reply = list()
                reply.append(TextSendMessage(text="請選擇符合的項目:"))
                card_num_list = get_each_card_num(drug_len)
                message = "請問您要查詢的是:"
                d = deque(drug_types)
                for card_num in card_num_list:
                    actions = []
                    for i in range(card_num):
                        drug_type = d.popleft()  # type:DrugTypeModel
                        if drug_type.user_choice:
                            actions.append(
                                PostbackTemplateAction(
                                    label=drug_type.user_choice,
                                    data=DrugAskCallback(
                                        line_id=self.callback.line_id,
                                        action=Action.WAIT_DRUG_TYPE_CHOICE,
                                        fuzzy_drug_name=drug_type.user_choice).url
                                ))
                    if actions:
                        template_send_message = TemplateSendMessage(
                            alt_text=message,
                            template=ButtonsTemplate(
                                text=message,
                                actions=actions
                            )
                        )
                        reply.append(template_send_message)
            elif len(drug_types) == 1:
                drug_type = drug_types[0]
                drug_detail = DrugDetailModel.objects.get(type=drug_type.type)

                reply = self.reply_want_which_content(drug_type.answer, drug_detail.id)
            else:
                app_cache.delete()
                reply = TextSendMessage(text="Debby 找不到您輸入的藥物喔，試試其他的?")
        elif self.callback.action == Action.WAIT_DRUG_TYPE_CHOICE:
            drug_type = DrugTypeModel.objects.filter(user_choice=self.callback.fuzzy_drug_name)[0]
            drug_detail = DrugDetailModel.objects.filter(type=drug_type.type)

            if not drug_detail:
                reply = TextSendMessage(text='這種藥我還不大熟>"<')
            else:
                drug_detail = drug_detail[0]
                reply = self.reply_want_which_content(drug_type.answer, drug_detail.id)

        elif self.callback.action == Action.READ_DRUG_DETAIL:
            drug_detail_pk = self.callback.drug_detail_id

            drug_detail = DrugDetailModel.objects.get(pk=drug_detail_pk)
            message = "DRUG_ASK READ_DRUG_DETAIL ERROR!"
            if self.callback.choice == "1":
                message = "(1) 服用方式\n" + drug_detail.mechanism
            elif self.callback.choice == "2":
                message = "(2) 藥物機轉與副作用\n" + drug_detail.side_effect
            elif self.callback.choice == "3":
                message = "(3) 禁忌\n" + drug_detail.taboo
            elif self.callback.choice == "4":
                message = "(4) 注意事項\n" + drug_detail.awareness

            reply = TextSendMessage(text=message)

        return reply
