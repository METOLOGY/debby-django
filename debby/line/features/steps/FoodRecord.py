import io

from PIL import Image
from behave import *
from django.core.cache import cache
from hamcrest import *
from django.apps import apps
from linebot.models import ImageMessage
from linebot.models import MessageEvent

from food_record.manager import FoodRecordManager
from food_record.models import FoodModel
from line.callback import FoodRecordCallback
from line.handler import InputHandler, CallbackHandler
from user.models import CustomUserModel


@step("我有張照片")
def step_impl(context):
    context.image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
    byte_arr = io.BytesIO()
    context.image.save(byte_arr, 'jpeg')
    context.image_content = byte_arr.getvalue()


@step("我上傳了一張照片")
def step_impl(context):
    # https://devdocs.line.me/en/#webhook-event-object
    im = ImageMessage(id='55669487')
    event = MessageEvent(message=im)
    user_cache = {'event': 'record_food', 'message_id': im.id}
    cache.set(context.line_id, user_cache, 120)

    c = FoodRecordCallback(context.line_id, action='reply_if_want_to_record').url
    context.send_message = CallbackHandler(c).handle()


@step("在DB {model_name} 中有這筆資料使用者 {line_id} 並且有我那張照片")
def step_impl(context, model_name, line_id):
    model = apps.get_model(*model_name.split('.'))
    user = CustomUserModel.objects.get(line_id=line_id)
    obj = model.objects.get(user=user)
    image = Image.open(obj.food_image_upload)
    context.pk = obj.pk
    assert_that(image.size, equal_to(context.image.size))


@step("系統暫存了我的line_id {line_id} 和我那筆資料的 id")
def step_impl(context, line_id):
    user_cache = cache.get(line_id)
    assert_that(user_cache, not_none())
    food_record_pk = user_cache['food_record_pk']
    assert_that(food_record_pk, equal_to(context.pk))


@given('選單 "紀錄成功! 請問是否要補充文字說明 例如: 1.5份醣類"')
def step_impl(context):
    fr_manager = FoodRecordManager()
    context.given_template = fr_manager.reply_record_success_and_if_want_more_detail()


@step('"YOYOYO" 會跟照片記錄在同一筆中')
def step_impl(context):
    pk = context.pk
    obj = FoodModel.objects.get(pk=pk)
    image = Image.open(obj.food_image_upload)
    assert_that(image.size, equal_to(context.image.size))
    assert_that(obj.note, equal_to("YOYOYO"))
