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
        max-width: 500px; margin: 10vh auto; border-top: 12px solid #0b1f52;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 DB 및 승인 시스템] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        # 초기 관리자 계정 설정 (인천00@gmail.com)
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "count": 0, "month": date.today().month}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df): df.to_csv(DB_FILE, index=False)
user_db = load_db()

if 'auth_user' not in st.session_state: st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    c1, c2 = st.columns(2)
    if c1.button("로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.auth_user = email; st.rerun()
        else: st.error("승인이 필요한 계정입니다.")
    if c2.button("사용 신청", use_container_width=True):
        if email and user_db[user_db['email'] == email].empty:
            new_u = pd.DataFrame([{"email": email, "approved": False, "is_admin": False, "count": 0, "month": date.today().month}])
            user_db = pd.concat([user_db, new_u], ignore_index=True); save_db(user_db)
            st.success("신청 완료!")
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
        # 1. PDF 정밀 스캔 (개요.pdf 양식) [cite: 3, 5, 16, 64, 67]
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            txt = " ".join([p.extract_text() for p in reader.pages])
            
            # 기업명/대표자 (줄바꿈 및 공백 무시 검색)
            c_match = re.search(r'기업명\s*[:|-]\s*([가-힣\(\)A-Za-z0-9]+)', txt)
            if c_match: res['comp'] = c_match.group(1).strip()
            
            ceo_match = re.search(r'대표자\s*[:|-]\s*([가-힣]{2,4})', txt)
            if ceo_match: res['ceo'] = ceo_match.group(1).strip()
            
            # 종업원수 
            emp_match = re.search(r'종업원수\s*[:|-]?\s*(\d+)명', txt)
            if emp_match: res['emp'] = int(emp_match.group(1))
            
            # 인증 현황 [cite: 64, 67]
            for cert in res['certs'].keys():
                if cert in txt.replace(" ", ""): res['certs'][cert] = True

        # 2. 엑셀 정밀 스캔 (천원 단위 및 1차년도 0값 대응)
        if file.name.endswith(('.xlsx', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 키워드별 열(Column) 위치 고정 추출 (22년, 23년, 24년)
                    targets = {'매출액': '매출', '순이익': '이익', '자산': '자산', '부채': '부채'}
                    for kw, key in targets.items():
                        if kw in row_txt:
                            # 엑셀의 데이터 열 위치(2, 3, 4번 인덱스)를 강제로 읽어 1차년도 누락 방지
                            try:
                                v1, v2, v3 = clean_num(row.values[2]), clean_num(row.values[3]), clean_num(row.values[4])
                                if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
                            except: pass
            except: pass
    return res

# --- [3. 메인 화면 및 관리자 기능] ---
st.markdown('<div class="premium-header"><h1>📊 [PRIME] 파일 분석 기반 종합 경영진단 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 컨설턴트: **{st.session_state.auth_user}**")
    if st.button("로그아웃"): st.session_state.auth_user = None; st.rerun()
    
    # 관리자 메뉴 (허자현 대표님 전용 승인 관리)
    curr_u = user_db[user_db['email'] == st.session_state.auth_user].iloc[0]
    if curr_u['is_admin']:
        st.divider(); st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 변경 대상", user_db['email'])
        if st.button("승인 상태 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

col_in, col_out = st.columns([1, 1.4])

with col_in:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 한꺼번에 업로드하세요.", accept_multiple_files=True)
    
    if up_files:
        data = smart_analyzer(up_files)
        st.success("✅ 파일 데이터 추출 완료 (1~3차년도 매칭)")
        
        with st.expander("📝 추출 데이터 보정 및 확인", expanded=True):
            f_comp = st.text_input("🏢 기업 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 종업원수(명)", value=data['emp'])
            
            st.divider(); st.write("🛡️ **보유 인증 진단**")
            c_vals = {}
            for cert, have in data['certs'].items():
                c_vals[cert] = st.checkbox(cert, value=have)
            
            st.divider(); st.write("💰 **재무 수치 (단위: 천원)**")
            r_rev = st.number_input("24년 매출액", value=data['fin']['매출'][2])
            r_inc = st.number_input("24년 순이익", value=data['fin']['이익'][2])

with col_out:
    st.subheader("📈 실시간 리포트 구성 시뮬레이션")
    if up_files:
        # 노무 타입 결정
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"현재 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 전용 분석 페이지가 자동 생성됩니다.")
        
        # 가치 평가 (천원 -> 원 환산)
        stock_val = ((r_inc * 1000 / 0.1)*0.6 + (data['fin']['자산'][2]-data['fin']['부채'][2])*1000*0.4) / 100000
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시뮬레이션", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 미다스형 종합 정밀 보고서 발행", type="primary", use_container_width=True):
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
            
            # --- Page 2: 재무/가치 분석 ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 재무 데이터 분석 및 기업가치 평가", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"■ 최신 매출액: {r_rev:,.0f} 천원 (전기 대비 성장 중)", ln=True)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 15, txt=f"▶ 현시점 주당 가치: {int(stock_val):,} 원", ln=True)
            fig.savefig("midas_chart.png", dpi=300); pdf.image("midas_chart.png", x=15, w=180)
            
            # --- Page 3: 기업 인증 진단 (가변 페이지) ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 핵심 기업 인증 현황 및 필요성 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            cert_guide = {
                "벤처": "법인세 50% 감면 및 정책자금 한도 우대 혜택 필수",
                "연구개발전담부서": "연구원 인건비 25% 세액공제 최우선 설립 권장",
                "이노비즈": "금융권 금리 우대 및 입찰 시 가점 확보"
            }
            for c, desc in cert_guide.items():
                status = "보유" if c_vals.get(c, False) else "미보유 (도입필요)"
                pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
                pdf.cell(190, 10, txt=f"● {c} 인증 : {status}", ln=True)
                pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(185, 8, txt=f"컨설팅 가이드: {desc}\n")
                if "미보유" in status:
                    pdf.set_text_color(200, 0, 0); pdf.cell(190, 8, txt="→ 기업 경쟁력 향상을 위한 취득 전략이 필요합니다.", ln=True)
                pdf.ln(5); pdf.set_text_color(0,0,0)

            # --- Page 4: 노무 가이드 (인원수 가변 페이지) ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="3. 상시 인원별 노무 기준법 가이드", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"분석 결과: 근로자 {f_emp}명으로 '{labor_type} 사업장' 법규가 적용됩니다.", ln=True)
            
            rules = [("연차 유급 휴가", "의무 발생 (15일~)", "미적용 (자율)"), ("가산 수당", "50% 가산 지급", "시급만 지급"), ("부당해고 구제", "노동위원회 신청 가능", "민사 소송만 가능")]
            pdf.ln(5); pdf.set_fill_color(240, 240, 240)
            pdf.cell(60, 10, "노무 항목", 1, 0, 'C', True); pdf.cell(130, 10, f"{labor_type} 적용 기준", 1, 1, 'C', True)
            for title, high, low in rules:
                pdf.cell(60, 10, title, 1, 0, 'C'); pdf.cell(130, 10, high if f_emp >= 5 else low, 1, 1, 'L')

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
