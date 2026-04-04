"""API 엔드포인트 통합 테스트"""
import urllib.request
import json

BASE = "http://localhost:8000"

def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

print("=== 1. Root ===")
data = get("/")
print(json.dumps(data, ensure_ascii=False, indent=2))

print("\n=== 2. Today Price ===")
data = get("/api/price/today")
print(json.dumps(data, ensure_ascii=False, indent=2))

print("\n=== 3. Price History (14일) ===")
data = get("/api/price/history?days=14")
count = data.get("count", 0)
first = data.get("data", [{}])[0] if data.get("data") else {}
last = data.get("data", [{}])[-1] if data.get("data") else {}
print(f"데이터 수: {count}일")
print(f"첫 날: {first.get('date')} - {first.get('price'):,}원")
print(f"마지막: {last.get('date')} - {last.get('price'):,}원")

print("\n=== 4. Prediction (30일 기반 14일 예측) ===")
print("Chronos 모델 로딩 중... (최초 실행시 30-60초 소요)")
import urllib.request, urllib.error
try:
    with urllib.request.urlopen(BASE + "/api/predict?history_days=30", timeout=120) as r:
        data = json.loads(r.read())
    print(f"모델: {data['model']}")
    print(f"현재가: {data['summary']['current_price']:,.0f}원")
    print(f"14일 예측: {data['summary']['predicted_price_14d']:,.0f}원")
    print(f"변화율: {data['summary']['change_rate_pct']:+.1f}%")
    print(f"방향: {data['summary']['direction']}")
    print(f"\n--- Gemini 설명 (모델: {data['explanation_model']}) ---")
    print(data['explanation'][:500])
    print(f"\n첫 3일 예측:")
    for p in data['predictions'][:3]:
        print(f"  {p['date']}: {p['price']:,.0f}원 (하한:{p['lower']:,.0f} ~ 상한:{p['upper']:,.0f})")
except Exception as e:
    print(f"[ERROR] {e}")
