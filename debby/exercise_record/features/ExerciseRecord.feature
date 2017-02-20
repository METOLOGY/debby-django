# Created by PoHan at 2017/2/13
Feature: Exercise Record
  提供一個紀錄運動過程的功能

  身為一個糖尿病患，我希望我可以對chatbot記錄我的運動狀況，因為感覺很方便

  Scenario: exercise data-set from GET
    Given a set of exercise_record.Exercises in Database
    |id|type|start_from|duration|
    |1 |"跑步"|2017-01-21 00:00:00|60|
    |2 |"散步"|2017-01-21 00:00:00|180|
    When I go to /exercise/
    Then the return includes "跑步"
    And the return includes "散步"
