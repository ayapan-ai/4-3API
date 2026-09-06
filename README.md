# 4-3AIP 連携課題

各種 API（OpenAI / Google Workspace / YouTube / Slack / Zoom）を Python から呼び出す連携スクリプト集。

## セットアップ

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 各種キーを記入
```

認証ファイル（`.env`, `service_account.json`, `client_secret.json`, `token*.json`）は
`.gitignore` で除外しており、リポジトリには含まれません。各自で用意してください。

## スクリプト一覧

| ファイル | 内容 |
|---|---|
| `chat.py` | OpenAI Chat API 呼び出し |
| `sheets.py` | Google スプレッドシート読み書き |
| `docs_create.py` | Google ドキュメント作成 |
| `drive_upload.py` | Google ドライブへアップロード |
| `calendar_event.py` / `calendar_meet.py` | Google カレンダー予定作成 |
| `meet_create.py` | Google Meet リンク発行 |
| `send_gmail.py` | Gmail 送信 |
| `create_zoom_meeting.py` | Zoom ミーティング作成 |
| `zoom_to_calendar.py` | Zoom ミーティングをカレンダーに登録 |
| `line_to_calendar.py` | LINE メッセージからカレンダー登録 |
| `slack_post.py` | Slack へ投稿 |
| `youtube_search.py` | YouTube 動画検索 |

## 必要な環境変数

`.env.example` を参照。
