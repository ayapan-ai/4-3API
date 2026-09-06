import os
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# Meet API v2 で会議スペースを作成するためのスコープ
SCOPES = ["https://www.googleapis.com/auth/meetings.space.created"]
TOKEN_FILE = "token_meet.json"

CLIENT_SECRET_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_FILE")

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


def create_meeting(access_type: str = "TRUSTED"):
    """Meet の会議スペースを作成し、参加リンクを返す。

    access_type: OPEN / TRUSTED / RESTRICTED
    """
    creds = get_credentials()
    meet = build("meet", "v2", credentials=creds)

    space = (
        meet.spaces()
        .create(body={"config": {"accessType": access_type}})
        .execute()
    )
    return space


def main():
    space = create_meeting()
    print(f"会議コード: {space.get('meetingCode')}")
    print(f"参加リンク: {space.get('meetingUri')}")
    print(f"スペース名(API): {space.get('name')}")


if __name__ == "__main__":
    main()
