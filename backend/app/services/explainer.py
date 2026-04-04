"""
Gemini API 기반 가격 예측 설명 생성 서비스
"""

import os
import logging
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


def _build_prompt(summary: dict, recent_prices: list[dict]) -> str:
    """Gemini에 전달할 프롬프트 생성"""
    recent_5 = recent_prices[-5:] if len(recent_prices) >= 5 else recent_prices
    
    recent_str_lines = []
    for p in recent_5:
        line = f"  - {p['date']}: {p['price']:,.0f}원/10kg"
        if "weather_temp" in p and pd.notna(p["weather_temp"]):
            line += f" (평균기온: {p['weather_temp']:.1f}℃, 강수량: {p['weather_rain']:.1f}mm)"
        if "oil_diesel" in p and pd.notna(p["oil_diesel"]) and p["oil_diesel"] > 0:
            line += f" [경유가: {p['oil_diesel']:,.0f}원]"
        recent_str_lines.append(line)
        
    recent_str = "\n".join(recent_str_lines)
    direction_emoji = {"상승": "📈", "하락": "📉", "보합": "➡️"}.get(summary.get("direction", ""), "")
    grade = summary.get("grade", "상")

    return f"""당신은 농산물 도매시장 전문 분석가입니다. 아래 배추({grade} 등급) 도매가격 예측 결과와 기후/유가 데이터를 바탕으로 유통업자, 농민이 이해할 수 있게 명확히 설명해주세요.

[예측 데이터 ({grade} 등급)]
- 현재 가격: {summary['current_price']:,.0f}원/10kg
- 14일 후 예측 가격: {summary['predicted_price_14d']:,.0f}원/10kg
- 예측 변화율: {summary['change_rate_pct']:+.1f}%
- 예측 방향: {direction_emoji} {summary['direction']}
- 예측 범위: {summary['pred_min']:,.0f}원 ~ {summary['pred_max']:,.0f}원

[최근 실제 가격 (최근 5일)]
{recent_str}

[요청사항]
반드시 '{grade} 등급' 배추임을 명시하며 다음 형식으로 한국어로 답변해주세요:
1. **한 줄 요약**: 향후 2주간 {grade} 등급 배추 가격 전망을 한 문장으로 요약
2. **상세 분석** (2-3문장): 가격 변화 추이, 기후(기온/강수량) 및 유가 등 외부 요인이 {grade} 등급 가격과 물류에 미치는 영향 설명
3. **유통업자/농민 조언** (1-2문장): {grade} 등급 배추 예측에 기반한 실질적인 행동 지침

※ 주의: '상 등급', '특 등급', '중 등급', '하 등급' 등 등급명을 반드시 '{grade} 등급'으로 정확히 표기하세요. 10kg 기준으로 설명하고, 수치는 제공된 데이터만 사용하세요."""


class PriceExplainer:
    """Gemini API를 사용한 가격 예측 설명 생성기"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info("Gemini API 클라이언트 초기화 완료")
            except Exception as e:
                logger.error(f"Gemini 클라이언트 초기화 실패: {e}")
        return self._client

    def generate_explanation(
        self,
        summary: dict,
        recent_prices: list[dict],
    ) -> dict:
        """
        예측 요약 → Gemini LLM 설명 생성
        반환: {"explanation": str, "model": "gemini" or "rule_based"}
        """
        client = self._get_client()
        if client is None:
            return self._rule_based_explanation(summary)

        try:
            prompt = _build_prompt(summary, recent_prices)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text.strip()
            return {"explanation": text, "model": "gemini-2.5-flash"}

        except Exception as e:
            logger.error(f"Gemini API 오류: {e}")
            return self._rule_based_explanation(summary)

    def _rule_based_explanation(self, summary: dict) -> dict:
        """Gemini 사용 불가 시 규칙 기반 설명"""
        direction = summary.get("direction", "보합")
        change = summary.get("change_rate_pct", 0)
        current = summary.get("current_price", 0)
        pred = summary.get("predicted_price_14d", 0)
        grade = summary.get("grade", "상")

        direction_map = {
            "상승": f"향후 14일간 {grade} 등급 배추 도매가격은 약 {abs(change):.1f}% 상승이 예상됩니다. "
                    f"현재 {current:,.0f}원에서 {pred:,.0f}원(10kg 기준)으로 오를 것으로 보입니다.",
            "하락": f"향후 14일간 {grade} 등급 배추 도매가격은 약 {abs(change):.1f}% 하락이 예상됩니다. "
                    f"현재 {current:,.0f}원에서 {pred:,.0f}원(10kg 기준)으로 내릴 것으로 보입니다.",
            "보합": f"향후 14일간 {grade} 등급 배추 도매가격은 {current:,.0f}원 수준(10kg 기준)을 유지할 것으로 예상됩니다.",
        }
        text = direction_map.get(direction, "예측 정보를 분석 중입니다.")
        return {"explanation": text, "model": "rule_based"}
