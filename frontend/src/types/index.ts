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
