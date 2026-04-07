import pandas as pd
import numpy as np
import os
import glob
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
import re

def translate_item_id(item_id_kor):
    # Mapping for common terms
    mapping = {
        '감자': 'potato', '고구마': 'sweet_potato', '배추': 'cabbage', '무': 'radish',
        '양파': 'onion', '대파': 'green_onion', '오이': 'cucumber', '호박': 'pumpkin',
        '당근': 'carrot', '시금치': 'spinach', '상추': 'lettuce', '깻잎': 'perilla_leaf',
        '풋고추': 'green_chili', '토마토': 'tomato', '딸기': 'strawberry', '참외': 'melon',
        '수박': 'watermelon', '사과': 'apple', '배': 'pear', '포도': 'grape',
        '단감': 'persimmon', '귤': 'mandarin', '밤': 'chestnut', '대추': 'jujube',
        '건고추': 'dried_chili', '마늘': 'garlic', '생강': 'ginger', '쪽파': 'chive',
        '미나리': 'water_parsley', '청상추': 'green_lettuce', '적상추': 'red_lettuce',
        '취나물': 'chwinamul', '얼갈이': 'eolgari', '알배기': 'albaegi', '방울': 'cherry',
        '홍로': 'hongro', '부사': 'fuji', '신고': 'shingo', '거봉': 'kyohou',
        '고랭지': 'highland', '가을': 'autumn', '봄': 'spring', '월동': 'winter',
        '시설': 'facility', '등급': 'grade', '특': 'top', '상': 'high', '중': 'medium',
        '하': 'low', '킬로': 'kg', '그램': 'g', '포기': 'head', '망': 'net',
        '상자': 'box', '봉지': 'bag', '박스': 'box', '개': 'ea'
    }
    
    translated = item_id_kor
    for kor, eng in mapping.items():
        translated = translated.replace(kor, eng)
    
    # Replace non-alphanumeric with underscore and clean up
    translated = re.sub(r'[^a-zA-Z0-9]', '_', translated)
    translated = re.sub(r'_+', '_', translated).strip('_')
    
    # If translation didn't change anything (still has non-ascii), use a hash/id
    if any(ord(c) > 127 for c in translated):
        # Fallback for untranslated parts
        return f"item_{abs(hash(item_id_kor)) % 10000:04d}"
    
    return translated

def prepare_dataset():
    input_dir = 'data/dataset_refined'
    output_dir = 'data/final_dataset'
    os.makedirs(output_dir, exist_ok=True)

    # Use os.listdir to get raw names first to avoid corruption
    try:
        files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    except Exception as e:
        print(f"Error accessing {input_dir}: {e}")
        return

    if not files:
        print("No files found in", input_dir)
        return

    all_dfs = []
    print(f"Loading {len(files)} files...")
    
    for f_name in tqdm(files):
        f_path = os.path.join(input_dir, f_name)
        
        # Determine cleaned item_id
        # We assume the OS gives us correct Unicode if we use os.listdir
        # If it's broken in console, it might be OK in Python.
        raw_name = f_name.replace('.csv', '')
        item_id_eng = translate_item_id(raw_name)
        
        try:
            df = pd.read_csv(f_path)
            df['item_id'] = item_id_eng
            df['date'] = pd.to_datetime(df['date'])
            all_dfs.append(df)
        except Exception as e:
            print(f"Error loading {f_name}: {e}")

    # Combine into multi-series format
    print("Combining dataframes...")
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df = full_df.sort_values(['item_id', 'date']).reset_index(drop=True)

    # 1. Target Transformation (arcsinh)
    print("Applying target transformation...")
    full_df['target'] = np.arcsinh(full_df['price'])

    # 2. Feature Engineering (Lags and Rolling)
    print("Generating lag and rolling features...")
    grouped = full_df.groupby('item_id')

    for lag in [1, 3, 7, 14, 28]:
        full_df[f'price_lag_{lag}'] = grouped['target'].shift(lag)

    full_df['price_diff'] = grouped['target'].diff(1)
    full_df['price_ma7'] = grouped['target'].transform(lambda x: x.rolling(window=7).mean())
    full_df['temp_rolling_mean_7'] = grouped['temp_avg'].transform(lambda x: x.rolling(window=7).mean())

    # 3. Time-based Features (Future Covariates)
    print("Generating time-based features...")
    full_df['dayofweek'] = full_df['date'].dt.dayofweek
    full_df['weekofyear'] = full_df['date'].dt.isocalendar().week.astype(int)
    full_df['month'] = full_df['date'].dt.month

    full_df['month_sin'] = np.sin(2 * np.pi * full_df['month'] / 12)
    full_df['month_cos'] = np.cos(2 * np.pi * full_df['month'] / 12)
    full_df['dow_sin'] = np.sin(2 * np.pi * full_df['dayofweek'] / 7)
    full_df['dow_cos'] = np.cos(2 * np.pi * full_df['dayofweek'] / 7)

    # 4. Interaction Features
    print("Generating interaction features...")
    full_df['weather_index'] = full_df['temp_avg'] - full_df['humid_avg']
    full_df['rain_impact'] = full_df['rain_sum'] * full_df['temp_avg']

    # 5. Exogenous Lags
    print("Generating exogenous lags...")
    full_df['oil_diesel_lag_1'] = grouped['oil_diesel'].shift(1)
    full_df['oil_diesel_lag_3'] = grouped['oil_diesel'].shift(3)
    full_df['temp_avg_lag_1'] = grouped['temp_avg'].shift(1)
    full_df['rain_sum_lag_1'] = grouped['rain_sum'].shift(1)

    # 6. Optimization: Remove redundant columns
    print("Optimizing columns...")
    cols_to_drop = ['cpi_agri_special']
    full_df = full_df.drop(columns=[c for c in cols_to_drop if c in full_df.columns])

    # 7. Scaling (StandardScaler for numeric features except 'target')
    print("Scaling numeric features...")
    exclude_cols = ['item_id', 'date', 'target', 'price']
    numeric_cols = [col for col in full_df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(full_df[col])]
    
    full_df[numeric_cols] = full_df[numeric_cols].fillna(0)

    scaler = StandardScaler()
    full_df[numeric_cols] = scaler.fit_transform(full_df[numeric_cols])

    # Final Sort
    full_df = full_df.sort_values(['item_id', 'date'])

    # Save
    output_path = os.path.join(output_dir, 'chronos2_preprocessed_v2.csv')
    print(f"Saving final dataset to {output_path}...")
    full_df.to_csv(output_path, index=False)
    print("Done!")

if __name__ == "__main__":
    prepare_dataset()
