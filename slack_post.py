import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
# 投稿先チャンネル（例: "#general" または チャンネルID "C0123456789"）
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

if not SLACK_BOT_TOKEN:
    sys.exit("SLACK_BOT_TOKEN が設定されていません。.env を確認してください。")


def post_message(channel: str, text: str):
    res = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={"channel": channel, "text": text},
    )
    res.raise_for_status()
    data = res.json()
    if not data.get("ok"):
        sys.exit(f"投稿失敗: {data.get('error')}")
    print(f"投稿完了: channel={data['channel']} ts={data['ts']}")


def main():
    channel = sys.argv[1] if len(sys.argv) > 1 else SLACK_CHANNEL
    text = sys.argv[2] if len(sys.argv) > 2 else input("メッセージ: ").strip()
    if not channel:
        sys.exit("チャンネルを指定してください（引数 または .env の SLACK_CHANNEL）。")
    post_message(channel, text)


if __name__ == "__main__":
    main()
