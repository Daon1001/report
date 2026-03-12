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
    .report-card { background-color: white !important; padding: 25px !important; border-radius: 12px !important; border-left: 8px solid #0b1f52 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; margin-bottom: 15px !important; }
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

# --- [3. PDF 분석 로직 (강화된 정규표현식)] ---
def process_pdf_data(file):
    info = {'company_name': file.name.replace('.pdf',''), 'ceo_name': '미상', 'credit_rating': '미상'}
    try:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([page.extract_text() for page in reader.pages])
        
        # 더 넓은 범위의 패턴 검색 (공백, 콜론 유무 대응)
        ceo_m = re.search(r'대표자(?:명)?\s*[:|：]?\s*([가-힣]{2,4})', text)
        if ceo_m: info['ceo_name'] = ceo_m.group(1).strip()
        
        credit_m = re.search(r'기업신용등급\s*[:|：]?\s*([a-zA-Z0-9\+\-]+)', text)
        if credit_m: info['credit_rating'] = credit_m.group(1).strip()
    except: pass
    return info

# --- [4. 메인 대시보드 UI] ---
st.markdown('<div class="premium-header"><h1>📊 기업 재무경영진단 자동화 시스템</h1></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("📁 파일 업로드")
    files = st.file_uploader("KREtop PDF 및 엑셀 업로드", accept_multiple_files=True)
    
    final_pdf_info = None
    if files:
        for f in files:
            if f.name.endswith('.pdf'): final_pdf_info = process_pdf_data(f)
        
        if final_pdf_info:
            st.markdown("### 🔍 추출 정보 확인 (수정 가능)")
            # 미상으로 나올 경우 사용자가 직접 입력할 수 있게 함
            final_pdf_info['company_name'] = st.text_input("🏢 기업명", final_pdf_info['company_name'])
            final_pdf_info['ceo_name'] = st.text_input("👤 대표자명", final_pdf_info['ceo_name'])
            final_pdf_info['credit_rating'] = st.text_input("⭐ 신용등급", final_pdf_info['credit_rating'])

with col2:
    st.subheader("📄 리포트 디자인 미리보기")
    if final_pdf_info:
        # 차트 예시 데이터 생성
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(['21년', '22년', '23년'], [4500, 5800, 7200], color='#0b1f52')
        ax.set_title("매출 성장 추이", fontsize=15, pad=20)
        st.pyplot(fig)
        
        if st.button("🚀 마스터 리포트 PDF 생성", type="primary", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            
            # 폰트 설정
            f_path = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
            if not os.path.exists(f_path): f_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            
            if os.path.exists(f_path):
                pdf.add_font("NanumGothic", "", f_path)
                pdf.set_font("NanumGothic", size=14)
            else: pdf.set_font("Arial", size=14)

            # 디자인 레이아웃 (테두리 및 헤더)
            pdf.rect(5, 5, 200, 287) # 전체 테두리
            pdf.set_fill_color(11, 31, 82) # 남색 배경
            pdf.rect(5, 5, 200, 30, 'F')
            
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("NanumGothic", size=20)
            pdf.cell(200, 20, txt="RE-PORT: 재무경영진단 결과 보고서", ln=True, align='C')
            
            pdf.set_text_color(0, 0, 0)
            pdf.ln(25)
            pdf.set_font("NanumGothic", size=15)
            pdf.cell(50, 15, txt=f"기업명: {final_pdf_info['company_name']}", ln=True)
            pdf.cell(50, 15, txt=f"대표자: {final_pdf_info['ceo_name']}", ln=True)
            pdf.cell(50, 15, txt=f"신용등급: {final_pdf_info['credit_rating']}", ln=True)
            
            pdf.ln(10)
            fig.savefig("chart_final.png", dpi=300)
            pdf.image("chart_final.png", x=20, y=None, w=170)
            
            pdf_bytes = bytes(pdf.output())
            st.download_button(label="💾 완성된 PDF 리포트 다운로드", data=pdf_bytes, file_name=f"진단리포트_{final_pdf_info['company_name']}.pdf", mime="application/pdf")
    else:
        st.info("좌측에 PDF 파일을 업로드하면 정밀 분석 리포트 생성이 시작됩니다.")
