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
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .login-box { 
        background-color: white !important; padding: 50px !important; border-radius: 20px !important; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1) !important; text-align: center !important; 
        max-width: 500px !important; margin: 10vh auto !important; border-top: 12px solid #0b1f52 !important;
    }
    .status-card { 
        background: white; padding: 25px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 8px solid #0b1f52; margin-bottom: 20px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 승인 시스템] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        # 초기 관리자 계정 설정 (인천00@gmail.com)
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
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52; margin-bottom:0;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 재무진단 및 가치평가 시스템 v10.0</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    
    col_l, col_r = st.columns(2)
    if col_l.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == login_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email
            st.rerun()
        elif not user_row.empty and not user_row.iloc[0]['approved']:
            st.warning("⚠️ 승인 대기 중입니다.")
        else:
            st.error("❌ 등록되지 않은 계정입니다.")
            
    if col_r.button("사용 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_user = pd.DataFrame([{
                "email": login_email, "approved": False, "is_admin": False, 
                "usage_count": 0, "last_month": date.today().month
            }])
            user_db = pd.concat([user_db, new_user], ignore_index=True)
            save_db(user_db)
            st.success("✅ 신청 완료! 대표자 승인 후 이용 가능합니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 데이터 추출 엔진 (개요 PDF 및 재무 엑셀 통합 분석)] ---

def clean_val(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def robust_analyzer(files):
    """파일을 통합 분석하여 재무, 인원, 인증 데이터를 추출"""
    res = {
        'company': "신용", 'ceo': "허자현", 'emp_count': 0,
        'financials': {'매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처': False, '이노비즈': False, '메인비즈': False, '연구소': False, '전담부서': False}
    }
    
    for file in files:
        # 1. 텍스트 데이터 추출 (PDF)
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + " "
            
            clean_text = full_text.replace(" ", "").replace("\n", "")
            
            # 기업명 추출 (개요.pdf: (주)메이홈) [cite: 3, 11]
            c_m = re.search(r'기업명:?([가-힣\(\)A-Za-z0-9]+)', clean_text)
            if c_m: res['company'] = c_m.group(1).strip()
            
            # 대표자 추출 (개요.pdf: 박승미) [cite: 5, 12, 15]
            ceo_m = re.search(r'대표자:?([가-힣]{2,4})', clean_text)
            if ceo_m: res['ceo'] = ceo_m.group(1).strip()
            
            # 종업원수 추출 (개요.pdf: 10명) 
            emp_m = re.search(r'종업원수:?(\d+)명', clean_text)
            if emp_m: res['emp_count'] = int(emp_m.group(1))
            
            # 인증 현황 추출 (벤처, 이노비즈, 전담부서 등) [cite: 64, 65, 66, 67, 81]
            for cert in res['certs'].keys():
                if f"{cert}인증" in clean_text or f"{cert}보유" in clean_text: 
                    res['certs'][cert] = True

        # 2. 재무 데이터 추출 (Excel/CSV - 천원 단위 대응)
        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 키워드 매핑 및 데이터 추출
                    target_map = {'매출액': '매출', '순이익': '이익', '자산': '자산', '부채': '부채'}
                    for kw, key in target_map.items():
                        if kw in txt:
                            nums = [clean_val(v) for v in row.values if clean_val(v) != 0]
                            if len(nums) >= 2: 
                                res['financials'][key] = nums[-3:] if len(nums)>=3 else [0.0]+nums[-2:]
            except: pass
    return res

# --- [4. 메인 화면 및 관리자 기능] ---

st.markdown('<div class="premium-header"><h1>📊 종합 경영진단 및 가변형 리포트 생성 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 접속: **{st.session_state.authenticated_user}**")
    if st.button("로그아웃"): 
        st.session_state.authenticated_user = None
        st.rerun()
    
    # 관리자 전용 승인 메뉴
    u_info = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if u_info['is_admin']:
        st.divider(); st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 상태 변경 대상", user_db['email'])
        if st.button("승인 상태 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

# --- [5. 메인 데이터 분석 섹션] ---

col_left, col_right = st.columns([1, 1.4])

with col_left:
    st.subheader("📂 진단 파일 업로드")
    up_files = st.file_uploader("개요 PDF 및 재무 파일을 업로드하세요.", accept_multiple_files=True)
    
    if up_files:
        analysis = robust_analyzer(up_files)
        st.success("✅ 파일 데이터 추출 완료")
        
        with st.expander("📝 데이터 보정 및 최종 확인", expanded=True):
            # 파일에서 읽어온 데이터로 자동 채움
            c_name = st.text_input("🏢 기업 명칭", analysis['company'])
            c_ceo = st.text_input("👤 대표자 성함", analysis['ceo'])
            c_emp = st.number_input("👥 상시 근로자수(명)", value=analysis['emp_count'])
            
            st.divider()
            st.write("🛡️ **보유 인증 항목**")
            cert_vals = {}
            for cert, have in analysis['certs'].items():
                cert_vals[cert] = st.checkbox(cert, value=have)
            
            st.divider()
            st.write("💰 **재무 지표 (천원 단위)**")
            r_rev = st.number_input("최신 매출액", value=analysis['financials']['매출'][2])
            r_inc = st.number_input("최신 순이익", value=analysis['financials']['이익'][2])
            r_asset = st.number_input("최신 자산총계", value=analysis['financials']['자산'][2])
            r_debt = st.number_input("최신 부채총계", value=analysis['financials']['부채'][2])

with col_right:
    st.subheader("📈 실시간 리포트 구성 미리보기")
    if up_files:
        # 노무 진단 기준 설정
        labor_type = "5인 이상" if c_emp >= 5 else "5인 미만"
        st.info(f"현재 근로자수 **{c_emp}명**으로 **'{labor_type} 사업장'** 전용 가이드가 리포트에 추가됩니다.")
        
        # 가치 평가 로직 (천원 -> 원 환산)
        stock_price = ((r_inc * 1000 / 0.1)*0.6 + (r_asset - r_debt)*1000*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{c_name} 기업가치 상승 예상 추이", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 정밀 보고서 발행 (가변 페이지 적용)", type="primary", use_container_width=True):
            with st.spinner("파일 데이터를 기반으로 맞춤형 리포트 생성 중..."):
                pdf = FPDF()
                f_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
                if os.path.exists(f_p): pdf.add_font("Nanum", "", f_p); pdf.set_font("Nanum", size=12)
                
                # --- [PAGE 1: 리포트 표지] ---
                pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
                pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
                pdf.cell(190, 25, txt="RE-PORT: 종합 경영진단 보고서", ln=True, align='C')
                pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"대상기업: {c_name} / 대표: {c_ceo}", ln=True, align='C')
                pdf.ln(100); pdf.set_font("Nanum", size=14)
                pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y년 %m월 %d일')}", ln=True, align='C')
                pdf.cell(190, 10, txt="중소기업경영지원단 AI 컨설팅 본부", ln=True, align='C')
                
                # --- [PAGE 2: 재무 및 가치 분석] ---
                pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
                pdf.cell(190, 15, txt="1. 정밀 재무 진단 및 기업가치 평가", ln=True)
                pdf.set_draw_color(11, 31, 82); pdf.set_line_width(1); pdf.line(10, 28, 200, 28); pdf.ln(15)
                pdf.set_font("Nanum", size=12)
                pdf.cell(190, 10, txt=f"■ 분석 대상: {c_name} (근로자 {c_emp}명)", ln=True)
                pdf.cell(190, 10, txt=f"■ 최신 매출액: {r_rev:,.0f} 천원", ln=True)
                pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82)
                pdf.cell(190, 15, txt=f"▶ 현시점 주당 추정가액: {int(stock_price):,} 원", ln=True)
                fig.savefig("val_chart.png", dpi=300); pdf.image("val_chart.png", x=15, w=180)
                
                # --- [PAGE 3: 기업 인증 필요성 진단 (가변 추가)] ---
                pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
                pdf.cell(190, 15, txt="2. 핵심 기업 인증 현황 및 로드맵", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
                
                cert_map = {
                    "벤처": "법인세 50% 감면 및 정부 정책자금 한도 우대를 위해 필수적입니다. [cite: 64]",
                    "연구소": "연구원 인건비의 25%를 세액공제 받을 수 있는 SME 최강의 절세 수단입니다. [cite: 67]",
                    "이노비즈": "기술력을 인정받아 금융권 금리 우대 및 정기 세무조사 유예 혜택이 있습니다. "
                }
                for c, desc in cert_map.items():
                    status = "보유" if cert_vals.get(c, False) else "미보유 (도입필요)"
                    pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
                    pdf.cell(190, 10, txt=f"● {c} 인증 : {status}", ln=True)
                    pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80)
                    pdf.multi_cell(185, 8, txt=f"혜택 및 필요성: {desc}\n")
                    if "미보유" in status:
                        pdf.set_text_color(200, 0, 0); pdf.cell(190, 8, txt="→ 기업 경쟁력 강화를 위해 조속한 취득 전략이 요구됩니다.", ln=True)
                    pdf.ln(5); pdf.set_text_color(0,0,0)

                # --- [PAGE 4: 인사 노무 가이드 (인원수 기반 가변 추가)] ---
                pdf.add_page(); pdf.set_font("Nanum", size=20)
                pdf.cell(190, 15, txt="3. 상시 인원별 맞춤형 노무 기준법", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
                pdf.set_font("Nanum", size=12)
                pdf.cell(190, 10, txt=f"귀사는 상시 근로자 {c_emp}명으로 '{labor_type} 사업장' 기준이 엄격히 적용됩니다. ", ln=True)
                
                rules = [
                    ("연차 유급 휴가", "의무 (15일~최대 25일)", "미적용 (자율)"),
                    ("가산 수당(연장/야간/휴일)", "50% 가산 지급 의무", "미적용 (시급만 지급)"),
                    ("부당해고 구제 신청", "노동위원회 신청 가능", "민사 소송만 가능"),
                    ("관공서 공휴일 유급휴무", "유급 휴무 의무 적용", "미적용 (자율)")
                ]
                pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Nanum", size=10)
                pdf.cell(65, 10, "노무 항목", 1, 0, 'C', True); pdf.cell(125, 10, f"{labor_type} 사업장 적용 기준", 1, 1, 'C', True)
                for title, high, low in rules:
                    pdf.cell(65, 10, title, 1, 0, 'C'); pdf.cell(125, 10, high if c_emp >= 5 else low, 1, 1, 'L')

                pdf_bytes = bytes(pdf.output())
                st.download_button("💾 종합 경영진단 보고서 다운로드", data=pdf_bytes, file_name=f"진단보고서_{c_name}.pdf")
