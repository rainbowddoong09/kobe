import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# 페이지 설정을 넓은 화면으로 지정
st.set_page_config(page_title="전국 고령화 단계구분도", layout="wide")

st.title("2026년 전국 시군구별 고령화율 단계구분도")


@st.cache_data
def load_data():
    # 1. 인구 데이터 로드 및 전처리
    pop_url = "https://raw.githubusercontent.com/first2022-cyber/contents//main/population_ts_yearly_gender.zip"
    df = pd.read_csv(pop_url)

    # 2026년 데이터만 필터링
    df_2026 = df[df["연도"] == 2026].copy()

    # 코드는 5자리 시군구 코드로 다루기 위해 문자열 변환 및 zfill 처리
    df_2026["sigungu_code"] = (
        df_2026["코드"].astype(str).str.zfill(8).str[:5]
    )

    # 계_로 시작하는 열 추출 (전체 인구 및 65세 이상 계산용)
    total_cols = [c for c in df_2026.columns if c.startswith("계_")]

    # 계_65세부터 계_100세 이상까지의 열 추출
    # 열 이름에서 숫자 부분만 추출하여 65세 이상 판별
    senior_cols = []
    for c in total_cols:
        age_str = c.replace("계_", "").replace("세 이상", "").replace("세", "")
        if age_str.isdigit() and int(age_str) >= 65:
            senior_cols.append(c)

    # 시군구별 인구수 합산
    df_2026["total_pop"] = df_2026[total_cols].sum(axis=1)
    df_2026["senior_pop"] = df_2026[senior_cols].sum(axis=1)

    grouped = (
        df_2026.groupby("sigungu_code")[["total_pop", "senior_pop"]]
        .sum()
        .reset_index()
    )

    # 고령화율(%) 계산
    grouped["고령화율"] = (grouped["senior_pop"] / grouped["total_pop"]) * 100
    grouped["고령화율"] = grouped["고령화율"].round(2)

    return grouped


@st.cache_data
def load_geojson():
    # 2. GeoJSON 데이터 로드
    geojson_url = "https://raw.githubusercontent.com/first2022-cyber/contents//main/sigungu_kr.geojson"
    response = requests.get(geojson_url)
    geojson_data = response.json()
    return geojson_data


# 데이터 불러오기
with st.spinner("데이터를 로드하는 중입니다..."):
    df_senior = load_data()
    geojson_data = load_geojson()

# Plotly Choropleth (단계구분도) 생성
fig = px.choropleth(
    df_senior,
    geojson=geojson_data,
    locations="sigungu_code",  # 데이터프레임의 연결 키
    featureidkey="properties.코드",  # GeoJSON의 연결 키
    color="고령화율",
    color_continuous_scale="Reds",
    range_color=(0, df_senior["고령화율"].max()),
    hover_data={"sigungu_code": False, "고령화율": ":.2f%"},
    labels={"고령화율": "고령화율 (%)"},
)

# 지도 스타일 및 호버 템플릿 설정 (타일/배경 없이 경계선만 그리기)
fig.update_geos(
    fitbounds="locations", visible=False  # 타일 지도 및 기본 지리 요소 숨김
)

fig.update_traces(
    # GeoJSON의 '시군구' 속성과 계산된 '고령화율' 표시
    hovertemplate="<b>%{properties.시도} %{properties.시군구}</b><br>고령화율: %{z:.2f}%<extra></extra>",
    marker_line_width=0.5,
    marker_line_color="gray",
)

fig.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    coloraxis_colorbar=dict(title="고령화율 (%)"),
)

# Streamlit 화면 출력
st.plotly_chart(fig, use_container_width=True)
