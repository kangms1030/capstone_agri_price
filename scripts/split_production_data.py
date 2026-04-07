"""
split_production_data.py
========================
Out-of-Time 검증 환경 구축을 위한 데이터 분리 스크립트.

분리 정책:
  - 테스트 품목 (TARGET_ITEMS): 품목별 마지막 379행(Context 365 + Prediction 14)만 test_data.csv로 추출.
  - 학습 데이터:
      * 테스트 품목의 마지막 379행 이전(전체 이력 - 마지막 379행) 데이터
      * 나머지 비-테스트 품목 전체 데이터
    두 가지를 합쳐서 train_data.csv로 저장. (미래 데이터 누수 완벽 차단)

사용법:
  python scripts/split_production_data.py \
      --input_csv data/final_dataset/chronos2_preprocessed_v2.csv \
      --output_dir data/production_split \
      --test_items cucumber_100ea_high mandarin_5_high_medium \
      --test_window 379
"""

import os
import argparse
import pandas as pd

# ──────────────────────────────────────────────
# 기본값 설정
# ──────────────────────────────────────────────
DEFAULT_INPUT_CSV = "data/final_dataset/chronos2_preprocessed_v2.csv"
DEFAULT_OUTPUT_DIR = "data/production_split"
DEFAULT_TEST_ITEMS = ["cucumber_100ea_high", "mandarin_5_high_medium"]
DEFAULT_TEST_WINDOW = 379  # Context(365) + Prediction(14)


def split_production_data(
    input_csv: str,
    output_dir: str,
    test_items: list[str],
    test_window: int,
) -> None:
    # ── 1. 원본 데이터 로드 ──────────────────────────────────
    print(f"\n[1/4] 원본 데이터 로드 중: {input_csv}")
    df = pd.read_csv(input_csv, parse_dates=["date"])
    df = df.sort_values(["item_id", "date"]).reset_index(drop=True)
    print(f"      → 전체 행 수: {len(df):,}  |  고유 품목 수: {df['item_id'].nunique()}")

    # ── 2. 테스트 품목 존재 여부 검증 ───────────────────────
    unknown = [it for it in test_items if it not in df["item_id"].unique()]
    if unknown:
        raise ValueError(f"다음 item_id가 데이터에 없습니다: {unknown}")

    # ── 3. 테스트/학습 분리 ────────────────────────────────
    print(f"\n[2/4] 데이터 분리 중 (테스트 품목: {test_items}, window={test_window}행)")

    test_frames = []
    train_frames = []

    for item_id, group in df.groupby("item_id"):
        group = group.sort_values("date").reset_index(drop=True)
        n = len(group)

        if item_id in test_items:
            if n < test_window:
                raise ValueError(
                    f"'{item_id}'의 행 수({n})가 test_window({test_window})보다 적습니다."
                )
            # 마지막 test_window 행 → 테스트
            test_frames.append(group.iloc[-test_window:].copy())
            # 그보다 앞에 있는 데이터 → 학습 (Past History of target items)
            past_history = group.iloc[:-test_window].copy()
            if len(past_history) > 0:
                train_frames.append(past_history)
            print(f"      [TARGET] {item_id}: train={n - test_window}행, test={test_window}행")
        else:
            # 비-테스트 품목은 전체가 학습용
            train_frames.append(group.copy())

    test_df = pd.concat(test_frames, ignore_index=True)
    train_df = pd.concat(train_frames, ignore_index=True)

    print(f"\n[3/4] 분리 결과")
    print(f"      Train: {len(train_df):,}행  |  {train_df['item_id'].nunique()}개 품목 시리즈")
    print(f"      Test : {len(test_df):,}행   |  {test_df['item_id'].nunique()}개 품목 시리즈")

    # 테스트 통계 상세
    for item_id in test_items:
        item_test = test_df[test_df["item_id"] == item_id]
        print(f"        └ {item_id}: {len(item_test)}행  "
              f"({item_test['date'].min().date()} ~ {item_test['date'].max().date()})")

    # ── 4. 저장 ───────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    train_path = os.path.join(output_dir, "train_data.csv")
    test_path = os.path.join(output_dir, "test_data.csv")

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"\n[4/4] 저장 완료")
    print(f"      Train → {train_path}")
    print(f"      Test  → {test_path}")
    print("\n[완료] Out-of-Time 데이터 분리 완료. 미래 데이터 누수 없음.")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Out-of-Time 검증을 위한 데이터 분리 스크립트")
    parser.add_argument("--input_csv",  type=str, default=DEFAULT_INPUT_CSV)
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--test_items", type=str, nargs="+", default=DEFAULT_TEST_ITEMS,
                        help="테스트용으로 분리할 품목 이름 목록 (item_id)")
    parser.add_argument("--test_window", type=int, default=DEFAULT_TEST_WINDOW,
                        help="테스트용으로 추출할 마지막 N행 (default: 379 = 365 + 14)")
    args = parser.parse_args()

    split_production_data(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        test_items=args.test_items,
        test_window=args.test_window,
    )
