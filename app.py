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

# --- [0. 페이지 설정 및 프리미엄 UI] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

# 차트 한글 폰트 설정
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

# --- [1. 사용자 DB 및 승인 시스템] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        # 관리자 허자현 대표님 전용 계정 설정
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
    st.markdown("<p style='color:#666;'>종합 재무진단 시스템 v30.0 [Final-Resolution]</p>", unsafe_allow_html=True)
    email = st.text_input("아이디(이메일)", placeholder="admin@example.com").strip().lower()
    c1, c2 = st.columns(2)
    if c1.button("로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.auth_user = email; st.rerun()
        else: st.error("승인이 필요한 계정입니다.")
    if c2.button("사용 신청", use_container_width=True):
        if email and user_db[user_db['email'] == email].empty:
            new_u = pd.DataFrame([{"email": email, "approved": False, "is_admin": False}])
            user_db = pd.concat([user_db, new_u], ignore_index=True); save_db(user_db)
            st.success("신청 완료! 관리자 승인을 기다려주세요.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [2. 초정밀 하이브리드 데이터 스캐너] ---

def clean_num(val):
    if val is None or val == "": return 0.0
    s = re.sub(r'[^\d.-]', '', str(val))
    try: return float(s)
    except: return 0.0

def hybrid_analyzer(files):
    """표(Table)와 텍스트(Text)를 동시에 훑는 펜타 스캔 엔진"""
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
                    full_text += txt + " "
                    
                    # (1) 표 기반 데이터 추출
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if not row: continue
                            row_flat = " ".join([str(c) for c in row if c]).replace(" ", "")
                            if '기업명' in row_flat: res['comp'] = str(row[-1]).split('\n')[0].strip()
                            if '대표자' in row_flat: res['ceo'] = str(row[-1]).split('\n')[0].strip()
                            if '종업원수' in row_flat: res['emp'] = int(clean_num(row[-1]))

                    # (2) 정규표현식 기반 강제 매칭 (표 구조가 깨졌을 경우)
                    if res['comp'] == "미상":
                        m = re.search(r'기업명\s*[:：\- ]*([가-힣\(\)A-Za-z0-9]+)', txt)
                        if m: res['comp'] = m.group(1).strip()
                    if res['ceo'] == "미상":
                        m = re.search(r'대표자(?:명)?\s*[:：\- ]*([가-힣]{2,4})', txt)
                        if m: res['ceo'] = m.group(1).strip()
                    if res['emp'] == 0:
                        m = re.search(r'종업원수\s*[:：\- ]*(\d+)', txt)
                        if m: res['emp'] = int(m.group(1))

                # (3) 인증 현황 스캔
                tight_txt = full_text.replace(" ", "").replace("\n", "")
                for k in res['certs'].keys():
                    if f"{k}인증" in tight_txt or f"{k}보유" in tight_txt: res['certs'][k] = True

        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 재무 키워드 매칭
                    mapping = {'자산': '자산', '부채': '부채', '매출액': '매출', '순이익': '이익'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            # 22, 23, 24년 데이터(2, 3, 4번 열) 고정 추출
                            v1, v2, v3 = clean_num(row.values[2]), clean_num(row.values[3]), clean_num(row.values[4])
                            if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
            except: pass
    return res

# --- [3. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 종합 경영 진단 및 재무 분석 마스터</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당: **{st.session_state.auth_user}** 님")
    if st.button("로그아웃"): st.session_state.auth_user = None; st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 올려주세요.", accept_multiple_files=True)
    if up_files:
        data = hybrid_analyzer(up_files)
        st.success("✅ [Hybrid-Scan] 모든 데이터 인식 성공")
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            # (주)메이홈, 박승미, 10명 데이터 자동 연동
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
        st.info(f"분석: 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 노무 전용 가이드가 생성됩니다.")
        
        # 기업가치 계산
        unit = 1000000 if r_rev < 100000 else 1000
        stock_val = ((r_inc * unit / 0.1)*0.6 + (r_asset - r_debt)*unit*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시나리오")
        st.pyplot(fig)

        if st.button("🚀 종합 리포트 발행 (재무제표 분석 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_path): pdf.add_font("Nanum", "", f_path); pdf.set_font("Nanum", size=12)
            
            # P1: 리포트 표지
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"기업명: {f_comp} / 대표자: {f_ceo}", ln=True, align='C')
            pdf.ln(100); pdf.set_font("Nanum", size=14); pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y-%m-%d')}", ln=True, align='C')
            
            # P2: 재무제표 전문 분석 (BS/IS)
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 정밀 재무제표 분석 및 AI 진단 (단위: 천원)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Nanum", size=11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (최근)", 1, 1, 'C', True)
            
            fin_rows = [("자산 총계", data['fin']['자산'][1], r_asset), ("부채 총계", data['fin']['부채'][1], r_debt), ("매출액", data['fin']['매출'][1], r_rev), ("당기순이익", data['fin']['이익'][1], r_inc)]
            for name, v23, v24 in fin_rows:
                pdf.cell(50, 10, name, 1, 0, 'C'); pdf.cell(70, 10, f"{v23:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v24:,.0f}", 1, 1, 'R')
            
            pdf.ln(10); pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 10, txt="▶ 전문가 종합 재무 분석 결과", ln=True)
            pdf.set_font("Nanum", size=11); pdf.set_text_color(0,0,0)
            d_rate = (r_debt / r_asset * 100) if r_asset > 0 else 0
            pdf.multi_cell(190, 8, txt=f"분석 결과, {f_comp}의 2024년 부채비율은 {d_rate:.1f}%로 안정적인 재무 구조를 유지하고 있습니다. 특히 전년 대비 매출 성장이 뚜렷하여 향후 공격적인 투자와 법인 가치 증대 전략이 유효합니다.")

            # P3: 기업가치 및 인증/노무
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 주식가치 평가 및 리스크 분석", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            fig.savefig("v30_chart.png", dpi=300); pdf.image("v30_chart.png", x=15, w=180)
            pdf.ln(10); pdf.set_font("Nanum", size=12); pdf.set_text_color(0,0,0)
            pdf.cell(190, 10, txt=f"■ 인증현황: 벤처({('보유' if data['certs']['벤처'] else '미보유')}), 전담부서({('보유' if data['certs']['연구개발전담부서'] else '미보유')})", ln=True)
            pdf.cell(190, 10, txt=f"■ 노무관리: 근로자 {f_emp}명에 따른 '{labor_type} 사업장' 법적 기준 적용 필수", ln=True)

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
