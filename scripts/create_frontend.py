"""프론트엔드 파일 일괄 생성 스크립트"""
import os

BASE = r"c:\Users\minsoo\Desktop\capstone\frontend\src"

files = {}

# ── types/index.ts ──────────────────────────────────────────────────────────
files["types/index.ts"] = """\
export interface PricePoint {
  date: string;
  price: number;
  item_name?: string;
  unit?: string;
  rank?: string;
  source?: string;
}

export interface PredictionPoint {
  date: string;
  price: number;
  lower: number;
  upper: number;
}

export interface PredictionSummary {
  current_price: number;
  predicted_price_14d: number;
  change_rate_pct: number;
  pred_min: number;
  pred_max: number;
  direction: "상승" | "하락" | "보합";
}

export interface PredictionResponse {
  history: PricePoint[];
  predictions: PredictionPoint[];
  summary: PredictionSummary;
  model: string;
  explanation: string;
  explanation_model: string;
}

export interface TodayPrice {
  date: string;
  item_name: string;
  kind_name: string;
  rank: string;
  unit: string;
  price: number | null;
  market: string;
  product_cls: string;
  source: string;
}
"""

# ── lib/api.ts ───────────────────────────────────────────────────────────────
files["lib/api.ts"] = """\
import axios from "axios";
import { PredictionResponse, TodayPrice } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 120000, // Chronos 모델 로딩 시간 고려
});

export async function getTodayPrice(): Promise<TodayPrice> {
  const { data } = await api.get("/api/price/today");
  return data;
}

export async function getPrediction(historyDays = 90): Promise<PredictionResponse> {
  const { data } = await api.get("/api/predict", {
    params: { history_days: historyDays },
  });
  return data;
}
"""

# ── components/StatCard.tsx ──────────────────────────────────────────────────
files["components/StatCard.tsx"] = """\
interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  badge?: string;
  badgeColor?: string;
}

export default function StatCard({ label, value, sub, badge, badgeColor = "bg-emerald-500/20 text-emerald-400" }: StatCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-slate-400">{label}</p>
        {badge && (
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${badgeColor}`}>
            {badge}
          </span>
        )}
      </div>
      <p className="mt-3 text-3xl font-bold text-white tracking-tight">{value}</p>
      {sub && <p className="mt-1 text-sm text-slate-500">{sub}</p>}
      <div className="absolute -bottom-4 -right-4 h-20 w-20 rounded-full bg-emerald-500/5 blur-2xl" />
    </div>
  );
}
"""

# ── components/PriceChart.tsx ────────────────────────────────────────────────
files["components/PriceChart.tsx"] = """\
"use client";
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { PricePoint, PredictionPoint } from "@/types";

interface ChartData {
  date: string;
  actual?: number;
  predicted?: number;
  lower?: number;
  upper?: number;
  isPrediction?: boolean;
}

interface PriceChartProps {
  history: PricePoint[];
  predictions: PredictionPoint[];
}

const formatPrice = (v: number) => `${(v / 1000).toFixed(1)}천원`;
const formatDate = (d: string) => {
  const dt = new Date(d);
  return `${dt.getMonth() + 1}/${dt.getDate()}`;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-sm p-3 shadow-2xl text-sm">
      <p className="font-semibold text-slate-200 mb-2">{label}</p>
      {payload.map((p: { name: string; value: number; color: string }, i: number) => (
        <p key={i} style={{ color: p.color }} className="flex gap-2">
          <span>{p.name}:</span>
          <span className="font-bold">{p.value ? `${p.value.toLocaleString()}원` : "-"}</span>
        </p>
      ))}
    </div>
  );
};

export default function PriceChart({ history, predictions }: PriceChartProps) {
  // 최근 60일 이력 + 예측 14일 합치기
  const recent = history.slice(-60);
  const lastDate = recent[recent.length - 1]?.date;

  const chartData: ChartData[] = [
    ...recent.map((h) => ({
      date: formatDate(h.date),
      actual: h.price,
      isPrediction: false,
    })),
    ...predictions.map((p) => ({
      date: formatDate(p.date),
      predicted: p.price,
      lower: p.lower,
      upper: p.upper,
      isPrediction: true,
    })),
  ];

  const splitIndex = recent.length;

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <defs>
            <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#64748b" }}
            interval={Math.floor(chartData.length / 8)}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatPrice}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
            width={60}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: "12px", color: "#94a3b8", paddingTop: "12px" }}
          />
          <ReferenceLine x={formatDate(lastDate)} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
          {/* 신뢰구간 영역 */}
          <Area
            dataKey="upper"
            name="상한(90%)"
            fill="#6366f1"
            fillOpacity={0.08}
            stroke="none"
            legendType="none"
          />
          <Area
            dataKey="lower"
            name="하한(10%)"
            fill="#fff"
            fillOpacity={0}
            stroke="none"
            legendType="none"
          />
          {/* 실제 가격 */}
          <Area
            dataKey="actual"
            name="실제 가격"
            stroke="#10b981"
            strokeWidth={2}
            fill="url(#actualGrad)"
            dot={false}
            activeDot={{ r: 5, fill: "#10b981" }}
          />
          {/* 예측 가격 */}
          <Line
            dataKey="predicted"
            name="예측 가격"
            stroke="#6366f1"
            strokeWidth={2.5}
            strokeDasharray="6 3"
            dot={false}
            activeDot={{ r: 5, fill: "#6366f1" }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
"""

# ── components/ExplanationCard.tsx ──────────────────────────────────────────
files["components/ExplanationCard.tsx"] = """\
interface ExplanationCardProps {
  explanation: string;
  model: string;
  isLoading?: boolean;
}

export default function ExplanationCard({ explanation, model, isLoading }: ExplanationCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 animate-pulse">
        <div className="h-4 bg-white/10 rounded w-1/4 mb-4" />
        <div className="space-y-2">
          <div className="h-3 bg-white/10 rounded w-full" />
          <div className="h-3 bg-white/10 rounded w-5/6" />
          <div className="h-3 bg-white/10 rounded w-4/6" />
        </div>
      </div>
    );
  }

  const modelLabel = model === "gemini-2.0-flash" ? "Gemini 2.0 Flash" : model === "rule_based" ? "규칙 기반" : model;

  return (
    <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 backdrop-blur-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🤖</span>
        <h3 className="font-semibold text-slate-200">AI 가격 분석</h3>
        <span className="ml-auto text-xs px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-400 font-medium">
          {modelLabel}
        </span>
      </div>
      <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
        {explanation}
      </div>
    </div>
  );
}
"""

# ── app/globals.css ──────────────────────────────────────────────────────────
files["app/globals.css"] = """\
@import "tailwindcss";

:root {
  --bg-primary: #020818;
  --bg-secondary: #0a1628;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  background: var(--bg-primary);
  color: #f1f5f9;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* 스크롤바 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f1629; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

/* 배경 그라데이션 애니메이션 */
@keyframes pulse-slow {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}
.animate-pulse-slow { animation: pulse-slow 4s ease-in-out infinite; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn { animation: fadeIn 0.6s ease both; }
"""

# ── app/layout.tsx ───────────────────────────────────────────────────────────
files["app/layout.tsx"] = """\
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Agri-Insight | 배추 도매가격 예측",
  description:
    "KAMIS 도매가격 데이터 + Chronos TSFM + Gemini AI를 활용한 배추 가격 14일 예측 대시보드",
  keywords: ["배추 가격", "농산물 예측", "KAMIS", "도매가격", "AI 예측"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
"""

# ── app/page.tsx ─────────────────────────────────────────────────────────────
files["app/page.tsx"] = """\
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

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [todayData, predData] = await Promise.all([
        getTodayPrice(),
        getPrediction(historyDays),
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
  }, [historyDays]);

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
              { label: "KAMIS API", color: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" },
              { label: "Chronos-T5-small", color: "bg-purple-500/10 border-purple-500/30 text-purple-400" },
              { label: "Gemini 2.0 Flash", color: "bg-blue-500/10 border-blue-500/30 text-blue-400" },
              { label: today?.source === "mock" ? "📋 Mock 데이터" : "✅ 실시간 데이터", color: "bg-amber-500/10 border-amber-500/30 text-amber-400" },
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
                label="현재 도매가"
                value={`${prediction.summary.current_price.toLocaleString()}원`}
                sub="20kg 기준 · 서울"
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
                  <h2 className="text-lg font-semibold text-white">🥬 배추 도매가격 추이 및 예측</h2>
                  <p className="text-xs text-slate-500 mt-1">실선: 실제 가격 | 점선: Chronos 예측 | 음영: 90% 신뢰구간</p>
                </div>
                <span className="text-xs text-slate-500">단위: 원/20kg</span>
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
          <p>데이터 출처: KAMIS (한국농수산식품유통공사) · AI 모델: Chronos-T5-small, Gemini 2.0 Flash</p>
          <p className="mt-1">⚠️ 예측 결과는 참고용이며 실제 가격과 다를 수 있습니다.</p>
        </footer>
      </div>
    </div>
  );
}
"""

# 파일 생성
for rel_path, content in files.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {rel_path}")

print("\n✅ 프론트엔드 파일 생성 완료!")
