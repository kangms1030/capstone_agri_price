"""
KAMIS (한국농수산식품유통공사) API 클라이언트
배추 도매가격 데이터 조회

API 문서: https://www.kamis.or.kr/customer/reference/openapi_list.do?action=detail&boardno=1
엔드포인트: http://www.kamis.or.kr/service/price/xml.do?action=dailyPriceByCategoryList
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# KAMIS API 상수
KAMIS_BASE_URL = "http://www.kamis.or.kr/service/price/xml.do"
CABBAGE_CATEGORY_CODE = "200"   # 채소류
CABBAGE_ITEM_CODE = "211"       # 배추
WHOLESALE_CODE = "02"           # 도매

# 배추 Mock 데이터 생성 (2년치 일별 데이터)
def _generate_mock_cabbage_prices() -> pd.DataFrame:
    """
    실제 배추 도매가격 패턴을 반영한 Mock 데이터 생성
    배추는 계절성이 강함: 여름(7-8월) 고가, 봄/가을 저가 패턴
    """
    np.random.seed(42)
    today = datetime.now()
    dates = pd.date_range(end=today, periods=730, freq="D")

    # 계절 패턴 (배추 가격 특성)
    days = np.arange(len(dates))
    # 연간 사이클: 여름에 높고 봄/가을에 낮음
    seasonal = 3000 * np.sin(2 * np.pi * (days - 60) / 365) + 500 * np.sin(4 * np.pi * days / 365)
    # 기저 가격 (20kg 기준, 원)
    base_price = 15000
    # 랜덤 노이즈
    noise = np.random.normal(0, 800, len(dates))
    # 트렌드 (최근 가격 상승)
    trend = days * 2

    prices = base_price + seasonal + noise + trend
    prices = np.maximum(prices, 2000)  # 최소 2,000원

    df = pd.DataFrame({
        "date": dates,
        "item_name": "배추",
        "item_code": CABBAGE_ITEM_CODE,
        "kind_name": "배추",
        "rank": "상품",
        "unit": "20kg",
        "price": prices.round(0).astype(int),
        "market": "서울",
        "product_cls": "도매",
    })
    return df


class KamisClient:
    """KAMIS API 클라이언트 (API 키 미설정 시 Mock 데이터 사용)"""

    def __init__(self):
        self.api_key = os.getenv("KAMIS_API_KEY", "")
        self.api_id = os.getenv("KAMIS_API_ID", "")
        self.use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

        # API 키가 있으면 실제 API 사용
        if self.api_key and self.api_id and not self.use_mock:
            self.use_mock = False
            logger.info("KAMIS API 실제 연결 모드")
        else:
            self.use_mock = True
            logger.info("KAMIS API Mock 모드 (API 키 발급 후 .env 업데이트)")

        # Mock 데이터 캐시
        self._mock_df: Optional[pd.DataFrame] = None

    def _get_mock_df(self) -> pd.DataFrame:
        if self._mock_df is None:
            self._mock_df = _generate_mock_cabbage_prices()
        return self._mock_df

    async def get_daily_price(
        self,
        target_date: Optional[str] = None,
        country_code: str = "1101",  # 서울
    ) -> dict:
        """특정 일자의 배추 도매가격 조회"""
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")

        if self.use_mock:
            return self._get_mock_daily_price(target_date)
        else:
            return await self._fetch_real_price(target_date, country_code)

    def _get_mock_daily_price(self, target_date: str) -> dict:
        """Mock 일별 가격 반환"""
        df = self._get_mock_df()
        dt = pd.to_datetime(target_date)
        row = df[df["date"].dt.date == dt.date()]
        if row.empty:
            # 가장 최근 날짜로 대체
            row = df.tail(1)
        r = row.iloc[0]
        return {
            "date": str(r["date"].date()),
            "item_name": r["item_name"],
            "kind_name": r["kind_name"],
            "rank": r["rank"],
            "unit": r["unit"],
            "price": int(r["price"]),
            "market": r["market"],
            "product_cls": r["product_cls"],
            "source": "mock",
        }

    async def _fetch_real_price(self, target_date: str, country_code: str) -> dict:
        """실제 KAMIS API 호출"""
        params = {
            "action": "dailyPriceByCategoryList",
            "p_cert_key": self.api_key,
            "p_cert_id": self.api_id,
            "p_returntype": "json",
            "p_product_cls_code": WHOLESALE_CODE,
            "p_item_category_code": CABBAGE_CATEGORY_CODE,
            "p_country_code": country_code,
            "p_regday": target_date,
            "p_convert_kg_yn": "N",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(KAMIS_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        # 응답 파싱
        items = data.get("data", {}).get("item", [])
        cabbage_items = [
            it for it in items
            if str(it.get("item_code", "")) == CABBAGE_ITEM_CODE
        ]
        if not cabbage_items:
            return {"date": target_date, "price": None, "source": "real", "error": "no_data"}

        item = cabbage_items[0]
        price_str = item.get("dpr1", "0").replace(",", "")
        try:
            price = int(float(price_str)) if price_str and price_str != "-" else None
        except ValueError:
            price = None

        return {
            "date": target_date,
            "item_name": item.get("item_name", "배추"),
            "kind_name": item.get("kind_name", "배추"),
            "rank": item.get("rank", "상품"),
            "unit": item.get("unit", "20kg"),
            "price": price,
            "market": "서울",
            "product_cls": "도매",
            "source": "real",
        }

    async def get_price_history(
        self,
        days: int = 90,
        country_code: str = "1101",
    ) -> list[dict]:
        """
        최근 N일 배추 도매가격 이력 조회
        실제 API는 하루씩 호출해야 하므로 Mock 모드에서는 한번에 반환
        """
        if self.use_mock:
            return self._get_mock_history(days)
        else:
            return await self._fetch_real_history(days, country_code)

    def _get_mock_history(self, days: int) -> list[dict]:
        """Mock 이력 데이터 반환"""
        df = self._get_mock_df()
        recent = df.tail(days).copy()
        result = []
        for _, row in recent.iterrows():
            result.append({
                "date": str(row["date"].date()),
                "price": int(row["price"]),
                "item_name": row["item_name"],
                "unit": row["unit"],
                "rank": row["rank"],
                "source": "mock",
            })
        return result

    async def _fetch_real_history(self, days: int, country_code: str) -> list[dict]:
        """실제 API로 이력 데이터 수집 (날짜별 순차 호출)"""
        results = []
        today = datetime.now()
        for i in range(days, 0, -1):
            target = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                price_data = await self._fetch_real_price(target, country_code)
                if price_data.get("price") is not None:
                    results.append(price_data)
            except Exception as e:
                logger.warning(f"가격 조회 실패 ({target}): {e}")
        return results
