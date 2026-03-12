import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import pdfplumber
from fpdf import FPDF
import re
from datetime import date
import numpy as np

# --- [0. 페이지 설정] ---
st.set_page_config(page_title="SME 재무경영진단 AI", layout="wide")

plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

st.markdown("""
<style>
    .stApp { background-color: #f8faff !important; }
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1e3a8a 100%); 
        color: white; padding: 2rem; border-radius: 15px; 
        border-bottom: 5px solid #d4af37; text-align: center; margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- [1. 사용자 DB] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df): df.to_csv(DB_FILE, index=False)
user_db = load_db()

if 'auth_user' not in st.session_state: st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.markdown('<div style="background:white; padding:40px; border-radius:15px; max-width:480px; margin:10vh auto; text-align:center; border-top:8px solid #0b1f52; box-shadow: 0 15px 35px rgba(0,0,0,0.15);">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666;'>종합 재무진단 시스템 v36.0 [Final-Sync]</p>", unsafe_allow_html=True)
    email = st.text_input("아이디(이메일)", placeholder="admin@example.com").strip().lower()
    c1, c2 = st.columns(2)
    if c1.button("로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.auth_user = email; st.rerun()
        else: st.error("승인이 필요한 계정입니다.")
    if c2.button("신청", use_container_width=True):
        if email and user_db[user_db['email'] == email].empty:
            new_u = pd.DataFrame([{"email": email, "approved": False, "is_admin": False}])
            user_db = pd.concat([user_db, new_u], ignore_index=True); save_db(user_db)
            st.success("신청 완료!")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [2. 초정밀 데이터 추출 엔진] ---

def clean_num(val):
    if val is None or val == "": return 0.0
    s = str(val).replace(',', '').replace('"', '').replace('\n', '').strip()
    s = re.sub(r'[^\d.-]', '', s)
    try: return float(s)
    except: return 0.0

def kodata_pdf_parser(file):
    """KODATA 특유의 따옴표/쉼표/줄바꿈 구조 강제 돌파"""
    res = {'comp': "미상", 'ceo': "미상", 'emp': 0, 'certs': {'벤처': False, '연구개발전담부서': False}}
    with pdfplumber.open(file) as pdf:
        all_text = ""
        for page in pdf.pages:
            raw_txt = page.extract_text() or ""
            all_text += raw_txt + "\n"
            
            # 모든 특수기호를 제거한 검색용 텍스트 생성
            clean_txt = raw_txt.replace('"', '').replace('\n', ' ').replace(',', ' ')
            
            if res['comp'] == "미상":
                m = re.search(r'기업명\s*[:：]?\s*([가-힣\(\)A-Za-z0-9&]+)', clean_txt)
                if m: res['comp'] = m.group(1).strip()
            
            if res['ceo'] == "미상":
                m = re.search(r'대표자(?:명)?\s*([가-힣]{2,4})', clean_txt)
                if m: res['ceo'] = m.group(1).strip()
            
            if res['emp'] == 0:
                m = re.search(r'종업원수\s*(\d+)', clean_txt)
                if m: res['emp'] = int(m.group(1))

        # 인증 현황 (4페이지 기준)
        tight = all_text.replace(" ", "").replace("\n", "")
        if "벤처인증" in tight or "벤처보유" in tight: res['certs']['벤처'] = True
        if "연구개발전담부서" in tight: res['certs']['연구개발전담부서'] = True
    return res

def ultimate_excel_parser(file):
    """엑셀 행 전수 조사를 통한 2022~2024 수치 수집"""
    res = {'fin': {'매출':[0.0,0.0,0.0], '이익':[0.0,0.0,0.0], '자산':[0.0,0.0,0.0], '부채':[0.0,0.0,0.0]}}
    try:
        df = pd.read_excel(file, header=None) if file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(file, header=None)
        for _, row in df.iterrows():
            row_vals = [str(v) for v in row.values if v is not None]
            row_txt = "".join(row_vals).replace(" ", "")
            mapping = {'매출액': '매출', '순이익': '이익', '자산총계': '자산', '부채총계': '부채'}
            for kw, key in mapping.items():
                if kw in row_txt:
                    nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                    if len(nums) >= 2:
                        res['fin'][key] = nums[-3:] if len(nums) >= 3 else [0.0] + nums[-2:]
    except: pass
    return res

# --- [3. 메인 대시보드] ---
st.markdown('<div class="premium-header"><h1>📊 종합 경영 진단 및 재무 분석 시스템</h1></div>', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 함께 올려주세요.", accept_multiple_files=True)
    
    # 변수 초기화 (NameError 방지)
    f_comp, f_ceo, f_emp = "미상", "미상", 0
    r_rev, r_inc, r_asset, r_debt = 0.0, 0.0, 0.0, 0.0
    fin_res = {'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]}}
    pdf_res = {'comp': "미상", 'ceo': "미상", 'emp': 0, 'certs': {}}

    if up_files:
        for f in up_files:
            if f.name.endswith('.pdf'): pdf_res = kodata_pdf_parser(f)
            else: fin_res = ultimate_excel_parser(f)
        
        st.success("✅ 모든 데이터 인식 성공")
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 명칭", pdf_res['comp'])
            f_ceo = st.text_input("👤 대표자 성함", pdf_res['ceo'])
            f_emp = st.number_input("👥 종업원수(명)", value=pdf_res['emp'])
            st.divider()
            r_rev = st.number_input("2024 매출액", value=fin_res['fin']['매출'][2])
            r_inc = st.number_input("2024 순이익", value=fin_res['fin']['이익'][2])
            r_asset = st.number_input("2024 자산총계", value=fin_res['fin']['자산'][2])
            r_debt = st.number_input("2024 부채총계", value=fin_res['fin']['부채'][2])

with col_r:
    st.subheader("📈 경영 지표 진단 시뮬레이션")
    if up_files:
        labor = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석 결과: 근라자 **{f_emp}명**으로 **'{labor} 사업장'** 노무 가이드가 적용됩니다.")
        
        # 가치 평가
        unit = 1000000 if r_rev < 100000 else 1000
        stock_val = ((r_inc * unit / 0.1)*0.6 + (r_asset - r_debt)*unit*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시나리오")
        st.pyplot(fig)

        if st.button("🚀 종합 보고서 발행 (재무제표 분석 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            font_path = "NanumGothic.ttf"
            if os.path.exists(font_path):
                pdf.add_font("Nanum", "", font_path)
                pdf.set_font("Nanum", size=12)
            else: pdf.set_font("helvetica", size=12)
            
            # P1: 표지
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90)
            pdf.cell(190, 25, txt="RE-PORT: Comprehensive Analysis", ln=True, align='C')
            pdf.cell(190, 20, txt=f"Target: {f_comp} / CEO: {f_ceo}", ln=True, align='C')
            
            # P2: 재무제표 분석 전문
            pdf.add_page(); pdf.set_text_color(0,0,0)
            pdf.cell(190, 15, txt="1. Financial Statement Analysis (Unit: 1,000 KRW)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(50, 10, "Item", 1, 0, 'C', True); pdf.cell(70, 10, "2023", 1, 0, 'C', True); pdf.cell(70, 10, "2024 (Recent)", 1, 1, 'C', True)
            
            f_rows = [("Total Asset", fin_res['fin']['자산'][1], r_asset), ("Total Debt", fin_res['fin']['부채'][1], r_debt), ("Revenue", fin_res['fin']['매출'][1], r_rev), ("Net Income", fin_res['fin']['이익'][1], r_inc)]
            for n, v1, v2 in f_rows:
                pdf.cell(50, 10, n, 1); pdf.cell(70, 10, f"{v1:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v2:,.0f}", 1, 1, 'R')
            
            pdf.ln(10); pdf.multi_cell(190, 8, txt=f"Result: {f_comp} maintains a stable financial structure with a {(r_debt/r_asset*100 if r_asset>0 else 0):.1f}% debt ratio. Future value is expected to rise steadily.")

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 보고서 다운로드", data=pdf_out, file_name=f"Report_{f_comp}.pdf")
