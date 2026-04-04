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
