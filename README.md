# Daemon_flask

###### flask version daemon

A app that collaborate with API.

## 目的

- 細化 API 工作量
- 遊戲訂單項目需要寫入資料的都分在Daemon
- 使用redis 當作溝通橋樑

## 傳送流程

1. API push data in redis
1. Daemon 發現有redis 訊號, 訂單進行消耗並寫入db
1. 萬一訂單建立失敗，重回redis 等待再次進行


