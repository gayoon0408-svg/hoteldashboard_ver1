import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# --- [필수] 한글 초성 추출 함수 ---
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

# 1. 페이지 설정
st.set_page_config(page_title="Hotel Intelligence Dash", layout="wide")

# --- 스타일 디자인 (기존 세팅 유지) ---
st.markdown("""
    <style>
        .stApp { background-color: #0A192F; color: #FFFFFF; }
        section[data-testid="stSidebar"] { background-color: #112240 !important; border-right: 2px solid #233554; }
        div.stButton > button {
            background-color: #172A45 !important; color: #64FFDA !important;
            border: 1px solid #64FFDA !important; font-weight: 800 !important; width: 100%; height: 45px;
        }
        div.stButton > button:hover { background-color: #64FFDA !important; color: #0A192F !important; }
        section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
            color: #FFFFFF !important; opacity: 1 !important;
        }
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: #64FFDA !important; font-weight: 800 !important; }
        .stTable, [data-testid="stDataFrame"] { background-color: #FFFFFF !important; border-radius: 8px !important; }
        .stTable td, .stTable th { color: #000000 !important; text-align: center !important; }
        .digital-scoreboard {
            background-color: #000000; border: 3px solid #333333; border-radius: 8px;
            padding: 20px; text-align: center; margin-bottom: 25px;
        }
        .digital-value { color: #64FFDA; font-family: 'Courier New', monospace; font-size: 2.5rem; font-weight: 900; }
        h1, h3 { color: #64FFDA !important; }
    </style>
""", unsafe_allow_html=True)

# --- 세션 상태 초기화 및 관리 ---
month_options = ["1월", "2월", "3월", "4월", "5월", "6월"]

# [강력 초기화 함수] 페이지 이동 시 모든 설정을 상반기 전체 데이터로 리셋
def reset_to_default():
    for m in month_options:
        st.session_state[f"chk_v18_{m}"] = True
    st.session_state['keep_type'] = "전체"
    st.session_state['keep_region'] = "전체"
    st.session_state['keep_star'] = "전체"

if 'init_v18' not in st.session_state:
    reset_to_default()
    st.session_state['current_page'] = "🏠 종합 분석 대시보드"
    st.session_state['init_v18'] = True

def set_period_selection(months_to_check):
    for m in month_options:
        st.session_state[f"chk_v18_{m}"] = (m in months_to_check)

# --- 데이터 로드 ---
def clean_num(v):
    if pd.isna(v): return 0
    cleaned = re.sub(r'[^0-9.]', '', str(v))
    return pd.to_numeric(cleaned, errors='coerce')

files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
if not files: 
    st.sidebar.error("📂 파일을 폴더에 넣어주세요.")
    st.stop()

selected_file = st.sidebar.selectbox("📂 분석 파일 선택", files)
df = pd.read_excel(selected_file)
df.columns = [str(col).strip() for col in df.columns]

NAME_COL, TYPE_COL, REGION_COL, STAR_COL = '업체명', '업종', '지역', '성급'
all_target_cols = [col for col in df.columns if any(key in col.upper() for key in ['OCC', 'ADR', 'REV'])]
for col in all_target_cols: df[col] = df[col].apply(clean_num)

# --- 사이드바 레이아웃 ---
with st.sidebar:
    st.markdown("### 📍 PAGE NAVIGATION")
    # 페이지 라디오
    new_page = st.radio("이동할 페이지 선택", ["🏠 종합 분석 대시보드", "🏆 상위 랭킹 TOP 30", "🔍 업체별 상세 분석"], 
                        index=["🏠 종합 분석 대시보드", "🏆 상위 랭킹 TOP 30", "🔍 업체별 상세 분석"].index(st.session_state['current_page']),
                        label_visibility="collapsed")
    
    # [핵심] 페이지 클릭 시 즉시 모든 필터/기간 리셋
    if new_page != st.session_state['current_page']:
        st.session_state['current_page'] = new_page
        reset_to_default() # 기간(1~6월)과 필터(전체) 모두 리셋
        st.rerun()

    page = st.session_state['current_page']
    
    st.markdown("---")
    st.markdown("### 📅 PERIOD SELECT")
    c1, c2, c3 = st.columns(3)
    if c1.button("1분기"): set_period_selection(["1월", "2월", "3월"]); st.rerun()
    if c2.button("2분기"): set_period_selection(["4월", "5월", "6월"]); st.rerun()
    if c3.button("상반기"): set_period_selection(month_options); st.rerun()
    
    cb_cols = st.columns(2)
    final_months = []
    for i, m in enumerate(month_options):
        with cb_cols[i % 2]:
            if st.checkbox(m, key=f"chk_v18_{m}"):
                final_months.append(m)
    
    st.markdown("---")
    st.markdown("### 🔍 BASIC FILTER")
    
    type_list = ["전체"] + sorted(df[TYPE_COL].dropna().unique().tolist())
    st.session_state['keep_type'] = st.selectbox("🏢 업종", type_list, index=type_list.index(st.session_state['keep_type']))
    
    region_list = ["전체"] + sorted(df[REGION_COL].dropna().unique().tolist())
    st.session_state['keep_region'] = st.selectbox("📍 지역(시도)", region_list, index=region_list.index(st.session_state['keep_region']))
    
    star_list = ["전체"] + sorted(df[STAR_COL].dropna().unique().tolist())
    st.session_state['keep_star'] = st.selectbox("⭐ 성급", star_list, index=star_list.index(st.session_state['keep_star']))

# 필터링 데이터 적용
f_df = df.copy()
if st.session_state['keep_type'] != "전체": f_df = f_df[f_df[TYPE_COL] == st.session_state['keep_type']]
if st.session_state['keep_region'] != "전체": f_df = f_df[f_df[REGION_COL] == st.session_state['keep_region']]
if st.session_state['keep_star'] != "전체": f_df = f_df[f_df[STAR_COL] == st.session_state['keep_star']]

# 데이터가 없는 상황 방지
if not final_months:
    st.info("📅 왼쪽 메뉴에서 분석할 **기간(월)**을 선택해주세요.")
    st.stop()

# --- 공통 함수 ---
def get_avg_data(data, m_key, months):
    target_cols = [c for c in all_target_cols if m_key in c.upper() and any(m in c for m in months)]
    return data[target_cols].mean(axis=1) if target_cols else pd.Series([0.0] * len(data))

def draw_scoreboard(occ, adr, rev):
    sc1, sc2, sc3 = st.columns(3)
    for i, (l, v, u) in enumerate([("AVG OCCUPANCY", occ, "%"), ("AVG ADR", adr, "만원"), ("AVG RevPAR", rev, "만원")]):
        with [sc1, sc2, sc3][i]:
            st.markdown(f'<div class="digital-scoreboard"><div class="digital-label">{l}</div><div class="digital-value">{v:.1f}<span class="digital-unit">{u}</span></div></div>', unsafe_allow_html=True)

# 페이지별 출력
if page == "🏠 종합 분석 대시보드":
    st.title("HOTEL PERFORMANCE INTELLIGENCE")
    f_df['선택_OCC'] = get_avg_data(f_df, 'OCC', final_months).round(1)
    f_df['선택_ADR'] = get_avg_data(f_df, 'ADR', final_months).round(1)
    f_df['선택_REV'] = get_avg_data(f_df, 'REV', final_months).round(1)
    draw_scoreboard(f_df['선택_OCC'].mean(), f_df['선택_ADR'].mean(), f_df['선택_REV'].mean())
    st.subheader("📋 HOTEL PERFORMANCE DATA LIST")
    st.dataframe(f_df[[NAME_COL, TYPE_COL, REGION_COL, STAR_COL, '선택_OCC', '선택_ADR', '선택_REV']].style.format({'선택_OCC': '{:.1f}', '선택_ADR': '{:.1f}', '선택_REV': '{:.1f}'}), use_container_width=True)
    
    st.subheader("📈 MONTHLY TREND (GROUP AVG)")
    t_cols = st.columns(3)
    for i, (mk, ml) in enumerate([('OCC', '🏨 OCCUPANCY (%)'), ('ADR', '💰 ADR (만원)'), ('REV', '📊 RevPAR (만원)')]):
        tl = [{'Month': m, 'Value': round(f_df[[c for c in all_target_cols if mk in c.upper() and m in c][0]].mean(), 1)} for m in final_months if [c for c in all_target_cols if mk in c.upper() and m in c]]
        if tl:
            with t_cols[i]:
                fig = px.line(pd.DataFrame(tl), x='Month', y='Value', markers=True, text='Value')
                fig.update_layout(title={'text': f"<b>{ml}</b>", 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 20, 'color': '#64FFDA'}}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', xaxis_title="", yaxis_title="")
                fig.update_traces(line_color='#64FFDA', line_width=4, textposition="top center", texttemplate='%{text:.1f}')
                st.plotly_chart(fig, use_container_width=True)

elif page == "🏆 상위 랭킹 TOP 30":
    st.title("TOP 30 PERFORMANCE RANKING")
    f_df['선택_OCC'] = get_avg_data(f_df, 'OCC', final_months).round(1)
    f_df['선택_ADR'] = get_avg_data(f_df, 'ADR', final_months).round(1)
    f_df['선택_REV'] = get_avg_data(f_df, 'REV', final_months).round(1)
    draw_scoreboard(f_df['선택_OCC'].mean(), f_df['선택_ADR'].mean(), f_df['선택_REV'].mean())
    r_cols = st.columns(3)
    for i, (mc, ti, un) in enumerate([('선택_OCC', '🔥 OCC TOP 30', '%'), ('선택_ADR', '💰 ADR TOP 30', '만원'), ('선택_REV', '📊 RevPAR TOP 30', '만원')]):
        with r_cols[i]:
            st.markdown(f"### {ti}")
            top30 = f_df.sort_values(by=mc, ascending=False).head(30)[[NAME_COL, mc]]
            top30.columns = ['Hotel Name', f'Value({un})']
            st.dataframe(top30.style.format({f'Value({un})': '{:.1f}'}), use_container_width=True)

elif page == "🔍 업체별 상세 분석":
    st.title("INDIVIDUAL HOTEL ANALYSIS")
    filtered_list = sorted(f_df[NAME_COL].dropna().unique().tolist())
    sc1, sc2 = st.columns(2)
    with sc1: keyword = st.text_input("📝 필터 내 업체명/초성 검색", placeholder="예: ㄱㄹㄷ")
    final_list = [h for h in filtered_list if keyword in h or keyword in get_chosung(h)] if keyword else filtered_list
    
    if not final_list and keyword:
        st.warning(f"⚠️ '{keyword}'와 일치하는 업체명이 현재 필터 내에 없습니다.")
    else:
        with sc2: search_hotel = st.selectbox(f"🏨 업체 선택 (검색결과: {len(final_list)}건)", final_list) if final_list else None
        if search_hotel:
            # 상세 분석 출력 로직 유지
            target_hotel = f_df[f_df[NAME_COL] == search_hotel].iloc[0]
            draw_scoreboard(round(get_avg_data(f_df[f_df[NAME_COL] == search_hotel], 'OCC', final_months).values[0], 1),
                            round(get_avg_data(f_df[f_df[NAME_COL] == search_hotel], 'ADR', final_months).values[0], 1),
                            round(get_avg_data(f_df[f_df[NAME_COL] == search_hotel], 'REV', final_months).values[0], 1))
            td = []
            for m in final_months:
                m_occ = round(target_hotel[[c for c in all_target_cols if 'OCC' in c.upper() and m in c][0]], 1)
                m_adr = round(target_hotel[[c for c in all_target_cols if 'ADR' in c.upper() and m in c][0]], 1)
                m_rev = round(target_hotel[[c for c in all_target_cols if 'REV' in c.upper() and m in c][0]], 1)
                td.append({'Month': m, 'OCC(%)': m_occ, 'ADR(만원)': m_adr, 'RevPAR(만원)': m_rev})
            st.write("---")
            gt_cols = st.columns(3)
            for i, (y_col, ml) in enumerate([('OCC(%)', '🏨 OCCUPANCY (%)'), ('ADR(만원)', '💰 ADR (만원)'), ('RevPAR(만원)', '📊 RevPAR (만원)')]):
                with gt_cols[i]:
                    fig = px.line(pd.DataFrame(td), x='Month', y=y_col, markers=True, text=y_col)
                    fig.update_layout(title={'text': f"<b>{ml}</b>", 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 20, 'color': '#64FFDA'}}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', xaxis_title="", yaxis_title="")
                    fig.update_traces(line_color='#64FFDA', line_width=4, textposition="top center", texttemplate='%{text:.1f}')
                    st.plotly_chart(fig, use_container_width=True)
            st.subheader(f"📊 {search_hotel} DATA TABLE")
            st.table(pd.DataFrame(td).set_index('Month').style.format("{:.1f}"))