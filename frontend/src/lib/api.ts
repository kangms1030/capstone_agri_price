import axios from "axios";
import { PredictionResponse, TodayPrice } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 120000, // Chronos 모델 로딩 시간 고려
});

export async function getTodayPrice(date?: string, market: string = "1101", grade: string = "상"): Promise<TodayPrice> {
  const { data } = await api.get("/api/price/today", {
    params: { date, market, grade },
  });
  return data;
}

export async function getPrediction(historyDays = 90, grade: string = "상"): Promise<PredictionResponse> {
  const { data } = await api.get("/api/predict", {
    params: { history_days: historyDays, grade },
  });
  return data;
}
