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
