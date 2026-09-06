import base64
import os
import sys
from email.message import EmailMessage

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "token_gmail.json"

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


def send_mail(to_addr: str, subject: str, body: str):
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    msg = EmailMessage()
    msg["To"] = to_addr
    msg["From"] = "me"
    msg["Subject"] = subject
    msg.set_content(body)

    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(
        userId="me", body={"raw": encoded}
    ).execute()
    print(f"送信完了: id={sent['id']}")


def main():
    to_addr = sys.argv[1] if len(sys.argv) > 1 else input("宛先: ").strip()
    subject = sys.argv[2] if len(sys.argv) > 2 else input("件名: ").strip()
    body = sys.argv[3] if len(sys.argv) > 3 else input("本文: ").strip()
    send_mail(to_addr, subject, body)


if __name__ == "__main__":
    main()
