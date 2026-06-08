import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. 페이지 기본 설정 (가장 먼저 호출되어야 함) ---
st.set_page_config(page_title="지진 위험도 분석", page_icon="🌍", layout="wide")

# 데이터 불러오기 (캐싱을 적용하여 속도 최적화)
@st.cache_data
def load_data():
    return pd.read_csv("earthquake.csv")

try:
    df_new = load_data()
except FileNotFoundError:
    st.error("earthquake.csv 파일을 찾을 수 없습니다. 실행 경로를 확인해주세요.")
    st.stop()

# 위험도 사전 및 군집 색상
risk_dict = {0: '높음', 1: '낮음', 2: '중간'}
colors = {0: 'red', 1: 'blue', 2: 'green'}

# --- 2. 메인 화면 헤더 ---
st.title("🌍 세계 지진 위험도 분석 시스템")
st.markdown("**위도와 경도를 입력하면 주변 지진 데이터를 기반으로 위험도를 분석해 드립니다.**")
st.divider()

# --- 3. 사이드바 (사용자 입력 영역) ---
with st.sidebar:
    st.header("📍 위치 입력")
    st.info("분석을 원하는 지역의 좌표를 입력하세요.")
    
    lat = st.number_input("위도 (Latitude)", value=37.5, step=0.1)
    lon = st.number_input("경도 (Longitude)", value=127.0, step=0.1)
    
    st.markdown("<br>", unsafe_allow_html=True) # 시각적 여백
    analyze_btn = st.button("🚨 위험도 분석 실행", use_container_width=True)
    
    st.divider()
    st.markdown("### 🎨 지도 범례")
    st.markdown("- 🔴 **위험도 높음**\n- 🟢 **위험도 중간**\n- 🔵 **위험도 낮음**")

# --- 4. 메인 화면 (결과 출력 영역) ---
if analyze_btn:
    # 주변 지진 찾기
    near_df = df_new[
        (df_new['위도'] >= lat - 5) &
        (df_new['위도'] <= lat + 5) &
        (df_new['경도'] >= lon - 5) &
        (df_new['경도'] <= lon + 5)
    ]

    # 주변 데이터가 없는 경우
    if len(near_df) == 0:
        st.warning("⚠️ 지정하신 반경 내에 기록된 주변 지진 데이터가 없습니다.")
    else:
        # 군집 비율 계산 및 가장 많은 군집 추출
        cluster_ratio = near_df['cluster'].value_counts(normalize=True)
        main_cluster = cluster_ratio.idxmax()
        
        # 화면을 두 개의 컬럼으로 분할 (1:3 비율)
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("분석 결과")
            # 핵심 지표를 강조하는 UI
            st.metric(label="예상 위험도", value=risk_dict[main_cluster])
            st.caption(f"분석에 사용된 주변 지진: **{len(near_df)}** 건")
            
        with col2:
            # 지도 생성
            m = folium.Map(location=[lat, lon], zoom_start=5, tiles="CartoDB positron")

            # 데이터 샘플링 (전체 데이터가 500개 미만일 경우 오류 방지)
            sample_size = min(len(df_new), 500)
            df_sample = df_new.sample(sample_size, random_state=42)

            # 지도에 점 표시
            for i in range(len(df_sample)):
                cluster = df_sample.iloc[i]['cluster']
                folium.CircleMarker(
                    location=[df_sample.iloc[i]['위도'], df_sample.iloc[i]['경도']],
                    radius=df_sample.iloc[i]['규모'],
                    color=colors[cluster],
                    fill=True,
                    fill_color=colors[cluster],
                    fill_opacity=0.7
                ).add_to(m)

            # 사용자 위치 표시 (아이콘 스타일 변경)
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup("입력 위치", max_width=100),
                icon=folium.Icon(color='black', icon='star', prefix='fa')
            ).add_to(m)

            # 스트림릿에 지도 출력 (컬럼 너비에 맞춰 반응형으로 작동하도록 width 제한 해제)
            st_folium(m, width=800, height=500, returned_objects=[])
else:
    # 최초 접속 시 안내 문구
    st.info("👈 좌측 사이드바에서 위도와 경도를 설정한 후 '위험도 분석 실행' 버튼을 눌러주세요.")