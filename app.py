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

# 차트 한글 폰트 설정 (시스템 내 나눔고딕 기준)
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
        # 관리자 허자현 대표님 설정
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

# --- [2. 로그인 및 보안 화면] ---
if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52; margin-bottom:0;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 경영진단 AI 마스터 v23.0 [Ultra-Logic]</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    
    col_l, col_r = st.columns(2)
    if col_l.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == login_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email
            st.rerun()
        elif not user_row.empty and not user_row.iloc[0]['approved']:
            st.warning("⚠️ 관리자의 승인을 기다리는 중입니다.")
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

# --- [3. 울트라 스캐너 엔진 (PDF/엑셀 무결점 인식)] ---

def clean_num(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def ultra_analyzer(files):
    """문서 파편화를 해결하는 문맥 재구성 엔진"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False}
    }
    
    for file in files:
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            full_txt = ""
            for page in reader.pages:
                full_txt += page.extract_text() + " \n "
            
            # 텍스트 노멀라이징 (모든 공백과 특수문자를 압축하여 검색)
            clean_txt = full_txt.replace(" ", "").replace("\n", "").replace("\t", "").replace(":", "")
            
            # 기업명 추출 (개요.pdf: (주)메이홈)
            comp_m = re.search(r'기업명\s*[:：\- ]+\s*([가-힣\(\)A-Za-z0-9&]+)', full_txt)
            if not comp_m: comp_m = re.search(r'기업명([가-힣\(\)A-Za-z0-9&]+)', clean_txt)
            if comp_m: res['comp'] = comp_m.group(1).strip()
            
            # 대표자 추출 (박승미)
            ceo_m = re.search(r'대표자(?:명)?\s*[:：\- ]+\s*([가-힣]{2,4})', full_txt)
            if not ceo_m: ceo_m = re.search(r'대표자(?:명)?([가-힣]{2,4})', clean_txt)
            if ceo_m: res['ceo'] = ceo_m.group(1).strip()
            
            # 종업원수 추출 (10명)
            emp_m = re.search(r'종업원수\s*[:：\- ]*(\d+)', full_txt)
            if not emp_m: emp_m = re.search(r'종업원수(\d+)', clean_txt)
            if emp_m: res['emp'] = int(emp_m.group(1))
            
            # 인증 현황
            for key in res['certs'].keys():
                if key in clean_txt: res['certs'][key] = True

        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 재무 키워드 매칭 (자산, 부채, 매출 등)
                    mapping = {'자산': '자산', '부채': '부채', '매출액': '매출', '순이익': '이익'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            # 2022~2024 데이터 위치(B, C, D열) 강제 추출
                            try:
                                v1, v2, v3 = clean_num(row.values[2]), clean_num(row.values[3]), clean_num(row.values[4])
                                if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
                            except: pass
            except: pass
    return res

# --- [4. 메인 화면 및 관리자 기능] ---

st.markdown('<div class="premium-header"><h1>📊 [MASTER] 종합 경영진단 리포트 & 재무분석 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당: **{st.session_state.authenticated_user}** 팀장님")
    if st.button("로그아웃"): 
        st.session_state.authenticated_user = None
        st.rerun()
    
    u_info = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if u_info['is_admin']:
        st.divider(); st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 상태 변경", user_db['email'])
        if st.button("상태 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 한꺼번에 올려주세요.", accept_multiple_files=True)
    
    if up_files:
        data = ultra_analyzer(up_files)
        st.success("✅ [퀀텀 스캔] 데이터 인식 성공 (22~24년 자동 매칭)")
        
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 상시 근로자수(명)", value=data['emp'])
            
            st.divider(); st.write("🛡️ **보유 인증 진단**")
            cert_vals = {}
            for cert, have in data['certs'].items():
                cert_vals[cert] = st.checkbox(cert, value=have)
            
            st.divider(); st.write("💰 **최신 재무 (단위: 천원)**")
            r_rev = st.number_input("2024년 매출액", value=data['fin']['매출'][2])
            r_inc = st.number_input("2024년 순이익", value=data['fin']['이익'][2])
            r_asset = st.number_input("2024년 자산총계", value=data['fin']['자산'][2])
            r_debt = st.number_input("2024년 부채총계", value=data['fin']['부채'][2])

with col_r:
    st.subheader("📈 실시간 진단 결과 시뮬레이션")
    if up_files:
        # 노무 타입 자동 결정 (10명 기준 5인 이상)
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석: 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 전용 분석 가이드가 추가됩니다.")
        
        # 가치 평가 (천원 -> 원 환산)
        stock_price = ((r_inc * 1000 / 0.1)*0.6 + (r_asset - r_debt)*1000*0.4) / 100000
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시뮬레이션", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 경영진단 보고서 발행 (재무제표 전문 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_path): pdf.add_font("Nanum", "", f_path); pdf.set_font("Nanum", size=12)
            
            # --- [PAGE 1: 리포트 표지] ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="RE-PORT: 종합 경영진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"대상기업: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            pdf.ln(100); pdf.set_font("Nanum", size=14); pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y-%m-%d')}", ln=True, align='C')
            pdf.cell(190, 10, txt="중소기업경영지원단 AI 컨설팅 본부", ln=True, align='C')
            
            # --- [PAGE 2: 재무제표 전문 (BS/IS)] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 주요 재무제표 분석 (단위: 천원)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            
            # 재무제표 테이블 구성
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Nanum", size=11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (최근 기말)", 1, 1, 'C', True)
            
            # 자산/부채 행
            f_data = data['fin']
            rows = [("자산 총계", f_data['자산'][1], r_asset), ("부채 총계", f_data['부채'][1], r_debt), ("매출액", f_data['매출'][1], r_rev), ("당기순이익", f_data['이익'][1], r_inc)]
            for name, v23, v24 in rows:
                pdf.cell(50, 10, name, 1, 0, 'C'); pdf.cell(70, 10, f"{v23:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v24:,.0f}", 1, 1, 'R')
            
            pdf.ln(10); pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 10, txt="▶ 재무 지표 진단 결과", ln=True)
            pdf.set_font("Nanum", size=11); pdf.set_text_color(0,0,0)
            pdf.multi_cell(190, 8, txt=f"귀사의 2024년 자산총계는 {r_asset:,.0f}천원이며, 당기순이익 {r_inc:,.0f}천원을 기록하며 안정적인 성장세를 보이고 있습니다. 부채 비율은 {(r_debt/r_asset*100):.1f}%로 건전한 수준입니다.")

            # --- [PAGE 3: 기업가치 평가] ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 비상장주식 가치 평가 시뮬레이션", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 15, txt=f"▶ 현시점 주당 추정가액: {int(stock_price):,} 원", ln=True)
            fig.savefig("v_chart_v23.png", dpi=300); pdf.image("v_chart_v23.png", x=15, w=180)
            
            # --- [PAGE 4: 인증 및 노무 (가변 추가)] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="3. 기업 인증 및 노무 리스크 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            cert_g = {"벤처": "법인세 50% 감면 필수인증", "연구개발전담부서": "인건비 25% 세액공제", "이노비즈": "금리 우대 및 입찰 가점"}
            for c, desc in cert_g.items():
                status = "보유" if cert_vals.get(c, False) else "미보유 (도입필요)"
                pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82); pdf.cell(190, 10, txt=f"● {c} 인증 : {status}", ln=True)
                pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80); pdf.multi_cell(185, 8, txt=f"필요성: {desc}\n")
            
            pdf.ln(5); pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82); pdf.cell(190, 10, txt="▶ 인사 노무 기준법 진단", ln=True)
            pdf.set_font("Nanum", size=11); pdf.set_text_color(0,0,0); pdf.cell(190, 10, txt=f"상시 근로자 {f_emp}명으로 '{labor_type} 사업장' 법규가 적용됩니다.", ln=True)
            rules = [("연차 유급 휴가", "의무 (15일~)", "미적용"), ("가산 수당", "50% 가산 지급", "시급만 지급"), ("부당해고 구제", "노동위원회 가능", "민사 소송만")]
            for title, hi, lo in rules:
                pdf.cell(60, 10, title, 1, 0, 'C'); pdf.cell(130, 10, hi if f_emp >= 5 else lo, 1, 1, 'L')

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
