# Created by PoHan at 2017/2/27
Feature: Food record
  # Enter feature description here
  身為一個糖尿病患，我希望可以拍照記錄我的飲食，因為這樣可以簡單紀錄

  Scenario: 點選選單後會請我記錄飲食
    When 我點擊了選單 "紀錄飲食"
    Then 他會回傳 "請上傳餐點的照片"

  Scenario: 上傳照片並記錄飲食
    When 我上傳了一張照片


