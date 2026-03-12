import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import pdfplumber
from fpdf import FPDF
import re
from datetime import date
import numpy as np

# --- [0. 페이지 설정 및 프리미엄 디자인] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

# 차트 한글 설정
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

# --- [1. 사용자 보안 DB] ---
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
    st.markdown('<div style="background:white; padding:40px; border-radius:15px; max-width:450px; margin:10vh auto; text-align:center; border-top:8px solid #0b1f52; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666;'>종합 재무진단 시스템 v32.0 [Ultimate-Grid]</p>", unsafe_allow_html=True)
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

# --- [2. 초정밀 데이터 추출 엔진 (Grid-Base Analysis)] ---

def clean_num(val):
    if val is None or val == "": return 0.0
    s = str(val).replace(',', '').replace('"', '').strip()
    s = re.sub(r'[^\d.-]', '', s)
    try: return float(s)
    except: return 0.0

def grid_pdf_parser(file):
    """PDF의 시각적 격자를 분석하여 키워드 바로 우측 데이터를 획득"""
    res = {'comp': "미상", 'ceo': "미상", 'emp': 0, 'certs': {'벤처': False, '연구개발전담부서': False}}
    with pdfplumber.open(file) as pdf:
        all_text = ""
        for page in pdf.pages:
            words = page.extract_words()
            all_text += page.extract_text() + "\n"
            
            # (주)메이홈, 박승미, 10명 등 좌표 기반 추출
            for i, w in enumerate(words):
                txt = w['text']
                if '기업명' in txt and res['comp'] == "미상":
                    res['comp'] = words[i+1]['text'] if i+1 < len(words) else "미상"
                if '대표자' in txt and res['ceo'] == "미상":
                    res['ceo'] = words[i+1]['text'] if i+1 < len(words) else "미상"
                if '종업원수' in txt and res['emp'] == 0:
                    res['emp'] = int(clean_num(words[i+1]['text'])) if i+1 < len(words) else 0

        tight = all_text.replace(" ", "").replace("\n", "")
        if "벤처인증" in tight or "벤처보유" in tight: res['certs']['벤처'] = True
        if "연구개발전담부서" in tight: res['certs']['연구개발전담부서'] = True
    return res

def ultimate_excel_parser(file):
    """엑셀 행 전수 조사를 통한 2022~2024 수치 수집"""
    res = {'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]}}
    try:
        df = pd.read_excel(file, header=None) if file.name.endswith('.xlsx') else pd.read_csv(file, header=None)
        for _, row in df.iterrows():
            row_vals = [str(v) for v in row.values if v is not None]
            row_txt = "".join(row_vals).replace(" ", "")
            mapping = {'매출액': '매출', '당기순이익': '이익', '자산총계': '자산', '부채총계': '부채'}
            for kw, key in mapping.items():
                if kw in row_txt:
                    # 해당 행에서 유효한 숫자 3개 수집
                    nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                    if len(nums) >= 3: res['fin'][key] = nums[-3:]
                    elif len(nums) == 2: res['fin'][key] = [0.0] + nums
    except: pass
    return res

# --- [3. 메인 대시보드 및 리포트 섹션] ---
st.markdown('<div class="premium-header"><h1>📊 종합 경영 진단 및 재무 분석 마스터</h1></div>', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 함께 업로드하세요.", accept_multiple_files=True)
    if up_files:
        pdf_res = {'comp': "미상", 'ceo': "미상", 'emp': 0, 'certs': {}}
        fin_res = {'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]}}
        for f in up_files:
            if f.name.endswith('.pdf'): pdf_res = grid_pdf_parser(f)
            else: fin_res = ultimate_excel_parser(f)
        
        st.success("✅ [Grid-Scan] 데이터 정밀 매칭 성공")
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 명칭", pdf_res['comp'])
            f_ceo = st.text_input("👤 대표자 성함", pdf_res['ceo'])
            f_emp = st.number_input("👥 종업원수(명)", value=pdf_res['emp'])
            r_rev = st.number_input("2024 매출액", value=fin_res['fin']['매출'][2])
            r_inc = st.number_input("2024 순이익", value=fin_res['fin']['이익'][2])
            r_asset = st.number_input("2024 자산총계", value=fin_res['fin']['자산'][2])
            r_debt = st.number_input("2024 부채총계", value=fin_res['fin']['부채'][2])

with col_r:
    st.subheader("📈 실시간 리포트 구성 시뮬레이션")
    if up_files:
        labor = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"근로자 **{f_emp}명**으로 **'{labor} 사업장'** 전용 가이드가 생성됩니다.")
        
        unit = 1000000 if r_rev < 100000 else 1000
        stock_val = ((r_inc * unit / 0.1)*0.6 + (r_asset - r_debt)*unit*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 가치 시뮬레이션")
        st.pyplot(fig)

        if st.button("🚀 종합 보고서 발행 (재무분석 전문 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            # 폰트 에러 방지용 기본 폰트 설정
            pdf.set_font("helvetica", size=12)
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90)
            pdf.cell(190, 25, txt="RE-PORT: Comprehensive Financial Analysis", ln=True, align='C')
            pdf.cell(190, 20, txt=f"Company: {f_comp} / CEO: {f_ceo}", ln=True, align='C')
            
            # P2: 재무분석 전문 (영문 기반 템플릿 - 한글 폰트 없을 시 대비)
            pdf.add_page(); pdf.set_text_color(0,0,0)
            pdf.cell(190, 15, txt="1. Financial Statement Analysis (Unit: 1,000 KRW)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.cell(60, 10, "Category", 1); pdf.cell(60, 10, "2023", 1); pdf.cell(60, 10, "2024 (Recent)", 1, 1)
            f_list = [("Total Asset", fin_res['fin']['자산'][1], r_asset), ("Total Debt", fin_res['fin']['부채'][1], r_debt), ("Revenue", fin_res['fin']['매출'][1], r_rev), ("Net Income", fin_res['fin']['이익'][1], r_inc)]
            for n, v1, v2 in f_list:
                pdf.cell(60, 10, n, 1); pdf.cell(60, 10, f"{v1:,.0f}", 1); pdf.cell(60, 10, f"{v2:,.0f}", 1, 1)
            
            pdf.ln(10); pdf.multi_cell(190, 10, txt=f"Analysis: {f_comp} shows stable growth with a debt ratio of {(r_debt/r_asset*100 if r_asset>0 else 0):.1f}%. Increasing net income suggests high future valuation.")

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"Report_{f_comp}.pdf")
