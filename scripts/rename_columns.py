import os
import glob
import pandas as pd

DATASET_DIR = r"C:\Users\minsoo\Desktop\capstone\data\dataset"
files = glob.glob(os.path.join(DATASET_DIR, "*.csv"))

# Column mapping
col_mapping = {
    'DATE': 'date',
    '평균가격': 'price',
    'month': 'month',
    'avgTa': 'temp_avg',
    'minTa': 'temp_min',
    'maxTa': 'temp_max',
    'temp_diff': 'temp_diff',
    'sumRn': 'rain_sum',
    'avgRhm': 'humid_avg',
    'sumSsHr': 'sunshine_sum',
    '면세유_경유': 'oil_diesel',
    '면세유_등유': 'oil_kerosene',
    '소비자물가총지수': 'cpi_total',
    '소비자물가지수채소및해조 ': 'cpi_veg_seaweed',
    '소비자물가지수(특수분류)채소': 'cpi_veg_special',
    '소비자물가지수(특수분류)농산물': 'cpi_agri_special',
    '국고채1년': 'gov_bond_1y',
    '국고채3년': 'gov_bond_3y',
    'epu': 'epu',
    '구 M2(말잔, 원계열)': 'old_m2_raw',
    '구 M2(말잔, 계절조정계열)': 'old_m2_sa',
    'M2(말잔, 계절조정계열)': 'm2_sa',
    'M2(말잔, 원계열)': 'm2_raw'
}

count = 0
for f in files:
    try:
        df = pd.read_csv(f)
        
        # Check if month is in there, if not, create it
        if 'month' not in df.columns and 'DATE' in df.columns:
            df['month'] = pd.to_datetime(df['DATE']).dt.month
        elif 'month' not in df.columns and 'date' in df.columns:
            df['month'] = pd.to_datetime(df['date']).dt.month
            
        # First rename columns to English
        rename_dict = {k: v for k, v in col_mapping.items() if k in df.columns}
        df.rename(columns=rename_dict, inplace=True)
        
        # Reorder columns: date, price, month, then others
        base_cols = []
        if 'date' in df.columns: base_cols.append('date')
        if 'price' in df.columns: base_cols.append('price')
        if 'month' in df.columns: base_cols.append('month')
        
        other_cols = [c for c in df.columns if c not in base_cols]
        df = df[base_cols + other_cols]
        
        # Save back
        df.to_csv(f, index=False, encoding='utf-8-sig')
        count += 1
    except Exception as e:
        print(f"Error processing {f}: {e}")

print(f"Successfully updated {count} files.")
