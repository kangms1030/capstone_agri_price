"""
train_chronos2_full_finetune.py
======================
Chronos-2 풀 파인튜닝(Full Fine-Tuning) & Out-of-Time 실전 추론 평가 스크립트.

Phase 1 (학습):
    train_data.csv를 읽어 풀 파인튜닝 수행 → run_YYYYMMDD_HHMMSS/final 에 저장.

Phase 2 (실전 추론 및 검증):
    저장된 모델을 다시 로드 → test_data.csv를 읽어 작물당 1회 14일 예측 수행.
    RMSE / MAE / MAPE(%) 출력 + 상하위 10~90% 예측 밴드(Prediction Band)와 함께 Matplotlib 그래프 저장.
"""

import os
import math
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tqdm import tqdm
import torch
from torch.utils.data import Dataset
from gluonts.dataset.common import ListDataset
from sklearn.metrics import mean_squared_error, mean_absolute_error

from transformers import Trainer, TrainingArguments
from chronos.chronos2.pipeline import Chronos2Pipeline as TSFMPipeline

# ==========================================
# TRAINING CONFIGURATION
# ==========================================
TRAINING_CONFIG = {
    "model_id":         "amazon/chronos-2",       # Chronos-2 베이스 모델
    "train_data_path":  "data/production_split/train_data.csv",
    "test_data_path":   "data/production_split/test_data.csv",
    "learning_rate":    5e-5,   # 풀 파인튜닝이므로 학습률을 LoRA보다 약간 낮게 설정
    "batch_size":       128,
    "context_length":   365,   # 과거 context 창
    "prediction_length": 14,   # 예측 기간
    "num_epochs":       3,
}

# ──────────────────────────────────────────
# MLOps: 타임스탬프 기반 고유 실행 폴더
# ──────────────────────────────────────────
RUN_ID          = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_BASE_DIR = f"./chronos_full_ft_output/run_{RUN_ID}"
FINAL_MODEL_DIR = f"{OUTPUT_BASE_DIR}/final"
PLOT_DIR        = f"{OUTPUT_BASE_DIR}/plots"

# ──────────────────────────────────────────────────────────────
# Covariate 컬럼 정의 (데이터 딕셔너리 기준)
# ──────────────────────────────────────────────────────────────
FUTURE_COVARIATE_COLS = [
    'month', 'temp_avg', 'rain_sum', 'humid_avg', 'sunshine_sum',
    'temp_diff', 'dayofweek', 'weekofyear', 'month_sin', 'month_cos',
    'dow_sin', 'dow_cos', 'weather_index', 'rain_impact'
]

PAST_COVARIATE_COLS = [
    'oil_diesel', 'cpi_total', 'gov_bond_3y', 'epu', 'm2_sa',
    'price_lag_1', 'price_lag_3', 'price_lag_7', 'price_lag_14',
    'price_lag_28', 'price_diff', 'price_ma7', 'temp_rolling_mean_7',
    'oil_diesel_lag_1', 'oil_diesel_lag_3', 'temp_avg_lag_1', 'rain_sum_lag_1'
]


# ==========================================
# 1. 데이터 로드 → raw_list 반환
# ==========================================
def load_and_prepare_dataset(csv_path: str) -> tuple[ListDataset, list[dict]]:
    """CSV → GluonTS ListDataset + raw_list (dict 리스트)."""
    print(f"\n[데이터 로드] {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df.sort_values(["item_id", "date"]).reset_index(drop=True)

    dataset_list = []
    print("GluonTS ListDataset 변환 중...")
    for item_id, group in tqdm(df.groupby("item_id")):
        group = group.sort_values("date").reset_index(drop=True)
        target     = group["target"].values
        start_date = group["date"].iloc[0]

        entry: dict = {"target": target, "start": start_date, "item_id": item_id}

        if all(c in group.columns for c in FUTURE_COVARIATE_COLS):
            entry["feat_dynamic_real"] = group[FUTURE_COVARIATE_COLS].values.T   # (F, T)

        if all(c in group.columns for c in PAST_COVARIATE_COLS):
            entry["past_feat_dynamic_real"] = group[PAST_COVARIATE_COLS].values.T  # (P, T)

        dataset_list.append(entry)

    gluon_dataset = ListDataset(dataset_list, freq="D")
    return gluon_dataset, dataset_list


# ==========================================
# 2. Phase 1: Full Fine-tuning
# ==========================================
from chronos.chronos2.dataset import Chronos2Dataset, DatasetMode

def train_model(model, raw_list: list[dict]):
    """train_data.csv의 raw_list를 받아 Transformers Trainer로 풀 파인튜닝."""
    print("\n[Phase 1] Transformers Trainer 기반 풀 파인튜닝 시작...")

    # Chronos-2 전용 학습 포맷 변환
    chronos2_train_inputs = []
    for ts_data in raw_list:
        past_covariates   = {}
        future_covariates = {}

        if "past_feat_dynamic_real" in ts_data:
            for i, row in enumerate(ts_data["past_feat_dynamic_real"]):
                past_covariates[f"past_only_cov_{i}"] = row

        if "feat_dynamic_real" in ts_data:
            for i, row in enumerate(ts_data["feat_dynamic_real"]):
                key = f"future_known_cov_{i}"
                past_covariates[key]   = row
                future_covariates[key] = []  # Chronos-2 파서 태그

        chronos2_train_inputs.append({
            "target":            ts_data["target"],
            "past_covariates":   past_covariates,
            "future_covariates": future_covariates,
        })

    output_patch_size = getattr(model.config, "output_patch_size", 64)
    train_dataset = Chronos2Dataset(
        inputs=chronos2_train_inputs,
        context_length=TRAINING_CONFIG["context_length"],
        prediction_length=TRAINING_CONFIG["prediction_length"],
        batch_size=TRAINING_CONFIG["batch_size"],
        output_patch_size=output_patch_size,
        min_past=1,
        mode=DatasetMode.TRAIN,
        convert_inputs=True,
    )

    training_args = TrainingArguments(
        output_dir=OUTPUT_BASE_DIR,
        max_steps=10000,
        per_device_train_batch_size=1,
        learning_rate=TRAINING_CONFIG["learning_rate"],
        logging_dir=f"{OUTPUT_BASE_DIR}/logs",
        logging_steps=10,
        save_strategy="steps",
        save_steps=2500,        # 2500 스텝마다 체크포인트 저장
        fp16=True,
        report_to="none",
        remove_unused_columns=False,
    )

    def dummy_data_collator(features):
        return features[0]

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=dummy_data_collator,
    )

    print("🚀 학습 시작 (Full Fine-tuning)...")
    trainer.train()

    os.makedirs(FINAL_MODEL_DIR, exist_ok=True)
    trainer.model.save_pretrained(FINAL_MODEL_DIR)
    print(f"\n✅ 학습 완료. 모델 저장 → {FINAL_MODEL_DIR}")
    return trainer.model


# ==========================================
# 3. Phase 2: Out-of-Time 실전 추론 평가
# ==========================================
def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Percentage Error (%)."""
    mask = actual != 0
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100


def production_evaluate(pipeline, test_raw_list: list[dict]) -> None:
    """
    테스트 품목별로 딱 1회(14일) 추론을 수행.
    Input 구성:
        target              : 앞쪽 365일 (과거)
        past_covariates     : 앞쪽 365일 (과거 공변량)
        future_covariates   : 전체 379일 (미래 시점까지 아는 달력/날씨 등)
    """
    context_length   = TRAINING_CONFIG["context_length"]   # 365
    prediction_length = TRAINING_CONFIG["prediction_length"]  # 14

    os.makedirs(PLOT_DIR, exist_ok=True)

    print("\n" + "=" * 60)
    print("[Phase 2] Out-of-Time 실전 추론 평가")
    print("=" * 60)

    summary_rows = []

    for ts_data in test_raw_list:
        item_id     = ts_data["item_id"]
        full_target = ts_data["target"]  # 379행

        if len(full_target) < context_length + prediction_length:
            print(f"  ⚠ [{item_id}] 데이터 길이 부족 ({len(full_target)}행), SKIP.")
            continue

        # ── Context(과거 365일) / Ground-Truth(미래 14일) 분리 ──────────
        context_arcsinh = full_target[:context_length]          # [365]
        actuals_arcsinh = full_target[context_length:]          # [14]

        # ── pred_input 구성 (API 서빙 모의) ──────────────────────────────
        pred_input = {"target": context_arcsinh}

        past_cov_dict   = {}
        future_cov_dict = {}

        # Future-Known Covariates: 과거 365일(past) + 미래 14일(future) 모두 주입
        if "feat_dynamic_real" in ts_data:
            full_fdc = ts_data["feat_dynamic_real"]  # (F, 379)
            for i in range(full_fdc.shape[0]):
                key = f"future_known_cov_{i}"
                past_cov_dict[key]   = full_fdc[i, :context_length]   # 과거 365
                future_cov_dict[key] = full_fdc[i, context_length:]    # 미래 14

        # Past-Only Covariates: 과거 365일만 주입
        if "past_feat_dynamic_real" in ts_data:
            past_arr = ts_data["past_feat_dynamic_real"]  # (P, 379)
            for i in range(past_arr.shape[0]):
                past_cov_dict[f"past_only_cov_{i}"] = past_arr[i, :context_length]

        if past_cov_dict:
            pred_input["past_covariates"] = past_cov_dict
        if future_cov_dict:
            pred_input["future_covariates"] = future_cov_dict

        # ── 추론 ──────────────────────────────────────────────────────────
        forecast_result = pipeline.predict(
            [pred_input],
            prediction_length=prediction_length,
        )
        forecast_obj      = list(forecast_result)[0]
        
        # 샘플들에서 중앙값 및 상/하위(10%, 90%) 밴드 추출
        forecast_samples = forecast_obj.numpy()[0]
        
        forecast_arcsinh  = np.median(forecast_samples, axis=0)  # [14]
        lower_arcsinh = np.percentile(forecast_samples, 10, axis=0) # [14]
        upper_arcsinh = np.percentile(forecast_samples, 90, axis=0) # [14]

        # ── Arcsinh 역변환 ────────────────────────────────────────────────
        actuals_real  = np.sinh(actuals_arcsinh)
        forecast_real = np.sinh(forecast_arcsinh)
        lower_real    = np.sinh(lower_arcsinh)
        upper_real    = np.sinh(upper_arcsinh)

        # ── 지표 계산 ─────────────────────────────────────────────────────
        rmse = math.sqrt(mean_squared_error(actuals_real, forecast_real))
        mae  = mean_absolute_error(actuals_real, forecast_real)
        mape_val = mape(actuals_real, forecast_real)

        print(f"\n  [{item_id}]")
        print(f"    RMSE : {rmse:.2f}")
        print(f"    MAE  : {mae:.2f}")
        print(f"    MAPE : {mape_val:.2f}%")
        summary_rows.append({"item_id": item_id, "RMSE": rmse, "MAE": mae, "MAPE(%)": mape_val})

        # ── Matplotlib 그래프 저장 ────────────────────────────────────────
        # 과거 30일 실제 가격(회색) / 미래 14일 실제(초록) / 예측(빨강 점선) 및 예측 밴드
        past_30_arcsinh = full_target[context_length - 30: context_length]
        past_30_real    = np.sinh(past_30_arcsinh)

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.set_title(f"Out-of-Time Forecast (Full Fine-tuning): {item_id}", fontsize=13, fontweight="bold")

        past_x    = range(-30, 0)
        future_x  = range(0, prediction_length)

        ax.plot(past_x,   past_30_real,  color="gray",  linewidth=1.8, label="Past (30d actual)")
        ax.plot(future_x, actuals_real,  color="green", linewidth=2.0, marker="o", markersize=4, label="Future (actual)")
        ax.plot(future_x, forecast_real, color="red",   linewidth=2.0, linestyle="--", marker="x", markersize=5, label="Forecast (predicted)")
        
        # 10~90% 예측 밴드 색칠
        ax.fill_between(future_x, lower_real, upper_real, color="red", alpha=0.15, label="Prediction Band (10~90%)")

        ax.axvline(0, color="black", linewidth=1.0, linestyle=":")
        ax.set_xlabel("Days (0 = forecast origin)")
        ax.set_ylabel("Price (KRW)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 지표 텍스트 박스
        stats_txt = f"RMSE={rmse:.1f}  MAE={mae:.1f}  MAPE={mape_val:.1f}%"
        ax.text(0.02, 0.96, stats_txt, transform=ax.transAxes,
                fontsize=9, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

        plt.tight_layout()
        plot_path = os.path.join(PLOT_DIR, f"forecast_{item_id}.png")
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"    그래프 저장 → {plot_path}")

    # ── 전체 요약 ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("[평가 요약]")
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        print(summary_df.to_string(index=False))
        summary_path = os.path.join(OUTPUT_BASE_DIR, "evaluation_summary.csv")
        summary_df.to_csv(summary_path, index=False)
        print(f"\n전체 평균 RMSE : {summary_df['RMSE'].mean():.2f}")
        print(f"전체 평균 MAE  : {summary_df['MAE'].mean():.2f}")
        print(f"전체 평균 MAPE : {summary_df['MAPE(%)'].mean():.2f}%")
        print(f"\n요약 CSV 저장 → {summary_path}")
    print("=" * 60)


# ==========================================
# main
# ==========================================
def main():
    print(f"\n{'=' * 60}")
    print(f" Chronos-2 풀 파인튜닝 + Out-of-Time 평가 (Prediction Band)")
    print(f" RUN_ID: {RUN_ID}")
    print(f"{'=' * 60}")

    # ── Phase 1: 학습 ────────────────────────────────────────
    print(f"\n[Phase 1] 학습 데이터 로드: {TRAINING_CONFIG['train_data_path']}")
    _, train_raw_list = load_and_prepare_dataset(TRAINING_CONFIG["train_data_path"])

    print(f"\n기저 파이프라인 로드 → {TRAINING_CONFIG['model_id']}")
    base_pipeline = TSFMPipeline.from_pretrained(
        TRAINING_CONFIG["model_id"],
        device_map="auto",
        torch_dtype=torch.float32,
    )
    model = base_pipeline.model

    model = train_model(model, train_raw_list)

    # ── Phase 2: 저장된 모델 재로드 → 실전 추론 ─────────────
    print(f"\n[Phase 2] 저장된 모델 재로드: {FINAL_MODEL_DIR}")
    pipeline = TSFMPipeline.from_pretrained(
        FINAL_MODEL_DIR,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    pipeline.model.eval()

    print(f"테스트 데이터 로드: {TRAINING_CONFIG['test_data_path']}")
    _, test_raw_list = load_and_prepare_dataset(TRAINING_CONFIG["test_data_path"])

    production_evaluate(pipeline, test_raw_list)

    print(f"\n🏁 전체 파이프라인 완료. 결과 폴더: {OUTPUT_BASE_DIR}")


if __name__ == "__main__":
    main()
