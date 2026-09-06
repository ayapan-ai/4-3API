import os
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = "token.json"

CLIENT_SECRET_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_FILE")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

if not CLIENT_SECRET_FILE:
    sys.exit("GOOGLE_OAUTH_CLIENT_FILE が設定されていません。.env を確認してください。")
if not DRIVE_FOLDER_ID:
    sys.exit("GOOGLE_DRIVE_FOLDER_ID が設定されていません。.env を確認してください。")


def get_service():
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
    return build("drive", "v3", credentials=creds)


def upload_file(file_path: str):
    service = get_service()
    metadata = {
        "name": os.path.basename(file_path),
        "parents": [DRIVE_FOLDER_ID],
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=metadata, media_body=media, fields="id, webViewLink").execute()
    return file


def main():
    file_path = input("アップロードするファイルのパス: ").strip()
    file = upload_file(file_path)
    print(f"アップロードしました: {file.get('webViewLink')}")


if __name__ == "__main__":
    main()
