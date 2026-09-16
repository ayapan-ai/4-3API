from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs

import requests
from dotenv import load_dotenv
from flask import Flask, abort, request
from openai import OpenAI

from calendar_event import create_event
from calendar_freebusy import find_candidate_slots

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not LINE_CHANNEL_SECRET:
    sys.exit("LINE_CHANNEL_SECRET が設定されていません。.env を確認してください。")
if not LINE_CHANNEL_ACCESS_TOKEN:
    sys.exit("LINE_CHANNEL_ACCESS_TOKEN が設定されていません。.env を確認してください。")
if not OPENAI_API_KEY:
    sys.exit("OPENAI_API_KEY が設定されていません。.env を確認してください。")

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o-mini"
REPLY_URL = "https://api.line.me/v2/bot/message/reply"
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]
PENDING_FILE = Path(__file__).parent / "pending_events.json"

app = Flask(__name__)

SYSTEM_PROMPT = """\
あなたはLINEメッセージを解析するアシスタントです。メッセージの意図を判定し、JSONで返してください。

intent は次のいずれか:
- "register": 予定の登録依頼（例:「明日14時に歯医者」）
- "candidates": 打ち合わせなどの候補日程を提案してほしい依頼（例:「来週の打ち合わせで候補日3つ出して」）
- "other": 上記どちらでもない

register の場合:
{"intent": "register", "events": [{"summary": "予定名", "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM"}]}
- 「明日」「来週火曜」などの相対表現は基準日から絶対日付に変換する。
- 終了時刻が書かれていなければ開始の1時間後にする。
- 時刻が全く不明な場合は start="09:00", end="10:00" とする。

candidates の場合:
{"intent": "candidates", "title": "打ち合わせ", "period": "this_week" | "next_week" | "custom", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "duration_minutes": 60, "count": 3, "business_start": "HH:MM", "business_end": "HH:MM"}
- 「今週」なら period="this_week"、「来週」なら period="next_week" とする。この2つの場合、start_date/end_dateは省略してよい（自動計算されるため）。
- 具体的な日付・期間が指定された場合は period="custom" とし、start_date/end_dateに絶対日付（YYYY-MM-DD）を設定する。
- 期間の指定が全く無ければ period="next_week" とする。
- 「10時から17時まで」のように時間帯の指定があれば business_start/business_end に設定する。指定が無ければ省略する。
- 件数の指定が無ければ 3、所要時間の指定が無ければ 60 とする。

other の場合: {"intent": "other"}
"""


def analyze_message(text: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"基準日: {date.today().isoformat()}\n\nメッセージ:\n{text}"},
        ],
    )
    return json.loads(response.choices[0].message.content)


def verify_signature(body: bytes, signature: str) -> bool:
    digest = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


def reply_messages(reply_token: str, messages: list[dict]):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    body = {"replyToken": reply_token, "messages": messages[:5]}
    res = requests.post(REPLY_URL, headers=headers, json=body, timeout=10)
    res.raise_for_status()


def reply_text(reply_token: str, text: str):
    reply_messages(reply_token, [{"type": "text", "text": text}])


def load_pending() -> dict:
    if PENDING_FILE.exists():
        return json.loads(PENDING_FILE.read_text())
    return {}


def save_pending(data: dict):
    PENDING_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def format_event_line(ev: dict) -> str:
    return f"・{ev['summary']} {ev['date']} {ev['start']}〜{ev['end']}"


def register_event(ev: dict):
    create_event(
        summary=ev["summary"],
        start=f"{ev['date']}T{ev['start']}:00",
        end=f"{ev['date']}T{ev['end']}:00",
    )


def build_confirm_template(pending_id: str, ev: dict) -> dict:
    text = f"{ev['summary']}\n{ev['date']} {ev['start']}〜{ev['end']}\nカレンダーに追加しますか？"
    return {
        "type": "template",
        "altText": f"予定確認: {ev['summary']} {ev['date']} {ev['start']}〜{ev['end']}",
        "template": {
            "type": "confirm",
            "text": text[:240],
            "actions": [
                {"type": "postback", "label": "はい", "data": f"action=approve&id={pending_id}"},
                {"type": "postback", "label": "いいえ", "data": f"action=reject&id={pending_id}"},
            ],
        },
    }


def build_register_reply(events: list[dict]) -> list[dict]:
    if not events:
        return [{"type": "text", "text": "予定が読み取れませんでした。日時をもう少し具体的に教えてください。"}]

    pending = load_pending()
    messages = []
    for ev in events:
        pending_id = uuid.uuid4().hex[:8]
        pending[pending_id] = {**ev, "requested_at": datetime.now(timezone.utc).isoformat()}
        messages.append(build_confirm_template(pending_id, ev))
    save_pending(pending)
    return messages


def _next_week_range(today: date) -> tuple[date, date]:
    next_monday = today + timedelta(days=(7 - today.weekday()))
    return next_monday, next_monday + timedelta(days=4)


def _this_week_range(today: date) -> tuple[date, date]:
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    start = max(today, monday)
    if start > friday:
        return _next_week_range(today)
    return start, friday


def build_candidates_reply(data: dict) -> list[dict]:
    today = date.today()
    period = data.get("period")
    if period == "this_week":
        start_date, end_date = _this_week_range(today)
    elif period == "custom" and data.get("start_date") and data.get("end_date"):
        start_date = date.fromisoformat(data["start_date"])
        end_date = date.fromisoformat(data["end_date"])
    else:
        start_date, end_date = _next_week_range(today)

    duration = data.get("duration_minutes", 60)
    count = data.get("count", 3)
    title = data.get("title", "打ち合わせ")

    slot_kwargs = {}
    if data.get("business_start"):
        slot_kwargs["business_start"] = data["business_start"]
    if data.get("business_end"):
        slot_kwargs["business_end"] = data["business_end"]

    slots = find_candidate_slots(start_date, end_date, duration_minutes=duration, count=count, **slot_kwargs)
    if not slots:
        return [{"type": "text", "text": f"{title}の候補日が見つかりませんでした。期間を変えて試してください。"}]

    pending = load_pending()
    lines = [f"{title}の候補日程です。選んでください:"]
    quick_items = []
    for i, (s, e) in enumerate(slots, 1):
        weekday = WEEKDAY_JA[s.weekday()]
        lines.append(f"{i}. {s.month}/{s.day}({weekday}) {s.strftime('%H:%M')}〜{e.strftime('%H:%M')}")

        pending_id = uuid.uuid4().hex[:8]
        pending[pending_id] = {
            "summary": title,
            "date": s.date().isoformat(),
            "start": s.strftime("%H:%M"),
            "end": e.strftime("%H:%M"),
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        quick_items.append(
            {
                "type": "action",
                "action": {
                    "type": "postback",
                    "label": f"{i}. {s.month}/{s.day}({weekday}){s.strftime('%H:%M')}"[:20],
                    "data": f"action=select_candidate&id={pending_id}",
                    "displayText": f"{i}を選択しました",
                },
            }
        )
    save_pending(pending)

    return [
        {
            "type": "text",
            "text": "\n".join(lines),
            "quickReply": {"items": quick_items[:13]},
        }
    ]


def handle_postback(event: dict):
    reply_token = event.get("replyToken")
    parsed = parse_qs(event.get("postback", {}).get("data", ""))
    action = parsed.get("action", [None])[0]
    pending_id = parsed.get("id", [None])[0]

    pending = load_pending()
    ev = pending.pop(pending_id, None) if pending_id else None
    save_pending(pending)

    if ev is None:
        reply_text_value = "対象の予定が見つかりません（既に処理済みの可能性があります）。"
    elif action in ("approve", "select_candidate"):
        register_event(ev)
        reply_text_value = "予定を登録しました:\n" + format_event_line(ev)
    elif action == "reject":
        reply_text_value = "登録しませんでした:\n" + format_event_line(ev)
    else:
        reply_text_value = "不明な操作です。"

    if reply_token:
        try:
            reply_text(reply_token, reply_text_value)
        except Exception as exc:
            print(f"postback応答エラー: {exc}")


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()

    if not verify_signature(body, signature):
        abort(400)

    payload = request.get_json()
    for event in payload.get("events", []):
        if event.get("type") == "postback":
            handle_postback(event)
            continue

        if event.get("type") != "message" or event["message"].get("type") != "text":
            continue

        text = event["message"]["text"]
        reply_token = event["replyToken"]

        try:
            data = analyze_message(text)
            intent = data.get("intent")
            if intent == "register":
                messages = build_register_reply(data.get("events", []))
            elif intent == "candidates":
                messages = build_candidates_reply(data)
            else:
                messages = [
                    {
                        "type": "text",
                        "text": "予定登録（例:「明日14時に歯医者」）か、候補日提案（例:「来週の打ち合わせで候補日3つ出して」）を送ってください。",
                    }
                ]
        except Exception as exc:
            print(f"処理エラー: {exc}")
            messages = [{"type": "text", "text": "処理中にエラーが発生しました。もう一度お試しください。"}]

        reply_messages(reply_token, messages)

    return "OK"


def main():
    app.run(port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()
