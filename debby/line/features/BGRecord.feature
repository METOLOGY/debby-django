# Created by PoHan at 2017/3/5
Feature: 紀錄血糖
  身為一個糖尿病患，我希望對chatbot打入數字就可以記錄血糖，因為這樣感覺很方便

  Background: 有個User 5566
    Given 我的line_id是 5566

#  Scenario: 隨便亂打字就會問我要不要紀錄血糖
#    Given 我打開 debby 對話框
#    When 我輸入 "嗨"
#    Then debby會有個選單回我 "嗨，現在要記錄血糖嗎？"
#    And 並問我是要選項 "好啊"
#    And 還是選項 "等等再說"

  Scenario: 回應要記錄血糖嗎的選單
    Given 選單 "嗨，現在要記錄血糖嗎？"
    When 我選選項 "好啊"
    Then debby會回我 "那麼，輸入血糖～"
    When 我選選項 "等等再說"
    Then debby會回我 "好，要隨時注意自己的血糖狀況哦！"

  Scenario: 打數字會幫我紀錄血糖
    When 我輸入 "183"
    Then debby會回我 "紀錄成功！ 血糖還是稍微偏高,要多注意喔!"
    And 在DB bg_record.BGModel 中有這筆資料使用者 5566 血糖 183


