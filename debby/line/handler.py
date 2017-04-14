import random
from urllib.parse import parse_qsl

from linebot.models import ImageMessage
from linebot.models import Message
from linebot.models import SendMessage
from linebot.models import TextMessage
from linebot.models import TextSendMessage

from bg_record.manager import BGRecordManager
from chat.manager import ChatManager
from consult_food.manager import ConsultFoodManager
from drug_ask.manager import DrugAskManager
from food_record.manager import FoodRecordManager
from line.callback import FoodRecordCallback, Callback, BGRecordCallback, ChatCallback, ConsultFoodCallback, \
    DrugAskCallback
from line.models import EventModel
from user.cache import AppCache
from user.models import CustomUserModel


class InputHandler(object):
    def __init__(self, line_id: str, message: Message = None):
        self.line_id = line_id
        self.current_user = CustomUserModel.objects.get(line_id=line_id)
        self.message = message
        self.text = ''
        self.image_id = ''

    def is_input_a_bg_value(self):
        """
        Check the int input from user is a blood glucose value or not.
        We defined the blood value is between 20 to 999
        :return: boolean
        """
        return self.text.isdigit() and 20 < int(self.text) < 999

    def find_best_answer_for_text(self) -> SendMessage:
        """
        Mainly response for replying.
        :return: SendMessage
        """
        app_cache = AppCache(self.line_id)
        events = EventModel.objects.filter(phrase=self.text)

        # managers
        bg_manager = BGRecordManager(BGRecordCallback(line_id=self.line_id, text=self.text))
        # chat_manager = ChatManager(callback_url)
        # food_manager = FoodRecordManager(callback_url)

        # event founded in event model(app, action)
        if events:
            event = random.choice(events)
            print(event.callback, event.action)

            callback = Callback(line_id=self.line_id,
                                app=event.callback,
                                action=event.action,
                                text=self.text)
            return CallbackHandler(callback).handle()

        # user might input number directly.
        elif self.is_input_a_bg_value():
            bg_manager.record_bg_record(self.current_user, int(self.text))
            text1 = bg_manager.reply_record_success()
            text2 = bg_manager.reply_by_check_value(self.text)
            text1.text += " " + text2.text
            return text1
        # elif chat_manager.is_input_a_chat(self.text):
        #     return chat_manager.reply_answer()

        # user type the description after uploading a food image.
        elif app_cache.is_app_running():
            callback = None
            if app_cache.app == "FoodRecord":
                callback = FoodRecordCallback(self.line_id,
                                              action=app_cache.action,
                                              text=self.text
                                              )
            elif app_cache.app == "DrugAsk":
                callback = DrugAskCallback(self.line_id,
                                           action=app_cache.action,
                                           text=self.text)

            return CallbackHandler(callback).handle()

        # Debby can't understand what user saying.
        else:
            # here should response something like: "哎呀，我有點笨，你可以換句話說嗎 (bittersmile)(bittersmile)(bittersmile)"
            # return bg_manager.reply_does_user_want_to_record()
            return TextSendMessage(text='哎呀，我不太清楚你說了什麼，你可以換句話說嗎 ~ ')

    def handle_image(self, image_id):
        callback = FoodRecordCallback(self.line_id,
                                      action="DIRECT_UPLOAD_IMAGE",
                                      image_id=image_id)
        return CallbackHandler(callback).handle()

    def handle_postback(self, data):
        app_cache = AppCache(self.line_id)
        data_dict = dict(parse_qsl(data))
        c = Callback(line_id=self.line_id, **data_dict)
        if c.app == "FoodRecord" and not app_cache.is_app_running():  # not sure if this is a common rule for all apps
            return None
        return CallbackHandler(c).handle()

    def handle(self):
        # check the input type
        if isinstance(self.message, TextMessage):
            self.text = self.message.text
            return self.find_best_answer_for_text()

        elif isinstance(self.message, ImageMessage):
            return self.handle_image(self.message.id)


class CallbackHandler(object):
    """
    Distribute the tasks (ex: the query result from EventModel) to corresponding App.manager
    """
    image_content = bytes()

    def __init__(self, callback: Callback):
        self.callback = callback

    def is_callback_from_food_record(self):
        return self.callback == FoodRecordCallback and self.callback.action == 'CREATE'

    def handle(self) -> SendMessage:
        """
        First convert the input Callback to proper type of Callback, then run the manager.
        """
        print("{}, {}\n".format(self.callback.app, self.callback.action))
        if self.callback == BGRecordCallback:
            callback = self.callback.convert_to(FoodRecordCallback)
            bg_manager = BGRecordManager(callback)
            return bg_manager.handle()

        elif self.callback == FoodRecordCallback:
            callback = self.callback.convert_to(FoodRecordCallback)
            fr_manager = FoodRecordManager(callback)
            return fr_manager.handle()

        elif self.callback == ChatCallback:
            callback = self.callback.convert_to(ChatCallback)
            chat_manager = ChatManager(callback)
            return chat_manager.handle()

        elif self.callback == ConsultFoodCallback:
            callback = self.callback.convert_to(ConsultFoodCallback)
            cf_manager = ConsultFoodManager(callback)
            return cf_manager.handle()

        elif self.callback == DrugAskCallback:
            callback = self.callback.convert_to(DrugAskCallback)
            da_manager = DrugAskManager(callback)
            return da_manager.handle()

        else:
            print('not find corresponding app.')
