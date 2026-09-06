import os
import sys

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

if not SERVICE_ACCOUNT_FILE:
    sys.exit("GOOGLE_SERVICE_ACCOUNT_FILE が設定されていません。.env を確認してください。")
if not CALENDAR_ID:
    sys.exit("GOOGLE_CALENDAR_ID が設定されていません。.env を確認してください。")


def get_service():
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("calendar", "v3", credentials=credentials)


def create_event(summary: str, start: str, end: str, timezone: str = "Asia/Tokyo"):
    service = get_service()
    event = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": timezone},
        "end": {"dateTime": end, "timeZone": timezone},
    }
    return service.events().insert(calendarId=CALENDAR_ID, body=event).execute()


def main():
    while True:
        summary = input("予定のタイトル: ")
        date = input("日付 (例: 2026-08-25): ")
        start_time = input("開始時刻 (例: 10:00): ")
        end_time = input("終了時刻 (例: 11:00): ")

        event = create_event(
            summary=summary,
            start=f"{date}T{start_time}:00",
            end=f"{date}T{end_time}:00",
        )
        print(f"予定を登録しました: {event.get('htmlLink')}")

        if input("続けて登録しますか？ (y/n): ").strip().lower() != "y":
            break


if __name__ == "__main__":
    main()