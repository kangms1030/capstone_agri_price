import os
import pandas as pd
import glob
import re
from datetime import datetime

# --- CONFIGURATION (Paths) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

AGRI_PRICE_DIR = r"G:\내 드라이브\캡스톤_민간인\data\농넷 데이터\agri_price"
CROP_REGION_FILE = r"G:\내 드라이브\캡스톤_민간인\data\농넷 데이터\작물_주산지.txt"
ECO_VAR_DIR = r"G:\내 드라이브\캡스톤_민간인\data\경제변수"
OIL_PRICE_FILE = os.path.join(PROJECT_ROOT, "backend", "data", "주유소_제품별_면세유평균판매가격.csv")
WEATHER_ALL_FILE = os.path.join(PROJECT_ROOT, "backend", "data", "weather_all_2015_2025.csv")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "dataset")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Station Map
STATION_MAP = {
    '제주시': 184, '서귀포시': 189, '평창군': 100, '정선군': 214,
    '해남군': 261, '무안군': 165, '금산군': 238, '밀양시': 288,
    '진주시': 192, '창녕군': 288,  # 창녕은 밀양 인접으로 대체
    '서산시': 129, '태안군': 129,  # 태안은 서산 인접
    '고흥군': 262, '진도군': 175, '신안군': 165,  # 신안 목포(165) 인접
    '나주시': 156, '천안시': 232, '태백시': 216,
    '남양주시': 108, '이천시': 203, '포천시': 98,
    '음성군': 131, '청송군': 276, '안동시': 136,
    '김포시': 112, '봉화군': 271, '김제시': 146,
    '영양군': 276, '보은군': 226, '상주시': 137, '제주특별자치도 제주시': 184
}

# --- 1. Load Crop Setup ---
crop_to_stations = {}
with open(CROP_REGION_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # e.g., "감귤: 제주시, 서귀포시"
        parts = line.split(':')
        if len(parts) == 2:
            crop = parts[0].strip()
            regions = [r.strip() for r in parts[1].split(',')]
            stns = []
            for r in regions:
                if r in STATION_MAP:
                    stns.append(STATION_MAP[r])
            if stns:
                crop_to_stations[crop] = list(set(stns))

# --- 2. Load and Prepare Weather Data ---
print(">> 기상 데이터 로딩 중...")
df_wthr = pd.read_csv(WEATHER_ALL_FILE)
df_wthr['tm'] = pd.to_datetime(df_wthr['tm']).dt.normalize()
# Numeric conversions
for col in ['avgTa', 'minTa', 'maxTa', 'sumRn', 'avgRhm', 'sumSsHr']:
    df_wthr[col] = pd.to_numeric(df_wthr[col], errors='coerce').fillna(0)

def get_crop_weather(crop_name):
    if crop_name not in crop_to_stations:
        return None
    stn_ids = crop_to_stations[crop_name]
    # Filter weather data for these stations
    df_c = df_wthr[df_wthr['stnId'].isin(stn_ids)]
    if df_c.empty:
        return None
    # Group by date with specific aggregation rules for extremes
    df_agg = df_c.groupby('tm', as_index=False).agg({
        'avgTa': 'mean',
        'minTa': 'min',     # 주산지 중 가장 추운 온도
        'maxTa': 'max',     # 주산지 중 가장 더운 온도
        'sumRn': 'mean',
        'avgRhm': 'mean',
        'sumSsHr': 'mean'
    })
    df_agg.rename(columns={'tm': 'DATE'}, inplace=True)
    # 일교차 파생변수 생성
    df_agg['temp_diff'] = df_agg['maxTa'] - df_agg['minTa']
    return df_agg

# --- 3. Load and Prepare Economic Variables ---
print(">> 경제 변수 로딩 및 병합 중...")
eco_dfs = []
for root, dirs, files in os.walk(ECO_VAR_DIR):
    for f in files:
        if f.endswith('선형보간.xlsx'):
            path = os.path.join(root, f)
            try:
                # Read first and second column
                df_e = pd.read_excel(path, usecols=[0, 1])
                # Date format is usually missing string or datetime. Force datetime
                date_col = df_e.columns[0]
                val_col = df_e.columns[1]
                df_e['DATE'] = pd.to_datetime(df_e[date_col], errors='coerce').dt.normalize()
                
                # Cleanup column name dynamically from filename
                col_name_cleaned = f.replace('_선형보간.xlsx', '').replace('_일별', '')
                df_e = df_e[['DATE', val_col]].rename(columns={val_col: col_name_cleaned})
                df_e.dropna(subset=['DATE'], inplace=True) # Drop invalid dates
                eco_dfs.append(df_e)
            except Exception as e:
                print(f"Failed to read {f}: {e}")

if eco_dfs:
    # Build complete Date range from eco
    df_eco = eco_dfs[0]
    for i in range(1, len(eco_dfs)):
        df_eco = pd.merge(df_eco, eco_dfs[i], on='DATE', how='outer')
else:
    df_eco = pd.DataFrame(columns=['DATE'])

# --- 4. Load and Prepare Oil Data ---
print(">> 유가 데이터 로딩 중...")
df_oil = pd.read_csv(OIL_PRICE_FILE, encoding='cp949')
date_col = df_oil.columns[0] # Usually '구분'
col_diesel = df_oil.columns[1]  # '자동차용경유'
col_kerosene = df_oil.columns[2]  # '실내등유'

# Reformat string dates "2015년11월16일" to datetime
def parse_korean_date(d_str):
    if pd.isna(d_str): return pd.NaT
    d_str = str(d_str).replace('년', '-').replace('월', '-').replace('일', '')
    try:
        return pd.to_datetime(d_str).normalize()
    except:
        return pd.NaT

df_oil['DATE'] = df_oil[date_col].apply(parse_korean_date)
df_oil = df_oil[['DATE', col_diesel, col_kerosene]].rename(columns={
    col_diesel: '면세유_경유', 
    col_kerosene: '면세유_등유'
})
df_oil.dropna(subset=['DATE'], inplace=True)
df_oil = df_oil.groupby('DATE').mean().reset_index() # To handle any dups

# Setup Cutoff Date
CUTOFF_DATE = pd.to_datetime('2015-11-16')

# --- 5. Merge loop over Agri_Price files ---
print(">> 농넷 데이터 파일 순회 및 병합 시작...")

agri_files = glob.glob(os.path.join(AGRI_PRICE_DIR, "*.csv"))

success_count = 0

for filepath in agri_files:
    filename = os.path.basename(filepath)
    # Extract short crop name: "감귤_3키로상자_상.csv" => "감귤"
    crop_name = filename.split('_')[0]
    
    try:
        # Load price data
        df_agri = pd.read_csv(filepath)
        df_agri['DATE'] = pd.to_datetime(df_agri['DATE'], errors='coerce').dt.normalize()
        df_agri.dropna(subset=['DATE'], inplace=True)
        
        # Merge Weather
        df_weather = get_crop_weather(crop_name)
        if df_weather is not None:
            df_merged = pd.merge(df_agri, df_weather, on='DATE', how='left')
        else:
            # If no weather, just dummy columns with NaN
            df_merged = df_agri.copy()
            for wcol in ['avgTa', 'minTa', 'maxTa', 'sumRn', 'avgRhm', 'sumSsHr', 'temp_diff']:
                df_merged[wcol] = pd.NA
                
        # Merge Oil
        df_merged = pd.merge(df_merged, df_oil, on='DATE', how='left')
        
        # Merge Eco
        if not df_eco.empty:
            df_merged = pd.merge(df_merged, df_eco, on='DATE', how='left')
            
        # 1-day Forward fill strategy for eco & oil to cover weekends if missing
        df_merged.sort_values('DATE', inplace=True)
        # Interpolate missing values for columns
        cols_to_fill = [c for c in df_merged.columns if c not in ['DATE']]
        df_merged[cols_to_fill] = df_merged[cols_to_fill].ffill()
        
        # Filter cutoff date
        df_merged = df_merged[df_merged['DATE'] >= CUTOFF_DATE]
        
        # --- Add Month and Rename Columns to English ---
        df_merged['month'] = df_merged['DATE'].dt.month
        
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
        
        # Rename only existing columns to prevent KeyError
        rename_dict = {k: v for k, v in col_mapping.items() if k in df_merged.columns}
        df_merged.rename(columns=rename_dict, inplace=True)
        
        # Reorder columns: date, price, month, then others
        base_cols = ['date', 'price', 'month']
        other_cols = [c for c in df_merged.columns if c not in base_cols]
        df_merged = df_merged[base_cols + other_cols]
        
        # Save output
        out_path = os.path.join(OUTPUT_DIR, filename)
        df_merged.to_csv(out_path, index=False, encoding='utf-8-sig')
        success_count += 1
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")

print(f"✅ 처리가 완료되었습니다. {success_count} / {len(agri_files)} 파일 생성 완료.")
print(f"📁 결과물 저장 경로: {OUTPUT_DIR}")
