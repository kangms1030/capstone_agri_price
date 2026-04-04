"""
Agri-Insight FastAPI 백엔드
배추 도매가격 예측 시스템
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# .env 로드 (백엔드 디렉토리 기준)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .api.price import router as price_router
from .api.predict import router as predict_router
from .services.predictor import get_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 Chronos 모델 사전 로드"""
    logger.info("=== Agri-Insight 백엔드 시작 ===")
    logger.info("Chronos 모델 사전 로딩 중...")
    get_pipeline()  # 모델 미리 로드
    logger.info("서버 준비 완료!")
    yield
    logger.info("서버 종료")


app = FastAPI(
    title="Agri-Insight API",
    description=(
        "배추 도매가격 예측 시스템 (Chronos TSFM + Gemini LLM)\n\n"
        "- **KAMIS API**: 농수산물 도매가격 데이터\n"
        "- **Chronos-T5**: Time-Series Foundation Model 예측\n"
        "- **Gemini**: 자연어 설명 생성"
    ),
    version="0.1.0-prototype",
    lifespan=lifespan,
)

# CORS 설정 (프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(price_router)
app.include_router(predict_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "Agri-Insight API",
        "version": "0.1.0-prototype",
        "description": "배추 도매가격 예측 시스템",
        "docs": "/docs",
        "endpoints": {
            "today_price": "/api/price/today",
            "price_history": "/api/price/history",
            "predict": "/api/predict",
        },
    }


@app.get("/health", tags=["root"])
async def health():
    import torch
    return {
        "status": "healthy",
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
