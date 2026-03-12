import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import PyPDF2
from fpdf import FPDF
import re
from datetime import date, datetime

# --- [0. 페이지 기본 설정 및 프리미엄 UI 디자인] ---
st.set_page_config(page_title="재무경영진단 AI 마스터", layout="wide", initial_sidebar_state="expanded")

# 차트 한글 폰트 설정 (나눔고딕 기준)
plt.rc('font', family='NanumGothic') 
plt.rcParams['axes.unicode_minus'] = False

# 커스텀 CSS 디자인
custom_css = """
<style>
    /* 기본 배경 및 폰트 설정 */
    .block-container { padding-top: 1.5rem !important; }
    header { display: none !important; }
    .stApp { background-color: #f4f7f9 !important; }
    
    /* 상단 프리미엄 헤더 */
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%); 
        color: white; 
        padding: 3rem; 
        border-radius: 20px; 
        border-bottom: 8px solid #d4af37; 
        text-align: center; 
        margin-bottom: 3rem;
        box-shadow: 0 10px 30px rgba(11, 31, 82, 0.2);
    }
    
    /* 데이터 입력 및 카드 섹션 */
    .edit-section { 
        background: white; 
        padding: 30px; 
        border-radius: 15px; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.08); 
        border-top: 6px solid #0b1f52;
        margin-bottom: 20px;
    }
    
    /* 로그인 박스 */
    .login-container {
        max-width: 500px;
        margin: 15vh auto;
        background: white;
        padding: 50px;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 10px solid #0b1f52;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 관리 및 보안 시스템] ---
DB_FILE = "users.csv"

def load_user_database():
    if not os.path.exists(DB_FILE):
        # 관리자 초기 이메일 설정
        initial_df = pd.DataFrame([{
            "email": "incheon00@gmail.com", 
            "approved": True, 
            "is_admin": True, 
            "usage_count": 0, 
            "last_month": date.today().month
        }])
        initial_df.to_csv(DB_FILE, index=False)
        return initial_df
    return pd.read_csv(DB_FILE)

def save_user_database(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_user_database()

# 로그인 세션 관리
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52; margin-bottom:10px;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#666; margin-bottom:30px;">재무경영진단 AI 마스터 로그인</p>', unsafe_allow_html=True)
    
    user_input_email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    
    col_login, col_apply = st.columns(2)
    if col_login.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == user_input_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = user_input_email
            st.rerun()
        elif not user_row.empty and not user_row.iloc[0]['approved']:
            st.warning("계정 승인 대기 중입니다.")
        else:
            st.error("등록되지 않은 계정입니다.")
            
    if col_apply.button("사용 신청", use_container_width=True):
        if user_input_email and user_db[user_db['email'] == user_input_email].empty:
            new_entry = pd.DataFrame([{
                "email": user_input_email, "approved": False, "is_admin": False, 
                "usage_count": 0, "last_month": date.today().month
            }])
            user_db = pd.concat([user_db, new_entry], ignore_index=True)
            save_user_database(user_db)
            st.success("신청이 완료되었습니다. 관리자에게 문의하세요.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [2. 핵심 데이터 추출 엔진] ---
def extract_business_data(pdf_file):
    """PDF에서 대표자명, 신용등급 등 핵심 키워드 추출"""
    extracted = {'company': pdf_file.name.replace('.pdf',''), 'ceo': '미상', 'rating': '미상'}
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + " "
        
        # 정규표현식을 이용한 데이터 매칭
        ceo_regex = re.search(r'대표자(?:명)?\s*[:|：]?\s*([가-힣]{2,4})', full_text)
        if ceo_regex:
            extracted['ceo'] = ceo_regex.group(1).strip()
            
        rating_regex = re.search(r'기업신용등급\s*[:|：]?\s*([a-zA-Z0-9\+\-]+)', full_text)
        if rating_regex:
            extracted['rating'] = rating_regex.group(1).strip()
    except Exception as e:
        st.error(f"데이터 추출 중 오류 발생: {e}")
    return extracted

# --- [3. 메인 대시보드 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 [PRIME] 기업 재무경영진단 통합 솔루션</h1><p>전문가용 멀티 페이지 정밀 리포트 생성 시스템</p></div>', unsafe_allow_html=True)

# 사이드바 (로그아웃 및 관리자)
with st.sidebar:
    st.markdown(f"### 👤 컨설턴트\n**{st.session_state.authenticated_user}**")
    if st.button("로그아웃"):
        st.session_state.authenticated_user = None
        st.rerun()
    
    st.divider()
    admin_check = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if admin_check['is_admin']:
        st.subheader("👑 관리자 설정")
        st.write("사용자 승인 관리")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target_email = st.selectbox("변경 대상", user_db['email'])
        if st.button("승인 상태 전환"):
            user_db.loc[user_db['email'] == target_email, 'approved'] = not user_db.loc[user_db['email'] == target_email, 'approved'].iloc[0]
            save_user_database(user_db)
            st.rerun()

# 메인 콘텐츠 영역
left_col, right_col = st.columns([1, 1.4])

with left_col:
    st.subheader("📂 진단 파일 업로드")
    uploaded_files = st.file_uploader("KREtop PDF 및 재무 엑셀(XLSX) 파일을 업로드하세요.", accept_multiple_files=True)
    
    current_meta = None
    if uploaded_files:
        for f in uploaded_files:
            if f.name.endswith('.pdf'):
                current_meta = extract_business_data(f)
        
        if current_meta:
            st.markdown('<div class="edit-section">', unsafe_allow_html=True)
            st.markdown("### 📝 정밀 보정 및 추가 정보")
            st.caption("자동 추출이 정확하지 않을 경우 아래에서 직접 보정하세요.")
            
            # 사용자 직접 수정 필드
            final_c_name = st.text_input("🏢 기업 공식 명칭", current_meta['company'])
            final_ceo_name = st.text_input("👤 대표자 성명", current_meta['ceo'])
            final_c_rating = st.text_input("⭐ 최종 신용등급", current_meta['rating'])
            final_c_goal = st.text_area("🎯 컨설팅 중점 과제", "가지급금 정리, 기업 가치 평가 및 가업 승계 전략 수립")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 최종 데이터 묶음
            report_payload = {
                "name": final_c_name, 
                "ceo": final_ceo_name, 
                "rating": final_c_rating, 
                "goal": final_c_goal
            }
        else:
            report_payload = None
    else:
        report_payload = None

with right_col:
    st.subheader("📈 시각화 및 리포트 구성")
    if report_payload:
        # 1. 차트 시각화 (성장 지표)
        fig, ax = plt.subplots(figsize=(8, 4.5))
        years = ['2021년', '2022년', '2023년']
        rev_data = [4500, 5900, 7500] # 임시 데이터 (엑셀 연동 시 대체 가능)
        profit_data = [350, 480, 820]
        
        ax.bar(years, rev_data, color='#0b1f52', label='매출액(백만)', width=0.5)
        ax.plot(years, profit_data, color='#d4af37', marker='s', markersize=8, linewidth=2, label='영업이익(백만)')
        
        ax.set_title(f"{report_payload['name']} 연도별 주요 성장 지표", fontsize=15, pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend()
        st.pyplot(fig)
        
        st.divider()
        
        # 2. PDF 생성 로직 (FPDF 멀티 페이지)
        if st.button("🚀 전문가용 정밀 리포트(Multi-Page) 발행", type="primary", use_container_width=True):
            with st.spinner("AI 컨설팅 엔진 가동 중..."):
                pdf = FPDF()
                font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
                
                # --- [Page 1: 리포트 표지] ---
                pdf.add_page()
                if os.path.exists(font_path):
                    pdf.add_font("NanumGothic", "", font_path)
                    pdf.set_font("NanumGothic", size=12)
                
                # 배경 디자인
                pdf.set_fill_color(11, 31, 82)
                pdf.rect(0, 0, 210, 297, 'F')
                
                pdf.set_text_color(255, 255, 255)
                pdf.ln(85)
                pdf.set_font("NanumGothic", size=32)
                pdf.cell(190, 25, txt="재무경영진단 리포트", ln=True, align='C')
                
                pdf.set_font("NanumGothic", size=18)
                pdf.cell(190, 20, txt=f"기업명 : {report_payload['name']}", ln=True, align='C')
                
                pdf.ln(100)
                pdf.set_font("NanumGothic", size=13)
                pdf.cell(190, 10, txt=f"발행일: {datetime.now().strftime('%Y년 %m월 %d일')}", ln=True, align='C')
                pdf.cell(190, 10, txt="중소기업경영지원단 AI 분석 센터", ln=True, align='C')

                # --- [Page 2: 종합 진단 결과 요약] ---
                pdf.add_page()
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("NanumGothic", size=18)
                pdf.cell(190, 20, txt="1. 종합 진단 및 분석 요약", ln=True)
                pdf.set_draw_color(11, 31, 82); pdf.set_line_width(1)
                pdf.line(10, 28, 200, 28)
                
                pdf.ln(15)
                pdf.set_font("NanumGothic", size=12)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(190, 12, txt=f"  ■ 분석 대상 : {report_payload['name']} (대표자: {report_payload['ceo']})", ln=True, fill=True)
                pdf.cell(190, 12, txt=f"  ■ 종합 등급 : {report_payload['rating']} 등급", ln=True)
                pdf.cell(190, 12, txt=f"  ■ 핵심 과제 : {report_payload['goal']}", ln=True, fill=True)
                
                # 차트 삽입
                pdf.ln(15)
                fig.savefig("current_report_chart.png", dpi=300, bbox_inches='tight')
                pdf.image("current_report_chart.png", x=15, w=170)
                
                pdf.ln(10)
                pdf.set_font("NanumGothic", size=11)
                pdf.multi_cell(185, 8, txt="위 차트는 해당 기업의 최근 3개년 매출 및 수익성 지표를 나타냅니다. 지속적인 성장이 관찰되나, 신용등급 유지를 위해 부채 비율 관리 및 유동성 확보 전략이 필요합니다.")

                # --- [Page 3: 전문가 솔루션 제안] ---
                pdf.add_page()
                pdf.set_font("NanumGothic", size=18)
                pdf.cell(190, 20, txt="2. 주요 경영 이슈별 솔루션", ln=True)
                pdf.line(10, 28, 200, 28)
                pdf.ln(15)
                
                strategies = [
                    ("📌 가지급금 및 미처분이익잉여금 관리", "과도한 이익잉여금은 가업 승계 시 세부담의 원인이 됩니다. 자사주 매입 및 차등 배당을 통해 효율적인 자금 인출 전략을 제안합니다."),
                    ("📌 법인 정관 정비 및 임원 보상 체계", "임원 퇴직금 지급 규정 및 유고 시 보상 체계를 정비하여 법적 리스크를 최소화하고 절세 효과를 극대화해야 합니다."),
                    ("📌 기업 가치 평가 및 가업 승계", "비상장 주식 가치 평가를 주기적으로 수행하여 최적의 증여 시점을 파악하고 상속세 재원을 마련하는 플랜이 시급합니다."),
                    ("📌 정책 자금 및 금융 활용 전략", "개선된 신용등급을 바탕으로 저금리 정책 자금을 확보하여 시설 투자 및 운영 자금의 유동성을 강화하는 로직을 수립합니다.")
                ]
                
                for title, detail in strategies:
                    pdf.set_font("NanumGothic", size=13); pdf.set_text_color(11, 31, 82)
                    pdf.cell(190, 10, txt=title, ln=True)
                    pdf.set_font("NanumGothic", size=11); pdf.set_text_color(60, 60, 60)
                    pdf.multi_cell(185, 7, txt=detail)
                    pdf.ln(8)

                # PDF 데이터 변환 및 다운로드 버튼
                pdf_data_bytes = bytes(pdf.output())
                st.download_button(
                    label="💾 완성된 3페이지 정밀 리포트 다운로드",
                    data=pdf_data_bytes,
                    file_name=f"경영진단결과_{report_payload['name']}.pdf",
                    mime="application/pdf"
                )
                st.success("✅ 고품격 경영진단 리포트 생성이 완료되었습니다!")
    else:
        st.info("좌측 업로드 섹션에 고객사의 PDF 보고서 파일을 드래그하여 분석을 시작하세요.")
