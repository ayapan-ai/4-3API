import os
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]
TOKEN_FILE = "token_docs.json"

CLIENT_SECRET_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_FILE")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

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


def create_document(title: str, text: str):
    creds = get_credentials()
    docs = build("docs", "v1", credentials=creds)

    # 新しいドキュメントを作成
    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    # 先頭にテキストを挿入
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": text,
                    }
                }
            ]
        },
    ).execute()

    # 指定フォルダへ移動（任意）
    if DRIVE_FOLDER_ID:
        drive = build("drive", "v3", credentials=creds)
        drive.files().update(
            fileId=doc_id,
            addParents=DRIVE_FOLDER_ID,
            fields="id, parents",
        ).execute()

    return doc_id, f"https://docs.google.com/document/d/{doc_id}/edit"


def main():
    title = input("ドキュメントのタイトル: ").strip()
    print("挿入するテキストを入力してください（終了は Ctrl-D）:")
    text = sys.stdin.read()

    _, url = create_document(title, text)
    print(f"作成しました: {url}")


if __name__ == "__main__":
    main()
