
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
st.sidebar.header("조회 옵션")

# 1. 지표 선택
metric_option = st.sidebar.selectbox(
    "지표 선택",
    ["65세 이상 비율 (고령화율)", "0~14세 비율 (유소년 비율)"],
)
is_senior = "65세" in metric_option
target_col = "고령화율" if is_senior else "유소년 비율"

# 2. 연도 선택 슬라이더
available_years = sorted(df_all["연도"].unique())
min_year, max_year = int(min(available_years)), int(max(available_years))
selected_year = st.sidebar.slider(
    "연도 선택", min_value=min_year, max_value=max_year, value=max_year, step=1
)

# 3. 시도 선택 드롭다운
sido_options = ["전국"] + sorted(list(set(sido_map.values())))
selected_sido = st.sidebar.selectbox("지역 선택 (시도)", sido_options)

# --- 데이터 필터링 ---
df_year = df_all[df_all["연도"] == selected_year].copy()

# 시도명 매핑 추가 (sigungu_code 앞 2자리 활용)
df_year["시도코드"] = df_year["sigungu_code"].str[:2]
df_year["시도명"] = df_year["시도코드"].map(sido_map)

# GeoJSON에 존재하지 않는 미매칭 지역 확인
geojson_codes = set(
    f["properties"]["코드"] for f in geojson_data["features"]
)
unmatched_df = df_year[~df_year["sigungu_code"].isin(geojson_codes)]

# 시도 필터 적용
if selected_sido != "전국":
    df_filtered = df_year[df_year["시도명"] == selected_sido].copy()
    filtered_features = [
        f
        for f in geojson_data["features"]
        if f["properties"]["시도"] == selected_sido
    ]
    current_geojson = {
        "type": "FeatureCollection",
        "features": filtered_features,
    }
else:
    df_filtered = df_year.copy()
    current_geojson = geojson_data

# --- 상단 핵심 지표 카드 (Metric Cards) ---
col1, col2, col3 = st.columns(3)

# 전국 평균 비율 계산
nat_total_pop = df_year["total_pop"].sum()
nat_target_pop = (
    df_year["senior_pop"].sum() if is_senior else df_year["youth_pop"].sum()
)
nat_rate = (
    (nat_target_pop / nat_total_pop * 100) if nat_total_pop > 0 else 0.0
)

# 최고/최저 시군구 추출 (전국 기준)
max_row = df_year.loc[df_year[target_col].idxmax()]
min_row = df_year.loc[df_year[target_col].idxmin()]

# 시군구 명칭 매핑
code_to_name = {
    f["properties"]["코드"]: f"{f['properties']['시도']} {f['properties']['시군구']}"
    for f in geojson_data["features"]
}
max_code = str(max_row["sigungu_code"])
min_code = str(min_row["sigungu_code"])
max_name = code_to_name.get(max_code, f"코드({max_code})")
min_name = code_to_name.get(min_code, f"코드({min_code})")

with col1:
    st.metric(
        label=f"전국 평균 {target_col} ({selected_year}년)",
        value=f"{nat_rate:.2f}%",
    )
with col2:
    st.metric(
        label="가장 높은 시군구",
        value=f"{max_row[target_col]:.2f}%",
        delta=max_name,
        delta_color="normal",
    )
with col3:
    st.metric(
        label="가장 낮은 시군구",
        value=f"{min_row[target_col]:.2f}%",
        delta=min_name,
        delta_color="normal",
    )

st.markdown("---")

# --- 색상 구간 및 범주 설정 ---
if is_senior:
    # 고령화율 고정 구간: [0, 19, 23, 28, 38, max]
    bounds = [0, 19, 23, 28, 38, max(45.0, df_all["고령화율"].max())]
    colorscale = "Reds"
else:
    # 유소년 비율 구간: [0, 6, 9, 12, 15, max]
    bounds = [0, 6, 9, 12, 15, max(20.0, df_all["유소년 비율"].max())]
    colorscale = "Blues"

# --- Plotly Choropleth 생성 ---
fig = px.choropleth(
    df_filtered,
    geojson=current_geojson,
    locations="sigungu_code",
    featureidkey="properties.코드",
    color=target_col,
    color_continuous_scale=colorscale,
    range_color=(bounds[0], bounds[-1]),
    labels={target_col: f"{target_col} (%)"},
)

# 지도 스타일 및 바운드 설정
fig.update_geos(fitbounds="locations", visible=False)

hover_text = (
    f"<b>%{{properties.시도}} %{{properties.시군구}}</b><br>{target_col}: %{{z:.2f}}%<extra></extra>"
)
fig.update_traces(
    hovertemplate=hover_text, marker_line_width=0.5, marker_line_color="gray"
)

fig.update_layout(
    margin={"r": 0, "t": 10, "l": 0, "b": 0},
    coloraxis_colorbar=dict(title=f"{target_col} (%)"),
)

# 지도 출력
st.plotly_chart(fig, use_container_width=True)

# --- 미매칭 행정구역 안내 문구 ---
if not unmatched_df.empty:
    st.caption(
        f"⚠️ **안내**: {selected_year}년 데이터 중 일부 옛 행정구역 코드({len(unmatched_df)}건)는 "
        "현재 경계 지도 파일과 일치하지 않아 지도에서 **회색**으로 표시되거나 생략되었을 수 있습니다."
    )
