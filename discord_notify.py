from __future__ import annotations

import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

# 通知先チャンネルの Webhook URL
# （Discord: チャンネルの編集 → 連携サービス → ウェブフックを作成 → URL をコピー）
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# 表示名・アイコンを上書きしたい場合（任意）
DISCORD_USERNAME = os.getenv("DISCORD_USERNAME")
DISCORD_AVATAR_URL = os.getenv("DISCORD_AVATAR_URL")

if not DISCORD_WEBHOOK_URL:
    sys.exit("DISCORD_WEBHOOK_URL が設定されていません。.env を確認してください。")


def send_notification(content: str, *, title: str | None = None, color: int = 0x5865F2):
    """Webhook で通知を送る。title を渡すと embed 付きで送信する。"""
    payload: dict = {}
    if DISCORD_USERNAME:
        payload["username"] = DISCORD_USERNAME
    if DISCORD_AVATAR_URL:
        payload["avatar_url"] = DISCORD_AVATAR_URL

    if title:
        payload["embeds"] = [{"title": title, "description": content, "color": color}]
    else:
        payload["content"] = content

    for attempt in range(5):
        res = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json=payload, timeout=10)

        # レート制限。retry_after 秒待って再送
        if res.status_code == 429:
            retry_after = res.json().get("retry_after", 1)
            print(f"レート制限中。{retry_after}s 待機して再送します…")
            time.sleep(float(retry_after))
            continue

        res.raise_for_status()
        data = res.json()
        print(f"送信完了: message_id={data.get('id')} channel_id={data.get('channel_id')}")
        return

    sys.exit("レート制限が解消されず、送信できませんでした。")


def main():
    title = None
    if len(sys.argv) > 2:
        title, content = sys.argv[1], sys.argv[2]
    elif len(sys.argv) > 1:
        content = sys.argv[1]
    else:
        content = input("メッセージ: ").strip()

    if not content:
        sys.exit("メッセージが空です。")
    send_notification(content, title=title)


if __name__ == "__main__":
    main()
