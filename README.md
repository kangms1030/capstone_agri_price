# Agri-Insight: 배추 도매가격 예측 시스템

> **TSFM (Chronos) + LLM (Gemini)** 기반 농산물 가격 예측 프로토타입

## 🏗️ 프로젝트 구조

```
capstone/
├── backend/                   # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py            # FastAPI 진입점
│   │   ├── api/
│   │   │   ├── price.py       # 가격 조회 API
│   │   │   └── predict.py     # 예측 API (Chronos + Gemini)
│   │   ├── services/
│   │   │   ├── kamis.py       # KAMIS API 클라이언트
│   │   │   ├── predictor.py   # Chronos 예측 서비스
│   │   │   └── explainer.py   # Gemini 설명 서비스
│   │   └── models/
│   │       └── schemas.py     # Pydantic 스키마
│   ├── .env                   # 환경 변수 (API 키)
│   └── requirements.txt
├── frontend/                  # Next.js 프론트엔드
│   └── src/
│       ├── app/               # Next.js App Router
│       ├── components/        # React 컴포넌트
│       ├── lib/               # API 클라이언트
│       └── types/             # TypeScript 타입
└── README.md
```

## 🚀 실행 방법

### 1. 백엔드 실행

```bash
# capstone 환경에서
conda activate capstone
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

### 2. 프론트엔드 실행

```bash
cd frontend
npm run dev
```

대시보드: http://localhost:3000

## 🔑 API 키 설정

`backend/.env` 파일 수정:

```env
# KAMIS API (발급 후 입력)
KAMIS_API_KEY=your_key_here
KAMIS_API_ID=your_id_here

# Gemini API
GEMINI_API_KEY=your_gemini_key

# Mock 모드 (KAMIS 키 발급 전 테스트)
USE_MOCK_DATA=true
```

## 📡 주요 API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/price/today` | 오늘 배추 도매가격 |
| `GET /api/price/history?days=90` | 최근 N일 가격 이력 |
| `GET /api/predict?history_days=90` | Chronos 14일 예측 + Gemini 설명 |
| `GET /health` | 서버 상태 및 GPU 정보 |

## 🤖 사용 모델

- **가격 예측**: `amazon/chronos-t5-base` (HuggingFace)
  - Zero-shot time-series forecasting
  - GPU 가속 지원 (CUDA)
- **자연어 설명**: `gemini-2.0-flash` (Google AI)
  - 예측 결과를 한국어로 설명

## 📊 데이터 소스 (로컬 데이터 기반)

- **배추 도매가격**: `data/agri_price/cabbage.xlsx` (2015-01-01 ~ 2025-12-31, 특/상/중/하 등급별)
- **기상 데이터**: `data/weather_data_2015_2025.csv` (주산지 기온 및 강수량)
- **유가 데이터**: `data/국내_원유_면세유가격.csv` (농업용 면세유 가격 추이)

*기존 방식의 KAMIS API 실시간 연동 대신 로컬 데이터를 병합하여 Chronos 예측 및 Gemini 분석 프롬프트에 활용합니다.*

## ⚠️ 주의사항

- Chronos 모델 최초 실행 시 HuggingFace에서 모델 다운로드 (약 800MB)
- `gemini-2.5-flash` 모델을 사용하여 기후 및 유가 변화 요인을 종합적인 분석 리포트로 제공합니다.
- 데이터 경로 변경 시 `kamis.py` 데이터 로딩 구조를 업데이트해야 합니다.
