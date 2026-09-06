import os
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TOKEN_FILE = "token_calendar.json"

CLIENT_SECRET_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_FILE")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

if not CLIENT_SECRET_FILE:
    sys.exit("GOOGLE_OAUTH_CLIENT_FILE が設定されていません。.env を確認してください。")

# ↓ Zoom会議の情報を書き換える
SUMMARY = "テスト"
START = "2026-08-31T18:00:00"
END = "2026-08-31T19:00:00"
TIMEZONE = "Asia/Tokyo"
ZOOM_JOIN_URL = "https://us06web.zoom.us/j/87204980630?pwd=9BX6hVyvmYHeI1UaEBEQWg7Frc33ym.1"
ZOOM_MEETING_ID = "87204980630"


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def main():
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    body = {
        "summary": SUMMARY,
        "location": ZOOM_JOIN_URL,
        "description": f"Zoom ミーティング\n参加URL: {ZOOM_JOIN_URL}\nMeeting ID: {ZOOM_MEETING_ID}",
        "start": {"dateTime": START, "timeZone": TIMEZONE},
        "end": {"dateTime": END, "timeZone": TIMEZONE},
    }

    event = service.events().insert(calendarId=CALENDAR_ID, body=body).execute()
    print(f"予定を登録しました: {event.get('htmlLink')}")


if __name__ == "__main__":
    main()
