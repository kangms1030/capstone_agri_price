import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 스크립트 실행 경로 기준 /backend 디렉토리의 .env 파일을 불러옴
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', '.env')
load_dotenv(env_path)

# .env 파일에서 기상청 API 키 읽어오기
SERVICE_KEY = os.getenv('WEATHER_API')

URL = 'http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList'
# 매핑 딕셔너리 구성 (지역명 -> 대표 ASOS 지점 번호)
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
    '영양군': 276,  # 영양은 청송 인접
    '보은군': 226, '상주시': 137, '제주특별자치도 제주시': 184
}

UNIQUE_STATIONS = list(set(STATION_MAP.values()))
YEARS = range(2015, 2026)

if not SERVICE_KEY:
    print("⚠️ 경고: .env 파일에서 'WEATHER_API' 키를 찾을 수 없습니다.")

all_data = []

# 수집 대상 컬럼
target_columns = ['tm', 'stnId', 'avgTa', 'minTa', 'maxTa', 'sumRn', 'avgRhm', 'sumSsHr']

# 이미 수집된 데이터가 있다면 그 지점/연도는 패스하기 위해 체크
save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', 'data')
os.makedirs(save_dir, exist_ok=True)
save_path = os.path.join(save_dir, 'weather_all_2015_2025.csv')

existing_df = None
if os.path.exists(save_path):
    existing_df = pd.read_csv(save_path)
    existing_df['stnId'] = existing_df['stnId'].astype(int)
    existing_df['year'] = pd.to_datetime(existing_df['tm']).dt.year

print(f"--- 기상 데이터 수집 시작 (총 {len(UNIQUE_STATIONS)}개 관측소) ---")

needs_save = False

for stn in UNIQUE_STATIONS:
    for year in YEARS:
        # 이미 수집된지 확인
        if existing_df is not None:
            if not existing_df[(existing_df['stnId'] == stn) & (existing_df['year'] == year)].empty:
                print(f"⏭️ 스킵: 지점 {stn}, 연도 {year} (이미 존재함)")
                continue

        params = {
            'serviceKey': SERVICE_KEY,
            'dataType': 'JSON',
            'numOfRows': '366',  
            'pageNo': '1',
            'dataCd': 'ASOS',    
            'dateCd': 'DAY',     
            'stnIds': str(stn),
            'startDt': f'{year}0101',
            'endDt': f'{year}1231'
        }
        
        try:
            response = requests.get(URL, params=params, verify=False, timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    header = data.get('response', {}).get('header', {})
                    result_code = header.get('resultCode')
                    
                    if result_code == '00':
                        body = data.get('response', {}).get('body', {})
                        items = body.get('items', {}).get('item', [])
                        
                        if items:
                            for item in items:
                                row = {col: item.get(col, '') for col in target_columns}
                                all_data.append(row)
                            print(f"✅ 수집 성공: 지점 {stn}, 연도 {year} (데이터 {len(items)}건)")
                            needs_save = True
                        else:
                            print(f"⚠️ 데이터 없음: 지점 {stn}, 연도 {year}")
                    else:
                        error_msg = header.get('resultMsg', 'Unknown Error')
                        print(f"❌ API 에러 (코드 {result_code}): {error_msg} - 지점 {stn}")
                except Exception as e:
                    print(f"JSON 파싱 에러 - 지점 {stn}: {e}")
            else:
                print(f"❌ HTTP 에러: {response.status_code} - 지점 {stn}")
        except Exception as e:
            print(f"❌ 요청 에러 - 지점 {stn}: {e}")
            
        time.sleep(0.1)  # API Threshold 

if needs_save and all_data:
    new_df = pd.DataFrame(all_data)
    new_df['sumRn'] = pd.to_numeric(new_df['sumRn'].replace('', '0'), errors='coerce').fillna(0)
    for col in ['stnId', 'avgTa', 'minTa', 'maxTa', 'avgRhm', 'sumSsHr']:
        new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
        
    if existing_df is not None:
        final_df = pd.concat([existing_df.drop(columns=['year'], errors='ignore'), new_df], ignore_index=True)
    else:
        final_df = new_df
        
    # 중복제거
    final_df = final_df.drop_duplicates(subset=['tm', 'stnId'])
    final_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n🎉 업데이트 저장 완료! 최종 데이터 수: {len(final_df)}건")
else:
    print("\n✅ 모두 수집되어 있거나 추가할 새 데이터가 없습니다.")
