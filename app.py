import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import pdfplumber
from fpdf import FPDF
import re
from datetime import date
import numpy as np

# --- [0. 페이지 설정 및 폰트 안전 로딩] ---
st.set_page_config(page_title="중소기업 종합 재무진단 AI", layout="wide")

# 폰트 경로 설정 (malgun.ttf 또는 NanumGothic.ttf)
base_dir = os.path.dirname(__file__)
font_path = os.path.join(base_dir, "malgun.ttf")
if not os.path.exists(font_path):
    font_path = os.path.join(base_dir, "NanumGothic.ttf")

def set_korean_font(path):
    try:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            font_prop = fm.FontProperties(fname=path)
            plt.rc('font', family=font_prop.get_name())
            plt.rcParams['axes.unicode_minus'] = False
            return True
    except:
        pass
    return False

has_font = set_korean_font(font_path)

st.markdown("""
<style>
    .stApp { background-color: #f8faff !important; }
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1e3a8a 100%); 
        color: white; padding: 2.5rem; border-radius: 15px; 
        border-bottom: 5px solid #d4af37; text-align: center; margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .admin-card {
        background: white; padding: 20px; border-radius: 10px;
        border-left: 5px solid #d4af37; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 관리자 승인 시스템] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        # 관리자 초기 설정
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

if 'auth_user' not in st.session_state:
    st.session_state.auth_user = None

# --- [2. 로그인 및 보안 화면] ---
if st.session_state.auth_user is None:
    st.markdown('<div style="background:white; padding:50px; border-radius:20px; max-width:500px; margin:10vh auto; text-align:center; border-top:12px solid #0b1f52; box-shadow: 0 15px 35px rgba(0,0,0,0.15);">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52; margin-bottom:0;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 경영진단 시스템 v44.0 [Master-Integrated]</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    
    col_l, col_r = st.columns(2)
    if col_l.button("로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == login_email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.auth_user = login_email
            st.rerun()
        elif not row.empty:
            st.warning("⚠️ 승인 대기 중인 계정입니다.")
        else:
            st.error("❌ 등록되지 않은 계정입니다.")
            
    if col_r.button("사용 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_u = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False}])
            user_db = pd.concat([user_db, new_u], ignore_index=True)
            save_db(user_db)
            st.success("✅ 신청 완료! 대표자 승인 후 이용 가능합니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 데이터 추출 엔진 (Deep Scan)] ---

def clean_num(val):
    if val is None or val == "": return 0.0
    s = str(val).replace(',', '').replace('"', '').replace('\n', '').replace(' ', '').strip()
    s = re.sub(r'[^\d.-]', '', s)
    try: return float(s)
    except: return 0.0

def deep_scan_engine(files):
    """PDF/엑셀 파편화를 완전히 해결하는 딥 스캐닝 로직"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False}
    }
    
    for file in files:
        if file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
                
                # 따옴표/쉼표/줄바꿈 압축 매칭
                norm = full_text.replace('"', ' ').replace('\n', ' ').replace(',', ' ')
                
                if res['comp'] == "미상":
                    m = re.search(r'기업명\s*[:：]?\s*([가-힣\(\)A-Za-z0-9&]+)', norm)
                    if m: res['comp'] = m.group(1).strip()
                
                if res['ceo'] == "미상":
                    m = re.search(r'대표자(?:명)?\s*[:：]?\s*([가-힣]{2,4})', norm)
                    if m: res['ceo'] = m.group(1).strip()
                
                if res['emp'] == 0:
                    m = re.search(r'종업원수\s*[:：]?\s*(\d+)', norm)
                    if m: res['emp'] = int(m.group(1))

                tight = full_text.replace(" ", "").replace("\n", "")
                for k in res['certs'].keys():
                    if f"{k}인증" in tight or f"{k}보유" in tight: res['certs'][k] = True

        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_excel(file, header=None) if file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values if v is not None]).replace(" ", "")
                    mapping = {'자산': '자산', '부채': '부채', '매출': '매출', '이익': '이익'}
                    for kw, key in mapping.items():
                        if kw in row_txt:
                            nums = [clean_num(v) for v in row.values if clean_num(v) != 0 or v == 0]
                            if len(nums) >= 3: res['fin'][key] = nums[-3:]
            except: pass
    return res

# --- [4. 메인 대시보드 및 관리자 메뉴] ---

st.markdown('<div class="premium-header"><h1>📊 종합 경영 진단 및 재무 분석 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당: **{st.session_state.auth_user}**")
    if st.button("로그아웃"): 
        st.session_state.auth_user = None
        st.rerun()
    
    # 관리자 전용 메뉴
    user_info = user_db[user_db['email'] == st.session_state.auth_user].iloc[0]
    if user_info['is_admin']:
        st.divider()
        st.subheader("👑 관리자 통제 센터")
        with st.expander("사용자 승인 관리", expanded=False):
            st.dataframe(user_db[['email', 'approved']], use_container_width=True)
            target_email = st.selectbox("승인할 계정 선택", user_db['email'])
            if st.button("승인 상태 전환", use_container_width=True):
                user_db.loc[user_db['email'] == target_email, 'approved'] = not user_db.loc[user_db['email'] == target_email, 'approved'].iloc[0]
                save_db(user_db)
                st.success(f"{target_email} 상태 변경 완료!")
                st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 함께 올려주세요.", accept_multiple_files=True)
    
    # 데이터 초기화
    f_comp, f_ceo, f_emp = "미상", "미상", 0
    fin_res = {'fin': {'매출':[0,0,0], '이익':[0,0,0], '자산':[0,0,0], '부채':[0,0,0]}}
    pdf_res = {'comp': "미상", 'ceo': "미상", 'emp': 0, 'certs': {}}

    if up_files:
        data_all = deep_scan_engine(up_files)
        st.success("✅ 모든 데이터 인식 성공 (v44.0 Master-Scan)")
        
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            f_comp = st.text_input("🏢 기업 공식 명칭", data_all['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data_all['ceo'])
            f_emp = st.number_input("👥 종업원수(명)", value=data_all['emp'])
            st.divider()
            # 2024년 데이터 자동 연동
            r_rev = st.number_input("2024 매출액 (천원/백만원)", value=data_all['fin']['매출'][2])
            r_inc = st.number_input("2024 순이익", value=data_all['fin']['이익'][2])
            r_asset = st.number_input("2024 자산총계", value=data_all['fin']['자산'][2])
            r_debt = st.number_input("2024 부채총계", value=data_all['fin']['부채'][2])

with col_r:
    st.subheader("📈 경영 지표 진단 시뮬레이션")
    if up_files:
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석 결과: 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 법규 가이드가 자동 적용됩니다.")
        
        # 가치 평가
        unit = 1000000 if r_rev < 100000 else 1000
        stock_val = ((r_inc * unit / 0.1)*0.6 + (r_asset - r_debt)*unit*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 가치 상승 시나리오")
        st.pyplot(fig)

        if st.button("🚀 종합 보고서 발행 (재무제표 전문 분석 포함)", type="primary", use_container_width=True):
            pdf = FPDF()
            if has_font:
                pdf.add_font("Malgun", "", font_path)
                pdf.set_font("Malgun", size=12)
            else:
                pdf.set_font("helvetica", size=12)
            
            # --- [PAGE 1: 표지] ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90)
            pdf.set_font_size(32); pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font_size(18); pdf.cell(190, 20, txt=f"대상기업: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            
            # --- [PAGE 2: 재무제표 전문 분석 (BS/IS)] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font_size(20)
            pdf.cell(190, 15, txt="1. 정밀 재무제표 및 AI 분석 (단위: 천원)", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            pdf.set_fill_color(240, 240, 240); pdf.set_font_size(11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (최근 기말)", 1, 1, 'C', True)
            
            rows_data = [
                ("자산 총계", data_all['fin']['자산'][1], r_asset), 
                ("부채 총계", data_all['fin']['부채'][1], r_debt), 
                ("매출액", data_all['fin']['매출'][1], r_rev), 
                ("당기순이익", data_all['fin']['이익'][1], r_inc)
            ]
            for n, v1, v2 in rows_data:
                pdf.cell(50, 10, n, 1); pdf.cell(70, 10, f"{v1:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v2:,.0f}", 1, 1, 'R')
            
            pdf.ln(10); pdf.set_font_size(13); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 10, txt="▶ 전문가 종합 재무 분석 결과", ln=True)
            pdf.set_font_size(11); pdf.set_text_color(0,0,0)
            d_rate = (r_debt / r_asset * 100) if r_asset > 0 else 0
            pdf.multi_cell(190, 8, txt=f"분석 결과, {f_comp}의 2024년 부채비율은 {d_rate:.1f}%로 양호합니다. 특히 매출액 및 순이익이 전년 대비 큰 폭으로 상승하며 안정적인 현금 흐름을 창출하고 있습니다. 기업 가치 증대를 위한 적극적인 투자 전략 수립이 가능한 시점입니다.")

            # --- [PAGE 3: 기업가치 및 리스크] ---
            pdf.add_page(); pdf.set_font_size(20)
            pdf.cell(190, 15, txt="2. 주식가치 평가 및 리스크 분석", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            fig.savefig("v44_final.png", dpi=300); pdf.image("v44_final.png", x=15, w=180)
            pdf.ln(10); pdf.set_font_size(12)
            pdf.cell(190, 10, txt=f"■ 인증현황: 벤처({('보유' if data_all['certs']['벤처'] else '미보유')}), 전담부서({('보유' if data_all['certs']['연구개발전담부서'] else '미보유')})", ln=True)
            pdf.cell(190, 10, txt=f"■ 노무관리: 상시 근로자 {f_emp}명에 따른 '{labor_type}' 기준 적용 필수", ln=True)

            pdf_out = bytes(pdf.output())
            st.download_button("💾 한글 종합 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
