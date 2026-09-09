import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

# 「Messaging API設定」タブで発行する長期のチャネルアクセストークン
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# 送信先の userId（自分宛テストは「チャネル基本設定」タブの Your user ID）
LINE_TO = os.getenv("LINE_TO")

if not LINE_CHANNEL_ACCESS_TOKEN:
    sys.exit("LINE_CHANNEL_ACCESS_TOKEN が設定されていません。.env を確認してください。")


def push_message(to: str, text: str):
    res = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"},
        json={"to": to, "messages": [{"type": "text", "text": text}]},
        timeout=10,
    )
    if res.status_code != 200:
        sys.exit(f"送信失敗: {res.status_code} {res.text}")
    print(f"送信完了: to={to}")


def main():
    to = sys.argv[1] if len(sys.argv) > 2 else LINE_TO
    text = sys.argv[2] if len(sys.argv) > 2 else (
        sys.argv[1] if len(sys.argv) > 1 else input("メッセージ: ").strip()
    )
    if not to:
        sys.exit("送信先を指定してください（引数 または .env の LINE_TO）。")
    if not text:
        sys.exit("メッセージが空です。")
    push_message(to, text)


if __name__ == "__main__":
    main()
