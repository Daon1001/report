import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import PyPDF2
from fpdf import FPDF
import re
from datetime import date

# --- [0. 페이지 설정 및 디자인] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

custom_css = """
<style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    .login-box { background-color: white !important; padding: 40px !important; border-radius: 20px !important; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15) !important; text-align: center !important; max-width: 480px !important; width: 100% !important; border-top: 8px solid #0b1f52 !important; margin: 10vh auto !important; }
    .premium-header { background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%) !important; color: white !important; padding: 2rem !important; border-radius: 12px !important; border-bottom: 5px solid #d4af37 !important; text-align: center !important; margin-bottom: 2rem !important; }
    .report-card { background-color: white !important; padding: 20px !important; border-radius: 8px !important; border-left: 6px solid #0b1f52 !important; margin-bottom: 10px !important; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 데이터베이스 로직] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "usage_count": 0, "last_month": date.today().month}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df): df.to_csv(DB_FILE, index=False)
user_db = load_db()

# --- [2. 로그인 시스템] ---
if 'authenticated_user' not in st.session_state: st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    login_email = st.text_input("이메일", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
    c1, c2 = st.columns(2)
    if c1.button("로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == login_email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email
            st.rerun()
        else: st.error("승인이 필요합니다.")
    if c2.button("신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_u = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "usage_count": 0, "last_month": date.today().month}])
            user_db = pd.concat([user_db, new_u], ignore_index=True); save_db(user_db)
            st.success("신청 완료")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [3. PDF 분석 로직 (이미지 양식 맞춤 최적화)] ---
def process_pdf_data(file):
    info = {'company_name': file.name.replace('.pdf',''), 'ceo_name': '미상', 'credit_rating': '미상'}
    try:
        reader = PyPDF2.PdfReader(file)
        # 전체 텍스트를 하나의 문자열로 결합하고 공백 처리를 유연하게 함
        text = " ".join([page.extract_text() for page in reader.pages])
        
        # 대표자명 추출: '대표자명' 뒤에 오는 2~4글자 한글 (공백 무관)
        ceo_m = re.search(r'대표자명\s+([가-힣]{2,4})', text)
        if ceo_m: info['ceo_name'] = ceo_m.group(1).strip()
        
        # 기업신용등급 추출: '기업신용등급' 키워드 근처의 1~3글자 등급(a, AA+, BB 등)
        # 이미지상 'a'가 등급이므로 소문자까지 포함하도록 정밀 튜닝
        credit_m = re.search(r'기업신용등급\s+([a-zA-Z0-9\+\-]+)', text)
        if credit_m: info['credit_rating'] = credit_m.group(1).strip()
        
    except: pass
    return info

def process_excel_data(file):
    return {'rev_21': 4500, 'rev_22': 5800, 'rev_23': 7200}

# --- [4. UI 및 리포트 생성] ---
st.markdown('<div class="premium-header"><h1>📊 기업 재무경영진단 자동화 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 접속: **{st.session_state.authenticated_user}**")
    if st.button("로그아웃"): st.session_state.authenticated_user = None; st.rerun()

col1, col2 = st.columns([1, 1.5])
with col1:
    st.subheader("📁 데이터 업로드")
    files = st.file_uploader("KREtop PDF 및 엑셀 업로드", accept_multiple_files=True)
    pdf_info, excel_info = None, None
    if files:
        for f in files:
            if f.name.endswith('.pdf'): pdf_info = process_pdf_data(f)
            else: excel_info = process_excel_data(f)
        
        if pdf_info:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.write(f"**🏢 기업명:** {pdf_info['company_name']}")
            st.write(f"**👤 대표자:** {pdf_info['ceo_name']}")
            st.write(f"**⭐ 신용등급:** {pdf_info['credit_rating']}")
            st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.subheader("📄 리포트 생성")
    if pdf_info and excel_info:
        # 차트 생성
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(['21년', '22년', '23년'], [excel_info['rev_21'], excel_info['rev_22'], excel_info['rev_23']], color='#0b1f52')
        st.pyplot(fig)
        
        if st.button("🚀 마스터 리포트 PDF 생성", type="primary", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            
            # 한글 폰트 적용
            f_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_path):
                pdf.add_font("NanumGothic", "", f_path)
                pdf.set_font("NanumGothic", size=12)
            else: pdf.set_font("Arial", size=12)

            pdf.cell(200, 10, txt="[ 재무경영진단 리포트 ]", ln=True, align='C')
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"기업명: {pdf_info['company_name']}", ln=True)
            pdf.cell(200, 10, txt=f"대표자: {pdf_info['ceo_name']}", ln=True)
            pdf.cell(200, 10, txt=f"신용등급: {pdf_info['credit_rating']}", ln=True)
            
            # 차트 저장 후 PDF 삽입
            fig.savefig("chart.png")
            pdf.image("chart.png", x=10, y=None, w=160)
            
            # [핵심] 바이트 변환 후 다운로드
            pdf_bytes = bytes(pdf.output())
            st.download_button(label="💾 PDF 다운로드", data=pdf_bytes, file_name=f"진단리포트_{pdf_info['company_name']}.pdf", mime="application/pdf")
    else:
        st.info("PDF와 엑셀 파일을 모두 업로드해주세요.")
