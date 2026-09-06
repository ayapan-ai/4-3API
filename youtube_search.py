import os
import requests
from dotenv import load_dotenv

load_dotenv()  # .env を読み込む

# Google Cloud で発行した YouTube Data API v3 の API キー
API_KEY = os.environ["YOUTUBE_API_KEY"]

MAX_RESULTS = 10  # 取得件数（1〜50）


def search(query):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": API_KEY,
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": MAX_RESULTS,
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    items = res.json().get("items", [])

    print(f'\n検索キーワード: "{query}"  ({len(items)} 件)')
    print("=" * 60)
    for i, item in enumerate(items, 1):
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"\n{i:2}. {title}")
        print(f"    {video_url}")
    print("=" * 60 + "\n")


def main():
    print("YouTube 検索。検索語を入力してください（何も入力せず Enter で終了）")
    while True:
        try:
            query = input("検索語> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            break
        try:
            search(query)
        except requests.HTTPError as e:
            print(f"エラー: {e}\n")


if __name__ == "__main__":
    main()
