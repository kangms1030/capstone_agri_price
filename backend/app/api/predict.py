"""예측 API 라우터"""

from fastapi import APIRouter, HTTPException, Query
from ..services.kamis import KamisClient
from ..services.predictor import CabbagePricePredictor
from ..services.explainer import PriceExplainer
from ..models.schemas import PredictionResponse, PredictionPoint, PredictionSummary, PricePoint

router = APIRouter(prefix="/api/predict", tags=["prediction"])

kamis = KamisClient()
predictor = CabbagePricePredictor(forecast_horizon=14)
explainer = PriceExplainer()


@router.get("", summary="배추 가격 14일 예측 (Chronos + Gemini 설명)")
async def predict_cabbage_price(
    history_days: int = Query(90, ge=30, le=365, description="예측에 사용할 과거 데이터 기간 (일)"),
    market: str = Query("1101", description="지역코드 (기본: 서울=1101)"),
):
    """
    Chronos TSFM 모델을 이용한 배추 도매가격 14일 예측
    - 과거 N일 데이터 → Chronos-T5-small 예측
    - Gemini API로 한국어 자연어 설명 생성
    """
    try:
        # 1. 이력 데이터 수집
        history = await kamis.get_price_history(days=history_days, country_code=market)
        if len(history) < 14:
            raise HTTPException(status_code=422, detail="데이터가 부족합니다. 최소 14일 이상의 데이터가 필요합니다.")

        # 2. Chronos 예측
        pred_result = predictor.predict(history)
        summary = pred_result["summary"]
        model_name = pred_result["model"]

        # 3. Gemini 설명 생성
        explanation_result = explainer.generate_explanation(summary, history)

        # 4. 응답 조합
        history_points = [PricePoint(**{**h, "item_name": h.get("item_name", "배추")}) for h in history]
        pred_points = [PredictionPoint(**p) for p in pred_result["predictions"]]

        return {
            "history": [h.model_dump() for h in history_points],
            "predictions": [p.model_dump() for p in pred_points],
            "summary": PredictionSummary(**summary).model_dump(),
            "model": model_name,
            "explanation": explanation_result["explanation"],
            "explanation_model": explanation_result["model"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 오류: {str(e)}")
