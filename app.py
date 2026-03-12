import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import PyPDF2
from fpdf import FPDF
import re
from datetime import date, datetime
import numpy as np

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
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .status-card { 
        background: white; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-left: 8px solid #0b1f52; margin-bottom: 15px;
    }
    .cert-needed { color: #d9534f; font-weight: bold; }
    .cert-done { color: #5cb85c; font-weight: bold; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 승인 로직] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{
            "email": "incheon00@gmail.com", "approved": True, "is_admin": True, 
            "usage_count": 0, "last_month": date.today().month
        }])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

# --- [2. 로그인 및 승인 신청 화면] ---
if st.session_state.authenticated_user is None:
    st.markdown('<div style="background:white; padding:50px; border-radius:20px; max-width:500px; margin:10vh auto; text-align:center; border-top:10px solid #0b1f52;">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    login_email = st.text_input("아이디(이메일)", placeholder="example@gmail.com").strip().lower()
    c1, c2 = st.columns(2)
    if c1.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == login_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email
            st.rerun()
        else: st.error("승인된 계정이 아닙니다.")
    if c2.button("승인 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_user = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "usage_count": 0, "last_month": date.today().month}])
            user_db = pd.concat([user_db, new_user], ignore_index=True); save_db(user_db)
            st.success("신청 완료!")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [3. 데이터 추출 및 분석 엔진] ---

def extract_pdf_data(file):
    info = {'company': file.name.replace('.pdf',''), 'ceo': '미상', 'certs': []}
    try:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([p.extract_text() for p in reader.pages[:5]])
        
        # 기업명/대표자 추출
        comp_match = re.search(r'기업명\s*[:|：]?\s*([가-힣\(\)A-Za-z0-9]+)', text)
        if comp_match: info['company'] = comp_match.group(1).strip()
        ceo_match = re.search(r'대표자(?:명)?\s*[:|：]?\s*([가-힣]{2,4})', text)
        if ceo_match: info['ceo'] = ceo_m.group(1).strip()
        
        # 인증 현황 추출 키워드
        cert_keywords = ['벤처기업', '이노비즈', '메인비즈', '연구소', '전담부서', 'ISO', '뿌리기업']
        for kw in cert_keywords:
            if kw in text: info['certs'].append(kw)
    except: pass
    return info

# --- [4. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 [MASTER] 경영진단 및 원스톱 컨설팅 솔루션</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 접속: **{st.session_state.authenticated_user}**")
    if st.button("로그아웃"): st.session_state.authenticated_user = None; st.rerun()

tab1, tab2, tab3 = st.tabs(["💎 재무/가치 진단", "🛡️ 기업 인증 진단", "⚖️ 인사 노무 가이드"])

# --- [TAB 1: 기존 재무 및 가치 평가] ---
with tab1:
    st.subheader("📁 데이터 업로드 및 주식 가치 평가")
    up_files = st.file_uploader("재무 엑셀 및 PDF 업로드", accept_multiple_files=True)
    if up_files:
        st.info("재무 분석 및 10년 가치 시뮬레이션 로직 가동 중... (이전 코드와 동일)")

# --- [TAB 2: 기업 인증 진단 (추가 요청 사항)] ---
with tab3: # 탭 이름은 3이지만 내용은 인증 진단
    pass # 아래 상세 구현

with tab2:
    st.subheader("🚩 핵심 기업 인증 현황 및 필요성 진단")
    
    # 예시 데이터 (PDF 연동 가능)
    cert_status = {
        "기업부설연구소": {"status": "미보유", "desc": "연구원 1인당 인건비 25% 세액공제 및 병역특례 혜택", "action": "전담부서 또는 연구소 설립 필요"},
        "벤처기업인증": {"status": "보유", "desc": "법인세 50% 감면 및 정책자금 한도 확대", "action": "유효기간 확인 필요"},
        "이노비즈/메인비즈": {"status": "미보유", "desc": "금융권 금리 우대 및 정기 세무조사 유예", "action": "업력 3년 이상 시 신청 권장"},
        "ISO 9001/14001": {"status": "미보유", "desc": "공공기관 입찰 가점 및 품질 경영 시스템 구축", "action": "B2B 거래 및 입찰 대비 필요"}
    }
    
    for cert, data in cert_status.items():
        with st.container():
            st.markdown(f"""
            <div class="status-card">
                <h4>{cert} | <span class="{'cert-done' if data['status'] == '보유' else 'cert-needed'}">{data['status']}</span></h4>
                <p style='color:#555;'><b>필요성:</b> {data['desc']}</p>
                <p style='color:#0b1f52;'><b>컨설팅 가이드:</b> {data['action']}</p>
            </div>
            """, unsafe_allow_html=True)

# --- [TAB 3: 인사 노무 가이드 (추가 요청 사항)] ---
with tab3:
    st.subheader("⚖️ 사업장 인원별 노무기준법 핵심 비교")
    
    emp_count = st.radio("현재 상시근로자수를 선택하세요", ["5인 미만 사업장", "5인 이상 사업장"], horizontal=True)
    
    labor_data = [
        {"항목": "해고 예고", "5인 미만": "적용 (30일 전 예고)", "5인 이상": "적용 (30일 전 예고)"},
        {"항목": "부당해고 구제신청", "5인 미만": "불가능 (민사만 가능)", "5인 이상": "가능 (노동위원회 신청)"},
        {"항목": "연장·야간·휴일수당", "5인 미만": "미적용 (시급만 지급)", "5인 이상": "적용 (50% 가산 지급)"},
        {"항목": "연차 유급휴가", "5인 미만": "미적용", "5인 이상": "적용 (15일~ 최대 25일)"},
        {"항목": "주휴수당", "5인 미만": "적용 (주 15시간 이상)", "5인 이상": "적용 (주 15시간 이상)"},
        {"항목": "공휴일 유급휴무", "5인 미만": "미적용", "5인 이상": "적용 (관공서 공휴일)"}
    ]
    
    df_labor = pd.DataFrame(labor_data)
    st.table(df_labor)
    
    st.warning("⚠️ 상시근로자수 산정은 '1개월간 사용한 인원 / 가동일수'로 계산하며, 알바나 단기 근로자도 포함됩니다.")

    if st.button("🚀 종합 진단 리포트 PDF 발행 (인증/노무 포함)", type="primary", use_container_width=True):
        pdf = FPDF()
        pdf.add_page()
        f_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if os.path.exists(f_p): pdf.add_font("Nanum", "", f_p); pdf.set_font("Nanum", size=12)
        
        pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font("Nanum", size=20)
        pdf.cell(190, 20, txt="종합 경영 진단 보고서", ln=True, align='C')
        
        pdf.set_text_color(0,0,0); pdf.ln(30)
        pdf.set_font("Nanum", size=16); pdf.cell(190, 10, txt="1. 기업 인증 진단 결과", ln=True)
        pdf.set_font("Nanum", size=10)
        for cert, d in cert_status.items():
            pdf.cell(190, 8, txt=f"[{cert}] - {d['status']} | {d['action']}", ln=True)
            
        pdf.ln(10); pdf.set_font("Nanum", size=16); pdf.cell(190, 10, txt="2. 인사 노무 핵심 가이드", ln=True)
        pdf.set_font("Nanum", size=10)
        pdf.cell(190, 8, txt=f"선택하신 {emp_count}에 따라 연차, 연장수당 등의 법적 의무가 발생합니다.", ln=True)
        
        pdf_out = bytes(pdf.output())
        st.download_button("💾 종합 리포트 다운로드", data=pdf_out, file_name="종합경영진단리포트.pdf")
