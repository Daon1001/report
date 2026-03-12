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

# --- [1. 사용자 데이터베이스 및 승인 시스템] ---
# 대표자 허자현님의 관리 권한을 위한 DB 설정
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
    st.markdown("<p style='color:#666; margin-bottom:30px;'>종합 경영진단 AI 마스터 v20.0 [Universal-Scraper]</p>", unsafe_allow_html=True)
    
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

# --- [3. 유니버설 스캐너 엔진 (개요.pdf & 엑셀 정밀 타겟팅)] ---

def clean_num(val):
    """모든 형태의 숫자 텍스트를 실수로 변환"""
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = re.sub(r'[^\d.-]', '', str(val))
    return float(s) if s else 0.0

def universal_analyzer(files):
    """텍스트 파편화를 방지하는 최상위 스캐닝 로직"""
    res = {
        'comp': "미상", 'ceo': "미상", 'emp': 0,
        'fin': {'매출': [0.0,0.0,0.0], '이익': [0.0,0.0,0.0], '자산': [0.0,0.0,0.0], '부채': [0.0,0.0,0.0]},
        'certs': {'벤처': False, '연구개발전담부서': False, '이노비즈': False, '메인비즈': False, '기업부설연구소': False}
    }
    
    for file in files:
        # 1. PDF 초정밀 스캔 (개요.pdf 특수 양식 대응)
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            txt_blocks = []
            for page in reader.pages:
                txt_blocks.append(page.extract_text())
            
            # 모든 텍스트를 하나의 문자열로 결합 (줄바꿈 및 공백 정규화)
            full_txt = " ".join(txt_blocks)
            tight_txt = full_txt.replace(" ", "").replace("\n", "").replace("\t", "")
            
            # (1) 기업명: '기업명' 키워드 주변 텍스트 재조합
            # (주)메이홈 등 특수기호 대응을 위해 정규표현식 강화
            comp_m = re.search(r'기업명\s*[:：\- ]+\s*([가-힣\(\)A-Za-z0-9&]+)', full_txt)
            if comp_m: res['comp'] = comp_m.group(1).strip()
            
            # (2) 대표자: '대표자' 뒤 2~4자 한글 매칭
            ceo_m = re.search(r'대표자(?:명)?\s*[:：\- ]+\s*([가-힣]{2,4})', full_txt)
            if ceo_m: res['ceo'] = ceo_m.group(1).strip()
            
            # (3) 종업원수: '종업원수'와 '명' 사이의 숫자 추출
            emp_m = re.search(r'종업원수\s*[:：\- ]+\s*(\d+)', full_txt)
            if emp_m: res['emp'] = int(emp_m.group(1))
            elif "종업원수" in tight_txt:
                res['emp'] = int(re.search(r'종업원수(\d+)', tight_txt).group(1))
            
            # (4) 인증 정보: '인증' 키워드 보유 확인
            cert_targets = {'벤처': '벤처', '연구개발전담부서': '연구개발전담부서', '이노비즈': '이노비즈', '메인비즈': '메인비즈', '기업부설연구소': '부설연구소'}
            for key, kw in cert_targets.items():
                if f"{kw}인증" in tight_txt or f"{kw}보유" in tight_txt:
                    # '미인증' 여부 더블체크
                    if f"{kw}미인증" not in tight_txt:
                        res['certs'][key] = True

        # 2. 엑셀/CSV 데이터 전수 조사 (키워드 기반 행 분석)
        if file.name.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
                for _, row in df.iterrows():
                    row_txt = "".join([str(v) for v in row.values]).replace(" ", "")
                    # 재무 키워드 매칭
                    targets = {'매출액': '매출', '순이익': '이익', '자산총계': '자산', '부채총계': '부채'}
                    for kw, key in targets.items():
                        if kw in row_txt:
                            # 행 내 모든 숫자 수집 (2022~2024 데이터 확보)
                            row_nums = [clean_num(v) for v in row.values if isinstance(v, (int, float, str)) and clean_num(v) != 0]
                            if len(row_nums) >= 2:
                                # 가장 우측 3개 연도 추출 (22년, 23년, 24년)
                                res['fin'][key] = row_nums[-3:] if len(row_nums) >= 3 else [0.0] + row_nums[-2:]
            except: pass
            
    return res

# --- [4. 메인 화면 구성 및 관리 기능] ---

st.markdown('<div class="premium-header"><h1>📊 [PRIME] 종합 경영진단 리포트 마스터</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 담당: **{st.session_state.authenticated_user}** 팀장님")
    if st.button("로그아웃"): 
        st.session_state.authenticated_user = None
        st.rerun()
    
    # 관리자 전용 승인 메뉴 (허자현 대표님 전용)
    u_info = user_db[user_db['email'] == st.session_state.authenticated_user].iloc[0]
    if u_info['is_admin']:
        st.divider(); st.subheader("👑 관리자 메뉴")
        st.dataframe(user_db[['email', 'approved']], use_container_width=True)
        target = st.selectbox("승인 상태 변경 대상", user_db['email'])
        if st.button("상태 전환 (승인/해제)"):
            user_db.loc[user_db['email'] == target, 'approved'] = not user_db.loc[user_db['email'] == target, 'approved'].iloc[0]
            save_db(user_db); st.rerun()

col_l, col_r = st.columns([1, 1.4])

with col_l:
    st.subheader("📂 진단 파일 통합 업로드")
    up_files = st.file_uploader("개요.pdf 및 재무 자료를 함께 업로드하세요.", accept_multiple_files=True)
    
    if up_files:
        data = universal_analyzer(up_files)
        st.success("✅ 파일 데이터 추출 성공 (유니버설 엔진 가동)")
        
        with st.expander("📝 데이터 최종 확인 및 보정", expanded=True):
            # 파일에서 읽어온 (주)메이홈, 박승미, 10명 데이터를 자동으로 채움
            f_comp = st.text_input("🏢 기업 명칭", data['comp'])
            f_ceo = st.text_input("👤 대표자 성함", data['ceo'])
            f_emp = st.number_input("👥 상시 근로자수(명)", value=data['emp'])
            
            st.divider(); st.write("🛡️ **보유 인증 진단 현황**")
            cert_vals = {}
            for cert, have in data['certs'].items():
                cert_vals[cert] = st.checkbox(cert, value=have)
            
            st.divider(); st.write("💰 **최신 재무 (단위: 백만원/천원 자동 대응)**")
            # PDF/엑셀에서 읽어온 2024년 데이터 자동 연동
            r_rev = st.number_input("2024년 매출액", value=data['fin']['매출'][2] if len(data['fin']['매출'])>2 else 0.0)
            r_inc = st.number_input("2024년 순이익", value=data['fin']['이익'][2] if len(data['fin']['이익'])>2 else 0.0)
            r_asset = st.number_input("2024년 자산총계", value=data['fin']['자산'][2] if len(data['fin']['자산'])>2 else 0.0)
            r_debt = st.number_input("2024년 부채총계", value=data['fin']['부채'][2] if len(data['fin']['부채'])>2 else 0.0)

with col_r:
    st.subheader("📈 실시간 리포트 구성 시뮬레이션")
    if up_files:
        # 노무 가이드 타입 결정 (10명 기준 5인 이상 자동 적용)
        labor_type = "5인 이상" if f_emp >= 5 else "5인 미만"
        st.info(f"분석 결과: 현재 근로자 **{f_emp}명**으로 **'{labor_type} 사업장'** 노무 전용 가이드가 생성됩니다.")
        
        # 가치 평가 로직 (단위가 '백만원'일 경우 원 단위 환산)
        # 매출액이 50,000 이하면 보통 '백만원' 단위로 판단
        unit_multiplier = 1000000 if r_rev < 50000 else 1000
        stock_price = ((r_inc * unit_multiplier / 0.1)*0.6 + (r_asset - r_debt)*unit_multiplier*0.4) / 100000
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(['현재', '3년후', '10년후'], [stock_price, stock_price*1.4, stock_price*2.8], marker='o', color='#d4af37', linewidth=4)
        ax.set_title(f"{f_comp} 주식 가치 상승 시뮬레이션", fontsize=15)
        st.pyplot(fig)

        if st.button("🚀 종합 경영진단 보고서 발행 (PDF)", type="primary", use_container_width=True):
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
            
            # --- [PAGE 2: 재무 및 가치 분석] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="1. 정밀 재무 진단 및 기업가치 평가", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(15)
            pdf.set_font("Nanum", size=12); pdf.cell(190, 10, txt=f"■ 분석 기업: {f_comp} (상시 근로자 {f_emp}명)", ln=True)
            pdf.set_font("Nanum", size=15); pdf.set_text_color(11, 31, 82); pdf.cell(190, 15, txt=f"▶ 현시점 주당 추정가액: {int(stock_price):,} 원", ln=True)
            fig.savefig("midas_v_final.png", dpi=300); pdf.image("midas_v_final.png", x=15, w=180)
            
            # --- [PAGE 3: 기업 인증 진단 (가변 추가)] ---
            pdf.add_page(); pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="2. 핵심 기업 인증 현황 및 로드맵", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            
            cert_guide = {
                "벤처": "법인세 50% 감면 및 정부 정책자금 한도 우대를 위한 필수 인증 항목",
                "연구개발전담부서": "연구원 인건비의 25%를 세액공제 받을 수 있는 최강의 절세 수단",
                "이노비즈": "기술력을 인정받아 금융권 금리 우대 및 입찰 가점 확보 가능"
            }
            for c, desc in cert_guide.items():
                status = "보유" if cert_vals.get(c, False) else "미보유 (도입필요)"
                pdf.set_font("Nanum", size=13); pdf.set_text_color(11, 31, 82)
                pdf.cell(190, 10, txt=f"● {c} 인증 : {status}", ln=True)
                pdf.set_font("Nanum", size=11); pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(185, 8, txt=f"필요성 안내: {desc}\n")
                if "미보유" in status:
                    pdf.set_text_color(200, 0, 0); pdf.cell(190, 8, txt="→ 기업 경쟁력 강화를 위해 조속한 취득 전략 수립을 제안합니다.", ln=True)
                pdf.ln(5); pdf.set_text_color(0,0,0)

            # --- [PAGE 4: 노무 기준법 가이드 (인원수 기반 가변 추가)] ---
            pdf.add_page(); pdf.set_font("Nanum", size=20)
            pdf.cell(190, 15, txt="3. 상시 인원별 맞춤형 노무 가이드", ln=True); pdf.line(10, 28, 200, 28); pdf.ln(10)
            pdf.set_font("Nanum", size=12); pdf.cell(190, 10, txt=f"진단 결과: 현재 근로자 {f_emp}명으로 '{labor_type} 사업장' 기준이 적용됩니다.", ln=True)
            
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
