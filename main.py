import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------
# 1. 페이지 설정 및 디자인 (따뜻한 톤)
# ----------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="centered"
)

# 따뜻한 톤을 위한 커스텀 CSS 적용
st.markdown("""
    <style>
    .main {
        background-color: #FAF7F2;
    }
    h1 {
        color: #4A3E3D;
        font-family: 'Malgun Gothic', sans-serif;
    }
    .stSelectbox label {
        color: #5C4B49 !important;
        font-weight: bold;
    }
    .desc-box {
        background-color: #FFF8F0;
        border-left: 5px solid #FF8882;
        padding: 15px;
        border-radius: 8px;
        font-size: 16px;
        color: #4A3E3D;
        margin-top: 15px;
        line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption("전국 읍·면·동의 최신 인구 구조를 연령별·성별로 한눈에 확인해보세요.")

# ----------------------------------------------------
# 2. 데이터 불러오기 (캐싱 적용으로 속도 향상)
# ----------------------------------------------------
DATA_URL = "https://raw.githubusercontent.com/first2022-cyber/contents/main/population_ts_yearly_gender.zip"

@st.cache_data
def load_data():
    # 판다스로 zip 압축 파일 형태의 CSV를 직접 로드
    df = pd.read_csv(DATA_URL)
    
    # 최신 연도 데이터만 추출
    max_year = df['연도'].max()
    latest_df = df[df['연도'] == max_year].copy()
    
    return latest_df, max_year

# 데이터 로딩
df_latest, latest_year = load_data()

st.info(f"💡 현재 표시되는 데이터는 **{latest_year}년** 기준 최신 인구 데이터입니다.")

# ----------------------------------------------------
# 3. 시도 -> 시군구 -> 동 3단계 드롭다운 선택기
# ----------------------------------------------------
st.subheader("📍 지역 선택")

col1, col2, col3 = st.columns(3)

# 1) 시도 선택
sido_list = sorted(df_latest['시도'].dropna().unique())
with col1:
    selected_sido = st.selectbox("시·도 선택", sido_list)

# 선택된 시도에 맞는 시군구 목록 추출
df_sido = df_latest[df_latest['시도'] == selected_sido]
sigungu_list = sorted(df_sido['시군구'].dropna().unique())

# 2) 시군구 선택
with col2:
    selected_sigungu = st.selectbox("시·군·구 선택", sigungu_list)

# 선택된 시군구에 맞는 동 목록 추출
df_sigungu = df_sido[df_sido['시군구'] == selected_sigungu]
dong_list = sorted(df_sigungu['동'].dropna().unique())

# 3) 동 선택
with col3:
    selected_dong = st.selectbox("읍·면·동 선택", dong_list)

# ----------------------------------------------------
# 4.
