import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# 페이지 설정을 넓은 화면으로 지정
st.set_page_config(
    page_title="시군구별 연령별 인구비율 단계구분도", layout="wide"
)

st.title("전국 시군구별 인구 지표 단계구분도")


@st.cache_data
def load_and_preprocess_data():
    # 1. 인구 데이터 로드
    pop_url = "https://raw.githubusercontent.com/first2022-cyber/contents//main/population_ts_yearly_gender.zip"
    df = pd.read_csv(pop_url)

    # 행정구역 개편 코드 보정 함수
    def fix_sigungu_code(code_str):
        code_str = str(code_str).zfill(8)[:5]
        # 옛 시도 코드 변경: 42 -> 51(강원), 45 -> 52(전북)
        if code_str.startswith("42"):
            code_str = "51" + code_str[2:]
        elif code_str.startswith("45"):
            code_str = "52" + code_str[2:]
        # 군위군 코드 변경: 47720 -> 27720
        if code_str == "47720":
            code_str = "27720"
        return code_str

    df["sigungu_code"] = df["코드"].apply(fix_sigungu_code)

    # 연령별 컬럼 분류
    total_cols = [c for c in df.columns if c.startswith("계_")]

    youth_cols = []  # 0~14세
    senior_cols = []  # 65세 이상

    for c in total_cols:
        age_str = c.replace("계_", "").replace("세 이상", "").replace("세", "")
        if age_str.isdigit():
            age = int(age_str)
            if 0 <= age <= 14:
                youth_cols.append(c)
            elif age >= 65:
                senior_cols.append(c)

    # 행별 합계 계산
    df["total_pop"] = df[total_cols].sum(axis=1)
    df["youth_pop"] = df[youth_cols].sum(axis=1)
    df["senior_pop"] = df[senior_cols].sum(axis=1)

    # 연도 및 시군구별 그룹화
    grouped = (
        df.groupby(["연도", "sigungu_code"])[
            ["total_pop", "youth_pop", "senior_pop"]
        ]
        .sum()
        .reset_index()
    )

    # 비율 계산 (%)
    grouped["고령화율"] = (
        grouped["senior_pop"] / grouped["total_pop"]
    ) * 100
    grouped["유소년 비율"] = (
        grouped["youth_pop"] / grouped["total_pop"]
    ) * 100

    return grouped


@st.cache_data
def load_geojson():
    # GeoJSON 데이터 로드
    geojson_url = "https://raw.githubusercontent.com/first2022-cyber/contents//main/sigungu_kr.geojson"
    response = requests.get(geojson_url)
    geojson_data = response.json()

    # 시도 이름 및 코드 매핑 정보 생성
    sido_map = {}
    for feature in geojson_data["features"]:
        props = feature["properties"]
        sido_code = props["코드"][:2]
        sido_name = props["시도"]
        sido_map[sido_code] = sido_name

    return geojson_data, sido_map


# 데이터 불러오기
with st.spinner("데이터를 로드하는 중입니다..."):
    df_all = load_and_preprocess_data()
    geojson_data, sido_map = load_geojson()

# --- 사이드바 컨트롤 영역 ---
st.sidebar.header("조회
