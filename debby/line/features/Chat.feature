# Created by PoHan at 2017/3/16
Feature: 閒聊
  身為一個來試玩的，我希望我隨便跟Debby講話，他會回答我好笑的東西，因為這樣感覺很有趣

  Background: 有個User 5566
    Given 我的line_id是 5566

  Scenario: 隨便輸入文字
    When 我輸入 "嗨"
    Then debby會回我以下裡面其中一樣
      | answer           |
      | 嗨~有什麼事是我可以幫忙的呢?  |
      | hi~有什麼問題想問我嗎?    |
      | 哈囉~想知道什麼資訊呢?     |
      | Hello~有需要協助什麼事嗎? |
      | 你好~有想要問我什麼事嗎?    |
      | 您好~需要任何協助嗎?      |
