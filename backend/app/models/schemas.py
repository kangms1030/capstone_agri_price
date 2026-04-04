"""Pydantic 데이터 스키마"""

from pydantic import BaseModel
from typing import Optional, List


class PricePoint(BaseModel):
    date: str
    price: float
    item_name: str = "배추"
    unit: str = "20kg"
    rank: str = "상품"
    grade: str = "상"
    source: str = "mock"


class HistoryItem(BaseModel):
    date: str
    price: int
    item_name: str
    unit: str
    grade: str = "상"
    rank: str = "상품"
    source: str = "mock"


class PredictionPoint(BaseModel):
    date: str
    price: float
    lower: float
    upper: float


class PredictSummary(BaseModel):
    current_price: float
    predicted_price_14d: float
    change_rate_pct: float
    pred_min: float
    pred_max: float
    direction: str
    grade: str = "상"


class PredictionResponse(BaseModel):
    history: List[PricePoint]
    predictions: List[PredictionPoint]
    summary: PredictSummary
    model: str
    explanation: str
    explanation_model: str
    grade: str = "상"


class TodayPriceResponse(BaseModel):
    date: str
    item_name: str
    grade: str = "상"
    kind_name: Optional[str] = None
    rank: str = "상품"
    unit: str = "10kg"
    price: Optional[float]
    market: str = "1101"
    product_cls: str = "02"
    source: str
