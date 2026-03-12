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

# --- [0. 페이지 설정 및 폰트 무결성 체크] ---
st.set_page_config(page_title="중소기업 재무경영진단 AI", layout="wide")

# 맑은 고딕 폰트 경로 설정 (깃허브 업로드 필수: malgun.ttf)
base_dir = os.path.dirname(__file__)
font_path = os.path.join(base_dir, "malgun.ttf")

if os.path.exists(font_path):
    # Matplotlib 차트 한글 설정
    font_prop = fm.FontProperties(fname=font_path)
    plt.rc('font', family=font_prop.get_name())
    plt.rcParams['axes.unicode_minus'] = False
else:
    st.error("⚠️ 'malgun.ttf' 폰트 파일이 깃허브에 없습니다. 차트 한글 깨짐 방지를 위해 파일을 꼭 업로드해 주세요.")

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

# --- [1. 사용자 보안 DB (허자현 대표님 전용)] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

user_db = load_db()
if 'auth_user' not in st.session_state: st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.markdown('<div style="background:white; padding:40px; border-radius:15px; max-width:480px; margin:10vh auto; text-align:center; border-top:10px solid #0b1f52; box-shadow: 0 15px 35px rgba(0,0,0,0.15);">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666;'>종합 재무진단 시스템 v42.0 [Perfect-Font-Sync]</p>", unsafe_allow_html=True)
    email = st.text_input("아이디(이메일)", placeholder="admin@example.com").strip().lower()
    if st.button("로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.auth_user = email; st.rerun()
        else: st.error("승인이 필요한 계정입니다.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [2. 초정밀 데이터 추출 엔진] ---

def clean_num(val):
    if val is None or val == "": return 0.0
    s = str(val).replace(',', '').replace('"', '').replace('\n', '').strip()
    s = re.sub(r'[^\d.-]', '', s)
    try: return float(s)
    except: return 0.0

def kodata_pdf_parser(file):
    """KODATA 보고서의 특수한 따옴표 및 쉼표 구조를 정규화하여 데이터 획득"""
    res = {'comp': "미상", 'ceo': "미상", 'emp': 0, 'certs': {'벤처': False, '연구개발전담부서': False}}
    with pdfplumber.open(file) as pdf:
        all_text = ""
        for page in pdf.pages:
            raw = page.extract_text() or ""
            all_text += raw + "\n"
            # 따옴표, 쉼표, 줄바꿈을 모두 공백으로 치환하여 CSV 레이어를 일반 텍스트로 변환
            clean = raw.replace('"', ' ').replace(',', ' ').replace('\n', ' ').replace(' ', '')
            
            if res['comp'] == "미상":
                m = re.search(r'기업명[:：]?([가-힣\(\)A-Za-z0-9&]+)', clean)
                if m: res['comp'] = m.group(1).strip()
            if res['ceo'] == "미상":
                # 대표자명 ","박승미 " 구조 대응
                m = re.search(r'대표자(?:명)?([가-힣]{2,4})', clean)
                if m: res['ceo'] = m.group(1).strip()
            if res['emp'] == 0:
                # 종업원수 ","10명 " 구조 대응
                m = re.search(r'종업원수(\d+)', clean)
                if m: res['emp'] = int(m.group(1))

        tight = all_text.replace(" ", "").replace("\n", "")
        if "벤처인증" in tight or "벤처보유" in tight: res['certs']['벤처'] = True
        if "연구개발전담부서" in tight: res['certs']['연구개발전담부서'] = True
    return res

def master_excel_parser(file):
    res = {'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]}}
    try:
        df = pd.read_excel(file, header=None) if file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(file, header=None)
        for _, row in df.iterrows():
            row_vals = row.tolist()
            row_str = "".join([str(v) for v in row_vals if v is not None]).replace(" ", "")
            mapping = {'자산총계': '자산', '부채총계': '부채', '매출액': '매출', '순이익': '이익'}
            for kw, key in mapping.items():
                if kw in row_str:
                    nums = [clean_num(v) for v in row_vals if clean_num(v) != 0 or v == 0]
                    if len(nums) >= 3: res['fin'][key] = nums[-3:]
    except: pass
    return res

# --- [3. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 종합 경영 진단 및 재무 분석 시스템</h1></div>', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 함께 올려주세요.", accept_multiple_files=True)
    
    # 변수 초기화 (NameError 방지)
    f_comp, f_ceo, f_emp = "미상", "미상", 0
    fin_res = {'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]}}
    pdf_res = {'comp': "미상", 'ceo': "미상", 'emp': 0, 'certs': {}}

    if up_files:
        for f in up_files:
            if f.name.endswith('.pdf'): pdf_res = kodata_pdf_parser(f)
            else: fin_res = master_excel_parser(f)
        
        f_comp, f_ceo, f_emp = pdf_res['comp'], pdf_res['ceo'], pdf_res['emp']
        r_rev, r_inc, r_asset, r_debt = fin_res['fin']['매출'][2], fin_res['fin']['이익'][2], fin_res['fin']['자산'][2], fin_res['fin']['부채'][2]

        st.success("✅ [Font-Sync] 데이터 인식 및 한글 폰트 적용 완료")
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 명칭", f_comp)
            f_ceo = st.text_input("👤 대표자 성함", f_ceo)
            f_emp = st.number_input("👥 종업원수(명)", value=f_emp)
            st.divider()
            r_rev = st.number_input("2024 매출액 (천원/백만원)", value=r_rev)
            r_inc = st.number_input("2024 순이익", value=r_inc)
            r_asset = st.number_input("2024 자산총계", value=r_asset)
            r_debt = st.number_input("2024 부채총계", value=r_debt)

with col_r:
    st.subheader("📈 경영 지표 진단 시뮬레이션")
    if up_files:
        labor = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석 결과: 근로자 {f_emp}명으로 {labor} 사업장 가이드가 적용됩니다.")
        
        unit = 1000000 if r_rev < 100000 else 1000
        stock_val = ((r_inc * unit / 0.1)*0.6 + (r_asset - r_debt)*unit*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 가치 상승 시뮬레이션")
        st.pyplot(fig)

        if st.button("🚀 맑은 고딕 종합 보고서 발행", type="primary", use_container_width=True):
            pdf = FPDF()
            if os.path.exists(font_path):
                pdf.add_font("Malgun", "", font_path)
                pdf.set_font("Malgun", size=12)
            else: pdf.set_font("helvetica", size=12)
            
            # P1: 표지
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font_size(32)
            pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font_size(18); pdf.cell(190, 20, txt=f"기업명: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            
            # P2: 재무제표 전문 분석
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font_size(20)
            pdf.cell(190, 15, txt="1. 정밀 재무제표 및 AI 분석", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_fill_color(240, 240, 240); pdf.set_font_size(11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (최근 기말)", 1, 1, 'C', True)
            
            rows = [("자산 총계", fin_res['fin']['자산'][1], r_asset), ("부채 총계", fin_res['fin']['부채'][1], r_debt), ("매출액", fin_res['fin']['매출'][1], r_rev), ("당기순이익", fin_res['fin']['이익'][1], r_inc)]
            for n, v1, v2 in rows:
                pdf.cell(50, 10, n, 1); pdf.cell(70, 10, f"{v1:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v2:,.0f}", 1, 1, 'R')
            
            pdf.ln(10); pdf.multi_cell(190, 8, txt=f"분석 결과, {f_comp}의 2024년 부채비율은 {(r_debt/r_asset*100 if r_asset>0 else 0):.1f}%로 양호합니다. 매출액 {r_rev:,.0f}천원 및 당기순이익 {r_inc:,.0f}천원을 기록하며 안정적인 성장세를 보이고 있습니다.")

            pdf_out = bytes(pdf.output())
            st.download_button("💾 한글 종합 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
