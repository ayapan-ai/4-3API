import json
import os
import sys
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI

from calendar_event import create_event

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    sys.exit("OPENAI_API_KEY が設定されていません。.env を確認してください。")

client = OpenAI(api_key=api_key)

MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """\
あなたはLINEの会話文からカレンダー予定を抽出するアシスタントです。
本文に含まれるすべての予定を JSON で返してください。形式:
{"events": [
  {"summary": "予定名", "date": "YYYY-MM-DD", "start": "HH:MM", "end": "HH:MM"}
]}
ルール:
- 「明日」「来週火曜」などの相対表現は基準日から絶対日付に変換する。
- 終了時刻が書かれていない場合は開始の1時間後にする。
- 時刻が全く不明な場合は start="09:00", end="10:00" とする。
- 予定が無ければ {"events": []} を返す。
"""


def parse_events(text: str) -> list[dict]:
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"基準日: {date.today().isoformat()}\n\n本文:\n{text}"},
        ],
    )
    return json.loads(response.choices[0].message.content).get("events", [])


def read_input() -> str:
    args = [a for a in sys.argv[1:] if a != "-y"]
    if args:
        with open(args[0], encoding="utf-8") as f:
            return f.read()
    print("LINEの文章を貼り付けてください（入力し終えたら Ctrl-D）:")
    return sys.stdin.read()


def main():
    text = read_input()
    if not text.strip():
        sys.exit("本文が空です。")

    events = parse_events(text)
    if not events:
        sys.exit("予定が見つかりませんでした。")

    print("\n以下の予定を登録します:")
    for i, ev in enumerate(events, 1):
        print(f"  {i}. {ev['summary']}  {ev['date']} {ev['start']}-{ev['end']}")

    if "-y" not in sys.argv and input("\n登録しますか？ (y/n): ").strip().lower() != "y":
        sys.exit("中止しました。")

    for ev in events:
        created = create_event(
            summary=ev["summary"],
            start=f"{ev['date']}T{ev['start']}:00",
            end=f"{ev['date']}T{ev['end']}:00",
        )
        print(f"登録しました: {ev['summary']} -> {created.get('htmlLink')}")


if __name__ == "__main__":
    main()
