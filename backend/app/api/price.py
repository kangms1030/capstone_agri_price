"""가격 조회 API 라우터"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
from ..services.kamis import KamisClient
from ..models.schemas import PricePoint, TodayPriceResponse

router = APIRouter(prefix="/api/price", tags=["price"])
kamis = KamisClient()


@router.get("/today", response_model=TodayPriceResponse, summary="오늘 배추 도매가격")
async def get_today_price(
    date: Optional[str] = Query(None, description="조회 날짜 (YYYY-MM-DD), 기본값: 오늘"),
    market: str = Query("1101", description="지역코드 (기본: 서울=1101)"),
    grade: str = Query("상", description="배추 등급 (특, 상, 중, 하)"),
):
    """당일 배추 도매가격 조회"""
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    try:
        result = await kamis.get_daily_price(target_date=target_date, country_code=market, grade=grade)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", summary="배추 도매가격 이력")
async def get_price_history(
    days: int = Query(90, ge=14, le=730, description="조회 기간 (일수, 최소 14일)"),
    market: str = Query("1101", description="지역코드 (기본: 서울=1101)"),
    grade: str = Query("상", description="배추 등급 (특, 상, 중, 하)"),
):
    """최근 N일 배추 도매가격 이력 조회"""
    try:
        history = await kamis.get_price_history(days=days, country_code=market, grade=grade)
        return {
            "count": len(history),
            "item": "배추",
            "unit": "20kg",
            "market": "서울",
            "data": history,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
