import os
import requests
from dotenv import load_dotenv

load_dotenv()  # .env を読み込む

# Server-to-Server OAuth の認証情報（Zoom App Marketplace で作成）
ACCOUNT_ID = os.environ["ZOOM_ACCOUNT_ID"]
CLIENT_ID = os.environ["ZOOM_CLIENT_ID"]
CLIENT_SECRET = os.environ["ZOOM_CLIENT_SECRET"]


def get_access_token():
    res = requests.post(
        "https://zoom.us/oauth/token",
        params={"grant_type": "account_credentials", "account_id": ACCOUNT_ID},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    res.raise_for_status()
    return res.json()["access_token"]


ACCESS_TOKEN = get_access_token()

# ↓ここを書き換える
TOPIC = "テスト"
START_TIME = "2026-08-31T18:00:00"  # timezoneに対するローカル時刻
DURATION = 60  # 分
TIMEZONE = "Asia/Tokyo"

url = "https://api.zoom.us/v2/users/me/meetings"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}
payload = {
    "topic": TOPIC,
    "type": 2,  # 2=予約制, 1=今すぐ開始
    "start_time": START_TIME,
    "duration": DURATION,
    "timezone": TIMEZONE,
}

res = requests.post(url, headers=headers, json=payload)
res.raise_for_status()
data = res.json()

print("Meeting ID:", data["id"])
print("Join URL:", data["join_url"])
