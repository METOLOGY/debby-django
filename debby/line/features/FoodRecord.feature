# Created by PoHan at 2017/2/27
Feature: 紀錄飲食
  # Enter feature description here
  身為一個糖尿病患，我希望可以拍照記錄我的飲食，因為這樣可以簡單紀錄

  Background: 有個User 5566
    Given 我的line_id是 5566
    And 我有張照片

  Scenario: 上傳照片並記錄飲食
    When 我上傳了一張照片
    Then 在DB food_record.FoodModel 中有這筆資料使用者 5566 並且有我那張照片
    And 系統暫存了我的line_id 5566 和我那筆資料的 id

    And debby會回我 "您是否要繼續增加文字說明? (請輸入; 若已完成紀錄請回傳英文字母N )"

    When 我輸入 "YOYOYO"
    Then debby會回我 "繼續說"
    And "YOYOYO" 會跟照片記錄在同一筆中
    When 我輸入 "YOYOYOYO"
    Then debby會回我 "繼續說"
    When 我輸入 "N"
    Then debby會回我 "記錄成功!"
    And 在DB 中有這筆資料使用者 5566 並且記錄 "YOYOYO\nYOYOYOYO"
    When 我輸入 "YO"
    Then debby會回我 "哎呀，我不太清楚你說了什麼，你可以換句話說嗎 ~ "
