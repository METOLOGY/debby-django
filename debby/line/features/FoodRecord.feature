# Created by PoHan at 2017/2/27
Feature: 紀錄飲食
  # Enter feature description here
  身為一個糖尿病患，我希望可以拍照記錄我的飲食，因為這樣可以簡單紀錄

  Background: 有個User 5566
    Given 我的line_id是 5566
    And 我有張照片

  Scenario: 上傳照片並記錄飲食
    When 我上傳了一張照片
    Then debby會有個選單回我 "請問是否要記錄飲食"
    And 並問我是要選項 "好喔"
    And 還是選項 "跟你玩玩的"

    When 我選選項 "好喔"
    Then debby會有個選單回我 "紀錄成功! 請問是否要補充文字說明? 例如: 1.5份醣類"
    And 並問我是要選項 "好啊"
    And 還是選項 "不用了"
    And 在DB food_record.FoodModel 中有這筆資料使用者 5566 並且有我那張照片
    And 系統暫存了我的line_id 5566 和我那筆資料的 id

    When 我選選項 "好啊"
    Then debby會回我 "請輸入補充說明"
    Then debby在Log裡面記錄了剛剛我打的句子 "好啊", 跟回覆 "請輸入補充說明"

    When 我輸入 "YOYOYO"
    Then debby會回我 "紀錄成功!"
    And "YOYOYO" 會跟照片記錄在同一筆中

  Scenario: 上傳照片並記錄飲食回應
    When 我上傳了一張照片
    Then debby會有個選單回我 "請問是否要記錄飲食"
    And 並問我是要選項 "好喔"
    And 還是選項 "跟你玩玩的"

    When 我選選項 "跟你玩玩的"
    Then debby會回我 "什麼啊原來只是讓我看看啊"

  Scenario: 紀錄完成的後續回應
    Given 選單 "紀錄成功! 請問是否要補充文字說明 例如: 1.5份醣類"
    When 我選選項 "不用了"
    Then debby會回我 "好的"
