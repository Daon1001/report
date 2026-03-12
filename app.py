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

# --- [0. 페이지 설정 및 프리미엄 디자인] ---
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
    }
    .login-box { 
        background: white; padding: 50px; border-radius: 20px; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.1); text-align: center; 
        max-width: 500px; margin: 10vh auto; border-top: 10px solid #0b1f52;
    }
    .cert-tag { padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 0.85rem; }
    .tag-have { background-color: #e8f5e9; color: #2e7d32; }
    .tag-none { background-color: #ffebee; color: #c62828; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 승인 시스템] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "usage_count": 0, "last_month": date.today().month}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df): df.to_csv(DB_FILE, index=False)
user_db = load_db()

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    email = st.text_input("아이디(이메일)", placeholder="admin@example.com").strip().lower()
    c1, c2 = st.columns(2)
    if c1.button("로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.authenticated_user = email; st.rerun()
        else: st.error("승인이 필요한 계정입니다.")
    if c2.button("승인 신청", use_container_width=True):
        if email and user_db[user_db['email'] == email].empty:
            new_u = pd.DataFrame([{"email": email, "approved": False, "is_admin": False, "usage_count": 0, "last_month": date.today().month}])
            user_db = pd.concat([user_db, new_u], ignore_index=True); save_db(user_db)
            st.success("신청 완료! 관리자 승인 후 이용 가능합니다.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [2. 정밀 파일 파싱 엔진 (재무/인증/노무)] ---

def clean_num(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def analyze_files(files):
    """파일을 읽어 재무, 인증, 인원수 데이터를 통합 추출"""
    data = {
        'financials': {'매출액': [0.0,0.0,0.0], '당기순이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처기업': False, '이노비즈': False, '메인비즈': False, '기업부설연구소': False, 'ISO': False},
        'employee_count': 0,
        'company_name': "신용",
        'ceo_name': "허자현"
    }
    
    for file in files:
        # 1. 재무 데이터 추출 (Excel/CSV)
        if file.name.endswith(('.xlsx', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 재무 키워드 매칭
                    if '매출액' in row_txt:
                        nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                        if len(nums) >= 3: data['financials']['매출액'] = nums[-3:]
                    if '순이익' in row_txt:
                        nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                        if len(nums) >= 3: data['financials']['당기순이익'] = nums[-3:]
                    if '자산총계' in row_txt:
                        nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                        if len(nums) >= 3: data['financials']['자산'] = nums[-3:]
                    if '부채총계' in row_txt:
                        nums = [clean_num(v) for v in row.values if clean_num(v) != 0]
                        if len(nums) >= 3: data['financials']['부채'] = nums[-3:]
            except: pass

        # 2. 기업 정보 및 인증/노무 추출 (PDF/Excel)
        try:
            full_text = ""
            if file.name.endswith('.pdf'):
                reader = PyPDF2.PdfReader(file)
                full_text = " ".join([p.extract_text() for p in reader.pages])
            else:
                full_text = str(df.values)

            # 대표자/기업명
            ceo_m = re.search(r'대표자(?:명)?\s*[:|：]?\s*([가-힣]{2,4})', full_text)
            if ceo_m: data['ceo_name'] = ceo_m.group(1).strip()
            
            # 인원수 추출
            emp_m = re.search(r'(?:종업원수|근로자수|임직원수)\s*[:|：]?\s*(\d+)', full_text)
            if emp_m: data['employee_count'] = int(emp_m.group(1))
            
            # 인증 추출
            for cert in data['certs'].keys():
                if cert in full_text.replace(" ", ""): data['certs'][cert] = True
        except: pass
        
    return data

# --- [3. 메인 대시보드 및 리포트 섹션] ---
st.markdown('<div class="premium-header"><h1>📊 파일 분석 기반 종합 경영진단 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 접속: **{st.session_state.authenticated_user}**")
    if st.button("로그아웃"): st.session_state.authenticated_user = None; st.rerun()

col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("📂 진단 파일 업로드")
    up_files = st.file_uploader("KREtop PDF 및 재무 엑셀을 모두 선택하세요.", accept_multiple_files=True)
    
    if up_files:
        analysis = analyze_files(up_files)
        st.success("✅ 파일 데이터 추출 완료")
        
        with st.expander("📝 추출 결과 보정 (필요시 수정)", expanded=True):
            comp_name = st.text_input("기업명", analysis['company_name'])
            ceo_name = st.text_input("대표자", analysis['ceo_name'])
            emp_count = st.number_input("상시 근로자수(명)", value=analysis['employee_count'])
            
            st.divider()
            st.write("🚩 **핵심 인증 보유 현황**")
            c_cols = st.columns(2)
            c_vals = {}
            for i, (cert, have) in enumerate(analysis['certs'].items()):
                c_vals[cert] = c_cols[i%2].checkbox(cert, value=have)
            
            st.divider()
            st.write("💰 **재무 수치 (천원 단위)**")
            f_rev = st.number_input("최신 매출액", value=analysis['financials']['매출액'][2])
            f_inc = st.number_input("최신 순이익", value=analysis['financials']['당기순이익'][2])

with col_right:
    st.subheader("📋 실시간 리포트 구성 미리보기")
    if up_files:
        # 1. 노무 진단 영역
        st.markdown("#### ⚖️ 인사 노무 기준법 진단")
        labor_type = "5인 이상" if emp_count >= 5 else "5인 미만"
        st.info(f"현재 **{emp_count}명**으로 **{labor_type} 사업장** 기준이 적용됩니다.")
        
        # 2. 주식 가치 시뮬레이션
        # 천원 -> 원 환산 계산 로직 적용
        stock_price = ((f_inc * 1000 / 0.1) * 0.6 + (analysis['financials']['자산'][2] - analysis['financials']['부채'][2]) * 1000 * 0.4) / 100000
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.3, stock_price*2.5], marker='o', color='#0b1f52')
        ax.set_title("미래 주식가치 상승 예측")
        st.pyplot(fig)

        if st.button("🚀 자동화 종합 리포트 발행 (PDF)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_p): pdf.add_font("Nanum", "", f_p); pdf.set_font("Nanum", size=12)
            
            # --- [PAGE 1: 표지] ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(80); pdf.set_font("Nanum", size=30)
            pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=18); pdf.cell(190, 20, txt=f"고객사: {comp_name}", ln=True, align='C')
            
            # --- [PAGE 2: 재무 및 가치평가] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=18)
            pdf.cell(190, 15, txt="1. 재무 지표 및 가치 평가", ln=True); pdf.line(10, 25, 200, 25); pdf.ln(10)
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"■ 최신 매출액: {f_rev:,.0f} 천원", ln=True)
            pdf.cell(190, 15, txt=f"▶ 현시점 주당 추정가액: {int(stock_price):,} 원", ln=True)
            fig.savefig("p2_chart.png", dpi=300); pdf.image("p2_chart.png", x=15, w=180)
            
            # --- [PAGE 3: 기업 인증 진단 (자동 추가)] ---
            pdf.add_page(); pdf.set_font("Nanum", size=18)
            pdf.cell(190, 15, txt="2. 핵심 기업 인증 진단 리포트", ln=True); pdf.line(10, 25, 200, 25); pdf.ln(10)
            pdf.set_font("Nanum", size=12)
            
            cert_details = {
                "기업부설연구소": "연구원 인건비 25% 세액공제 및 취득세 감면 필수 인증",
                "벤처기업": "법인세 50% 감면 및 정부 정책자금 한도 우대 혜택",
                "ISO": "공공기관 입찰 가점 및 품질 경영 시스템 대외 신뢰도 확보"
            }
            
            for cert, desc in cert_details.items():
                status = "보유" if c_vals.get(cert, False) else "미보유 (필요)"
                pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
                pdf.cell(190, 10, txt=f"● {cert} : {status}", ln=True)
                pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(180, 8, txt=f"필요성: {desc}\n")
                if "미보유" in status:
                    pdf.set_text_color(200, 0, 0)
                    pdf.cell(190, 8, txt="→ 조속한 시일 내 취득 전략 수립이 필요합니다.", ln=True)
                pdf.ln(5); pdf.set_text_color(0,0,0)

            # --- [PAGE 4: 노무 기준 진단 (자동 추가)] ---
            pdf.add_page(); pdf.set_font("Nanum", size=18)
            pdf.cell(190, 15, txt="3. 상시 인원별 노무 의무 진단", ln=True); pdf.line(10, 25, 200, 25); pdf.ln(10)
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"귀사의 상시 근로자수는 {emp_count}명으로, '{labor_type} 사업장' 법규가 적용됩니다.", ln=True)
            pdf.ln(5)
            
            labor_rules = [
                ("연차 유급 휴가", "적용 (15일~)", "미적용"),
                ("연장/야간 수당", "적용 (50% 가산)", "미적용 (시급 지급)"),
                ("부당해고 구제", "노동위원회 신청 가능", "민사 소송만 가능"),
                ("주휴 수당", "공통 적용", "공통 적용")
            ]
            
            pdf.set_fill_color(240, 240, 240); pdf.cell(60, 10, "구분", 1, 0, 'C', True)
            pdf.cell(130, 10, f"{labor_type} 사업장 적용 기준", 1, 1, 'C', True)
            for title, high, low in labor_rules:
                pdf.cell(60, 10, title, 1, 0, 'C')
                pdf.cell(130, 10, high if emp_count >= 5 else low, 1, 1, 'L')

            pdf_bytes = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_bytes, file_name=f"종합진단_{comp_name}.pdf")
    else:
        st.info("좌측에 파일을 업로드하면 인증 및 노무 페이지가 포함된 리포트가 자동 구성됩니다.")
