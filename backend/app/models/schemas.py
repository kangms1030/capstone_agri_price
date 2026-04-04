"""Pydantic 데이터 스키마"""

from pydantic import BaseModel
from typing import Optional, List


class PricePoint(BaseModel):
    date: str
    price: float
    item_name: str = "배추"
    unit: str = "20kg"
    rank: str = "상품"
    source: str = "mock"


class PredictionPoint(BaseModel):
    date: str
    price: float
    lower: float
    upper: float


class PredictionSummary(BaseModel):
    current_price: float
    predicted_price_14d: float
    change_rate_pct: float
    pred_min: float
    pred_max: float
    direction: str


class PredictionResponse(BaseModel):
    history: List[PricePoint]
    predictions: List[PredictionPoint]
    summary: PredictionSummary
    model: str
    explanation: str
    explanation_model: str


class TodayPriceResponse(BaseModel):
    date: str
    item_name: str
    kind_name: str
    rank: str
    unit: str
    price: Optional[float]
    market: str
    product_cls: str
    source: str
