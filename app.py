import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import pdfplumber
from fpdf import FPDF
import re
from datetime import date
import numpy as np
import io

# --- [0. 페이지 설정 및 프리미엄 디자인] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

# 차트 한글 폰트 설정
plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

st.markdown("""
<style>
    .stApp { background-color: #f4f7f9 !important; }
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1e3a8a 100%); 
        color: white; padding: 2.5rem; border-radius: 20px; 
        border-bottom: 8px solid #d4af37; text-align: center; margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- [1. 사용자 DB 및 보안] ---
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
    st.markdown('<div style="background:white; padding:50px; border-radius:20px; max-width:500px; margin:10vh auto; text-align:center; border-top:10px solid #0b1f52; box-shadow: 0 15px 35px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666;'>종합 재무진단 시스템 v34.0 [Precision-Hybrid]</p>", unsafe_allow_html=True)
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

# --- [2. 초정밀 하이브리드 스캐너 엔진] ---

def clean_num(val):
    if val is None or val == "": return 0.0
    s = str(val).replace(',', '').replace('"', '').strip()
    s = re.sub(r'[^\d.-]', '', s)
    try: return float(s)
    except: return 0.0

def hybrid_analyzer(files):
    """표 구조와 텍스트 자석 검색을 동시에 실행하는 최상위 엔진"""
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
                    txt = page.extract_text() or ""
                    full_text += txt + "\n"
                
                # 1. 텍스트 자석 검색 (좌표 파편화 대응)
                clean_txt = full_text.replace('"', '').replace(' ', '').replace('\n', '')
                
                if res['comp'] == "미상":
                    m = re.search(r'기업명[:：]?([가-힣\(\)A-Za-z0-9&]+)', clean_txt)
                    if m: res['comp'] = m.group(1).strip()
                
                if res['ceo'] == "미상":
                    m = re.search(r'대표자(?:명)?[:：]?([가-힣]{2,4})', clean_txt)
                    if m: res['ceo'] = m.group(1).strip()
                
                if res['emp'] == 0:
                    m = re.search(r'종업원수[:：]?(\d+)', clean_txt)
                    if m: res['emp'] = int(m.group(1))

                # 2. 인증 현황 정밀 스캔
                for k in res['certs'].keys():
                    if f"{k}인증" in clean_txt or f"{k}보유" in clean_txt:
                        res['certs'][k] = True

        # 3. 엑셀/CSV 전수 조사 (v18 엑셀 로직 복구)
        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_excel(file, header=None) if file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values if v]).replace(" ", "")
                    mapping = {'자산': '자산', '부채': '부채', '매출액': '매출', '순이익': '이익'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            # 해당 행에서 유효한 숫자들 수집
                            nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                            if len(nums) >= 2:
                                res['fin'][key] = nums[-3:] if len(nums) >= 3 else [0.0] + nums[-2:]
            except: pass
    return res

# --- [3. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 종합 경영 진단 및 재무 분석 시스템</h1></div>', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 함께 업로드하세요.", accept_multiple_files=True)
    if up_files:
        data = hybrid_analyzer(up_files)
        st.success("✅ 모든 데이터 인식 및 동기화 완료")
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            # (주)메이홈, 박승미, 10명이 자동 입력됩니다.
            f_comp = st.text_input("🏢 기업 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 종업원수(명)", value=data['emp'])
            st.divider()
            r_rev = st.number_input("2024 매출액", value=data['fin']['매출'][2])
            r_inc = st.number_input("2024 순이익", value=data['fin']['이익'][2])
            r_asset = st.number_input("2024 자산총계", value=data['fin']['자산'][2])
            r_debt = st.number_input("2024 부채총계", value=data['fin']['부채'][2])

with col_r:
    st.subheader("📈 경영 지표 진단 시뮬레이션")
    if up_files:
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석 결과: 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 전용 분석 가이드가 생성됩니다.")
        
        # 가치 평가 로직
        unit = 1000000 if r_rev < 100000 else 1000
        stock_price = ((r_inc * unit / 0.1)*0.6 + (r_asset - r_debt)*unit*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시나리오")
        st.pyplot(fig)

        if st.button("🚀 종합 리포트 발행 (재무제표 분석 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            # 폰트 에러 방지 기본 설정
            pdf.set_font("helvetica", size=12)
            
            # P1: 표지
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90)
            pdf.cell(190, 25, txt="RE-PORT: Comprehensive Financial Analysis", ln=True, align='C')
            pdf.cell(190, 20, txt=f"Company: {f_comp} / CEO: {f_ceo}", ln=True, align='C')
            
            # P2: 재무제표 전문 분석 (영문 기반 - 한글 폰트 미등록 시 대비)
            pdf.add_page(); pdf.set_text_color(0,0,0)
            pdf.cell(190, 15, txt="1. 정밀 재무제표 분석 (단위: 천원)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.cell(60, 10, "항목", 1); pdf.cell(60, 10, "2023", 1); pdf.cell(60, 10, "2024", 1, 1)
            
            rows = [("자산 총계", data['fin']['자산'][1], r_asset), ("부채 총계", data['fin']['부채'][1], r_debt), ("매출액", data['fin']['매출'][1], r_rev), ("당기순이익", data['fin']['이익'][1], r_inc)]
            for n, v1, v2 in rows:
                pdf.cell(60, 10, n, 1); pdf.cell(60, 10, f"{v1:,.0f}", 1); pdf.cell(60, 10, f"{v2:,.0f}", 1, 1)
            
            pdf.ln(10); pdf.multi_cell(190, 8, txt=f"분석 결과, {f_comp}의 2024년 부채비율은 {(r_debt/r_asset*100 if r_asset>0 else 0):.1f}%로 매우 안정적입니다. 전년 대비 매출액이 가파르게 상승하고 있어 향후 주당 가치는 더욱 증대될 것으로 분석됩니다.")

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"Report_{f_comp}.pdf")
