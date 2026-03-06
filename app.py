import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# --- [1] 필수 함수 정의 (사용 전 상단 배치) ---

# 한글 초성 추출 함수
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    result = ""
    for char in str(text):
        if '가' <= char <= '힣':
            char_code = ord(char) - ord('가')
            chosung_index = char_code // 588
            result += CHOSUNG_LIST[chosung_index]
        else:
            result += char
    return result

# 데이터 정제 함수
def clean_num(v):
    if pd.isna(v): return 0
    cleaned = re.sub(r'[^0-9.]', '', str(v))
    return pd.to_numeric(cleaned, errors='coerce')

# [에러 해결 포인트] 데이터 평균 계산 함수 (사용하는 곳보다 위에 위치)
def get_avg_data(data, m_key, months, all_target_cols):
    target_cols = [c for c in all_target_cols if m_key in c.upper() and any(m in c for m in months)]
    return data[target_cols].mean(axis=1) if target_cols else pd.Series([0.0] * len(data))

# 전광판 그리기 함수
def draw_scoreboard(occ, adr, rev):
    sc1, sc2, sc3 = st.columns(3)
    for i, (l, v, u) in enumerate([("AVG OCCUPANCY", occ, "%"), ("AVG ADR", adr, "만원"), ("AVG RevPAR", rev, "만원")]):
        with [sc1, sc2, sc3][i]:
            st.markdown(f'<div class="digital-scoreboard"><div class="digital-label" style="color:#64FFDA; font-weight:800;">{l}</div><div class="digital-value">{v:.1f}<span style="font-size:1rem; margin-left:5px;">{u}</span></div></div>', unsafe_allow_html=True)

# 그래프 그리기 함수
def draw_line_chart(df_plot, x_col, y_col, title_text):
    fig = px.line(df_plot, x=x_col, y=y_col, markers=True, text=y_col)
    fig.update_layout(
        title={'text': f"<b>{title_text}</b>", 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 22, 'color': '#FFFFFF'}},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#FFFFFF',
        margin=dict(t=60, b=40, l=40, r=40), xaxis_title="", yaxis_title=""
    )
    fig.update_traces(
        line_color='#64FFDA', line_width=4, marker=dict(size=10),
        textposition="top center", textfont=dict(size=16, color='#64FFDA', family='Arial Black'),
        texttemplate='%{text:.1f}'
    )
    st.plotly_chart(fig, use_container_width=True)

# --- [2] 페이지 설정 및 스타일 ---
st.set_page_config(page_title="Hotel Intelligence Dash", layout="wide")
st.markdown("""
    <style>
        .stApp { background-color: #0A192F; color: #FFFFFF; }
        section[data-testid="stSidebar"] { background-color: #112240 !important; border-right: 2px solid #233554; }
        div[data-testid="stSidebarUserContent"] .st-emotion-cache-6q9sum.e1nzilvr4,
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { color: #FFFFFF !important; opacity: 1 !important; font-weight: 700 !important; }
        .stApp [data-testid="stWidgetLabel"] p { color: #FFFFFF !important; font-size: 1.2rem !important; font-weight: 800 !important; }
        div.stButton > button { background-color: #172A45 !important; color: #64FFDA !important; border: 1px solid #64FFDA !important; font-weight: 800 !important; }
        .stTable, [data-testid="stDataFrame"] { background-color: #FFFFFF !important; border-radius: 8px !important; }
        .stTable td, .stTable th { color: #000000 !important; text-align: center !important; }
        .digital-scoreboard { background-color: #000000; border: 3px solid #333333; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 25px; }
        .digital-value { color: #64FFDA; font-family: 'Courier New', monospace; font-size: 2.5rem; font-weight: 900; }
        h1, h2, h3 { color: #64FFDA !important; }
    </style>
""", unsafe_allow_html=True)

# --- [3] 데이터 로드 및 세션 관리 ---
month_options = ["1월", "2월", "3월", "4월", "5월", "6월"]

def reset_to_default():
    for m in month_options: st.session_state[f"chk_v18_{m}"] = True
    st.session_state['keep_type'], st.session_state['keep_region'], st.session_state['keep_star'] = "전체", "전체", "전체"

if 'init_v18' not in st.session_state:
    reset_to_default()
    st.session_state['current_page'] = "🏠 종합 분석 대시보드"
    st.session_state['init_v18'] = True

files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
if not files: st.sidebar.error("📂 파일을 폴더에 넣어주세요."); st.stop()
selected_file = st.sidebar.selectbox("📂 분석 파일 선택", files)
df = pd.read_excel(selected_file)
df.columns = [str(col).strip() for col in df.columns]

NAME_COL, TYPE_COL, REGION_COL, STAR_COL = '업체명', '업종', '지역', '성급'
all_target_cols = [col for col in df.columns if any(key in col.upper() for key in ['OCC', 'ADR', 'REV'])]
for col in all_target_cols: df[col] = df[col].apply(clean_num)

# --- [4] 사이드바 필터 ---
with st.sidebar:
    st.markdown("### 📍 PAGE NAVIGATION")
    new_page = st.radio("이동", ["🏠 종합 분석 대시보드", "🏆 상위 랭킹 TOP 30", "🔍 업체별 상세 분석"], index=["🏠 종합 분석 대시보드", "🏆 상위 랭킹 TOP 30", "🔍 업체별 상세 분석"].index(st.session_state['current_page']), label_visibility="collapsed")
    if new_page != st.session_state['current_page']: st.session_state['current_page'] = new_page; reset_to_default(); st.rerun()
    page = st.session_state['current_page']
    
    st.markdown("---")
    st.markdown("### 📅 PERIOD SELECT")
    c1, c2, c3 = st.columns(3)
    def set_period(m_list):
        for m in month_options: st.session_state[f"chk_v18_{m}"] = (m in m_list)
        st.rerun()
    if c1.button("1분기"): set_period(["1월", "2월", "3월"])
    if c2.button("2분기"): set_period(["4월", "5월", "6월"])
    if c3.button("상반기"): set_period(month_options)
    
    cb_cols, final_months = st.columns(2), []
    for i, m in enumerate(month_options):
        with cb_cols[i % 2]:
            if st.checkbox(m, key=f"chk_v18_{m}"): final_months.append(m)
    
    st.markdown("---")
    st.markdown("### 🔍 BASIC FILTER")
    t_list = ["전체"] + sorted(df[TYPE_COL].dropna().unique().tolist())
    st.session_state['keep_type'] = st.selectbox("🏢 업종", t_list, index=t_list.index(st.session_state['keep_type']))
    r_list = ["전체"] + sorted(df[REGION_COL].dropna().unique().tolist())
    st.session_state['keep_region'] = st.selectbox("📍 지역(시도)", r_list, index=r_list.index(st.session_state['keep_region']))
    s_list = ["전체"] + sorted(df[STAR_COL].dropna().unique().tolist())
    st.session_state['keep_star'] = st.selectbox("⭐ 성급", s_list, index=s_list.index(st.session_state['keep_star']))

# --- [5] 필터 적용 및 페이지 출력 ---
f_df = df.copy()
if st.session_state['keep_type'] != "전체": f_df = f_df[f_df[TYPE_COL] == st.session_state['keep_type']]
if st.session_state['keep_region'] != "전체": f_df = f_df[f_df[REGION_COL] == st.session_state['keep_region']]
if st.session_state['keep_star'] != "전체": f_df = f_df[f_df[STAR_COL] == st.session_state['keep_star']]

if not final_months: st.info("📅 기간을 선택해주세요."); st.stop()

if page == "🏠 종합 분석 대시보드":
    st.title("HOTEL PERFORMANCE INDEX")
    f_df['선택_OCC'] = get_avg_data(f_df, 'OCC', final_months, all_target_cols).round(1)
    f_df['선택_ADR'] = get_avg_data(f_df, 'ADR', final_months, all_target_cols).round(1)
    f_df['선택_REV'] = get_avg_data(f_df, 'REV', final_months, all_target_cols).round(1)
    draw_scoreboard(f_df['선택_OCC'].mean(), f_df['선택_ADR'].mean(), f_df['선택_REV'].mean())
    st.subheader("📋 HOTEL PERFORMANCE DATA LIST")
    disp = f_df[[NAME_COL, TYPE_COL, REGION_COL, STAR_COL, '선택_OCC', '선택_ADR', '선택_REV']].copy()
    disp.index = range(1, len(disp) + 1)
    st.dataframe(disp.style.format({'선택_OCC': '{:.1f}', '선택_ADR': '{:.1f}', '선택_REV': '{:.1f}'}), use_container_width=True)
    st.subheader("📈 MONTHLY TREND (GROUP AVG)")
    t_cols = st.columns(3)
    for i, (mk, ml) in enumerate([('OCC', '🏨 OCCUPANCY (%)'), ('ADR', '💰 ADR (만원)'), ('REV', '📊 RevPAR (만원)')]):
        tl = [{'Month': m, 'Value': f_df[[c for c in all_target_cols if mk in c.upper() and m in c][0]].mean()} for m in final_months if [c for c in all_target_cols if mk in c.upper() and m in c]]
        if tl:
            with t_cols[i]: draw_line_chart(pd.DataFrame(tl), 'Month', 'Value', ml)

elif page == "🏆 상위 랭킹 TOP 30":
    st.title("TOP 30 PERFORMANCE RANKING")
    f_df['선택_OCC'] = get_avg_data(f_df, 'OCC', final_months, all_target_cols).round(1)
    f_df['선택_ADR'] = get_avg_data(f_df, 'ADR', final_months, all_target_cols).round(1)
    f_df['선택_REV'] = get_avg_data(f_df, 'REV', final_months, all_target_cols).round(1)
    draw_scoreboard(f_df['선택_OCC'].mean(), f_df['선택_ADR'].mean(), f_df['선택_REV'].mean())
    r_cols = st.columns(3)
    for i, (mc, ti, un) in enumerate([('선택_OCC', '🔥 OCC TOP 30', '%'), ('선택_ADR', '💰 ADR TOP 30', '만원'), ('선택_REV', '📊 RevPAR TOP 30', '만원')]):
        with r_cols[i]:
            st.markdown(f"### {ti}")
            top30 = f_df.sort_values(by=mc, ascending=False).head(30)[[NAME_COL, mc]].copy()
            top30.columns = ['Hotel Name', f'Value({un})']
            top30.index = range(1, len(top30) + 1)
            st.dataframe(top30.style.format({f'Value({un})': '{:.1f}'}), use_container_width=True)

elif page == "🔍 업체별 상세 분석":
    st.title("INDIVIDUAL HOTEL ANALYSIS")
    f_list = sorted(f_df[NAME_COL].dropna().unique().tolist())
    sc1, sc2 = st.columns(2)
    with sc1: kw = st.text_input("📝 필터 내 업체명/초성 검색", placeholder="예: ㄱㄹㄷ")
    res = [h for h in f_list if kw in h or kw in get_chosung(h)] if kw else f_list
    if not res and kw: st.warning("⚠️ 일치하는 업체가 없습니다.")
    else:
        with sc2: sh = st.selectbox(f"🏨 업체 선택 (검색결과: {len(res)}건)", res) if res else None
        if sh:
            target = f_df[f_df[NAME_COL] == sh].iloc[0]
            draw_scoreboard(round(get_avg_data(f_df[f_df[NAME_COL] == sh], 'OCC', final_months, all_target_cols).values[0], 1),
                            round(get_avg_data(f_df[f_df[NAME_COL] == sh], 'ADR', final_months, all_target_cols).values[0], 1),
                            round(get_avg_data(f_df[f_df[NAME_COL] == sh], 'REV', final_months, all_target_cols).values[0], 1))
            td = [{'Month': m, 'OCC(%)': target[[c for c in all_target_cols if 'OCC' in c.upper() and m in c][0]], 'ADR(만원)': target[[c for c in all_target_cols if 'ADR' in c.upper() and m in c][0]], 'RevPAR(만원)': target[[c for c in all_target_cols if 'REV' in c.upper() and m in c][0]]} for m in final_months]
            st.write("---")
            gt_cols = st.columns(3)
            for i, (y_col, ml) in enumerate([('OCC(%)', '🏨 OCCUPANCY (%)'), ('ADR(만원)', '💰 ADR (만원)'), ('RevPAR(만원)', '📊 RevPAR (만원)')]):
                with gt_cols[i]: draw_line_chart(pd.DataFrame(td), 'Month', y_col, ml)
            st.subheader(f"📊 {sh} DATA TABLE")
            dt_df = pd.DataFrame(td); dt_df.index = range(1, len(dt_df) + 1)
            st.table(dt_df.style.format("{:.1f}", subset=['OCC(%)', 'ADR(만원)', 'RevPAR(만원)']))