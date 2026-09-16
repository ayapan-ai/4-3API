from __future__ import annotations

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TO = os.getenv("LINE_TO")
PUSH_URL = "https://api.line.me/v2/bot/message/push"

if not LINE_CHANNEL_ACCESS_TOKEN:
    sys.exit("LINE_CHANNEL_ACCESS_TOKEN が設定されていません。.env を確認してください。")


def push_messages(messages: list[dict], to: str | None = None):
    """LINE Messaging API でメッセージ（最大5件）を送信する。to省略時は LINE_TO 宛。"""
    to = to or LINE_TO
    if not to:
        sys.exit("送信先が指定されていません。LINE_TO を設定するか to を渡してください。")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    body = {"to": to, "messages": messages}
    res = requests.post(PUSH_URL, headers=headers, json=body, timeout=10)
    res.raise_for_status()


def push_message(text: str, to: str | None = None):
    """LINE Messaging API でテキストメッセージを送信する。to省略時は LINE_TO 宛。"""
    push_messages([{"type": "text", "text": text}], to=to)


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else input("メッセージ: ").strip()
    if not text:
        sys.exit("メッセージが空です。")
    push_message(text)
    print("送信しました。")


if __name__ == "__main__":
    main()
