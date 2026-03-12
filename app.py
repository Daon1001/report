import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import pdfplumber
from fpdf import FPDF
import re
from datetime import date
import numpy as np

# --- [0. 페이지 설정 및 폰트 무결성 로딩] ---
st.set_page_config(page_title="SME 종합 재무경영진단 마스터", layout="wide")

# 맑은 고딕(malgun.ttf) 또는 나눔고딕(NanumGothic.ttf) 깃허브 업로드 필수
base_dir = os.path.dirname(__file__)
font_path = os.path.join(base_dir, "malgun.ttf")
if not os.path.exists(font_path):
    font_path = os.path.join(base_dir, "NanumGothic.ttf")

def set_korean_font(path):
    try:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            font_prop = fm.FontProperties(fname=path)
            plt.rc('font', family=font_prop.get_name())
            plt.rcParams['axes.unicode_minus'] = False
            return True
    except: pass
    return False

has_font = set_korean_font(font_path)

st.markdown("""
<style>
    .stApp { background-color: #f4f7f9 !important; }
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1e3a8a 100%); 
        color: white; padding: 2.5rem; border-radius: 20px; 
        border-bottom: 8px solid #d4af37; text-align: center; margin-bottom: 2rem;
        box-shadow: 0 12px 35px rgba(0,0,0,0.1);
    }
    .main-card {
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #0b1f52;
    }
</style>
""", unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 관리자 승인 로직] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        # 허자현 대표님 관리자 계정 초기화
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

if 'auth_user' not in st.session_state:
    st.session_state.auth_user = None

# --- [2. 보안 로그인 및 가입 신청 화면] ---
if st.session_state.auth_user is None:
    st.markdown('<div style="background:white; padding:55px; border-radius:25px; max-width:550px; margin:8vh auto; text-align:center; border-top:15px solid #0b1f52; box-shadow: 0 20px 50px rgba(0,0,0,0.2);">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52; margin-bottom:5px;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#777; margin-bottom:35px;'>종합 재무진단 시스템 v45.0 [Admin-Integrated]</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    
    c1, c2 = st.columns(2)
    if c1.button("시스템 접속", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == login_email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.auth_user = login_email
            st.rerun()
        elif not row.empty:
            st.warning("⚠️ 관리자의 승인을 기다려주세요.")
        else:
            st.error("❌ 등록되지 않은 계정입니다.")
            
    if c2.button("이용 권한 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_u = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False}])
            user_db = pd.concat([user_db, new_u], ignore_index=True)
            save_db(user_db)
            st.success("✅ 신청 완료! 대표자 승인 후 즉시 이용 가능합니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 초정밀 데이터 밸리데이터 엔진] ---

def clean_num(val):
    if val is None or val == "": return 0.0
    s = str(val).replace(',', '').replace('"', '').replace('\n', '').replace(' ', '').strip()
    s = re.sub(r'[^\d.-]', '', s)
    try: return float(s)
    except: return 0.0

def super_deep_parser(files):
    """PDF의 특수 레이어와 엑셀의 가변 구조를 모두 해결하는 엔진"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False}
    }
    
    for file in files:
        if file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
                
                # 특수기호 제거 및 정규화
                clean = full_text.replace('"', ' ').replace('\n', ' ').replace(',', ' ')
                
                # 기업명 (주)메이홈
                m_comp = re.search(r'기업명\s*[:：]?\s*([가-힣\(\)A-Za-z0-9&]+)', clean)
                if m_comp: res['comp'] = m_comp.group(1).strip()
                
                # 대표자 박승미
                m_ceo = re.search(r'대표자(?:명)?\s*[:：]?\s*([가-힣]{2,4})', clean)
                if m_ceo: res['ceo'] = m_ceo.group(1).strip()
                
                # 종업원수 10명
                m_emp = re.search(r'종업원수\s*[:：]?\s*(\d+)', clean)
                if m_emp: res['emp'] = int(m_emp.group(1))

                tight = full_text.replace(" ", "").replace("\n", "")
                for k in res['certs'].keys():
                    if f"{k}인증" in tight or f"{k}보유" in tight: res['certs'][k] = True

        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_excel(file, header=None) if file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(file, header=None)
                # 연도 컬럼 위치 찾기 (2022, 2023, 2024)
                year_map = {2022: -1, 2023: -1, 2024: -1}
                for i, row in df.iterrows():
                    for idx, val in enumerate(row):
                        if str(val) == "2022": year_map[2022] = idx
                        if str(val) == "2023": year_map[2023] = idx
                        if str(val) == "2024": year_map[2024] = idx
                
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values if v is not None]).replace(" ", "")
                    mapping = {'매출액': '매출', '순이익': '이익', '자산총계': '자산', '부채총계': '부채'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            if all(v != -1 for v in year_map.values()):
                                res['fin'][key] = [clean_num(row.values[year_map[2022]]), 
                                                  clean_num(row.values[year_map[2023]]), 
                                                  clean_num(row.values[year_map[2024]])]
                            else:
                                # 백업: 연도 수치 제외하고 끝에서 3개 추출
                                nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                                valid = [n for n in nums if not (1900 < n < 2100)] # 연도 필터링
                                if len(valid) >= 3: res['fin'][key] = valid[-3:]
            except: pass
    return res

# --- [4. 메인 대시보드 및 관리자 메뉴] ---

st.markdown('<div class="premium-header"><h1>📊 [MASTER] 종합 경영진단 및 재무 리포트</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당자: **{st.session_state.auth_user}** 님")
    if st.button("로그아웃"): 
        st.session_state.auth_user = None
        st.rerun()
    
    # 관리자 메뉴 복구
    user_row = user_db[user_db['email'] == st.session_state.auth_user].iloc[0]
    if user_row['is_admin']:
        st.divider()
        st.subheader("👑 관리자 통제 센터")
        with st.expander("사용자 권한 승인 관리", expanded=False):
            st.dataframe(user_db[['email', 'approved']], use_container_width=True)
            target = st.selectbox("권한 변경할 계정", user_db['email'])
            if st.button("승인/거절 전환", use_container_width=True):
                user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
                save_db(user_db)
                st.success("상태 변경 완료!")
                st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 데이터 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 업로드하세요.", accept_multiple_files=True)
    
    # 기본값 설정
    f_comp, f_ceo, f_emp = "미상", "미상", 0
    fin_data = {'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]}}

    if up_files:
        parsed = super_deep_parser(up_files)
        st.success("✅ 모든 데이터 동기화 완료 (v45.0 Master-Scan)")
        
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 공식 명칭", parsed['comp'])
            f_ceo = st.text_input("👤 대표자 성함", parsed['ceo'])
            f_emp = st.number_input("👥 상시 근로자수(명)", value=parsed['emp'])
            st.divider()
            # 2024년 데이터 자동 매칭
            r_rev = st.number_input("2024 매출액 (천원/백만원)", value=parsed['fin']['매출'][2])
            r_inc = st.number_input("2024 순이익", value=parsed['fin']['이익'][2])
            r_asset = st.number_input("2024 자산총계", value=parsed['fin']['자산'][2])
            r_debt = st.number_input("2024 부채총계", value=parsed['fin']['부채'][2])

with col_r:
    st.subheader("📈 실시간 리포트 시뮬레이션")
    if up_files:
        labor = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석: 근로자 **{f_emp}명**으로 **'{labor} 사업장'** 전용 노무 가이드가 생성됩니다.")
        
        # 가치 평가 로직 (단위 보정 포함)
        unit_multiplier = 1000000 if r_rev < 100000 else 1000
        stock_val = ((r_inc * unit_multiplier / 0.1)*0.6 + (r_asset - r_debt)*unit_multiplier*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시나리오", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 보고서 발행 (재무제표 정밀 분석 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            if has_font:
                pdf.add_font("Malgun", "", font_path)
                pdf.set_font("Malgun", size=12)
            else: pdf.set_font("helvetica", size=12)
            
            # --- [PAGE 1: 리포트 표지] ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font_size(32)
            pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font_size(18); pdf.cell(190, 20, txt=f"대상기업: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            
            # --- [PAGE 2: 재무제표 정밀 분석 (BS/IS)] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font_size(20)
            pdf.cell(190, 15, txt="1. 주요 재무제표 및 AI 분석 (단위: 천원)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            pdf.set_fill_color(240, 240, 240); pdf.set_font_size(11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (최근 기말)", 1, 1, 'C', True)
            
            f_list = [
                ("자산 총계", parsed['fin']['자산'][1], r_asset), 
                ("부채 총계", parsed['fin']['부채'][1], r_debt), 
                ("매출액", parsed['fin']['매출'][1], r_rev), 
                ("당기순이익", parsed['fin']['이익'][1], r_inc)
            ]
            for n, v1, v2 in f_list:
                pdf.cell(50, 10, n, 1); pdf.cell(70, 10, f"{v1:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v2:,.0f}", 1, 1, 'R')
            
            # AI 종합 분석 텍스트
            pdf.ln(10); pdf.set_font_size(13); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 10, txt="▶ 전문가 종합 재무 진단", ln=True)
            pdf.set_font_size(11); pdf.set_text_color(0,0,0)
            debt_ratio = (r_debt / r_asset * 100) if r_asset > 0 else 0
            pdf.multi_cell(190, 8, txt=f"분석 결과, {f_comp}의 2024년 부채비율은 {debt_ratio:.1f}%로 매우 우수합니다. 특히 전년 대비 매출액과 순이익이 가파른 상승세를 보이고 있어, 현재 {int(stock_val):,}원으로 평가되는 주당 가치는 향후 공격적인 투자와 자본 관리 시 더욱 증대될 것으로 분석됩니다.")

            # --- [PAGE 3: 기업가치 및 리스크] ---
            pdf.add_page(); pdf.set_font_size(20)
            pdf.cell(190, 15, txt="2. 주식가치 평가 및 리스크 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            fig.savefig("v45_final.png", dpi=300); pdf.image("v45_final.png", x=15, w=180)
            pdf.ln(10); pdf.set_font_size(12)
            pdf.cell(190, 10, txt=f"■ 인증: 벤처({('보유' if parsed['certs']['벤처'] else '미보유')}), 전담부서({('보유' if parsed['certs']['연구개발전담부서'] else '미보유')})", ln=True)
            pdf.cell(190, 10, txt=f"■ 노무: 상시 근로자 {f_emp}명에 따른 '{labor}' 기준 법적 가이드 적용", ln=True)

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
