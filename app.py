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

# 차트 한글 폰트 설정 (나눔고딕)
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
    .report-card { 
        background: white; padding: 25px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 8px solid #0b1f52; margin-bottom: 20px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 승인 로직] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        # 관리자 초기 이메일 설정
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
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 재무경영진단 AI 마스터 v7.0</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("아이디(이메일)", placeholder="admin@example.com", label_visibility="collapsed").strip().lower()
    
    col_login, col_apply = st.columns(2)
    if col_login.button("로그인", type="primary", use_container_width=True):
        user_row = user_db[user_db['email'] == login_email]
        if not user_row.empty and user_row.iloc[0]['approved']:
            st.session_state.authenticated_user = login_email
            st.rerun()
        elif not user_row.empty and not user_row.iloc[0]['approved']:
            st.warning("계정 승인 대기 중입니다.")
        else:
            st.error("등록되지 않은 계정입니다.")
            
    if col_apply.button("승인 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_user = pd.DataFrame([{
                "email": login_email, "approved": False, "is_admin": False, 
                "usage_count": 0, "last_month": date.today().month
            }])
            user_db = pd.concat([user_db, new_user], ignore_index=True)
            save_db(user_db)
            st.success("신청 완료! 관리자 승인 후 이용 가능합니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 정밀 데이터 추출 엔진 (특수 기호 및 천원단위 완벽 대응)] ---

def clean_value(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def robust_excel_parser(files):
    """여러 파일에서 데이터를 찾아 하나로 통합"""
    final_res = {
        '매출액': [0.0, 0.0, 0.0], '영업이익': [0.0, 0.0, 0.0], '당기순이익': [0.0, 0.0, 0.0],
        '자산총계': [0.0, 0.0, 0.0], '부채총계': [0.0, 0.0, 0.0], '원재료비': [0.0, 0.0, 0.0], '판관비': [0.0, 0.0, 0.0]
    }
    # 키워드 매핑 (데이터셋의 특수문자 대응)
    mapping = {
        '매출액': ['매출액', '매출액(*)', 'Ⅰ.매출액'],
        '영업이익': ['영업이익', '영업이익(손실)', 'Ⅵ.영업이익'],
        '당기순이익': ['당기순이익', '당기순이익(손실)', 'ⅩⅣ.당기순이익'],
        '자산총계': ['자산총계', '자산(*)', 'Ⅰ.자산'],
        '부채총계': ['부채총계', '부채(*)', 'Ⅱ.부채'],
        '원재료비': ['원재료비', '원재료비(*)', '1.원재료비'],
        '판관비': ['판매비와관리비', '판매비와관리비(*)', '판매비']
    }

    for file in files:
        try:
            if file.name.endswith('.csv'): df = pd.read_csv(file, header=None)
            else: df = pd.read_excel(file, header=None)
            
            for _, row in df.iterrows():
                row_list = [str(v).strip().replace(" ", "") for v in row.values]
                for key, keywords in mapping.items():
                    if any(kw in "".join(row_list) for kw in keywords):
                        nums = [clean_value(v) for v in row.values if clean_value(v) != 0]
                        if len(nums) >= 2:
                            # 엑셀 구조상 최근 2~3년치가 데이터임
                            extracted = nums[-3:] if len(nums) >= 3 else [0.0] + nums[-2:]
                            final_res[key] = extracted
        except: pass
    return final_res

def extract_pdf_meta(file):
    info = {'company': file.name.replace('.pdf',''), 'ceo': '미상', 'rating': '미상'}
    try:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([p.extract_text() for p in reader.pages[:3]])
        ceo_m = re.search(r'대표자(?:명)?\s*[:|：]?\s*([가-힣]{2,4})', text)
        if ceo_m: info['ceo'] = ceo_m.group(1).strip()
    except: pass
    return info

# --- [4. 메인 대시보드 및 관리자 기능] ---

st.markdown('<div class="premium-header"><h1>📊 종합 경영진단 리포트 & 가치평가 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### 👤 담당 컨설턴트\n**{st.session_state.authenticated_user}**")
    if st.button("로그아웃"):
        st.session_state.authenticated_user = None
        st.rerun()
    
    # 관리자 전용 메뉴
    curr_u = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if curr_u['is_admin']:
        st.divider(); st.subheader("👑 관리자 권한")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 대상", user_db['email'])
        if st.button("상태 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

# --- [5. 메인 분석 및 리포트 섹션] ---

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 업로드")
    up_files = st.file_uploader("KREtop PDF 및 재무 엑셀(3개년) 업로드", accept_multiple_files=True)
    
    report_data = None
    if up_files:
        p_meta = None
        for f in up_files:
            if f.name.endswith('.pdf'): p_meta = extract_pdf_meta(f)
        
        extracted_res = robust_excel_parser(up_files)
        
        if any(v != [0.0, 0.0, 0.0] for v in extracted_res.values()):
            st.success("✅ 엑셀 데이터 정밀 연동 완료")
            with st.expander("📝 추출 데이터 보정 (단위: 천원)", expanded=True):
                # 허자현 대표님의 성함 및 기업명 연동
                c_name = st.text_input("🏢 기업명", p_meta['company'] if p_meta else "신용")
                c_ceo = st.text_input("👤 대표자", p_meta['ceo'] if p_meta else "허자현")
                
                revs = [st.number_input(f"{i+1}차 매출액(천원)", value=extracted_res['매출액'][i]) for i in range(3)]
                incs = [st.number_input(f"{i+1}차 순이익(천원)", value=extracted_res['당기순이익'][i]) for i in range(3)]
                assets = [st.number_input(f"{i+1}차 자산(천원)", value=extracted_res['자산총계'][i]) for i in range(3)]
                debts = [st.number_input(f"{i+1}차 부채(천원)", value=extracted_res['부채총계'][i]) for i in range(3)]
                mats = [st.number_input(f"{i+1}차 원재료(천원)", value=extracted_res['원재료비'][i]) for i in range(3)]
                shares = st.number_input("발행주식 총수", value=100000)
                
                report_data = {"name": c_name, "ceo": c_ceo, "revs": revs, "incs": incs, "assets": assets, "debts": debts, "mats": mats, "shares": shares}

with col_r:
    st.subheader("📈 경영 진단 및 가치 시뮬레이션")
    if report_data:
        # 가치 평가 로직 (천원 -> 원 환산)
        growth = (revs[2]/revs[0])**(1/2) - 1 if revs[0]>0 else 0
        w_inc_won = ((incs[2]*3 + incs[1]*2 + incs[0]*1) / 6) * 1000
        stock_price = ((w_inc_won / 0.1)*0.6 + (assets[2]-debts[2])*1000*0.4) / shares if shares > 0 else 0
        
        f_vals = [stock_price * (1 + growth)**y for y in [0, 3, 5, 10]]

        # 시각화 차트
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '5년후', '10년후'], f_vals, marker='o', color='#d4af37', linewidth=4)
        for i, v in enumerate(f_vals): 
            ax.text(i, v*1.1, f"{int(v):,}원", ha='center', fontweight='bold', fontsize=11)
        ax.set_title(f"{c_name} 주식 가치 10개년 시뮬레이션", fontsize=15, pad=20)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        st.pyplot(fig)
        
        if st.button("🚀 미다스형 종합 리포트 발행 (PDF)", type="primary", use_container_width=True):
            pdf = FPDF()
            font_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            if os.path.exists(font_p): pdf.add_font("Nanum", "", font_p); pdf.set_font("Nanum", size=12)
            
            # --- Page 1: 표지 ---
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font("Nanum", size=32)
            pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=20); pdf.cell(190, 20, txt=f"기업명: {c_name}", ln=True, align='C')
            pdf.ln(100); pdf.set_font("Nanum", size=14)
            pdf.cell(190, 10, txt=f"발행일: {date.today().strftime('%Y-%m-%d')}", ln=True, align='C')
            pdf.cell(190, 10, txt="중소기업경영지원단 컨설팅 본부", ln=True, align='C')
            
            # --- Page 2: 재무 지표 분석 ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 3개년 주요 재무 지표 (단위: 천원)", ln=True)
            pdf.set_draw_color(11, 31, 82); pdf.set_line_width(1); pdf.line(10, 28, 200, 28); pdf.ln(15)
            
            d_ratio = (debts[2]/assets[2]*100) if assets[2] > 0 else 0
            m_ratio = (mats[2]/revs[2]*100) if revs[2] > 0 else 0
            
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"■ 매출액 추이: {revs[0]:,.0f} -> {revs[1]:,.0f} -> {revs[2]:,.0f}", ln=True)
            pdf.cell(190, 10, txt=f"■ 원재료비율: {m_ratio:.1f}% | 부채비율: {d_ratio:.1f}%", ln=True)
            
            # --- Page 3: 주식 가치 및 미래 예측 ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 비상장주식 평가 및 10개년 예측", ln=True)
            pdf.line(10, 28, 200, 28); pdf.ln(10); pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 15, txt=f"▶ 현시점 주당 평가액: {int(stock_price):,}원", ln=True)
            fig.savefig("final_rep_midas.png", dpi=300, bbox_inches='tight')
            pdf.image("final_rep_midas.png", x=15, w=180)

            # --- Page 4: 전문가 경영 솔루션 ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="3. 전문가 경영 리스크 진단", ln=True)
            pdf.line(10, 28, 200, 28); pdf.ln(15); pdf.set_font("Nanum", size=12)
            pdf.multi_cell(180, 10, txt="[진단 결과] 매출 및 순이익의 성장세에 따라 기업 가치가 가파르게 상승하고 있습니다. 가업 승계 시 세부담을 줄이기 위한 사전 지분 구조 정비가 시급하며, 원재료비 비중 상승에 따른 원가 방어 전략이 필요합니다.")

            pdf_bytes = bytes(pdf.output())
            st.download_button("💾 종합 진단 보고서 다운로드", data=pdf_bytes, file_name=f"진단보고서_{c_name}.pdf")
    else:
        st.info("좌측 섹션에서 재무제표 엑셀 파일을 업로드해주세요.")
