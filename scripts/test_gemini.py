"""Gemini API 연결 테스트 - 최신 모델"""
import os
from dotenv import load_dotenv
load_dotenv(r"c:\Users\minsoo\Desktop\capstone\backend\.env")

from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

test_models = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]

for model_name in test_models:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="배추 가격 10% 상승 시 한 문장 조언",
        )
        print(f"[OK] Model '{model_name}' works!")
        print(response.text[:200])
        break
    except Exception as e:
        print(f"[FAIL] '{model_name}': {str(e)[:120]}")
