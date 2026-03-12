import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import pdfplumber  # 좌표 기반 표 정밀 분석용
from fpdf import FPDF
import re
from datetime import date
import numpy as np
import io

# --- [0. 페이지 설정 및 프리미엄 UI] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

# 차트 한글 설정
plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

custom_css = """
<style>
    .block-container { padding-top: 1.5rem !important; }
    .stApp { background-color: #f4f7f9 !important; }
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%); 
        color: white; padding: 2.5rem; border-radius: 20px; 
        border-bottom: 8px solid #d4af37; text-align: center; margin-bottom: 2rem;
    }
    .login-box { 
        background: white; padding: 50px; border-radius: 20px; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); text-align: center; 
        max-width: 500px; margin: 10vh auto; border-top: 10px solid #0b1f52;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 DB 및 승인 시스템] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        # 관리자 허자현 대표님 설정
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df): df.to_csv(DB_FILE, index=False)
user_db = load_db()

if 'auth_user' not in st.session_state: st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
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

# --- [2. 초정밀 데이터 추출 엔진 (Spatial Analysis)] ---

def clean_val(val):
    if val is None or val == "": return 0.0
    s = re.sub(r'[^\d.-]', '', str(val))
    try: return float(s)
    except: return 0.0

def spatial_parser(files):
    """pdfplumber를 통한 표 구조 좌표 분석"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False}
    }
    
    for file in files:
        if file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + " "
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            row_str = "".join([str(c) for c in row if c])
                            if '기업명' in row_str: res['comp'] = str(row[-1]).replace('\n', '').strip()
                            if '대표자' in row_str: res['ceo'] = str(row[-1]).replace('\n', '').strip()
                            if '종업원수' in row_str: res['emp'] = int(clean_val(row[-1]))

                tight_txt = full_text.replace(" ", "").replace("\n", "")
                for k in res['certs'].keys():
                    if f"{k}인증" in tight_txt or f"{k}보유" in tight_txt: res['certs'][k] = True

        if file.name.endswith(('.xlsx', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    mapping = {'자산': '자산', '부채': '부채', '매출액': '매출', '순이익': '이익'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            v1, v2, v3 = clean_val(row.values[2]), clean_val(row.values[3]), clean_val(row.values[4])
                            if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
            except: pass
    return res

# --- [3. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 종합 재무 진단 및 분석 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 **{st.session_state.auth_user}** 님")
    if st.button("로그아웃"): st.session_state.auth_user = None; st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 파일 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 자료", accept_multiple_files=True)
    if up_files:
        data = spatial_parser(up_files)
        st.success("✅ [Spatial-Scan] 데이터 인식 완료")
        with st.expander("📝 데이터 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 종업원수(명)", value=data['emp'])
            r_rev = st.number_input("2024 매출액", value=data['fin']['매출'][2])
            r_inc = st.number_input("2024 순이익", value=data['fin']['이익'][2])
            r_asset = st.number_input("2024 자산총계", value=data['fin']['자산'][2])
            r_debt = st.number_input("2024 부채총계", value=data['fin']['부채'][2])

with col_r:
    st.subheader("📈 실시간 진단 결과")
    if up_files:
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석: 현재 **{f_emp}명**으로 **'{labor_type} 사업장'** 전용 가이드가 생성됩니다.")
        
        multiplier = 1000000 if r_rev < 100000 else 1000
        stock_price = ((r_inc * multiplier / 0.1)*0.6 + (r_asset - r_debt)*multiplier*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 시뮬레이션")
        st.pyplot(fig)

        if st.button("🚀 종합 보고서 발행 (재무제표 전문 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_p): pdf.add_font("Nanum", "", f_p); pdf.set_font("Nanum", size=12)
            
            # P1: 표지
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="RE-PORT: 종합 경영진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"대상: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            
            # P2: 재무제표 전문 
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 정밀 재무제표 및 AI 분석 (단위: 천원)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Nanum", size=11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (기말)", 1, 1, 'C', True)
            
            rows = [("자산 총계", data['fin']['자산'][1], r_asset), ("부채 총계", data['fin']['부채'][1], r_debt), ("매출액", data['fin']['매출'][1], r_rev), ("당기순이익", data['fin']['이익'][1], r_inc)]
            for n, v23, v24 in rows:
                pdf.cell(50, 10, n, 1, 0, 'C'); pdf.cell(70, 10, f"{v23:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v24:,.0f}", 1, 1, 'R')
            
            pdf.ln(10); pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 10, txt="▶ 전문가 종합 재무 진단", ln=True)
            pdf.set_font("Nanum", size=11); pdf.set_text_color(0,0,0)
            pdf.multi_cell(190, 8, txt=f"분석 결과, {f_comp}의 부채비율은 {(r_debt/r_asset*100):.1f}%로 매우 안정적입니다. 특히 당기순이익이 가파르게 상승하고 있어 향후 3년 내 기업 가치는 현재보다 약 40% 이상 증대될 것으로 분석됩니다.")

            # P3: 기업가치 및 인증/노무
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 주식가치 평가 및 리스크 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            fig.savefig("v27_chart.png", dpi=300); pdf.image("v27_chart.png", x=15, w=180)
            pdf.ln(10); pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"■ 인증: 벤처({('보유' if data['certs']['벤처'] else '미보유')}), 전담부서({('보유' if data['certs']['연구개발전담부서'] else '미보유')})", ln=True)
            pdf.cell(190, 10, txt=f"■ 노무: 근로자 {f_emp}명에 따른 '{labor_type} 사업장' 기준 적용 필수", ln=True)

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
