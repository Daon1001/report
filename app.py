import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import google.generativeai as genai
from fpdf import FPDF
import re
import json
from datetime import date
import io

# --- [0. 페이지 설정 및 Secrets 보안 로드] ---
st.set_page_config(page_title="AI 종합 경영진단 마스터", layout="wide")

base_dir = os.path.dirname(__file__)
font_path = os.path.join(base_dir, "malgun.ttf")

def set_korean_font(path):
    try:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            font_prop = fm.FontProperties(fname=path)
            plt.rc('font', family=font_prop.get_name())
            plt.rcParams['axes.unicode_minus'] = False
            return True
    except: pass
    return False

has_font = set_korean_font(font_path)

# Streamlit Secrets에서 API 키 호출
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = None

st.markdown("""
<style>
    .stApp { background-color: #f4f7f9 !important; }
    .premium-header { 
        background: linear-gradient(135deg, #0b1f52 0%, #1e3a8a 100%); 
        color: white; padding: 2.5rem; border-radius: 20px; text-align: center; margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-bottom: 8px solid #d4af37;
    }
</style>
""", unsafe_allow_html=True)

# --- [1. 사용자 보안 시스템] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

def save_db(df): df.to_csv(DB_FILE, index=False)
user_db = load_db()

if 'auth_user' not in st.session_state: st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.markdown('<div style="background:white; padding:50px; border-radius:20px; max-width:500px; margin:10vh auto; text-align:center; border-top:10px solid #0b1f52; box-shadow: 0 15px 30px rgba(0,0,0,0.15);">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#0b1f52;">🏛️ 중소기업경영지원단</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666;'>제미나이 AI 통합 시스템 v49.0</p>", unsafe_allow_html=True)
    email = st.text_input("아이디(이메일)").strip().lower()
    if st.button("시스템 로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.auth_user = email; st.rerun()
        else: st.error("승인이 필요한 계정입니다.")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- [2. 제미나이 AI 시각적 분석 엔진] ---

def analyze_with_gemini(files):
    if not GEMINI_API_KEY:
        st.error("Secrets에 API 키가 설정되지 않았습니다.")
        return None

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    이 파일들을 분석하여 기업 경영 진단 데이터를 추출해줘. 
    반드시 아래 JSON 형식으로만 답변해.
    {
        "comp_name": "기업명",
        "ceo_name": "대표자명",
        "emp_count": 0,
        "revenue": [2022매출, 2023매출, 2024매출],
        "profit": [2022순이익, 2023순이익, 2024순이익],
        "asset": [2022자산, 2023자산, 2024자산],
        "debt": [2022부채, 2023부채, 2024부채],
        "venture": true/false,
        "rnd_dept": true/false
    }
    재무 수치는 '단위:백만원'이면 숫자로 변환하고, 데이터가 없으면 0으로 채워줘.
    """
    
    content = [prompt]
    for f in files:
        f_bytes = f.read()
        content.append({"mime_type": f.type, "data": f_bytes})
        f.seek(0)
    
    try:
        response = model.generate_content(content)
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except Exception as e:
        st.error(f"AI 분석 오류: {e}")
        return None

# --- [3. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 AI 종합 경영 진단 시스템</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당자: **{st.session_state.auth_user}**")
    if st.button("로그아웃"): st.session_state.auth_user = None; st.rerun()
    
    user_row = user_db[user_db['email'] == st.session_state.auth_user].iloc[0]
    if user_row['is_admin']:
        st.divider(); st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 변경 계정", user_db['email'])
        if st.button("상태 전환"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 엑셀을 업로드하세요.", accept_multiple_files=True)
    
    if up_files:
        if 'ai_data' not in st.session_state:
            with st.spinner("🚀 AI가 시각적 데이터를 판독 중입니다..."):
                st.session_state.ai_data = analyze_with_gemini(up_files)
        
        if st.session_state.ai_data:
            d = st.session_state.ai_data
            st.success("✅ AI 데이터 동기화 완료")
            with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
                f_comp = st.text_input("🏢 기업 명칭", d.get('comp_name', '미상'))
                f_ceo = st.text_input("👤 대표자 성함", d.get('ceo_name', '미상'))
                f_emp = st.number_input("👥 종업원수(명)", value=d.get('emp_count', 0))
                st.divider()
                r_rev = st.number_input("2024 매출액", value=float(d.get('revenue', [0,0,0])[2]))
                r_inc = st.number_input("2024 순이익", value=float(d.get('profit', [0,0,0])[2]))
                r_asset = st.number_input("2024 자산총계", value=float(d.get('asset', [0,0,0])[2]))
                r_debt = st.number_input("2024 부채총계", value=float(d.get('debt', [0,0,0])[2]))

with col_r:
    st.subheader("📈 실시간 진단 결과")
    if up_files and 'ai_data' in st.session_state:
        labor = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석: 근로자 **{f_emp}명**으로 **'{labor} 사업장'** 가이드가 적용됩니다.")
        
        stock_val = ((r_inc * 1000 / 0.1)*0.6 + (r_asset - r_debt)*1000*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_val, stock_val*1.4, stock_val*2.8], marker='o', color='#0b1f52', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시나리오")
        st.pyplot(fig)

        if st.button("🚀 종합 한글 보고서 발행", type="primary", use_container_width=True):
            pdf = FPDF()
            if has_font:
                pdf.add_font("Malgun", "", font_path)
                pdf.set_font("Malgun", size=12)
            else: pdf.set_font("helvetica", size=12)
            
            pdf.add_page(); pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(90); pdf.set_font_size(32)
            pdf.cell(190, 25, txt="종합 재무경영 진단 보고서", ln=True, align='C')
            pdf.set_font_size(18); pdf.cell(190, 20, txt=f"대상기업: {f_comp} / 대표: {f_ceo}", ln=True, align='C')
            
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font_size(20)
            pdf.cell(190, 15, txt="1. 정밀 재무제표 및 AI 분석", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_fill_color(240, 240, 240); pdf.set_font_size(11)
            pdf.cell(50, 10, "항목", 1, 0, 'C', True); pdf.cell(70, 10, "2023년", 1, 0, 'C', True); pdf.cell(70, 10, "2024년 (최근)", 1, 1, 'C', True)
            
            f_rows = [
                ("자산 총계", st.session_state.ai_data.get('asset', [0,0,0])[1], r_asset), 
                ("부채 총계", st.session_state.ai_data.get('debt', [0,0,0])[1], r_debt), 
                ("매출액", st.session_state.ai_data.get('revenue', [0,0,0])[1], r_rev), 
                ("당기순이익", st.session_state.ai_data.get('profit', [0,0,0])[1], r_inc)
            ]
            for n, v1, v2 in f_rows:
                pdf.cell(50, 10, n, 1); pdf.cell(70, 10, f"{v1:,.0f}", 1, 0, 'R'); pdf.cell(70, 10, f"{v2:,.0f}", 1, 1, 'R')
            
            pdf.ln(10); pdf.set_font_size(13); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 10, txt="▶ 전문가 종합 재무 분석 결과", ln=True)
            pdf.set_font_size(11); pdf.set_text_color(0,0,0)
            d_rate = (r_debt / r_asset * 100) if r_asset > 0 else 0
            pdf.multi_cell(190, 8, txt=f"분석 결과, {f_comp}의 2024년 부채비율은 {d_rate:.1f}%로 우수합니다. 당기순이익 {r_inc:,.0f}백만원을 기록하며 가파른 기업가치 상승 곡선을 그리고 있습니다.")

            pdf.add_page(); pdf.set_font_size(20)
            pdf.cell(190, 15, txt="2. 주식가치 평가 및 리스크 진단", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            fig.savefig("v49_final.png", dpi=300); pdf.image("v49_final.png", x=15, w=180)
            pdf.ln(10); pdf.set_font_size(12)
            pdf.cell(190, 10, txt=f"■ 인증: 벤처({('보유' if st.session_state.ai_data.get('venture') else '미보유')}), 전담부서({('보유' if st.session_state.ai_data.get('rnd_dept') else '미보유')})", ln=True)
            pdf.cell(190, 10, txt=f"■ 노무: 상시 근로자 {f_emp}명에 따른 '{labor}' 기준 적용", ln=True)

            pdf_out = bytes(pdf.output())
            st.download_button("💾 한글 종합 보고서 다운로드", data=pdf_out, file_name=f"진단보고서_{f_comp}.pdf")
