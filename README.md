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
| `line_to_calendar.py` | LINE メッセージ（貼り付け）からカレンダー登録 |
| `line_push.py` | LINE Messaging API でメッセージ送信 |
| `line_webhook.py` | LINE Webhook。予定登録・候補日提案を自動応答 |
| `calendar_freebusy.py` | カレンダーの空き状況から候補日程を算出 |
| `line_reminder.py` | 直前リマインドをLINEへプッシュ通知（cron等で定期実行） |
| `slack_post.py` | Slack へ投稿 |
| `discord_notify.py` | Discord チャンネルへ Webhook 通知 |
| `youtube_search.py` | YouTube 動画検索 |

## 必要な環境変数

`.env.example` を参照。

## LINE連携（スケジュール・タスク自動管理）

LINEに「明日14時に歯医者」のように送ると、送信者へ「登録しますか？」と
はい/いいえボタン付きで確認が返り、「はい」を押すとGoogleカレンダーに登録されます。

「来週の打ち合わせで候補日3つ出して」「今週10時から17時までで候補日を出して」のように送ると、
カレンダーの空き状況（終日予定・通常の予定を考慮）から候補日程をQuick Replyボタン付きで提案し、
候補をタップするとその枠がそのまま登録されます。
確認待ち・候補提示中の内容は `pending_events.json` に保存されます（`.gitignore`済み）。

### セットアップ

1. [LINE Developers](https://developers.line.biz/) で Messaging API チャネルを作成
   - 基本設定タブ: `LINE_CHANNEL_SECRET`
   - Messaging API設定タブ: 長期チャネルアクセストークンを発行 → `LINE_CHANNEL_ACCESS_TOKEN`
   - 応答メッセージ・あいさつメッセージはOFF、Webhookの利用はONにする
2. Googleカレンダー側で、`GOOGLE_SERVICE_ACCOUNT_FILE` のサービスアカウントのメールアドレスに
   対象カレンダー（`GOOGLE_CALENDAR_ID`）の編集権限を共有しておく
3. `.env` に上記と `OPENAI_API_KEY` を設定
4. Webhookサーバーを起動

   ```bash
   python line_webhook.py   # デフォルト http://localhost:8000/webhook
   ```

5. ローカルで試す場合は ngrok などでトンネルを張り、発行されたURL（例:
   `https://xxxx.ngrok.io/webhook`）を LINE Developers の Webhook URL に設定する
6. リマインドは cron 等で `line_reminder.py` を定期実行する（例: 10分おき）

   ```cron
   */10 * * * * cd /path/to/4-3AIP連携課題 && ./venv/bin/python line_reminder.py
   ```

   `REMINDER_MINUTES_BEFORE`（デフォルト60分）以内に開始する予定を検知し、
   通知済みイベントは `reminded_events.json` に記録して二重送信を防ぐ。
