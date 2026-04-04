"""
로컬 데이터 로더 서비스 (기존 KAMIS API 클라이언트 대체)
배추 가격, 기상 공공데이터, 유가 데이터를 병합하여 사용합니다.
"""

import os
import logging
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

import glob

# 데이터 경로 상수
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
CABBAGE_EXCEL = os.path.join(DATA_DIR, "agri_price", "cabbage.xlsx")
WEATHER_CSV = os.path.join(DATA_DIR, "weather_data_2015_2025.csv")
# Find oil csv dynamically
_oil_candidates = glob.glob(os.path.join(DATA_DIR, "*원유*.csv"))
OIL_CSV = _oil_candidates[0] if _oil_candidates else ""

class LocalDataClient:
    """로컬 Excel 및 CSV 파일 기반 데이터 클라이언트"""

    def __init__(self):
        self._price_df = None
        self._weather_df = None
        self._oil_df = None
        self._load_data()

    def _load_data(self):
        # 1. 배추 가격 데이터 로드
        try:
            df = pd.read_excel(CABBAGE_EXCEL)
            # 컬럼 강제 영어 변경 방지, 한글로 읽히는 것 확인: 'DATE', '품목명', '단위', '등급명', '평균가격' ...
            cols = list(df.columns)
            # 인덱스 매핑 안전하게 하기 위해
            df = df.rename(columns={
                'DATE': 'date',
                cols[1]: 'item',
                cols[2]: 'unit',
                cols[3]: 'grade',
                cols[4]: 'price'
            })
            df['date'] = pd.to_datetime(df['date'])
            # 결측치, 0원 처리
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            
            # replace 0 with NA then forward/backward fill per grade
            def fill_group(group):
                return group.replace(0, pd.NA).ffill().bfill()
                
            df['price'] = df.groupby('grade', group_keys=False)['price'].apply(fill_group)
            
            self._price_df = df
            logger.info(f"배추 데이터 로드 완료 ({len(df)}행)")
        except Exception as e:
            logger.error(f"배추 데이터 로드 실패: {e}")
            self._price_df = pd.DataFrame(columns=['date', 'item', 'unit', 'grade', 'price'])

        # 2. 기상 데이터 로드
        try:
            w_df = pd.read_csv(WEATHER_CSV)
            w_df = w_df.rename(columns={'tm': 'date'})
            w_df['date'] = pd.to_datetime(w_df['date'])
            # 동일 날짜 여러 관측소일 경우 평균
            w_df = w_df.groupby('date').mean(numeric_only=True).reset_index()
            self._weather_df = w_df
        except Exception as e:
            logger.error(f"기상 데이터 로드 실패: {e}")
            self._weather_df = pd.DataFrame(columns=['date'])

        # 3. 유가 데이터 로드
        try:
            if not OIL_CSV:
                raise FileNotFoundError("유가 데이터 파일을 찾을 수 없습니다.")
                
            try:
                o_df = pd.read_csv(OIL_CSV, encoding='utf-8')
            except:
                o_df = pd.read_csv(OIL_CSV, encoding='cp949')
            # 컬럼 확인 후 이름 변경. 0: '구분'(날짜), 1: 자동차경유, 2: 실내등유
            o_cols = list(o_df.columns)
            o_df = o_df.rename(columns={o_cols[0]: 'date', o_cols[1]: 'diesel', o_cols[2]: 'kerosene'})
            # 날짜를 파싱 ('2015년11월16일' -> '2015-11-16')
            o_df['date'] = o_df['date'].str.replace('년', '-').str.replace('월', '-').str.replace('일', '')
            o_df['date'] = pd.to_datetime(o_df['date'])
            self._oil_df = o_df
        except Exception as e:
            logger.error(f"유가 데이터 로드 실패: {e}")
            self._oil_df = pd.DataFrame(columns=['date'])

    def _get_merged_data(self, grade: str) -> pd.DataFrame:
        """특정 등급의 데이터와 외부 데이터를 병합하여 반환"""
        if self._price_df.empty:
            return pd.DataFrame()
            
        df = self._price_df[self._price_df['grade'] == grade].copy()
        if df.empty:
            return pd.DataFrame()
            
        df = df.sort_values('date').reset_index(drop=True)
        
        # 기상, 유가 병합 (있는 경우만)
        if not self._weather_df.empty:
            df = pd.merge(df, self._weather_df, on='date', how='left')
        if not self._oil_df.empty:
            df = pd.merge(df, self._oil_df, on='date', how='left')
            
        # 결측치는 전일 데이터로 채움
        df = df.ffill().bfill()
        return df

    async def get_daily_price(self, target_date: str = None, country_code: str = "1101", grade: str = "상") -> dict:
        if target_date is None:
            target_date = self._price_df['date'].max().strftime("%Y-%m-%d") if not self._price_df.empty else datetime.now().strftime("%Y-%m-%d")
            
        df = self._get_merged_data(grade)
        dt = pd.to_datetime(target_date)
        row = df[df["date"].dt.date == dt.date()]
        if row.empty:
            row = df.tail(1)
            
        if row.empty:
             return {"error": "no_data"}
             
        r = row.iloc[0]
        return {
            "date": str(r["date"].date()),
            "item_name": r.get("item", "배추"),
            "grade": grade,
            "unit": r.get("unit", "10kg"),
            "price": int(r["price"]),
            "source": "local_excel"
        }

    async def get_price_history(self, days: int = 90, country_code: str = "1101", grade: str = "상") -> list[dict]:
        df = self._get_merged_data(grade)
        recent = df.tail(days).copy()
        result = []
        for _, row in recent.iterrows():
            item = {
                "date": str(row["date"].date()),
                "price": int(row["price"]),
                "item_name": row.get("item", "배추"),
                "unit": row.get("unit", "10kg"),
                "grade": grade,
                "weather_temp": float(row.get("avgTa", 0)),
                "weather_rain": float(row.get("sumRn", 0)),
                "oil_diesel": float(row.get("diesel", 0))
            }
            result.append(item)
        return result

# 하위 호환성 및 기존 파일 이름 유지용
KamisClient = LocalDataClient
