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

# --- [1. 사용자 데이터베이스 및 승인 시스템] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        # 초기 관리자 계정 설정 (인천00@gmail.com)
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

# --- [2. 정밀 파싱 엔진 (개요.pdf 및 천원단위 엑셀 대응)] ---

def clean_num(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def smart_analyzer(files):
    """파일에서 기업정보, 재무, 인증, 노무 데이터를 통합 스캔"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False}
    }
    
    for file in files:
        # 1. PDF 정밀 스캔 (개요.pdf 특화)
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            txt = ""
            for page in reader.pages:
                txt += page.extract_text() + "\n"
            
            # 기업명/대표자 (기호 및 줄바꿈 유연 대응)
            c_match = re.search(r'기업명\s*[:|-]\s*([가-힣\(\)A-Za-z0-9]+)', txt)
            if c_match: res['comp'] = c_match.group(1).strip()
            
            ceo_match = re.search(r'대표자(?:명)?\s*[:|-]\s*([가-힣]{2,4})', txt)
            if ceo_match: res['ceo'] = ceo_match.group(1).strip()
            
            # 종업원수 (개요.pdf 2페이지 하단 대응)
            emp_match = re.search(r'종업원수\s*[:|-]?\s*(\d+)명', txt)
            if emp_match: res['emp'] = int(emp_match.group(1))
            
            # 인증 현황 (기술력 페이지 대응)
            for cert in res['certs'].keys():
                if f"{cert} 인증" in txt or f"{cert}\n인증" in txt: res['certs'][cert] = True

        # 2. 엑셀/CSV 정밀 스캔 (천원 단위 및 연도 고정)
        if file.name.endswith(('.xlsx', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 키워드별 열 위치 고정 (22, 23, 24년)
                    mapping = {'매출액': '매출', '순이익': '이익', '자산': '자산', '부채': '부채'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            try:
                                # 엑셀 구조상 우측 3개 열이 데이터임
                                v1, v2, v3 = clean_num(row.values[2]), clean_num(row.values[3]), clean_num(row.values[4])
                                if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
                            except: pass
            except: pass
    return res

# --- [3. 메인 화면 및 관리자 기능] ---
st.markdown('<div class="premium-header"><h1>📊 [PRIME] 종합 경영진단 및 리포트 자동화 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 컨설턴트: **{st.session_state.authenticated_user}**")
    if st.button("로그아웃"): st.session_state.authenticated_user = None; st.rerun()
    
    # 관리자 전용 승인 메뉴 (허자현 대표님 전용)
    u_info = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if u_info['is_admin']:
        st.divider(); st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 상태 변경", user_db['email'])
        if st.button("승인 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

col_in, col_out = st.columns([1, 1.4])

with col_in:
    st.subheader("📂 진단 자료 통합 업로드")
    up_files = st.file_uploader("개요 PDF 및 재무 엑셀을 한꺼번에 업로드하세요.", accept_multiple_files=True)
    
    if up_files:
        data = smart_analyzer(up_files)
        st.success("✅ 파일 데이터 정밀 추출 완료")
        
        with st.expander("📝 데이터 보정 및 최종 확인", expanded=True):
            f_comp = st.text_input("🏢 기업 공식 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 상시 근로자수(명)", value=data['emp'])
            
            st.divider(); st.write("🛡️ **보유 인증 진단**")
            c_vals = {}
            for cert, have in data['certs'].items():
                c_vals[cert] = st.checkbox(cert, value=have)
            
            st.divider(); st.write("💰 **최신 재무 (단위: 천원)**")
            r_rev = st.number_input("2024년 매출액", value=data['fin']['매출'][2])
            r_inc = st.number_input("2024년 순이익", value=data['fin']['이익'][2])

with col_out:
    st.subheader("📈 실시간 리포트 구성 시뮬레이션")
    if up_files:
        # 노무 가이드 타입 결정
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"현재 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 법규 안내 페이지가 자동 추가됩니다.")
        
        # 가치 평가 (천원 -> 원 환산)
        stock_val = ((r_inc * 1000 / 0.1)*0.6 + (data['fin']['자산'][2]-data['fin']['부채'][2])*1000*0.4) / 100000
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시뮬레이션", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 경영진단 보고서 발행 (PDF)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_p): pdf.add_font("Nanum", "", f_p); pdf.set_font("Nanum", size=12)
            
            # --- Page 1: 표지 ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="RE-PORT: 종합 경영진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"대상기업: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            pdf.ln(100); pdf.set_font("Nanum", size=14)
            pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y년 %m월 %d일')}", ln=True, align='C')
            pdf.cell(190, 10, txt="중소기업경영지원단 컨설팅 본부", ln=True, align='C')
            
            # --- Page 2: 재무/가치 분석 ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 재무 데이터 분석 및 가치 평가", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"■ 최신 매출액: {r_rev:,.0f} 천원", ln=True)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 15, txt=f"▶ 현시점 주당 가치: {int(stock_val):,} 원", ln=True)
            fig.savefig("midas_rep.png", dpi=300); pdf.image("midas_rep.png", x=15, w=180)
            
            # --- Page 3: 인증 진단 ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 핵심 기업 인증 현황 및 로드맵", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            cert_desc = {
                "벤처": "법인세 50% 감면 및 정책자금 한도 우대 혜택 필수",
                "연구개발전담부서": "연구원 인건비 25% 세액공제 최우선 설립 권장",
                "이노비즈": "기술력을 인정받아 금융권 금리 우대 및 입찰 가점"
            }
            for c, desc in cert_desc.items():
                status = "보유" if c_vals.get(c, False) else "미보유 (도입필요)"
                pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
                pdf.cell(190, 10, txt=f"● {c} 인증 현황 : {status}", ln=True)
                pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(185, 8, txt=f"필요성: {desc}\n")
                if "미보유" in status:
                    pdf.set_text_color(200, 0, 0); pdf.cell(190, 8, txt="→ 기업 성장을 위해 조속한 취득 전략 수립을 제안합니다.", ln=True)
                pdf.ln(5); pdf.set_text_color(0,0,0)

            # --- Page 4: 노무 가이드 ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="3. 상시 인원별 맞춤형 노무 기준", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"분석 결과: 현재 {f_emp}명으로 '{labor_type} 사업장' 법규가 적용됩니다.", ln=True)
            
            rules = [("연차 유급 휴가", "의무 발생 (15일~)", "미적용"), ("가산 수당", "50% 가산 지급", "시급만 지급"), ("부당해고 구제", "노동위원회 신청 가능", "민사 소송만 가능")]
            pdf.ln(5); pdf.set_fill_color(240, 240, 240)
            pdf.cell(60, 10, "노무 항목", 1, 0, 'C', True); pdf.cell(130, 10, f"{labor_type} 적용 기준", 1, 1, 'C', True)
            for title, hi, lo in rules:
                pdf.cell(60, 10, title, 1, 0, 'C'); pdf.cell(130, 10, hi if f_emp >= 5 else lo, 1, 1, 'L')

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
    else:
        st.info("좌측 섹션에 '개요.pdf'와 재무 파일을 업로드해주세요.")
