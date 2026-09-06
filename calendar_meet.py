import os
import sys
import uuid

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


def create_event_with_meet(summary, start, end, timezone="Asia/Tokyo"):
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    body = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": timezone},
        "end": {"dateTime": end, "timeZone": timezone},
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    event = (
        service.events()
        .insert(calendarId=CALENDAR_ID, body=body, conferenceDataVersion=1)
        .execute()
    )
    return event


def main():
    summary = "テスト"
    start = "2026-08-31T21:00:00"
    end = "2026-08-31T22:00:00"

    event = create_event_with_meet(summary, start, end)

    meet_link = event.get("hangoutLink")
    print(f"予定を登録しました: {event.get('htmlLink')}")
    print(f"Meet リンク: {meet_link}")


if __name__ == "__main__":
    main()
