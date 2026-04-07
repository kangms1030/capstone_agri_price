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

**공통:** Python 작업 전에 Conda 환경을 켭니다.

```text
conda activate capstone
```

### 1. 백엔드 실행

프로젝트 **루트** 폴더(`capstone`)에서 `run_backend.py`를 실행합니다. `backend/.env`의 `HOST`, `PORT`를 읽습니다(기본: `0.0.0.0`, `8000`).

**명령 프롬프트(cmd) 또는 Anaconda Prompt:**

```cmd
cd 경로\capstone
conda activate capstone
python run_backend.py
```

**PowerShell** (`&&`가 안 될 수 있으면 한 줄씩 실행하거나 아래처럼 `;` 사용):

```powershell
cd C:\경로\capstone
conda activate capstone
python run_backend.py
```

시작 시 터미널에 `http://127.0.0.1:포트/docs` 주소가 출력됩니다.

- API 문서(기본 포트): http://localhost:8000/docs  
- **포트 충돌**(이미 8000 사용 중): `backend/.env`에서 `PORT=8001` 등으로 바꾸거나, 일회성으로  
  PowerShell: `$env:PORT=8001; python run_backend.py`  
  cmd: `set PORT=8001` 후 같은 창에서 `python run_backend.py`

### 2. 프론트엔드 실행

백엔드가 떠 있는 상태에서 **다른 터미널**에서:

```text
cd frontend
npm install
npm run dev
```

대시보드: http://localhost:3000  

백엔드 포트를 `8000`이 아닌 값으로 켠 경우, `frontend` 폴더에 `.env.local`을 만들고 예시처럼 맞춥니다(`frontend/.env.local.example` 참고).

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

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
- **자연어 설명**: `gemini-2.5-flash` (Google AI)
  - 예측 결과를 한국어로 설명

## 📊 데이터 소스 (로컬 데이터 기반)

실제 파일 위치는 **`backend/data/`** 아래입니다.

- **배추 도매가격**: `backend/data/agri_price/cabbage.xlsx` (등급별 시계열)
- **기상 데이터**: `backend/data/weather_data_2015_2025.csv`
- **유가 데이터**: `backend/data/` 아래 파일명에 `면세유`가 포함된 CSV (코드가 자동 탐색)

*기존 방식의 KAMIS API 실시간 연동 대신 로컬 데이터를 병합하여 Chronos 예측 및 Gemini 분석 프롬프트에 활용합니다.*

## 📊 Chronos-2 전용 전처리 데이터셋 (v2)

`data/final_dataset/chronos2_preprocessed_v2.csv`는 Chronos-2 모델의 학습 및 추론 성능을 극대화하기 위해 설계된 최신 데이터셋입니다. 모든 수치형 데이터는 표준화(z-score) 되거나 Arcsinh 변환이 적용되었으며, 미래 시점에서도 알 수 있는 'Future-Known' 공변량과 과거 정보 기반의 'Past-Only' 공변량이 구분되어 포함되어 있습니다.

### 📝 데이터 컬럼 사전

#### 1. 기본 정보 및 타겟 (Target)
| 컬럼명 | 설명 | 비고 |
| :--- | :--- | :--- |
| `date` | 일자 | YYYY-MM-DD |
| `item_id` | 품목 ID | 작물명 및 등급 정보 |
| `price` | 원본 가격 | 실제 KRW 가격 |
| `target` | 변환된 가격 | 모델 학습용 Arcsinh 변환된 타겟값 |

#### 2. Future-Known Covariates (미래 시점에도 알 수 있는 정보)
| 컬럼명 | 한국어 의미 | 설명 |
| :--- | :--- | :--- |
| `month`, `month_sin`, `month_cos` | 월 계절성 | 월 정보를 순환 피처(Sine/Cosine)로 변환 |
| `dayofweek`, `dow_sin`, `dow_cos` | 요일 정보 | 요일 정보를 순환 피처로 변환 |
| `weekofyear` | 연간 주차 | 1~53주 중 해당 주차 |
| `temp_avg`, `temp_diff` | 평균 기온, 일교차 | 당일 기상 관측 정보 |
| `rain_sum`, `humid_avg` | 강수량, 평균 습도 | 당일 기상 관측 정보 |
| `sunshine_sum` | 일조 시간 | 당일 기상 관측 정보 |
| `weather_index` | 종합 기상 지수 | 기온/습도 등을 결합한 파생 지수 |
| `rain_impact` | 강수 영향도 | 강수량 기반 파병 영향도 지수 |

#### 3. Past-Only Covariates (과거 시점의 정보)
| 컬럼명 | 한국어 의미 | 설명 |
| :--- | :--- | :--- |
| `oil_diesel`, `oil_diesel_lag_*` | 경유 가격 및 지연값 | 면세유(경유) 가격 및 1, 3일 전 값 |
| `cpi_total` | 소비자물가지수 | 거시 경제 지표 |
| `gov_bond_3y` | 국고채 3년물 금리 | 금리 및 시장 유동성 지표 |
| `epu` | 경제불확실성지수 | 뉴스 기반 정책 불확실성 지수 |
| `m2_sa` | 광의통화(계절조정) | 시장 통화량 지표 |
| `price_lag_*` | 가격 지연값 | 1, 3, 7, 14, 28일 전의 가격 정보 |
| `price_ma7` | 7일 이동평균 가격 | 가격 추세 정보 |
| `temp_rolling_mean_7` | 기온 이동평균 | 최근 7일간의 기온 추세 |
| `temp_avg_lag_1`, `rain_sum_lag_1` | 기상 지연값 | 전일 기상 정보 |

## ⚠️ 주의사항

- **서버 종료 및 메모리 관리 주의 (해결법):** 
  터미널에서 프론트엔드(`npm run dev`)나 백엔드 서버를 종료할 때 터미널 창의 **`X` 버튼을 눌러 강제로 닫지 마세요.** 반드시 터미널 안에서 **`Ctrl + C`**를 눌러 프로세스를 정상 종료한 뒤 창을 닫아야 합니다.
  비정상 종료 시 백그라운드에 `node.exe` 프로세스들이 쌓여 **메모리(RAM)를 90% 이상 점유하는 심각한 문제**가 발생할 수 있습니다. 
  만약 이미 메모리가 가득 찼다면, 관리자 권한 명령 프롬프트(cmd)에서 `taskkill /F /IM node.exe`를 입력해 좀비 프로세스들을 일괄 정리하세요.
- Chronos 모델 최초 실행 시 HuggingFace에서 모델 다운로드 (약 800MB)
- `gemini-2.5-flash` 모델을 사용하여 기후 및 유가 변화 요인을 종합적인 분석 리포트로 제공합니다.
- 데이터 경로 변경 시 `kamis.py` 데이터 로딩 구조를 업데이트해야 합니다.
