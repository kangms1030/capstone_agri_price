"""예측 API 라우터"""

from fastapi import APIRouter, HTTPException, Query
from ..services.kamis import KamisClient
from ..services.predictor import CabbagePricePredictor
from ..services.explainer import PriceExplainer
from ..models.schemas import PredictionResponse, PredictionPoint, PredictSummary, PricePoint

router = APIRouter(prefix="/api/predict", tags=["prediction"])

kamis = KamisClient()
predictor = CabbagePricePredictor(forecast_horizon=14)
explainer = PriceExplainer()


@router.get("", response_model=PredictionResponse)
async def get_prediction(
    history_days: int = Query(90, description="예측에 사용할 과거 일수"),
    market: str = Query("1101", description="지역코드"),
    grade: str = Query("상", description="배추 등급 (특, 상, 중, 하)")
):
    """배추 가격 예측 및 분석 정보 조회"""
    try:
        # 1. 가격 이력 조회 (로컬 엑셀 데이터, 등급 필터 적용)
        history = await kamis.get_price_history(days=history_days, country_code=market, grade=grade)
        if len(history) < 14:
            raise HTTPException(status_code=422, detail="데이터가 부족합니다. 최소 14일 이상의 데이터가 필요합니다.")

        # 2. Chronos 예측
        pred_result = predictor.predict(history)
        predictions = pred_result["predictions"]
        prediction_summary = pred_result["summary"]
        model_name = pred_result["model"]

        # 3. Gemini 설명 생성
        explanation = explainer.generate_explanation(prediction_summary, history)
        
        prediction_summary.update({"grade": grade})

        # 4. 응답 구성
        history_points = [PricePoint(**{**h, "item_name": h.get("item_name", "배추")}) for h in history]

        return {
            "history": [h.model_dump() for h in history_points],
            "predictions": predictions,
            "summary": prediction_summary,
            "model": model_name,
            "explanation": explanation["explanation"],
            "explanation_model": explanation["model"],
            "grade": grade
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 오류: {str(e)}")
