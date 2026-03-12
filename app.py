import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import base64
from datetime import datetime, date
import pdfkit
import PyPDF2
import shutil
import re

# --- [0. 페이지 설정 및 디자인 완전 강제 적용 CSS] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide")

# 리눅스(배포 환경) 한글 폰트 설정 (fonts-nanum 설치 전제)
plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

custom_css = """
<style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    
    /* 로그인 박스 */
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
    
    /* 헤더 및 카드 디자인 */
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%) !important; 
        color: white !important; 
        padding: 2rem !important; 
        border-radius: 12px !important; 
        border-bottom: 5px solid #d4af37 !important; 
        text-align: center !important; 
        margin-bottom: 2rem !important; 
    }
    .report-card { 
        background-color: white !important; 
        padding: 20px !important; 
        border-radius: 8px !important; 
        line-height: 1.8 !important; 
        border: 1px solid #e0e0e0 !important; 
        border-left: 6px solid #0b1f52 !important; 
        margin-bottom: 10px !important; 
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 데이터베이스 설정] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        # 초기 관리자 설정 (incheon00@gmail.com)
        initial_data = pd.DataFrame([
            {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "usage_count": 0, "last_month": date.today().month}
        ])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data
    return pd.read_csv(DB_FILE)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

# --- [2. 세션 및 로그인 시스템] ---
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    st.markdown("<p>재무진단 마스터 컨설턴트 로그인</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("이메일", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
    
    col_l, col_r = st.columns(2)
    if col_l.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == login_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email
            st.rerun()
        else:
            st.error("미등록 계정이거나 승인 대기 중입니다.")
            
    if col_r.button("승인 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_user = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "usage_count": 0, "last_month": date.today().month}])
            user_db = pd.concat([user_db, new_user], ignore_index=True)
            save_db(user_db)
            st.success("신청 완료! 관리자 승인을 기다려주세요.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 메인 대시보드 UI] ---
st.markdown('<div class="premium-header"><h1>📊 기업 재무경영진단 자동화 시스템</h1><p>KREtop 데이터 연동 리포트 생성기</p></div>', unsafe_allow_html=True)

# 사이드바 관리자 설정
with st.sidebar:
    st.write(f"👤 접속: **{st.session_state.authenticated_user}**")
    if st.button("로그아웃"):
        st.session_state.authenticated_user = None
        st.rerun()
    
    # 관리자 메뉴
    curr_user = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if curr_user['is_admin']:
        st.divider()
        st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 변경 대상", user_db['email'])
        if st.button("승인 상태 변경"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db)
            st.rerun()

# --- [4. 데이터 분석 로직] ---

def process_pdf_data(file):
    info = {'company_name': file.name.replace('.pdf',''), 'ceo_name': '미상', 'credit_rating': '미상'}
    try:
        reader = PyPDF2.PdfReader(file)
        text = "".join([page.extract_text() for page in reader.pages])
        # 알려주신 키워드 기반 추출
        ceo_m = re.search(r'대표자명\s*[:|：]?\s*([가-힣]+)', text)
        if ceo_m: info['ceo_name'] = ceo_m.group(1).strip()
        credit_m = re.search(r'기업신용등급\s*[:|：]?\s*([A-Z0-9+-]+)', text)
        if credit_m: info['credit_rating'] = credit_m.group(1).strip()
    except: pass
    return info

def process_excel_data(file):
    # 실제는 pd.read_excel(file) 로직이 들어가야 함
    return {'rev_21': 4500, 'rev_22': 5800, 'rev_23': 7200, 'debt': 125.4}

def create_chart(data):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(['2021', '2022', '2023'], [data['rev_21'], data['rev_22'], data['rev_23']], color='#0b1f52')
    ax.set_title("매출 성장 추이 (백만원)")
    chart_path = "temp_chart.png"
    fig.savefig(chart_path, bbox_inches='tight')
    plt.close(fig)
    return chart_path

# --- [5. 업로드 및 결과 화면] ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("📁 파일 업로드")
    uploaded_files = st.file_uploader("PDF 및 엑셀 파일을 드래그하세요", accept_multiple_files=True, type=['pdf', 'xlsx', 'xls'])
    
    pdf_info, excel_info = None, None
    if uploaded_files:
        for f in uploaded_files:
            if f.name.endswith('.pdf'): pdf_info = process_pdf_data(f)
            else: excel_info = process_excel_data(f)
            
        if pdf_info and excel_info:
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.write(f"**🏢 기업명:** {pdf_info['company_name']}")
            st.write(f"**👤 대표자명:** {pdf_info['ceo_name']}")
            st.write(f"**⭐ 기업신용등급:** {pdf_info['credit_rating']}")
            st.write(f"**📊 최근 매출:** {excel_info['rev_23']:,} 백만원")
            st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.subheader("📄 리포트 미리보기")
    if pdf_info and excel_info:
        cp = create_chart(excel_info)
        st.image(cp, use_column_width=True)
        
        if st.button("🚀 마스터 리포트 PDF 생성", type="primary", use_container_width=True):
            with st.spinner("PDF 생성 중..."):
                # wkhtmltopdf 경로 설정
                path = shutil.which("wkhtmltopdf") or '/usr/bin/wkhtmltopdf'
                config = pdfkit.configuration(wkhtmltopdf=path)
                
                html = f"""
                <html><head><meta charset='UTF-8'><style>
                body {{ font-family: 'NanumGothic', sans-serif; padding: 40px; }}
                .header {{ border-bottom: 3px solid #0b1f52; padding-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
                th {{ background-color: #f8f9fa; }}
                </style></head><body>
                <div class="header"><h1>재무경영진단 리포트</h1></div>
                <h3>기업 개요</h3>
                <table><tr><th>기업명</th><td>{pdf_info['company_name']}</td><th>대표자</th><td>{pdf_info['ceo_name']}</td></tr>
                <tr><th>신용등급</th><td colspan="3"><b>{pdf_info['credit_rating']}</b></td></tr></table>
                <h3>재무 지표</h3>
                <table><tr><th>구분</th><th>2021년</th><th>2022년</th><th>2023년</th></tr>
                <tr><td>매출액(백만원)</td><td>{excel_info['rev_21']}</td><td>{excel_info['rev_22']}</td><td>{excel_info['rev_23']}</td></tr></table>
                <div style="text-align:center; margin-top:30px;"><img src="{os.path.abspath(cp)}" width="500"></div>
                </body></html>
                """
                
                try:
                    pdf_bytes = pdfkit.from_string(html, False, configuration=config, options={'encoding': 'UTF-8', 'enable-local-file-access': None})
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="진단리포트_{pdf_info["company_name"]}.pdf" style="text-decoration:none;"><div style="background-color:#0b1f52; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold;">💾 PDF 리포트 다운로드</div></a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"PDF 생성 에러: {e}")
    else:
        st.info("왼쪽에서 PDF와 엑셀 파일을 모두 업로드해주세요.")
