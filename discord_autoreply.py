from __future__ import annotations

import os
import sys

import discord
from dotenv import load_dotenv

load_dotenv()

# Bot のトークン
# （Discord Developer Portal → アプリ作成 → Bot → Reset Token でコピー）
# ※ Bot タブで「MESSAGE CONTENT INTENT」を ON にしておくこと
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 反応するワードと返信内容（.env で上書き可）
TRIGGER_WORD = os.getenv("DISCORD_TRIGGER_WORD", "資料")
REPLY_TEXT = os.getenv("DISCORD_REPLY_TEXT", "ありがとうございます")

if not DISCORD_BOT_TOKEN:
    sys.exit("DISCORD_BOT_TOKEN が設定されていません。.env を確認してください。")


intents = discord.Intents.default()
intents.message_content = True  # メッセージ本文を読むのに必須
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"ログイン完了: {client.user}  監視ワード='{TRIGGER_WORD}'")


@client.event
async def on_message(message: discord.Message):
    # Bot 自身（および他の Bot）の発言には反応しない → 無限ループ防止
    if message.author.bot:
        return

    if TRIGGER_WORD in message.content:
        await message.reply(REPLY_TEXT)
        print(f"返信しました: #{message.channel} / {message.author}")


def main():
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
