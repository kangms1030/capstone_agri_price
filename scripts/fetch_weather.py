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
STATIONS = [100, 216, 261] # 100: 대관령, 216: 태백, 261: 해남
YEARS = range(2015, 2026)

if not SERVICE_KEY:
    print("⚠️ 경고: .env 파일에서 'WEATHER_API' 키를 찾을 수 없습니다.")

all_data = []

# 수집 대상 컬럼
target_columns = ['tm', 'stnId', 'avgTa', 'minTa', 'maxTa', 'sumRn', 'avgRhm', 'sumSsHr']

print("--- 기상 데이터 수집 시작 ---")

for stn in STATIONS:
    for year in YEARS:
        params = {
            'serviceKey': SERVICE_KEY,
            'dataType': 'JSON',
            'numOfRows': '999',  # 1년치(최대 366일) 일괄 조회
            'pageNo': '1',
            'dataCd': 'ASOS',    # 데이터 분류 (종관기상관측)
            'dateCd': 'DAY',     # 날짜 분류 (일자료)
            'stnIds': str(stn),
            'startDt': f'{year}0101',
            'endDt': f'{year}1231'
        }
        
        try:
            # API 호출
            response = requests.get(URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # 응답 헤더 및 결과 코드 확인
                header = data.get('response', {}).get('header', {})
                result_code = header.get('resultCode')
                
                if result_code == '00':
                    body = data.get('response', {}).get('body', {})
                    items = body.get('items', {}).get('item', [])
                    
                    if items:
                        for item in items:
                            # 타겟 컬럼만 추출, 빈 값은 빈 문자열로 처리
                            row = {col: item.get(col, '') for col in target_columns}
                            all_data.append(row)
                        print(f"✅ 수집 성공: 지점 {stn}, 연도 {year} (데이터 {len(items)}건)")
                    else:
                        print(f"⚠️ 데이터 없음: 지점 {stn}, 연도 {year}")
                else:
                    error_msg = header.get('resultMsg', 'Unknown Error')
                    print(f"❌ API 에러 (코드 {result_code}): {error_msg} - 지점 {stn}, 연도 {year}")
            else:
                print(f"❌ HTTP 에러: {response.status_code} - 지점 {stn}, 연도 {year}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 네트워크 요청 에러 - 지점 {stn}, 연도 {year}: {e}")
        except ValueError as e: # JSON Decode Error
            print(f"❌ JSON 파싱 에러 - 지점 {stn}, 연도 {year}: 서버 응답이 올바른 JSON이 아닙니다.")
        
        # API 과부하 방지용 딜레이
        time.sleep(0.5)

# 데이터 병합 및 정제
if all_data:
    df = pd.DataFrame(all_data)
    
    # sumRn(일강수량) 결측치 정제
    # 기상청 데이터의 강수량 빈칸은 '강수 없음'을 의미하므로 0으로 치환
    df['sumRn'] = df['sumRn'].replace('', '0')
    # NaN 등 결측치도 처리하기 위해 숫자로 변환 후 fillna
    df['sumRn'] = pd.to_numeric(df['sumRn'], errors='coerce').fillna(0)
    
    # 다른 숫자형 컬럼들 자료형 변환 (선택사항, 빈칸 등을 NaN으로 변환하여 분석 용이하게 함)
    numeric_cols = ['stnId', 'avgTa', 'minTa', 'maxTa', 'avgRhm', 'sumSsHr']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # 날짜 데이터 타입을 문자열 그대로 유지하거나 datetime 변환 가능
    # df['tm'] = pd.to_datetime(df['tm'])
    
    # 결과 저장 경로 지정 (backend/data/ 안)
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', 'data')
    os.makedirs(save_dir, exist_ok=True) # data 폴더 없을 경우 생성
    
    save_path = os.path.join(save_dir, 'weather_data_2015_2025.csv')
    df.to_csv(save_path, index=False, encoding='utf-8-sig') # 한글 깨짐 방지 위해 utf-8-sig
    
    print(f"\n🎉 데이터 수집 완료! 총 {len(df)}건의 데이터가 병합되었습니다.")
    print(f"📁 파일 저장 위치: {save_path}")
else:
    print("\n❌ 수집된 데이터가 없습니다. API 키나 네트워크 형태를 확인해주세요.")
