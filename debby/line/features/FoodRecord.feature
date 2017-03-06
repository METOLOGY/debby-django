# Created by PoHan at 2017/2/27
Feature: 紀錄飲食
  # Enter feature description here
  身為一個糖尿病患，我希望可以拍照記錄我的飲食，因為這樣可以簡單紀錄

  Background: 有個User 5566
    Given 我的line_id是 5566

  Scenario: 上傳照片並記錄飲食
    When 我上傳了一張照片
    Then debby會有個選單回我 "請問是否要記錄飲食"
    And 並問我是要選項 "好喔"
    And 還是選項 "跟你玩玩的"



