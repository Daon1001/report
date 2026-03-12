import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import PyPDF2
from fpdf import FPDF
import re
from datetime import date, datetime
import numpy as np

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
    .data-card { 
        background: white; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 4px solid #0b1f52;
        margin-bottom: 15px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [1. 데이터베이스 및 로그인 관리] ---
DB_FILE = "users.csv"
def load_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame([{"email": "incheon00@gmail.com", "approved": True, "is_admin": True}])
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

if 'user' not in st.session_state: st.session_state.user = None
user_db = load_db()

if st.session_state.user is None:
    st.markdown('<div style="text-align:center; margin-top:15vh;"><h1>🏛️ 중소기업경영지원단</h1><p>AI 재무진단 시스템 v2.0</p></div>', unsafe_allow_html=True)
    login_email = st.text_input("아이디(이메일)").strip().lower()
    if st.button("전문가 로그인", type="primary", use_container_width=True):
        row = user_db[user_db['email'] == login_email]
        if not row.empty and row.iloc[0]['approved']:
            st.session_state.user = login_email; st.rerun()
        else: st.error("승인된 계정이 아닙니다.")
    st.stop()

# --- [2. 엑셀 스마트 파싱 엔진] ---
def parse_financial_excel(file):
    """엑셀 파일에서 키워드 기반으로 3개년 재무 데이터를 자동 추출"""
    data = {
        '매출액': [0, 0, 0], '영업이익': [0, 0, 0], '당기순이익': [0, 0, 0],
        '자산총계': [0, 0, 0], '부채총계': [0, 0, 0]
    }
    try:
        # 모든 시트를 읽어서 키워드 검색
        df_dict = pd.read_excel(file, sheet_name=None)
        for sheet_name, df in df_dict.items():
            df = df.fillna(0)
            for idx, row in df.iterrows():
                row_str = " ".join([str(x) for x in row.values])
                for key in data.keys():
                    if key in row_str:
                        # 키워드 발견 시 해당 행에서 숫자만 골라내기
                        nums = [x for x in row.values if isinstance(x, (int, float)) and x != 0]
                        if len(nums) >= 3:
                            data[key] = nums[:3] # 앞의 3개 숫자를 3개년 데이터로 간주
    except Exception as e:
        st.error(f"엑셀 분석 중 오류: {e}")
    return data

# --- [3. 메인 화면 구성] ---
st.markdown('<div class="premium-header"><h1>📊 [EXCEL 연동] 재무분석 및 주식가치 시뮬레이션</h1></div>', unsafe_allow_html=True)

col_file, col_view = st.columns([1, 1.4])

with col_file:
    st.subheader("📂 파일 업로드")
    uploaded_files = st.file_uploader("재무제표 엑셀(.xlsx) 및 크레탑 PDF 업로드", accept_multiple_files=True)
    
    excel_data = None
    if uploaded_files:
        for f in uploaded_files:
            if f.name.endswith(('.xlsx', '.xls')):
                with st.spinner(f"{f.name} 분석 중..."):
                    excel_data = parse_financial_excel(f)
        
        if excel_data:
            st.success("✅ 엑셀 데이터 자동 추출 완료!")
            with st.expander("📝 추출된 데이터 확인 및 수정"):
                revs = [st.number_input(f"{i+1}차년도 매출액", value=float(excel_data['매출액'][i])) for i in range(3)]
                profits = [st.number_input(f"{i+1}차년도 영업이익", value=float(excel_data['영업이익'][i])) for i in range(3)]
                incomes = [st.number_input(f"{i+1}차년도 당기순이익", value=float(excel_data['당기순이익'][i])) for i in range(3)]
                assets = [st.number_input(f"{i+1}차년도 자산총계", value=float(excel_data['자산총계'][i])) for i in range(3)]
                debts = [st.number_input(f"{i+1}차년도 부채총계", value=float(excel_data['부채총계'][i])) for i in range(3)]
                total_shares = st.number_input("발행주식 총수", value=100000)
        else:
            st.warning("엑셀 파일을 업로드하면 데이터를 자동으로 읽어옵니다.")

with col_view:
    st.subheader("📈 경영 지표 및 미래 가치 예측")
    if excel_data:
        # 1. 재무 비율 계산
        margin = [p/r*100 if r!=0 else 0 for p, r in zip(profits, revs)]
        debt_ratio = [d/a*100 if a!=0 else 0 for d, a in zip(debts, assets)]
        growth = (revs[2]/revs[0])**(1/2) - 1 if revs[0]>0 else 0
        
        # 2. 주식 가치 평가 (상증세법 간이)
        avg_income = (incomes[2]*3 + incomes[1]*2 + incomes[0]*1) / 6
        net_asset_val = (assets[2] - debts[2])
        stock_val = ((avg_income / 0.1)*0.6 + net_asset_val*0.4) * 1000000 / total_shares # 단위 보정
        
        # 미래 가치 시뮬레이션 데이터
        future_years = [0, 3, 5, 10]
        future_vals = [stock_val * (1 + growth)**y for y in future_years]

        # 시각화 차트
        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax1.bar(['현재', '3년후', '5년후', '10년후'], [v/10000 for v in future_vals], color='#0b1f52', alpha=0.8)
        for i, v in enumerate(future_vals):
            ax1.text(i, (v/10000)*1.05, f"{int(v/10000):,}만", ha='center', fontweight='bold')
        ax1.set_title("향후 10년 비상장주식 가치 시뮬레이션 (단위: 만원)")
        st.pyplot(fig)
        
        # PDF 발행
        if st.button("🚀 정밀 진단 리포트(Multi-Page) 발행", type="primary", use_container_width=True):
            pdf = FPDF()
            f_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            
            # --- Page 1: 표지 ---
            pdf.add_page()
            if os.path.exists(font_path := f_path):
                pdf.add_font("Nanum", "", font_path); pdf.set_font("Nanum", size=12)
            pdf.set_fill_color(11, 31, 82); pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(255, 255, 255); pdf.ln(80)
            pdf.set_font("Nanum", size=30); pdf.cell(190, 25, txt="재무분석 및 주식평가 보고서", ln=True, align='C')
            pdf.set_font("Nanum", size=15); pdf.cell(190, 20, txt=f"분석일: {date.today()}", ln=True, align='C')

            # --- Page 2: 재무 분석 ---
            pdf.add_page(); pdf.set_text_color(0,0,0)
            pdf.set_font("Nanum", size=18); pdf.cell(190, 15, txt="1. 3개년 재무분석 결과", ln=True)
            pdf.line(10, 25, 200, 25); pdf.ln(10); pdf.set_font("Nanum", size=12)
            pdf.cell(190, 10, txt=f"■ 평균 영업이익률 : {np.mean(margin):.1f}%", ln=True)
            pdf.cell(190, 10, txt=f"■ 최신 부채비율 : {debt_ratio[2]:.1f}%", ln=True)
            pdf.cell(190, 10, txt=f"■ 연평균 매출성장률 : {growth*100:.1f}%", ln=True)

            # --- Page 3: 주식평가 및 미래예측 ---
            pdf.add_page()
            pdf.set_font("Nanum", size=18); pdf.cell(190, 15, txt="2. 주식가치 평가 및 10개년 시뮬레이션", ln=True)
            pdf.line(10, 25, 200, 25); pdf.ln(10)
            pdf.set_font("Nanum", size=14); pdf.set_text_color(11, 31, 82)
            pdf.cell(190, 15, txt=f"▶ 현시점 주당 평가액: {int(stock_val):,}원", ln=True)
            
            fig.savefig("f_chart.png", dpi=300); pdf.image("f_chart.png", x=15, w=180)
            pdf.set_text_color(0,0,0); pdf.set_font("Nanum", size=11)
            pdf.ln(10); pdf.multi_cell(180, 8, txt="귀사의 성장세를 고려할 때 10년 뒤 주식 가치는 현재의 약 2.5배 이상 상승할 것으로 기대됩니다. 이는 상속 및 증여세 부담의 급격한 증가를 의미하므로, 전략적인 지분 구조 정비가 필요합니다.")

            pdf_bytes = bytes(pdf.output())
            st.download_button(label="💾 전문가용 정밀 리포트 다운로드", data=pdf_bytes, file_name="재무정밀진단_리포트.pdf", mime="application/pdf")
    else:
        st.info("왼쪽 섹션에서 재무제표 엑셀 파일을 업로드해주세요.")
