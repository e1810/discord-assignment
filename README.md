## これは何？
課題管理用のdiscordBotです。締切の3日前から通知します。締切を過ぎた課題は自動で削除されます。

## どうやったら使えるの？

このbotと同じサーバに参加していれば利用できます。

サンプルとして以下のリンクのXをoに置き換えたものを踏んだ先のサーバに入れば使えます。

https://discXrd.gg/4W3qdfCEJh

以降はBOTとのDMでやりとりできます。

## 使い方(コマンド一覧)

`!help`,`!h`: ヘルプを表示します。

`!add`,`!a`: 課題を追加します。フォーマットは`!add {課題名} {締切} {備考}`です。
締切は'YYYY/MM/DD'の書式ですが、年は省略可です(コマンド呼び出し時点での時刻と同じ年になるので注意)。
備考は任意です。書かなくても構いませんし、空白を挟んでいくつも書いても構いません。

`!delete`,`!del`: 課題を削除します。フォーマットは`!delete {課題名}`です。削除した課題は元に戻せません。

`!list`,`!ls`: 現在登録されている課題の一覧を表示します。

## 定期通知について

おおよそ8時間ごとに締切が近い課題を確認するプログラムを巡回させています。サーバにいる必要があるのはこのためです。逆に言えば、サーバにいなくても定期通知が利用できないだけで、手動でなら問題なく利用できます。

サーバ内のメンバー全員について以下の動作を行います。
そのメンバーが追加した課題を全て確認し、締切が3日以内のものがあればまとめて記録します。
記録した課題をまとめてそのメンバーとのDMに送信します。特に締切が1日以内のものは明記します。

## 質問・要望などは

このリポジトリのissueか作者のTwitterなどに投げてください。
PRも歓迎しております。不備など見つけた場合は是非お願いします。
