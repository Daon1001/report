import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import PyPDF2
from fpdf import FPDF
import re
from datetime import date, datetime

# --- [0. 페이지 설정 및 프리미엄 디자인 CSS] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

# 차트 한글 폰트 설정
plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

custom_css = """
<style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    
    /* 로그인 박스 디자인 */
    .login-box { 
        background-color: white !important; 
        padding: 40px !important; 
        border-radius: 20px !important; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15) !important; 
        text-align: center !important; 
        max-width: 480px !important; 
        width: 100% !important; 
        border-top: 8px solid #0b1f52 !important; 
        margin: 10vh auto !important; 
    }
    
    /* 상단 헤더 디자인 */
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%) !important; 
        color: white !important; 
        padding: 2rem !important; 
        border-radius: 12px !important; 
        border-bottom: 5px solid #d4af37 !important; 
        text-align: center !important; 
        margin-bottom: 2rem !important; 
    }
    
    /* 정보 카드 디자인 */
    .report-card { 
        background-color: white !important; 
        padding: 25px !important; 
        border-radius: 12px !important; 
        border-left: 8px solid #0b1f52 !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; 
        margin-bottom: 15px !important; 
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 로직] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        # 초기 관리자 계정 설정
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "usage_count": 0, "last_month": date.today().month}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

# --- [2. 로그인 및 회원가입 시스템] ---
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666;'>재무진단 마스터 시스템</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("이메일 입력", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
    
    col_l, col_r = st.columns(2)
    if col_l.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == login_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email
            st.rerun()
        elif not user_row.empty and not user_row.iloc[0]['approved']:
            st.warning("⚠️ 관리자의 승인을 기다리는 중입니다.")
        else:
            st.error("❌ 등록되지 않은 이메일입니다. 신청을 먼저 해주세요.")
            
    if col_r.button("사용 신청", use_container_width=True):
        if login_email:
            if user_db[user_db['email'] == login_email].empty:
                new_user = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "usage_count": 0, "last_month": date.today().month}])
                user_db = pd.concat([user_db, new_user], ignore_index=True)
                save_db(user_db)
                st.success("✅ 신청 완료! 관리자 승인 후 이용 가능합니다.")
            else:
                st.info("이미 신청된 이메일입니다.")
        else:
            st.error("이메일을 입력해주세요.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. PDF 분석 및 데이터 추출 로직] ---
def process_pdf_data(file):
    info = {'company_name': file.name.replace('.pdf',''), 'ceo_name': '미상', 'credit_rating': '미상'}
    try:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([page.extract_text() for page in reader.pages])
        
        # 대표자명 추출 (이미지 양식 대응: '대표자명' 뒤의 한글 2~4자)
        ceo_match = re.search(r'대표자(?:명)?\s*[:|：]?\s*([가-힣]{2,4})', text)
        if ceo_match: info['ceo_name'] = ceo_match.group(1).strip()
        
        # 신용등급 추출 (이미지 양식 대응: '기업신용등급' 근처의 등급 기호)
        credit_match = re.search(r'기업신용등급\s*[:|：]?\s*([a-zA-Z0-9\+\-]+)', text)
        if credit_match: info['credit_rating'] = credit_match.group(1).strip()
    except:
        pass
    return info

# --- [4. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 기업 재무경영진단 자동화 시스템</h1></div>', unsafe_allow_html=True)

# 사이드바 관리자 설정
with st.sidebar:
    st.write(f"👤 **{st.session_state.authenticated_user}** 팀장님")
    if st.button("로그아웃"):
        st.session_state.authenticated_user = None
        st.rerun()
    
    # 관리자 전용 승인 메뉴
    curr_user = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if curr_user['is_admin']:
        st.divider()
        st.subheader("👑 관리자 권한")
        st.write("사용자 승인 관리")
        st.dataframe(user_db[['email', 'approved']], height=200)
        target = st.selectbox("상태 변경 대상", user_db['email'])
        if st.button("승인 상태 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db)
            st.rerun()

# 파일 업로드 및 분석 영역
col1, col2 = st.columns([1, 1.3])

with col1:
    st.subheader("📁 파일 업로드")
    uploaded_files = st.file_uploader("KREtop PDF 및 재무 엑셀 업로드", accept_multiple_files=True)
    
    extracted_info = None
    if uploaded_files:
        for f in uploaded_files:
            if f.name.endswith('.pdf'):
                extracted_info = process_pdf_data(f)
        
        if extracted_info:
            st.markdown("### 📝 정보 확인 및 수정")
            st.info("추출된 정보가 틀릴 경우 직접 수정하신 후 리포트를 생성하세요.")
            # 사용자 수정 가능 필드
            final_company = st.text_input("🏢 기업명", extracted_info['company_name'])
            final_ceo = st.text_input("👤 대표자명", extracted_info['ceo_name'])
            final_rating = st.text_input("⭐ 신용등급", extracted_info['credit_rating'])
            
            # 리포트 데이터 객체 업데이트
            report_data = {
                'company': final_company,
                'ceo': final_ceo,
                'rating': final_rating
            }
        else:
            report_data = None
    else:
        report_data = None

with col2:
    st.subheader("📄 리포트 디자인 미리보기")
    if report_data:
        # 차트 생성 (예시 데이터)
        fig, ax = plt.subplots(figsize=(7, 4))
        years = ['2021', '2022', '2023']
        revenues = [4500, 5800, 7200] # 나중에 엑셀 연동 시 실제 데이터로 교체
        ax.bar(years, revenues, color='#0b1f52')
        ax.set_title(f"{report_data['company']} 매출 성장 추이", fontsize=14, pad=15)
        st.pyplot(fig)
        
        # PDF 리포트 생성 버튼
        if st.button("🚀 마스터 리포트 PDF 생성", type="primary", use_container_width=True):
            with st.spinner("전문가용 리포트 구성 중..."):
                pdf = FPDF()
                pdf.add_page()
                
                # 서버 내 나눔 폰트 경로 설정
                font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
                if os.path.exists(font_path):
                    pdf.add_font("NanumGothic", "", font_path)
                    pdf.set_font("NanumGothic", size=12)
                else:
                    pdf.set_font("Arial", size=12)

                # --- PDF 디자인 레이아웃 ---
                # 상단 헤더 바
                pdf.set_fill_color(11, 31, 82)
                pdf.rect(0, 0, 210, 40, 'F')
                
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("NanumGothic", size=22)
                pdf.cell(190, 20, txt="RE-PORT: 전문 경영진단 보고서", ln=True, align='C')
                
                # 본문 내용
                pdf.set_text_color(0, 0, 0)
                pdf.ln(30)
                pdf.set_font("NanumGothic", size=16)
                pdf.set_draw_color(212, 175, 55) # 금색 선
                pdf.set_line_width(1)
                pdf.line(10, 55, 200, 55)
                
                pdf.ln(10)
                pdf.set_font("NanumGothic", size=14)
                pdf.cell(100, 12, txt=f"■ 기업명 : {report_data['company']}", ln=True)
                pdf.cell(100, 12, txt=f"■ 대표자 : {report_data['ceo']}", ln=True)
                pdf.cell(100, 12, txt=f"■ 신용등급 : {report_data['rating']}", ln=True)
                
                # 차트 삽입
                pdf.ln(15)
                fig.savefig("temp_report_chart.png", dpi=300)
                pdf.image("temp_report_chart.png", x=15, y=None, w=170)
                
                # 하단 푸터
                pdf.set_y(-30)
                pdf.set_font("NanumGothic", size=10)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(190, 10, txt=f"발행일: {datetime.now().strftime('%Y-%m-%d')} | 중소기업경영지원단 AI 분석 시스템", align='C')

                # PDF 바이트 변환 및 다운로드
                pdf_output = bytes(pdf.output())
                st.download_button(
                    label="💾 진단 리포트 PDF 다운로드",
                    data=pdf_output,
                    file_name=f"진단리포트_{report_data['company']}.pdf",
                    mime="application/pdf"
                )
                st.success("리포트가 완성되었습니다!")
    else:
        st.info("왼쪽에서 PDF 파일을 업로드하고 정보를 확인해 주세요.")
