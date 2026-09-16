from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from calendar_event import CALENDAR_ID, get_service

BUSINESS_START = os.getenv("CANDIDATE_BUSINESS_START", "10:00")
BUSINESS_END = os.getenv("CANDIDATE_BUSINESS_END", "18:00")


def _parse_hm(value: str) -> tuple[int, int]:
    h, m = value.split(":")
    return int(h), int(m)


def _at_time(day: date, hm: str) -> datetime:
    h, m = _parse_hm(hm)
    return datetime.combine(day, datetime.min.time().replace(hour=h, minute=m))


def get_busy_periods_and_blocked_dates(
    time_min: str, time_max: str
) -> tuple[list[tuple[datetime, datetime]], set[date]]:
    """busyな時間帯と、終日予定がある日（終日は必ずブロック扱い）を取得する。

    Googleカレンダーの終日予定は既定でtransparency="transparent"（空き扱い）になり、
    freebusy APIでは無視されてしまうため、events.listで直接取得して判定する。
    """
    service = get_service()
    result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    busy: list[tuple[datetime, datetime]] = []
    blocked_dates: set[date] = set()

    for ev in result.get("items", []):
        start = ev.get("start", {})
        end = ev.get("end", {})

        if "date" in start:
            day = date.fromisoformat(start["date"])
            end_day = date.fromisoformat(end["date"])
            while day < end_day:
                blocked_dates.add(day)
                day += timedelta(days=1)
            continue

        if ev.get("transparency") == "transparent":
            continue

        busy.append(
            (
                datetime.fromisoformat(start["dateTime"]).replace(tzinfo=None),
                datetime.fromisoformat(end["dateTime"]).replace(tzinfo=None),
            )
        )

    return busy, blocked_dates


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _round_up_to_30min(value: datetime) -> datetime:
    base = value.replace(second=0, microsecond=0)
    remainder = base.minute % 30
    if remainder == 0 and value == base:
        return base
    return base + timedelta(minutes=30 - remainder)


def find_candidate_slots(
    start_date: date,
    end_date: date,
    duration_minutes: int = 60,
    count: int = 3,
    exclude_weekends: bool = True,
    business_start: str = BUSINESS_START,
    business_end: str = BUSINESS_END,
) -> list[tuple[datetime, datetime]]:
    """指定期間の営業時間内から、空いている候補枠を探す（1日に複数枠可）。"""
    time_min = _at_time(start_date, business_start).isoformat() + "+09:00"
    time_max = _at_time(end_date, business_end).isoformat() + "+09:00"
    busy, blocked_dates = get_busy_periods_and_blocked_dates(time_min, time_max)

    now = datetime.now()
    duration = timedelta(minutes=duration_minutes)
    candidates: list[tuple[datetime, datetime]] = []
    day = start_date
    while day <= end_date and len(candidates) < count:
        if exclude_weekends and day.weekday() >= 5:
            day += timedelta(days=1)
            continue
        if day in blocked_dates:
            day += timedelta(days=1)
            continue

        slot_start = _at_time(day, business_start)
        day_end = _at_time(day, business_end)
        if day == now.date():
            slot_start = max(slot_start, _round_up_to_30min(now))

        while slot_start + duration <= day_end and len(candidates) < count:
            slot_end = slot_start + duration
            if not any(_overlaps(slot_start, slot_end, b_s, b_e) for b_s, b_e in busy):
                candidates.append((slot_start, slot_end))
                slot_start = slot_end
            else:
                slot_start += timedelta(minutes=30)

        day += timedelta(days=1)

    return candidates
