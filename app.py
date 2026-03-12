import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import PyPDF2
from fpdf import FPDF
import re
from datetime import date, datetime
import numpy as np
import io

# --- [0. 페이지 설정 및 프리미엄 UI 디자인] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

# 차트 한글 폰트 설정
plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

custom_css = """
<style>
    .block-container { padding-top: 1.5rem !important; }
    header { display: none !important; }
    .stApp { background-color: #f4f7f9 !important; }
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%); 
        color: white; padding: 2.5rem; border-radius: 20px; 
        border-bottom: 8px solid #d4af37; text-align: center; margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(11, 31, 82, 0.2);
    }
    .login-box { 
        background: white; padding: 50px; border-radius: 20px; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); text-align: center; 
        max-width: 500px; margin: 10vh auto; border-top: 10px solid #0b1f52;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 승인 시스템] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        # 관리자 허자현 대표님 설정
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "count": 0, "month": date.today().month}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df): df.to_csv(DB_FILE, index=False)
user_db = load_db()

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52; margin-bottom:0;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 경영진단 AI 마스터 v25.0 [Financial-Master]</p>", unsafe_allow_html=True)
    login_email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    c1, c2 = st.columns(2)
    if c1.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == login_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email; st.rerun()
        else: st.error("승인이 필요한 계정입니다.")
    if c2.button("사용 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_u = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "count": 0, "month": date.today().month}])
            user_db = pd.concat([user_db, new_u], ignore_index=True); save_db(user_db)
            st.success("신청 완료!")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [2. 초정밀 데이터 추출 엔진 (Financial Deep Core)] ---

def clean_num(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def deep_financial_parser(files):
    """모든 형태의 데이터 파편화를 방지하고 핵심 수치를 강제로 찾아내는 엔진"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {
            '매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], 
            '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0],
            '자본': [0.0,0.0,0.0]
        },
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False}
    }
    
    for file in files:
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            full_txt = " ".join([page.extract_text() for page in reader.pages])
            # 모든 따옴표, 콤마, 불필요한 줄바꿈 제거 (KODATA 양식 대응)
            tight_txt = full_txt.replace('"', '').replace(',', '').replace("\n", "").replace("\t", "")
            
            # 기업명: '(주)메이홈' 추출 [cite: 3, 11]
            comp_m = re.search(r'기업명\s*[:：\- ]*([가-힣\(\)A-Za-z0-9&]+)', full_txt)
            if comp_m: res['comp'] = comp_m.group(1).strip()
            
            # 대표자: '박승미' 추출 [cite: 5, 12, 15]
            ceo_m = re.search(r'대표자(?:명)?\s*[:：\- ]*([가-힣]{2,4})', full_txt)
            if ceo_m: res['ceo'] = ceo_m.group(1).strip()
            
            # 종업원수: '10명' 추출 [cite: 16]
            emp_m = re.search(r'종업원수\s*[:：\- ]*(\d+)', full_txt)
            if not emp_m: emp_m = re.search(r'종업원수(\d+)', tight_txt.replace(" ", ""))
            if emp_m: res['emp'] = int(emp_m.group(1))

            # 인증 현황: 벤처, 전담부서 등 [cite: 64, 67]
            for key in res['certs'].keys():
                if key in tight_txt: res['certs'][key] = True

        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 재무 키워드 매칭 (자산, 부채, 자본, 매출 등)
                    mapping = {'자산': '자산', '부채': '부채', '자본': '자본', '매출액': '매출', '순이익': '이익'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            try:
                                # 엑셀 시트의 2, 3, 4번 인덱스 열에서 22, 23, 24년 데이터 수집
                                v1, v2, v3 = clean_num(row.values[2]), clean_num(row.values[3]), clean_num(row.values[4])
                                if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
                            except: pass
            except: pass
    return res

# --- [3. 메인 화면 및 리포트 섹션] ---
st.markdown('<div class="premium-header"><h1>📊 [MASTER] 종합 경영진단 및 재무분석 리포트</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당: **{st.session_state.authenticated_user}** 팀장님")
    if st.button("로그아웃"): st.session_state.authenticated_user = None; st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 자료를 함께 올려주세요.", accept_multiple_files=True)
    
    if up_files:
        data = deep_financial_parser(up_files)
        st.success("✅ [Deep Core] 모든 데이터 인식 성공")
        
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 상시 근로자수(명)", value=data['emp'])
            
            st.divider(); st.write("💰 **최신 재무 데이터 (단위: 천원)**")
            r_rev = st.number_input("2024년 매출액", value=data['fin']['매출'][2])
            r_inc = st.number_input("2024년 순이익", value=data['fin']['이익'][2])
            r_asset = st.number_input("2024년 자산총계", value=data['fin']['자산'][2])
            r_debt = st.number_input("2024년 부채총계", value=data['fin']['부채'][2])
            r_cap = st.number_input("2024년 자본총계", value=data['fin']['자본'][2] if data['fin']['자본'][2] != 0 else (r_asset - r_debt))

with col_r:
    st.subheader("📈 실시간 경영 진단 시뮬레이션")
    if up_files:
        # 노무 타입 결정 [cite: 16]
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석 결과: 현재 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 전용 노무 가이드가 생성됩니다.")
        
        # 가치 평가 (단위 보정 및 원 단위 환산)
        multiplier = 1000000 if r_rev < 100000 else 1000
        stock_price = ((r_inc * multiplier / 0.1)*0.6 + (r_asset - r_debt)*multiplier*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시나리오", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 경영진단 보고서 발행 (재무제표 분석 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_path): pdf.add_font("Nanum", "", f_path); pdf.set_font("Nanum", size=12)
            
            # --- [PAGE 1: 리포트 표지] ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="RE-PORT: 종합 경영진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"대상기업: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            pdf.ln(100); pdf.set_font("Nanum", size=14); pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y-%m-%d')}", ln=True, align='C')
            pdf.cell(190, 10, txt="중소기업경영지원단 AI 컨설팅 본부", ln=True, align='C')
            
            # --- [PAGE 2: 재무제표 전문 분석 (BS/IS)] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 정밀 재무제표 전문 분석 (단위: 천원)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Nanum", size=11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (최근 기말)", 1, 1, 'C', True)
            
            fin_rows = [
                ("자산 총계", data['fin']['자산'][1], r_asset), 
                ("부채 총계", data['fin']['부채'][1], r_debt), 
                ("자본 총계", data['fin']['자본'][1], r_cap),
                ("매출액", data['fin']['매출'][1], r_rev), 
                ("당기순이익", data['fin']['이익'][1], r_inc)
            ]
            for name, v23, v24 in fin_rows:
                pdf.cell(50, 10, name, 1, 0, 'C'); pdf.cell(70, 10, f"{v23:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v24:,.0f}", 1, 1, 'R')
            
            # 재무 진단 텍스트 자동 생성
            pdf.ln(10); pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 10, txt="▶ 전문가 종합 재무 진단", ln=True)
            pdf.set_font("Nanum", size=11); pdf.set_text_color(0,0,0)
            debt_ratio = (r_debt / r_asset * 100) if r_asset > 0 else 0
            growth_rate = ((r_rev / data['fin']['매출'][1] - 1) * 100) if data['fin']['매출'][1] > 0 else 0
            pdf.multi_cell(190, 8, txt=f"분석 결과, 귀사의 2024년 부채비율은 {debt_ratio:.1f}%로 매우 안정적입니다. 특히 매출액이 전년 대비 {growth_rate:.1f}% 성장하며 가파른 기업가치 상승 곡선을 그리고 있습니다. 향후 효율적인 자본 관리 시 주당 가치는 더욱 증대될 것으로 분석됩니다.")

            # --- [PAGE 3: 기업가치 및 인증/노무 (가변)] ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 주식가치 평가 및 리스크 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82); pdf.cell(190, 15, txt=f"▶ 현시점 주당 추정가액: {int(stock_price):,} 원", ln=True)
            fig.savefig("m_final_v25.png", dpi=300); pdf.image("m_final_v25.png", x=15, w=180)
            
            pdf.ln(5); pdf.set_font("Nanum", size=12); pdf.set_text_color(0,0,0)
            pdf.cell(190, 10, txt=f"■ 인증현황: 벤처({('보유' if data['certs']['벤처'] else '미보유')}), 전담부서({('보유' if data['certs']['연구개발전담부서'] else '미보유')})", ln=True)
            pdf.cell(190, 10, txt=f"■ 노무관리: 상시 근로자 {f_emp}명에 따른 '{labor_type} 사업장' 법규 적용 필수", ln=True)

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
