import os
import sys

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "シート1")

if not SERVICE_ACCOUNT_FILE:
    sys.exit("GOOGLE_SERVICE_ACCOUNT_FILE が設定されていません。.env を確認してください。")
if not SPREADSHEET_ID:
    sys.exit("GOOGLE_SPREADSHEET_ID が設定されていません。.env を確認してください。")


def get_worksheet():
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)


def append_row(values: list):
    worksheet = get_worksheet()
    worksheet.append_row(values)


def append_rows(rows: list[list]):
    worksheet = get_worksheet()
    worksheet.append_rows(rows)


def write_range(cell_range: str, values: list[list]):
    worksheet = get_worksheet()
    worksheet.update(range_name=cell_range, values=values)


def main():
    write_range("A1:C3", [
        ["日付", "項目", "数値"],
        ["2026-07-22", "サンプルデータ", 123],
        ["2026-09-22", "サンプルデータ", 123],
   
   
    ])
    print("スプレッドシートにデータを送信しました。")


if __name__ == "__main__":
    main()
