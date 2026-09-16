from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from calendar_event import CALENDAR_ID, get_service
from line_push import push_message

load_dotenv()

REMINDER_MINUTES_BEFORE = int(os.getenv("REMINDER_MINUTES_BEFORE", "60"))
STATE_FILE = Path(__file__).parent / "reminded_events.json"


def load_notified() -> dict[str, str]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_notified(data: dict[str, str]):
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def prune(data: dict[str, str]) -> dict[str, str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    return {eid: ts for eid, ts in data.items() if datetime.fromisoformat(ts) > cutoff}


def get_upcoming_events(window_minutes: int) -> list[dict]:
    service = get_service()
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(minutes=window_minutes)
    result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=now.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])


def main():
    notified = prune(load_notified())
    events = get_upcoming_events(REMINDER_MINUTES_BEFORE)

    for ev in events:
        event_id = ev["id"]
        if event_id in notified:
            continue

        start = ev["start"].get("dateTime", ev["start"].get("date"))
        summary = ev.get("summary", "(タイトルなし)")
        push_message(f"【リマインド】{summary}\n{start}")
        print(f"リマインド送信: {summary}")
        notified[event_id] = datetime.now(timezone.utc).isoformat()

    save_notified(notified)


if __name__ == "__main__":
    main()
