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

# 따뜻한 톤을 위한 간단한 스타일 추가
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
# 4. 선택한 동네의 인구 데이터 가공
# ----------------------------------------------------
# 최종 선택된 지역의 데이터 1행(Row) 추출
target_data = df_sigungu[df_sigungu['동'] == selected_dong].iloc[0]

# 연령 라벨 생성 (0세, 1세, ..., 99세, 100세 이상)
# 맨 아래가 0세, 맨 위가 100세 이상이 되도록 순서를 지정합니다.
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 남/여 연령별 인구 수 가져오기
male_pop = []
female_pop = []

for age in age_labels:
    m_val = target_data.get(f"남_{age}", 0)
    f_val = target_data.get(f"여_{age}", 0)
    
    # 인구 피라미드에서 남자는 왼쪽 표시를 위해 음수로 전환
    male_pop.append(-m_val)
    female_pop.append(f_val)

# ----------------------------------------------------
# 5. Plotly 가로 막대 그래프 (인구 피라미드) 그리기
# ----------------------------------------------------
fig = go.Figure()

# 1) 남자 막대 그래프 (왼쪽, 음수 값)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_pop,
    name='남자',
    orientation='h',
    marker=dict(color='#6C9BCF'),  # 따뜻하고 부드러운 파란색
    hoverinfo='text',
    text=[f"남자 {age}: {abs(val):,}명" for age, val in zip(age_labels, male_pop)]
))

# 2) 여자 막대 그래프 (오른쪽, 양수 값)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_pop,
    name='여자',
    orientation='h',
    marker=dict(color='#FF8882'),  # 따뜻하고 부드러운 분홍색
    hoverinfo='text',
    text=[f"여자 {age}: {val:,}명" for age, val in zip(age_labels, female_pop)]
))

# 최대 인구수 계산 (X축 범위 및 눈금 설정을 위함)
max_val = max(max(abs(v) for v in male_pop), max(female_pop))
# 보기 좋은 단위로 축 범위 확장
axis_max = max(10, int(max_val * 1.1))

# X축 표시용 눈금 값 및 라벨 생성 (음수 축도 양수로 보이게)
tick_step = max(1, axis_max // 4)
tick_vals = list(range(-axis_max, axis_max + 1, tick_step))
tick_text = [f"{abs(v):,}명" for v in tick_vals]

# 3) 그래프 레이아웃 및 세로축(Y축) 순서 고정 설정
fig.update_layout(
    title=dict(
        text=f"<b>{selected_sido} {selected_sigungu} {selected_dong} 인구 피라미드</b>",
        x=0.5,
        font=dict(size=18, color="#4A3E3D")
    ),
    barmode='overlay',  # 막대 겹침 레이아웃
    bargap=0.1,
    xaxis=dict(
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_text,
        title="인구수",
        range=[-axis_max, axis_max]
    ),
    yaxis=dict(
        title="연령",
        # 축 뒤집기(autorange='reversed')나 정렬 옵션을 쓰지 않고,
        # 0세부터 100세 이상까지 명시적으로 범주 순서를 순방향 고정합니다.
        categoryorder='array',
        categoryarray=age_labels,
        dtick=10  # 10세 단위로 축 눈금 표시
    ),
    legend=dict(
        x=0.85,
        y=1.05,
        orientation="h"
    ),
    paper_bgcolor='#FAF7F2',
    plot_bgcolor='#FFFFFF',
    height=800,  # 100개 이상의 범주가 잘 보이도록 높이 지정
    margin=dict(l=50, r=50, t=80, b=50)
)

# ----------------------------------------------------
# 6. Streamlit 화면에 출력
# ----------------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# 주요 요약 정보 표시
total_m = sum(abs(v) for v in male_pop)
total_f = sum(female_pop)
total_pop = total_m + total_f

st.markdown("---")
col_a, col_b, col_c = st.columns(3)
col_a.metric("총 인구수", f"{total_pop:,} 명")
col_b.metric("남성 인구수", f"{total_m:,} 명")
col_c.metric("여성 인구수", f"{total_f:,} 명")
