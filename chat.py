import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    sys.exit("OPENAI_API_KEY が設定されていません。.env を確認してください。")

client = OpenAI(api_key=api_key)

MODEL = "gpt-4o-mini"

messages = [
    {"role": "system", "content": "あなたは親切なアシスタントです。"},
]


def ask(user_input: str) -> str:
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply


def main():
    print("ChatGPTとの対話を開始します。終了するには 'exit' と入力してください。")
    while True:
        user_input = input("あなた: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        reply = ask(user_input)
        print(f"ChatGPT: {reply}")


if __name__ == "__main__":
    main()
