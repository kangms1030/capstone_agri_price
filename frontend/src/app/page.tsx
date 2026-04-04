"use client";
import { useEffect, useState, useCallback } from "react";
import { getPrediction, getTodayPrice } from "@/lib/api";
import { PredictionResponse, TodayPrice } from "@/types";
import StatCard from "@/components/StatCard";
import PriceChart from "@/components/PriceChart";
import ExplanationCard from "@/components/ExplanationCard";

export default function DashboardPage() {
  const [today, setToday] = useState<TodayPrice | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [historyDays, setHistoryDays] = useState(90);
  const [grade, setGrade] = useState("상");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [todayData, predData] = await Promise.all([
        getTodayPrice(undefined, "1101", grade),
        getPrediction(historyDays, grade),
      ]);
      setToday(todayData);
      setPrediction(predData);
      setLastUpdated(new Date().toLocaleTimeString("ko-KR"));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "알 수 없는 오류";
      if (msg.includes("Network") || msg.includes("ECONNREFUSED")) {
        setError("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.");
      } else {
        setError(`데이터 로딩 실패: ${msg}`);
      }
    } finally {
      setLoading(false);
    }
  }, [historyDays, grade]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const directionColor = {
    "상승": "bg-red-500/20 text-red-400",
    "하락": "bg-blue-500/20 text-blue-400",
    "보합": "bg-slate-500/20 text-slate-400",
  };
  const directionEmoji = { "상승": "📈", "하락": "📉", "보합": "➡️" };

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #020818 0%, #0a1628 50%, #050d1a 100%)" }}>
      {/* 배경 글로우 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-emerald-500/5 blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-indigo-500/5 blur-3xl animate-pulse-slow" style={{ animationDelay: "2s" }} />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-8">
        {/* 헤더 */}
        <header className="mb-10 animate-fadeIn">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">🥬</span>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">Agri-Insight</h1>
              <p className="text-slate-400 text-sm">배추 도매가격 예측 대시보드 · Powered by Chronos + Gemini AI</p>
            </div>
            <div className="ml-auto flex flex-col items-end gap-1">
              {lastUpdated && (
                <span className="text-xs text-slate-500">최근 갱신: {lastUpdated}</span>
              )}
              <div className="flex gap-2 items-center">
                <select
                  value={grade}
                  onChange={(e) => setGrade(e.target.value)}
                  className="text-xs rounded-lg border border-white/10 bg-white/5 text-slate-300 px-3 py-1.5 focus:outline-none focus:border-emerald-500/50"
                >
                  <option value="특">특 등급</option>
                  <option value="상">상 등급</option>
                  <option value="중">중 등급</option>
                  <option value="하">하 등급</option>
                </select>
                <select
                  value={historyDays}
                  onChange={(e) => setHistoryDays(Number(e.target.value))}
                  className="text-xs rounded-lg border border-white/10 bg-white/5 text-slate-300 px-3 py-1.5 focus:outline-none focus:border-emerald-500/50"
                >
                  <option value={30}>최근 30일</option>
                  <option value={60}>최근 60일</option>
                  <option value={90}>최근 90일</option>
                  <option value={180}>최근 180일</option>
                </select>
                <button
                  onClick={fetchData}
                  disabled={loading}
                  className="flex items-center gap-1.5 text-xs px-4 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                      </svg>
                      분석 중...
                    </>
                  ) : "🔄 새로고침"}
                </button>
              </div>
            </div>
          </div>
          {/* 데이터 소스 배지 */}
          <div className="flex gap-2 mt-4 flex-wrap">
            {[
              { label: "로컬 데이터", color: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" },
              { label: "Chronos-T5-base", color: "bg-purple-500/10 border-purple-500/30 text-purple-400" },
              { label: "Gemini 2.5 Flash", color: "bg-blue-500/10 border-blue-500/30 text-blue-400" },
            ].map((b) => (
              <span key={b.label} className={`text-xs px-3 py-1 rounded-full border ${b.color}`}>{b.label}</span>
            ))}
          </div>
        </header>

        {/* 에러 */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400 text-sm animate-fadeIn">
            ⚠️ {error}
          </div>
        )}

        {/* 초기 로딩 */}
        {loading && !prediction && (
          <div className="flex flex-col items-center justify-center py-24 gap-4 animate-fadeIn">
            <svg className="animate-spin h-10 w-10 text-emerald-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            <p className="text-slate-400 text-sm">Chronos 모델로 예측 중... (첫 로딩은 30~60초 소요)</p>
          </div>
        )}

        {prediction && (
          <>
            {/* 통계 카드 */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6 animate-fadeIn">
              <StatCard
                label={`${grade} 등급 현재 도매가`}
                value={`${prediction.summary.current_price.toLocaleString()}원`}
                sub="10kg 기준 · 전국 주산지 평균"
                badge="오늘"
                badgeColor="bg-slate-500/20 text-slate-400"
              />
              <StatCard
                label="14일 후 예측가"
                value={`${prediction.summary.predicted_price_14d.toLocaleString()}원`}
                sub="Chronos 예측"
                badge={`${prediction.summary.change_rate_pct > 0 ? "+" : ""}${prediction.summary.change_rate_pct}%`}
                badgeColor={prediction.summary.change_rate_pct > 0 ? "bg-red-500/20 text-red-400" : prediction.summary.change_rate_pct < 0 ? "bg-blue-500/20 text-blue-400" : "bg-slate-500/20 text-slate-400"}
              />
              <StatCard
                label="예측 방향"
                value={`${directionEmoji[prediction.summary.direction]} ${prediction.summary.direction}`}
                sub="향후 2주 전망"
                badge={prediction.model === "chronos" ? "Chronos" : "통계"}
                badgeColor="bg-purple-500/20 text-purple-400"
              />
              <StatCard
                label="예측 범위"
                value={`${(prediction.summary.pred_min / 1000).toFixed(1)}k ~ ${(prediction.summary.pred_max / 1000).toFixed(1)}k원`}
                sub="10% ~ 90% 신뢰구간"
                badge="P10~P90"
                badgeColor="bg-indigo-500/20 text-indigo-400"
              />
            </div>

            {/* 차트 */}
            <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 mb-6 animate-fadeIn" style={{ animationDelay: "0.1s" }}>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-white">🥬 {grade} 등급 배추 가격 추이 및 예측</h2>
                  <p className="text-xs text-slate-500 mt-1">실선: 실제 가격 | 점선: Chronos 예측 | 음영: 90% 신뢰구간</p>
                </div>
                <span className="text-xs text-slate-500">단위: 원/10kg</span>
              </div>
              <PriceChart
                history={prediction.history}
                predictions={prediction.predictions}
              />
            </div>

            {/* AI 설명 */}
            <div className="mb-6 animate-fadeIn" style={{ animationDelay: "0.2s" }}>
              <ExplanationCard
                explanation={prediction.explanation}
                model={prediction.explanation_model}
                isLoading={loading}
              />
            </div>

            {/* 예측 테이블 */}
            <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 animate-fadeIn" style={{ animationDelay: "0.3s" }}>
              <h2 className="text-lg font-semibold text-white mb-4">📅 14일 예측 상세</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500 border-b border-white/10">
                      <th className="pb-3 pr-4 font-medium">날짜</th>
                      <th className="pb-3 pr-4 font-medium text-right">예측 가격</th>
                      <th className="pb-3 pr-4 font-medium text-right">하한 (P10)</th>
                      <th className="pb-3 font-medium text-right">상한 (P90)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prediction.predictions.map((p, i) => {
                      const change = p.price - prediction.summary.current_price;
                      const pct = (change / prediction.summary.current_price * 100).toFixed(1);
                      return (
                        <tr key={p.date} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                          <td className="py-2.5 pr-4 text-slate-300 font-mono">
                            {p.date} <span className="text-slate-600 text-xs">D+{i + 1}</span>
                          </td>
                          <td className="py-2.5 pr-4 text-right font-semibold text-white">
                            {p.price.toLocaleString()}원
                            <span className={`ml-2 text-xs ${change >= 0 ? "text-red-400" : "text-blue-400"}`}>
                              {change >= 0 ? "+" : ""}{pct}%
                            </span>
                          </td>
                          <td className="py-2.5 pr-4 text-right text-slate-400">{p.lower.toLocaleString()}원</td>
                          <td className="py-2.5 text-right text-slate-400">{p.upper.toLocaleString()}원</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* 푸터 */}
        <footer className="mt-10 text-center text-xs text-slate-600">
          <p>데이터: 로컬 데이터(기상, 유가 복합참조) · AI: Chronos-T5-base, Gemini 2.5 Flash</p>
          <p className="mt-1">⚠️ 예측 결과는 참고용이며 실제 가격과 다를 수 있습니다.</p>
        </footer>
      </div>
    </div>
  );
}
