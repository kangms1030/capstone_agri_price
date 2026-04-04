"""
Chronos 기반 배추 가격 예측 서비스
amazon/chronos-t5-small 모델로 T+14일 예측
"""

import logging
from typing import Optional
import numpy as np
import pandas as pd
import torch

logger = logging.getLogger(__name__)

# 전역 모델 인스턴스 (한 번만 로드)
_pipeline = None


def get_pipeline():
    """Chronos 파이프라인 싱글턴 로드 (GPU 사용)"""
    global _pipeline
    if _pipeline is None:
        try:
            from chronos import BaseChronosPipeline
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Chronos 모델 로딩 중... (device={device})")
            _pipeline = BaseChronosPipeline.from_pretrained(
                "amazon/chronos-t5-small",
                device_map=device,
                torch_dtype=torch.bfloat16,
            )
            logger.info(f"Chronos 모델 로딩 완료 (device={device})")
        except Exception as e:
            logger.error(f"Chronos 로드 실패: {e}")
            _pipeline = None
    return _pipeline


class CabbagePricePredictor:
    """배추 도매가격 예측기 (Chronos + 통계 Fallback)"""

    def __init__(self, forecast_horizon: int = 14):
        self.forecast_horizon = forecast_horizon

    def predict(self, price_history: list[dict]) -> dict:
        """
        가격 이력 데이터 → T+14일 예측
        반환: {
            "predictions": [{"date": str, "price": float, "lower": float, "upper": float}],
            "model": "chronos" or "statistical",
            "summary": {...}
        }
        """
        if len(price_history) < 14:
            raise ValueError("예측에 최소 14일 이상의 데이터가 필요합니다.")

        # 시계열 데이터 준비
        df = pd.DataFrame(price_history)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        prices = df["price"].values.astype(float)
        last_date = df["date"].iloc[-1]

        # Chronos로 예측 시도
        pipeline = get_pipeline()
        if pipeline is not None:
            return self._chronos_predict(prices, last_date, pipeline)
        else:
            logger.warning("Chronos 사용 불가 - 통계 기반 예측으로 대체")
            return self._statistical_predict(prices, last_date)

    def _chronos_predict(
        self, prices: np.ndarray, last_date: pd.Timestamp, pipeline
    ) -> dict:
        """Chronos 모델 예측"""
        try:
            context = torch.tensor(prices, dtype=torch.float32).unsqueeze(0)

            # 예측 실행 (quantile 포함)
            quantiles, mean = pipeline.predict_quantiles(
                context=context,
                prediction_length=self.forecast_horizon,
                quantile_levels=[0.1, 0.5, 0.9],
                num_samples=100,
            )
            # quantiles shape: (batch=1, quantile_levels, horizon)
            q10 = quantiles[0, 0].numpy()
            q50 = quantiles[0, 1].numpy()
            q90 = quantiles[0, 2].numpy()

            predictions = []
            for i in range(self.forecast_horizon):
                pred_date = last_date + pd.Timedelta(days=i + 1)
                predictions.append({
                    "date": str(pred_date.date()),
                    "price": max(0, float(q50[i])),
                    "lower": max(0, float(q10[i])),
                    "upper": max(0, float(q90[i])),
                })

            summary = self._calc_summary(prices, predictions)
            return {"predictions": predictions, "model": "chronos", "summary": summary}

        except Exception as e:
            logger.error(f"Chronos 예측 오류: {e}")
            return self._statistical_predict(prices, last_date)

    def _statistical_predict(
        self, prices: np.ndarray, last_date: pd.Timestamp
    ) -> dict:
        """통계 기반 Fallback 예측 (이동평균 + 계절 조정)"""
        # 최근 30일 이동평균 트렌드
        window = min(30, len(prices))
        recent = prices[-window:]
        mean_price = float(np.mean(recent))
        std_price = float(np.std(recent))
        # 최근 트렌드 (선형)
        x = np.arange(len(recent))
        coeffs = np.polyfit(x, recent, 1)
        slope = coeffs[0]

        predictions = []
        for i in range(self.forecast_horizon):
            pred_date = last_date + pd.Timedelta(days=i + 1)
            # 트렌드 기반 예측 + 계절 노이즈
            pred = mean_price + slope * (window + i)
            pred = max(0, pred)
            margin = std_price * 1.64  # 90% 신뢰구간
            predictions.append({
                "date": str(pred_date.date()),
                "price": round(pred, 0),
                "lower": max(0, round(pred - margin, 0)),
                "upper": round(pred + margin, 0),
            })

        summary = self._calc_summary(prices, predictions)
        return {"predictions": predictions, "model": "statistical", "summary": summary}

    def _calc_summary(self, prices: np.ndarray, predictions: list[dict]) -> dict:
        """예측 요약 통계"""
        pred_prices = [p["price"] for p in predictions]
        current = float(prices[-1])
        pred_end = float(pred_prices[-1])
        change_rate = (pred_end - current) / current * 100

        return {
            "current_price": round(current, 0),
            "predicted_price_14d": round(pred_end, 0),
            "change_rate_pct": round(change_rate, 2),
            "pred_min": round(min(pred_prices), 0),
            "pred_max": round(max(pred_prices), 0),
            "direction": "상승" if change_rate > 3 else ("하락" if change_rate < -3 else "보합"),
        }
