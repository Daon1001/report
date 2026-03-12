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
    }
    .login-box { 
        background-color: white !important; padding: 40px !important; border-radius: 20px !important; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15) !important; text-align: center !important; 
        max-width: 500px !important; margin: 10vh auto !important; border-top: 10px solid #0b1f52 !important;
    }
    .data-card { 
        background: white; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 5px solid #0b1f52; margin-bottom: 15px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 사용자 데이터베이스 및 승인 로직] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{
            "email": "incheon00@gmail.com", 
            "approved": True, 
            "is_admin": True, 
            "usage_count": 0, 
            "last_month": date.today().month
        }])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

# 세션 관리
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

# --- [2. 로그인 및 승인 신청 화면] ---
if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h2>', unsafe_allow_html=True)
    st.markdown("<p>재무경영진단 AI 마스터 v3.5</p>", unsafe_allow_html=True)
    
    login_email = st.text_input("아이디(이메일)", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
    
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
            
    if col_r.button("승인 신청", use_container_width=True):
        if login_email and user_db[user_db['email'] == login_email].empty:
            new_user = pd.DataFrame([{
                "email": login_email, "approved": False, "is_admin": False, 
                "usage_count": 0, "last_month": date.today().month
            }])
            user_db = pd.concat([user_db, new_user], ignore_index=True)
            save_db(user_db)
            st.success("✅ 신청 완료! 관리자 승인 후 이용 가능합니다.")
        elif login_email:
            st.info("이미 신청되었거나 등록된 이메일입니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 데이터 추출 엔진 (PDF & Excel)] ---

def extract_pdf_meta(file):
    info = {'company': file.name.replace('.pdf',''), 'ceo': '미상', 'rating': '미상'}
    try:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([p.extract_text() for p in reader.pages])
        ceo_m = re.search(r'대표자(?:명)?\s*[:|：]?\s*([가-힣]{2,4})', text)
        if ceo_m: info['ceo'] = ceo_m.group(1).strip()
        rate_m = re.search(r'기업신용등급\s*[:|：]?\s*([a-zA-Z0-9\+\-]+)', text)
        if rate_m: info['rating'] = rate_m.group(1).strip()
    except: pass
    return info

def parse_excel_financials(file):
    results = {
        '매출액': [0, 0, 0], '영업이익': [0, 0, 0], '당기순이익': [0, 0, 0],
        '자산총계': [0, 0, 0], '부채총계': [0, 0, 0],
        '원재료비': [0, 0, 0], '판매비와관리비': [0, 0, 0]
    }
    try:
        df_dict = pd.read_excel(file, sheet_name=None)
        for _, df in df_dict.items():
            df = df.fillna(0)
            for _, row in df.iterrows():
                row_str = " ".join([str(x) for x in row.values])
                for key in results.keys():
                    if key in row_str:
                        nums = [x for x in row.values if isinstance(x, (int, float)) and x != 0]
                        if len(nums) >= 3: results[key] = nums[:3]
    except: pass
    return results

# --- [4. 메인 대시보드 및 관리자 메뉴] ---

st.markdown('<div class="premium-header"><h1>📊 재무분석 및 비상장주식 가치평가 시스템</h1></div>', unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.write(f"👤 **{st.session_state.authenticated_user}** 팀장님")
    if st.button("로그아웃"):
        st.session_state.authenticated_user = None
        st.rerun()
    
    # [관리자 메뉴 복구]
    user_info = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if user_info['is_admin']:
        st.divider()
        st.subheader("👑 관리자 메뉴 (Admin)")
        st.write("사용자 승인 관리")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("상태 변경 대상", user_db['email'])
        if st.button("승인 상태 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db)
            st.rerun()

# --- [5. 메인 분석 영역] ---

col_in, col_out = st.columns([1, 1.4])

with col_in:
    st.subheader("📂 파일 업로드")
    files = st.file_uploader("크레탑 PDF 및 재무 엑셀 업로드", accept_multiple_files=True)
    
    final_meta, final_excel = None, None
    if files:
        for f in files:
            if f.name.endswith('.pdf'): final_meta = extract_pdf_meta(f)
            if f.name.endswith(('.xlsx', '.xls')): final_excel = parse_excel_financials(f)
            
        if final_meta or final_excel:
            st.markdown("### 📝 데이터 확인 및 보정")
            # PDF 정보 보정
            c_name = st.text_input("🏢 기업명", final_meta['company'] if final_meta else "미상")
            c_ceo = st.text_input("👤 대표자", final_meta['ceo'] if final_meta else "미상")
            c_rate = st.text_input("⭐ 신용등급", final_meta['rating'] if final_meta else "미상")
            
            # 엑셀 데이터 보정
            if final_excel:
                with st.expander("📊 재무 데이터 보정 (3개년)", expanded=False):
                    revs = [st.number_input(f"{i+1}년 매출", value=float(final_excel['매출액'][i])) for i in range(3)]
                    profs = [st.number_input(f"{i+1}년 영업이익", value=float(final_excel['영업이익'][i])) for i in range(3)]
                    incs = [st.number_input(f"{i+1}년 순이익", value=float(final_excel['당기순이익'][i])) for i in range(3)]
                    mats = [st.number_input(f"{i+1}년 원재료비", value=float(final_excel['원재료비'][i])) for i in range(3)]
                    exps = [st.number_input(f"{i+1}년 경비(판관비)", value=float(final_excel['판매비와관리비'][i])) for i in range(3)]
                    curr_asset = st.number_input("최신 순자산(백만)", value=float(final_excel['자산총계'][2]-final_excel['부채총계'][2]))
                    shares = st.number_input("발행주식 총수", value=100000)
            else:
                st.info("엑셀 파일을 업로드하면 자동으로 재무 수치가 채워집니다.")

with col_out:
    st.subheader("📈 경영 지표 및 가치 시뮬레이션")
    if final_excel:
        # 원가 분석
        mat_ratio = [m/r*100 if r!=0 else 0 for m, r in zip(mats, revs)]
        exp_ratio = [e/r*100 if r!=0 else 0 for e, r in zip(exps, revs)]
        
        # 주식 가치 평가 (3:2 가중평균)
        weighted_inc = (incs[2]*3 + incs[1]*2 + incs[0]*1) / 6
        inc_val = (weighted_inc * 1000000 / 0.1) / shares
        asset_val = (curr_asset * 1000000) / shares
        stock_price = (inc_val * 0.6) + (asset_val * 0.4)
        
        # 미래 시뮬레이션 (CAGR 기반)
        growth = (revs[2]/revs[0])**(1/2) - 1 if revs[0]>0 else 0
        f_years = [0, 3, 5, 10]
        f_prices = [stock_price * (1 + growth)**y for y in f_years]
        
        # 시각화
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '5년후', '10년후'], f_prices, marker='o', color='#0b1f52', linewidth=3)
        for i, v in enumerate(f_prices):
            ax.text(i, v*1.05, f"{int(v/10000):,}만", ha='center', fontweight='bold')
        ax.set_title("향후 10년 비상장주식 가치 추이 예측", fontsize=14)
        st.pyplot(fig)
        
        if st.button("🚀 정밀 리포트 PDF 발행", type="primary", use_container_width=True):
            pdf = FPDF()
            font_p = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            
            # Page 1: 표지
            pdf.add_page()
            if os.path.exists(font_p): pdf.add_font("Nanum", "", font_p); pdf.set_font("Nanum", size=12)
            pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(80)
            pdf.set_font("Nanum", size=30); pdf.cell(190, 25, txt="재무분석 및 주식평가 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=18); pdf.cell(190, 20, txt=f"고객사: {c_name}", ln=True, align='C')
            
            # Page 2: 원가 및 주식 가치
            pdf.add_page(); pdf.set_text_color(0,0,0)
            pdf.set_font("Nanum", size=18); pdf.cell(190, 15, txt="1. 재무 원가 및 주식 가치 평가", ln=True)
            pdf.line(10, 25, 200, 25); pdf.ln(10)
            pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"■ 원재료비율: {mat_ratio[2]:.1f}% | 경비율: {exp_ratio[2]:.1f}%", ln=True)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 15, txt=f"▶ 현시점 주당 가치: {int(stock_price):,}원", ln=True)
            
            # Page 3: 미래 예측
            pdf.add_page(); pdf.set_text_color(0,0,0)
            pdf.set_font("Nanum", size=18); pdf.cell(190, 15, txt="2. 향후 10개년 가치 시뮬레이션", ln=True)
            pdf.line(10, 25, 200, 25); pdf.ln(10)
            fig.savefig("f_val.png", dpi=300); pdf.image("f_val.png", x=15, w=170)
            pdf.ln(10); pdf.set_font("Nanum", size=11)
            pdf.multi_cell(180, 8, txt=f"연성장률 {growth*100:.1f}% 가정 시, 10년 뒤 주식 가치는 {int(f_prices[3]):,}원에 달할 것으로 예측됩니다. 상속 및 증여세 부담이 급증하기 전 지분 구조 정비가 필요합니다.")

            pdf_b = bytes(pdf.output())
            st.download_button("💾 정밀 리포트 다운로드", data=pdf_b, file_name=f"진단보고서_{c_name}.pdf", mime="application/pdf")
    else:
        st.info("파일을 업로드하면 3개년 분석 및 10년 예측이 시작됩니다.")
