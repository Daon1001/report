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

# 리눅스(배포 환경) 및 윈도우 한글 폰트 설정
plt.rc('font', family='Malgun Gothic') # 배포 시 'NanumGothic'으로 변경 필요
plt.rcParams['axes.unicode_minus'] = False

custom_css = """
<style>
    /* 1. Streamlit 기본 여백을 극한으로 줄임 */
    .block-container {
        padding-top: 1rem !important; 
        padding-bottom: 1rem !important;
        margin-top: 0 !important;
    }
    
    /* 기본 상단 투명 헤더 영역 완벽 제거 */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* 2. 배경 그라데이션 강제 적용 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    }
    
    /* 3. 로그인 컨테이너: 높이(height) 제한을 없애고 무조건 위로 붙임 */
    .login-container {
        display: flex !important;
        justify-content: center !important;
        align-items: flex-start !important; 
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* 4. 로그인 박스: 화면 맨 위에서 딱 2vh(약 2%)만 띄움 */
    .login-box {
        background-color: white !important;
        padding: 40px !important;
        border-radius: 20px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15) !important;
        text-align: center !important;
        max-width: 480px !important;
        width: 100% !important;
        border-top: 8px solid #0b1f52 !important;
        margin-top: 2vh !important; 
    }

    /* 텍스트 로고 타이틀 디자인 */
    .login-title {
        color: #0b1f52 !important;
        font-weight: 900 !important;
        font-size: 30px !important;
        margin-bottom: 5px !important;
        letter-spacing: -1px !important;
    }

    /* 대시보드 내부 프리미엄 헤더 */
    .premium-header {
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%) !important;
        color: white !important;
        padding: 2rem !important;
        border-radius: 12px !important;
        border-bottom: 5px solid #d4af37 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
    }
    
    /* 리포트 카드 디자인 */
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

# --- [DB 설정 및 자동 복구 로직] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = pd.DataFrame([
            {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month},
            {"email": "manager@gmail.com", "approved": True, "is_admin": False, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month}
        ])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data
    df = pd.read_csv(DB_FILE)
    for col in ['usage_count', 'last_month', 'created_at', 'approved', 'is_admin']:
        if col not in df.columns: df[col] = 0 if 'count' in col else (date.today().month if 'month' in col else False)
    return df

def save_db(df): df.to_csv(DB_FILE, index=False)

user_db = load_db()

# --- [1. 세션 관리] ---
if 'authenticated_user' not in st.session_state: st.session_state.authenticated_user = None
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = "1"
MAX_MONTHLY_LIMIT = 50 

# --- [2. 중앙 집중형 로그인 화면 (최상단 강제 고정)] ---
if st.session_state.authenticated_user is None:
    _, col_mid, _ = st.columns([0.5, 1, 0.5])
    
    with col_mid:
        st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
        
        st.markdown('<div class="login-title">🏛️ 중소기업경영지원단</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#666; font-size:1.05rem; margin-bottom: 25px;'>재무경영진단 마스터 컨설턴트 로그인</p>", unsafe_allow_html=True)
        
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
        
        st.write("")
        b_col1, b_col2 = st.columns(2)
        if b_col1.button("로그인", type="primary", use_container_width=True):
            user_row = user_db[user_db['email'] == login_email]
            if not user_row.empty and user_row.iloc[0]['approved']:
                st.session_state.authenticated_user = login_email
                st.rerun()
            else: st.error("❌ 미등록 계정 또는 승인 대기 중입니다.")
                
        if b_col2.button("승인 신청", use_container_width=True):
            if login_email and user_db[user_db['email'] == login_email].empty:
                new_user = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "created_at": datetime.now().strftime("%Y-%m-%d"), "usage_count": 0, "last_month": date.today().month}])
                user_db = pd.concat([user_db, new_user], ignore_index=True); save_db(user_db)
                st.success("📩 신청 완료!")
            else: st.warning("이미 신청된 이메일입니다.")
            
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# 로그인 성공 후 메인 페이지 (재무 리포트 생성기)
# =====================================================================

with st.sidebar:
    st.success(f"👤 접속: {st.session_state.authenticated_user}")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    
    idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
    st.write(f"📊 월 사용량: {user_db.at[idx, 'usage_count']} / {MAX_MONTHLY_LIMIT}")

    # 🚀 관리자 전용 제어판
    if user_db.at[idx, 'is_admin']:
        st.divider()
        with st.expander("👑 관리자 전용: 사용자 승인 관리", expanded=True):
            if 'admin_msg' in st.session_state:
                st.success(st.session_state.admin_msg)
                del st.session_state.admin_msg
                
            st.dataframe(user_db[['email', 'approved', 'usage_count']], use_container_width=True)
            target_email = st.selectbox("승인 상태 변경 대상", user_db['email'])
            c1, c2 = st.columns(2)
            if c1.button("✅ 승인", use_container_width=True):
                user_db.loc[user_db['email'] == target_email, 'approved'] = True
                save_db(user_db)
                st.session_state.admin_msg = f"'{target_email}' 계정이 승인되었습니다!"
                st.rerun()
            if c2.button("🚫 해제", use_container_width=True):
                user_db.loc[user_db['email'] == target_email, 'approved'] = False
                save_db(user_db)
                st.session_state.admin_msg = f"'{target_email}' 계정 승인이 해제되었습니다."
                st.rerun()

# --- [메인 대시보드 UI] ---
st.markdown(f"""
    <div class="premium-header">
        <h1>📊 기업 재무경영진단 자동화 대시보드</h1>
        <p><strong>크레탑(KREtop) 엑셀 및 PDF 연동</strong> 원클릭 마스터 리포트 생성 시스템</p>
    </div>
""", unsafe_allow_html=True)

# 0. wkhtmltopdf 경로 강제 확인 함수
def get_pdfkit_config():
    path = shutil.which("wkhtmltopdf")
    if not path:
        if os.path.exists('/usr/bin/wkhtmltopdf'):
            path = '/usr/bin/wkhtmltopdf'
        elif os.path.exists('/usr/local/bin/wkhtmltopdf'):
            path = '/usr/local/bin/wkhtmltopdf'
            
    if path:
        return pdfkit.configuration(wkhtmltopdf=path)
    return None

# 1. 크레탑 엑셀 분석 함수 (재무 데이터)
def process_excel_data(file):
    # 실제 엑셀 데이터 매핑을 위한 테스트 데이터
    return {
        'revenue_2021': 5200,
        'revenue_2022': 6800,
        'revenue_2023': 8500,
        'debt_ratio': 145.2,
        'analysis_text': "전년 대비 매출이 견고하게 성장하고 있으며, 부채비율은 안정적인 수준을 유지하고 있습니다."
    }

# 2. 크레탑 PDF 분석 함수 (알려주신 키워드 기반 정밀 추출)
def process_pdf_data(file):
    extracted_info = {
        'company_name': '미상',
        'ceo_name': '미상',
        'credit_rating': '미상'
    }
    
    try:
        reader = PyPDF2.PdfReader(file)
        full_text = ""
        # PDF 내의 모든 페이지 텍스트를 하나로 합침
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # ① 기업명/업체명 추출
        company_match = re.search(r'(업체명|기업명|상호명?)\s*[:|：]?\s*([^\n\s]+)', full_text)
        if company_match:
            extracted_info['company_name'] = company_match.group(2).strip()
        else:
            extracted_info['company_name'] = file.name.replace(".pdf", "").replace("크레탑", "").strip()

        # ② 대표자명 추출 (정확히 '대표자명' 타겟팅)
        ceo_match = re.search(r'대표자명\s*[:|：]?\s*([가-힣a-zA-Z]+)', full_text)
        if ceo_match:
            extracted_info['ceo_name'] = ceo_match.group(1).strip()
            
        # ③ 기업신용등급 추출 (정확히 '기업신용등급' 타겟팅)
        credit_match = re.search(r'기업신용등급\s*[:|：]?\s*([A-Z0-9\+\-]+)', full_text)
        if credit_match:
            extracted_info['credit_rating'] = credit_match.group(1).strip()

    except Exception as e:
        st.error(f"PDF 텍스트 추출 중 오류가 발생했습니다: {e}")
        
    return extracted_info

# 3. 차트 생성 함수
def create_chart(excel_data):
    fig, ax = plt.subplots(figsize=(6, 4))
    years = ['2021', '2022', '2023']
    values = [excel_data['revenue_2021'], excel_data['revenue_2022'], excel_data['revenue_2023']]
    ax.bar(years, values, color='#1a2a5a')
    ax.set_title("최근 3개년 매출액 추이 (단위: 백만원)")
    
    chart_path = "sales_chart_temp.png"
    fig.savefig(chart_path, bbox_inches='tight')
    plt.close(fig)
    return chart_path

# 화면 분할
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("1️⃣ 데이터 동시 업로드")
    
    uploaded_files = st.file_uploader(
        "크레탑 자료 (PDF 및 엑셀)를 모두 드래그해서 올려주세요", 
        type=['pdf', 'xlsx', 'xls'], 
        accept_multiple_files=True, 
        key=f"files_{st.session_state.uploader_key}"
    )
    
    pdf_data = {}
    excel_data = {}
    has_pdf = False
    has_excel = False
    
    if uploaded_files:
        for file in uploaded_files:
            if file.name.lower().endswith('.pdf'):
                pdf_data = process_pdf_data(file)
                has_pdf = True
            elif file.name.lower().endswith(('.xlsx', '.xls')):
                excel_data = process_excel_data(file)
                has_excel = True
        
        if has_pdf and has_excel:
            st.success("✅ PDF와 엑셀 파일이 모두 정상적으로 분석되었습니다!")
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.write(f"**🏢 진단 대상 기업:** {pdf_data['company_name']}")
            st.write(f"**👤 대표자:** {pdf_data['ceo_name']}")
            st.write(f"**⭐ 신용등급:** {pdf_data['credit_rating']}")
            st.write(f"**📈 23년 매출액:** {excel_data['revenue_2023']} 백만원")
            st.write(f"**⚖️ 부채비율:** {excel_data['debt_ratio']}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 추출 실패 시 안내 메시지
            if pdf_data['credit_rating'] == '미상' or pdf_data['ceo_name'] == '미상':
                st.warning("⚠️ 파일 업로드는 성공했으나 PDF 내에서 해당 텍스트를 정확히 추출하지 못했습니다. PDF 양식을 다시 확인해 주세요.")
        else:
            if not has_pdf:
                st.warning("⚠️ 엑셀은 확인되었습니다. 신용등급이 포함된 **PDF 파일**도 함께 올려주세요.")
            if not has_excel:
                st.warning("⚠️ PDF는 확인되었습니다. 재무 데이터가 포함된 **엑셀 파일**도 함께 올려주세요.")

with col2:
    st.subheader("2️⃣ 리포트 렌더링 및 출력")
    if not (has_pdf and has_excel):
        st.info("왼쪽에 PDF와 엑셀 파일을 모두 업로드해야 리포트가 생성됩니다.")
    else:
        chart_path = create_chart(excel_data)
        st.image(chart_path, caption="생성된 차트 미리보기", use_column_width=True)
        
        if st.button("마스터 리포트 PDF 생성 🚀", type="primary", use_container_width=True):
            if user_db.at[idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
                st.error("월간 사용 한도를 초과했습니다.")
            else:
                with st.spinner("최종 PDF 리포트를 생성하고 있습니다..."):
                    
                    config = get_pdfkit_config()
                    if config is None:
                        st.error("🚨 서버에 wkhtmltopdf가 감지되지 않았습니다. 깃허브 최상단에 'packages.txt' 파일(내용: wkhtmltopdf)이 존재하는지 확인한 후, 우측 하단 탭 메뉴에서 'Reboot app'을 실행해 주세요.")
                    else:
                        report_date = date.today().strftime("%Y-%m-%d")
                        
                        html_template = f"""
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <style>
                                @page {{ size: A4; margin: 0; }}
                                body {{ font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; margin: 0; padding: 0; color: #333; }}
                                .page {{ width: 210mm; height: 297mm; padding: 20mm; box-sizing: border-box; page-break-after: always; }}
                                .cover {{ background-color: #f4f7fa; text-align: center; display: flex; flex-direction: column; justify-content: center; height: 100vh; }}
                                .cover h1 {{ font-size: 40pt; color: #1a2a5a; margin-bottom: 10px; }}
                                .header {{ border-bottom: 2px solid #1a2a5a; padding-bottom: 10px; margin-bottom: 20px; }}
                                .header h2 {{ color: #1a2a5a; margin: 0; }}
                                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 30px; }}
                                th {{ background-color: #1a2a5a; color: white; padding: 10px; border: 1px solid #ddd; }}
                                td {{ padding: 10px; border: 1px solid #ddd; text-align: center; }}
                                .summary-box {{ background-color: #eef2f7; padding: 20px; border-radius: 10px; margin-top: 20px; line-height: 1.6; }}
                            </style>
                        </head>
                        <body>
                            <div class="page cover">
                                <p style="font-size: 20pt; color: #666;">재무경영진단 리포트</p>
                                <h1>{pdf_data['company_name']}</h1>
                                <p>작성일: {report_date}</p>
                            </div>
                            
                            <div class="page">
                                <div class="header">
                                    <h2>01. 기업 개요 및 신용등급</h2>
                                </div>
                                <table>
                                    <tr>
                                        <th>기업명</th><td>{pdf_data['company_name']}</td>
                                        <th>대표자명</th><td>{pdf_data['ceo_name']}</td>
                                    </tr>
                                    <tr>
                                        <th>기업신용등급</th><td colspan="3" style="font-weight: bold; color: #1a2a5a;">{pdf_data['credit_rating']}</td>
                                    </tr>
                                </table>

                                <div class="header">
                                    <h2>02. 기업재무분석 요약</h2>
                                </div>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>구분</th><th>2021년</th><th>2022년</th><th>2023년</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>매출액(백만원)</td>
                                            <td>{excel_data['revenue_2021']}</td><td>{excel_data['revenue_2022']}</td><td>{excel_data['revenue_2023']}</td>
                                        </tr>
                                    </tbody>
                                </table>
                                
                                <div style="text-align: center; margin-top: 20px;">
                                    <img src="{os.path.abspath(chart_path)}" width="450">
                                </div>
                                
                                <div class="summary-box">
                                    <strong>💡 컨설턴트 종합 진단</strong><br><br>
                                    {excel_data['analysis_text']}
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        try:
                            options = {'enable-local-file-access': None, 'encoding': 'UTF-8'}
                            pdf_bytes = pdfkit.from_string(html_template, False, options=options, configuration=config)
                            
                            user_db.at[idx, 'usage_count'] += 1
                            save_db(user_db)
                            
                            b64 = base64.b64encode(pdf_bytes).decode()
                            download_name = pdf_data['company_name'].replace(" ", "_").replace("(", "").replace(")", "")
                            href = f'<a href="data:application/octet-stream;base64,{b64}" download="재무경영진단_{download_name}.pdf" style="display: block; background-color: #1a3673; color: white; text-align: center; padding: 15px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">💾 마스터 리포트 다운로드 클릭</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            st.success("✅ 엑셀과 PDF가 병합된 리포트가 성공적으로 생성되었습니다!")
                            
                        except Exception as e:
                            st.error(f"PDF 생성 중 알 수 없는 오류가 발생했습니다: {e}")
