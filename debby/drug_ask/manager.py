from django.core.cache import cache
from django.db.models import QuerySet
from linebot.models import SendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction
from linebot.models import TextSendMessage

from drug_ask.models import DrugTypeModel, DrugDetailModel
from line.callback import DrugAskCallback


class DrugAskManager(object):
    def __init__(self, callback: DrugAskCallback):
        self.callback = callback

    @staticmethod
    def reply_choose_one(drug_types: QuerySet) -> TextSendMessage:
        choice_texts = ""
        for drug_type in drug_types:  # type: DrugTypeModel
            choice_texts += drug_type.user_choice + "\n"
        message = "請選擇符合的項目:\n"
        return TextSendMessage(text=message+choice_texts)

    def reply_want_which_content(self, drug_type: DrugTypeModel) -> TemplateSendMessage:
        drug_detail = DrugDetailModel.objects.get(type=drug_type.type)
        user_cache = {"drug_detail_pk": drug_detail.pk}
        cache.set(self.callback.line_id, user_cache, 120)
        message = drug_detail.type + "\n" + "請問您要查詢什麼項目呢?"
        reply = TemplateSendMessage(
            alt_text=message,
            template=ButtonsTemplate(
                text=message,
                actions=[
                    PostbackTemplateAction(
                        label='1.作用機轉和服用方式',
                        data='app="drug_ask"&action=READ_DRUG_DETAIL&choice=1'
                    ),
                    PostbackTemplateAction(
                        label='2.不良反應,副作用',
                        data='app="drug_ask"&action=READ_DRUG_DETAIL&choice=2'
                    ),
                    PostbackTemplateAction(
                        label='3.禁忌',
                        data='app="drug_ask"&action=READ_DRUG_DETAIL&choice=3'
                    ),
                    PostbackTemplateAction(
                        label='4.注意事項',
                        data='app="drug_ask"&action=READ_DRUG_DETAIL&choice=4'
                    )
                ]
            )
        )
        return reply

    def handle(self) -> SendMessage:
        reply = TextSendMessage(text='ERROR!')
        if self.callback.action == 'READ_FROM_MENU':
            reply = TextSendMessage(text="請輸入藥品名稱(中英文皆可):")
        elif self.callback.action == 'READ':
            drug_types = DrugTypeModel.objects.filter(question=self.callback.text)
            if len(drug_types) > 1:
                user_cache = {"app": "drug_ask", "action": "WAIT_DRUG_TYPE_CHOICE", "drug_types": drug_types}
                cache.set(self.callback.line_id, user_cache, 120)
                reply = self.reply_choose_one(drug_types)
            elif len(drug_types) == 1:
                drug_type = drug_types[0]
                reply = self.reply_want_which_content(drug_type)
            else:
                reply = TextSendMessage(text="ERROR!")
        elif self.callback.action == 'WAIT_DRUG_TYPE_CHOICE':
            if not self.callback.text.isdigit():
                reply = TextSendMessage(text="請輸入選項中的數字喔~")
            else:
                user_cache = cache.get(self.callback.line_id)
                if user_cache:
                    drug_types = user_cache.get('drug_types')  # type: QuerySet
                    drug_type = drug_types.get(user_choice__startswith=self.callback.text)  # type: DrugTypeModel
                    reply = self.reply_want_which_content(drug_type)
                else:
                    print('Error!')
        elif self.callback.action == "READ_DRUG_DETAIL":
            user_cache = cache.get(self.callback.line_id)
            drug_detail_pk = user_cache.get('drug_detail_pk')
            drug_detail = DrugDetailModel.objects.get(drug_detail_pk)
            message = "Error!"
            if self.callback.choice == "1":
                message = "1.作用機轉和服用方式\n" + drug_detail.mechanism
            elif self.callback.choice == "2":
                message = "2.不良反應,副作用\n" + drug_detail.side_effect
            elif self.callback.choice == "3":
                message = "3.禁忌\n" + drug_detail.taboo
            elif self.callback.choice == "4":
                message = "4.注意事項\n" + drug_detail.awareness

            cache.delete(self.callback.line_id)
            reply = TextSendMessage(text=message)

        return reply
