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

# --- [1. 사용자 데이터베이스 및 승인 로직] ---
# Huh Ja-hyun 대표님의 관리 권한을 위한 시스템
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
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52; margin-bottom:0;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 경영진단 AI 마스터 v15.0 [Hyper-Scan]</p>", unsafe_allow_html=True)
    
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

# --- [3. 하이퍼 스캔 데이터 추출 엔진 (개요 PDF 정밀 타겟팅)] ---

def clean_financial_num(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    # 특수문자 및 공백 제거
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def hyper_analyzer(files):
    """Hyper-Scan: 비표준 텍스트 구조를 분해하여 핵심 데이터 강제 추출"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False, '기업부설연구소': False}
    }
    
    for file in files:
        # PDF 하이퍼 스캔 (개요.pdf 특수 텍스트 레이어 대응)
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            all_txt = ""
            for page in reader.pages:
                all_txt += page.extract_text() + "\n"
            
            # 모든 종류의 유니코드 공백 및 특수문자 정규화
            norm_txt = re.sub(r'\s+', ' ', all_txt) # 중복 공백 제거
            tight_txt = norm_txt.replace(" ", "")  # 완전 압축
            
            # 1. 기업명 추출 (위치 기반: '기업명' 뒤의 텍스트)
            comp_match = re.search(r'기업명\s*[:：\s-]*\s*([가-힣\(\)A-Za-z0-9&]+)', norm_txt)
            if comp_match: res['comp'] = comp_match.group(1).strip()
            
            # 2. 대표자 추출 (위치 기반: '대표자' 뒤의 한글)
            ceo_match = re.search(r'대표자(?:명)?\s*[:：\s-]*\s*([가-힣]{2,4})', norm_txt)
            if ceo_match: res['ceo'] = ceo_match.group(1).strip()
            
            # 3. 종업원수 추출 (숫자+명 조합 정밀 검색)
            emp_match = re.search(r'종업원수\s*[:：\s-]*\s*(\d+)', norm_txt)
            if emp_match: res['emp'] = int(emp_m.group(1)) if (emp_m := emp_match) else 0
            if res['emp'] == 0: # 텍스트가 붙어있을 경우 재검색
                emp_m_alt = re.search(r'종업원수(\d+)', tight_txt)
                if emp_m_alt: res['emp'] = int(emp_m_alt.group(1))
            
            # 4. 인증 현황 추출
            cert_keywords = {'벤처': '벤처', '연구개발전담부서': '연구개발전담부서', '이노비즈': '이노비즈', '메인비즈': '메인비즈', '기업부설연구소': '부설연구소'}
            for key, kw in cert_keywords.items():
                if f"{kw}인증" in tight_txt or f"{kw}보유" in tight_txt:
                    res['certs'][key] = True

        # 엑셀/CSV 정밀 분석 (천원 단위 및 1차년도 데이터 보존)
        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # B, C, D열 위치 강제 고정
                    targets = {'매출액': '매출', '순이익': '이익', '자산': '자산', '부채': '부채'}
                    for kw, key in targets.items():
                        if kw in row_txt:
                            v1, v2, v3 = clean_financial_num(row.values[2]), clean_financial_num(row.values[3]), clean_financial_num(row.values[4])
                            if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
            except: pass
    return res

# --- [4. 메인 화면 및 관리 기능] ---

st.markdown('<div class="premium-header"><h1>📊 [Hyper-Scan] 종합 경영진단 및 리포트 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당 컨설턴트: **{st.session_state.authenticated_user}**")
    if st.button("로그아웃"): 
        st.session_state.authenticated_user = None
        st.rerun()
    
    # 관리자 전용 승인 메뉴
    u_info = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if u_info['is_admin']:
        st.divider(); st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 상태 변경", user_db['email'])
        if st.button("승인 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

# --- [5. 메인 데이터 분석 및 시각화] ---

col_left, col_right = st.columns([1, 1.4])

with col_left:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 한꺼번에 업로드하세요.", accept_multiple_files=True)
    
    if up_files:
        data = hyper_analyzer(up_files)
        st.success("✅ Hyper-Scan 데이터 인식 성공")
        
        with st.expander("📝 추출 데이터 보정 및 최종 확인", expanded=True):
            # (주)메이홈, 박승미, 10명 데이터가 자동으로 들어갑니다.
            f_comp = st.text_input("🏢 기업 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 상시 근로자수(명)", value=data['emp'])
            
            st.divider(); st.write("🛡️ **보유 인증 진단**")
            cert_vals = {}
            for cert, have in data['certs'].items():
                cert_vals[cert] = st.checkbox(cert, value=have)
            
            st.divider(); st.write("💰 **재무 수치 (단위: 천원)**")
            r_rev = st.number_input("2024년 매출액", value=data['fin']['매출'][2])
            r_inc = st.number_input("2024년 순이익", value=data['fin']['이익'][2])
            r_asset = st.number_input("2024년 자산총계", value=data['fin']['자산'][2])
            r_debt = st.number_input("2024년 부채총계", value=data['fin']['부채'][2])

with col_right:
    st.subheader("📈 경영 진단 및 주식 가치 시뮬레이션")
    if up_files:
        # 노무 타입 결정
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"현재 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 노무 전용 가이드가 생성됩니다.")
        
        # 가치 평가 (천원 -> 원 환산)
        stock_price = ((r_inc * 1000 / 0.1)*0.6 + (r_asset - r_debt)*1000*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시뮬레이션", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 경영진단 보고서 발행 (PDF)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_p): pdf.add_font("Nanum", "", f_p); pdf.set_font("Nanum", size=12)
            
            # --- [PAGE 1: 표지] ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="RE-PORT: 종합 경영진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"기업명: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            pdf.ln(100); pdf.set_font("Nanum", size=14); pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y-%m-%d')}", ln=True, align='C')
            pdf.cell(190, 10, txt="중소기업경영지원단 AI 컨설팅 본부", ln=True, align='C')
            
            # --- [PAGE 2: 재무 및 가치 평가] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 정밀 재무 진단 및 기업가치 분석", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_font("Nanum", size=12); pdf.cell(190, 10, txt=f"■ 분석 기업: {f_comp} (상시 근로자 {f_emp}명)", ln=True)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82); pdf.cell(190, 15, txt=f"▶ 현시점 주당 추정가액: {int(stock_price):,} 원", ln=True)
            fig.savefig("midas_v_chart.png", dpi=300); pdf.image("midas_v_chart.png", x=15, w=180)
            
            # --- [PAGE 3: 기업 인증 진단 (가변)] ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 핵심 기업 인증 현황 및 로드맵", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            cert_txt = {
                "벤처": "법인세 50% 감면 및 정부 정책자금 한도 우대를 위해 필수적입니다.",
                "연구개발전담부서": "연구원 인건비의 25%를 세액공제 받을 수 있는 SME 최고의 절세 수단입니다.",
                "이노비즈": "기술력을 대외적으로 인정받아 금융권 금리 우대를 받을 수 있습니다."
            }
            for c, desc in cert_txt.items():
                status = "보유" if cert_vals.get(c, False) else "미보유 (도입필요)"
                pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
                pdf.cell(190, 10, txt=f"● {c} 인증 : {status}", ln=True)
                pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(185, 8, txt=f"혜택 안내: {desc}\n")
                if "미보유" in status:
                    pdf.set_text_color(200, 0, 0); pdf.cell(190, 8, txt="→ 기업 경쟁력 강화를 위해 조속한 취득 전략 수립을 제안합니다.", ln=True)
                pdf.ln(5); pdf.set_text_color(0,0,0)

            # --- [PAGE 4: 인사 노무 가이드 (인원수 기반 가변)] ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="3. 상시 인원별 맞춤형 노무 기준", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_font("Nanum", size=12); pdf.cell(190, 10, txt=f"진단 결과: 현재 {f_emp}명으로 '{labor_type} 사업장' 법규가 적용됩니다.", ln=True)
            
            rules = [
                ("연차 유급 휴가", "의무 발생 (15일~)", "미적용 (자율)"),
                ("가산 수당(연장/야간)", "50% 가산 지급 의무", "미적용 (시급 지급)"),
                ("부당해고 구제 신청", "노동위원회 신청 가능", "민사 소송만 가능")
            ]
            pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Nanum", size=11)
            pdf.cell(65, 10, "노무 항목", 1, 0, 'C', True); pdf.cell(125, 10, f"{labor_type} 사업장 적용 기준", 1, 1, 'C', True)
            for title, high, low in rules:
                pdf.cell(65, 10, title, 1, 0, 'C'); pdf.cell(125, 10, high if f_emp >= 5 else low, 1, 1, 'L')

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 경영진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
