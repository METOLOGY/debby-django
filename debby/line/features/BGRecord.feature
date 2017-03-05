# Created by PoHan at 2017/3/5
Feature: 紀錄血糖
  身為一個糖尿病患，我希望對chatbot打入數字就可以記錄血糖，因為這樣感覺很方便

  Scenario: 隨便亂打字就會問我要不要紀錄血糖
    When 我輸入 "嗨"
    Then debby會有個選單回我 "嗨，現在要記錄血糖嗎？"
    And 並問我是要選項 "好啊"
    And 還是選項 "等等再說"
    
  Scenario: 打數字會問我要不要記錄血糖
    When 我輸入 "3"
    Then debby會回我 "紀錄成功！"
