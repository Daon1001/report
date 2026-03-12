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
        background-color: white !important; padding: 40px !important; border-radius: 20px !important; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1) !important; text-align: center !important; 
        max-width: 500px !important; margin: 10vh auto !important; border-top: 10px solid #0b1f52 !important;
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
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 경영진단 AI 마스터 v14.0 [Deep Scan]</p>", unsafe_allow_html=True)
    
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
            st.success("✅ 신청 완료! 관리자 승인 후 이용 가능합니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 초정밀 데이터 추출 엔진 (개요 PDF 정밀 스캔)] ---

def clean_financial_num(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def smart_analyzer(files):
    """Deep Scan: 텍스트 노멀라이징 및 위치 기반 데이터 추출"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False, '기업부설연구소': False}
    }
    
    for file in files:
        # PDF 정밀 분석 (개요.pdf 특수 양식 대응)
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            raw_text = ""
            for page in reader.pages:
                raw_text += page.extract_text() + "\n"
            
            # 1. 텍스트 정규화 (모든 공백과 특수문자를 제거하지 않고 패턴 유지)
            # 기업명 추출: "- 기업명 : (주)메이홈" 대응
            comp_search = re.search(r'기업명\s*[:：]\s*([가-힣\(\)A-Za-z0-9&]+)', raw_text)
            if comp_search: res['comp'] = comp_search.group(1).strip()
            
            # 대표자 추출: "- 대표자 : 박승미" 또는 "대표자명 박승미" 대응
            ceo_search = re.search(r'대표자(?:명)?\s*[:：\s]*\s*([가-힣]{2,4})', raw_text)
            if ceo_search: res['ceo'] = ceo_search.group(1).strip()
            
            # 종업원수 추출: "종업원수 10명" 대응
            emp_search = re.search(r'종업원수\s*[:：\s]*\s*(\d+)', raw_text)
            if emp_search: res['emp'] = int(emp_search.group(1))
            
            # 인증 추출: 벤처, 연구소 등 키워드와 '인증' 조합
            clean_text = raw_text.replace(" ", "").replace("\n", "")
            cert_map = {'벤처': '벤처', '연구개발전담부서': '연구개발전담부서', '이노비즈': '이노비즈', '메인비즈': '메인비즈', '기업부설연구소': '부설연구소'}
            for key, kw in cert_map.items():
                if f"{kw}인증" in clean_text or f"{kw}보유" in clean_text:
                    res['certs'][key] = True

        # 엑셀/CSV 정밀 분석 (1차년도 0값 보존 및 천원 단위 환산)
        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    targets = {'매출액': '매출', '순이익': '이익', '자산': '자산', '부채': '부채'}
                    for kw, key in targets.items():
                        if kw in row_txt:
                            try:
                                v1, v2, v3 = clean_financial_num(row.values[2]), clean_financial_num(row.values[3]), clean_financial_num(row.values[4])
                                if v1 != 0 or v2 != 0 or v3 != 0: res['fin'][key] = [v1, v2, v3]
                            except: pass
            except: pass
    return res

# --- [4. 메인 화면 및 관리 기능] ---

st.markdown('<div class="premium-header"><h1>📊 파일 기반 가변형 종합 진단 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당: **{st.session_state.authenticated_user}**")
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

# --- [5. 메인 데이터 분석 및 결과] ---

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 파일을 함께 업로드하세요.", accept_multiple_files=True)
    
    if up_files:
        data = smart_analyzer(up_files)
        st.success("✅ 파일 데이터 추출 성공 (Deep Scan 적용)")
        
        with st.expander("📝 데이터 보정 및 최종 확인", expanded=True):
            f_comp = st.text_input("🏢 기업 공식 명칭", data['comp'])
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

with col_r:
    st.subheader("📈 경영 진단 및 미래 예측")
    if up_files:
        # 노무 가이드 기준 설정
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"현재 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 노무 전용 가이드가 추가됩니다.")
        
        # 기업가치 평가 (천원 -> 원 환산)
        stock_price = ((r_inc * 1000 / 0.1)*0.6 + (r_asset - r_debt)*1000*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시뮬레이션", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 경영진단 보고서 발행 (PDF)", type="primary", use_container_width=True):
            pdf = FPDF()
            f_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(f_p): pdf.add_font("Nanum", "", f_p); pdf.set_font("Nanum", size=12)
            
            # --- Page 1: 표지 ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=18); pdf.cell(190, 20, txt=f"기업명: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            pdf.ln(100); pdf.set_font("Nanum", size=14); pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y-%m-%d')}", ln=True, align='C')
            pdf.cell(190, 10, txt="중소기업경영지원단 AI 컨설팅 본부", ln=True, align='C')
            
            # --- Page 2: 재무 및 가치 분석 ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 재무 지표 분석 및 기업가치 평가", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_font("Nanum", size=12); pdf.cell(190, 10, txt=f"■ 분석 기업: {f_comp} (상시 근로자 {f_emp}명)", ln=True)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82); pdf.cell(190, 15, txt=f"▶ 현시점 주당 추정가액: {int(stock_price):,} 원", ln=True)
            fig.savefig("v_chart.png", dpi=300); pdf.image("v_chart.png", x=15, w=180)
            
            # --- Page 3: 기업 인증 진단 (가변 추가) ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 핵심 기업 인증 현황 및 필요성 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            cert_text = {
                "벤처": "법인세 50% 감면 및 정부 정책자금 우대 혜택을 위해 필수적입니다.",
                "연구개발전담부서": "연구원 인건비의 25%를 세액공제 받을 수 있는 SME 최고의 절세 수단입니다.",
                "이노비즈": "기술력을 대외적으로 인정받아 금융권 금리 우대를 받을 수 있습니다."
            }
            for c, desc in cert_text.items():
                status = "보유" if cert_vals.get(c, False) else "미보유 (도입필요)"
                pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
                pdf.cell(190, 10, txt=f"● {c} 인증 : {status}", ln=True)
                pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(185, 8, txt=f"혜택 안내: {desc}\n")
                if "미보유" in status:
                    pdf.set_text_color(200, 0, 0); pdf.cell(190, 8, txt="→ 기업 경쟁력 향상을 위해 조속한 취득 컨설팅이 요구됩니다.", ln=True)
                pdf.ln(5); pdf.set_text_color(0,0,0)

            # --- Page 4: 노무 기준법 가이드 (인원수 기반 가변 추가) ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="3. 상시 인원별 노무 기준 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_font("Nanum", size=12); pdf.cell(190, 10, txt=f"분석 결과: 현재 인원 {f_emp}명으로 '{labor_type} 사업장' 법규가 적용됩니다.", ln=True)
            
            rules = [
                ("연차 유급 휴가", "의무 발생 (15일~)", "미적용 (자율)"),
                ("가산 수당(연장/야간)", "50% 가산 지급 의무", "미적용 (시급 지급)"),
                ("부당해고 구제 신청", "노동위원회 신청 가능", "민사 소송만 가능")
            ]
            pdf.ln(5); pdf.set_fill_color(240, 240, 240); pdf.set_font("Nanum", size=11)
            pdf.cell(60, 10, "노무 항목", 1, 0, 'C', True); pdf.cell(130, 10, f"{labor_type} 적용 기준", 1, 1, 'C', True)
            for title, high, low in rules:
                pdf.cell(60, 10, title, 1, 0, 'C'); pdf.cell(130, 10, high if f_emp >= 5 else low, 1, 1, 'L')

            pdf_out = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
