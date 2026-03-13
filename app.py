import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io
import os

# --- [폰트 설정] 배포 환경 대응 ---
def get_font():
    # 폰트 경로 후보군 (로컬 및 Streamlit Cloud 리눅스 환경)
    font_paths = [
        "./fonts/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('HanguI', path))
                return 'HanguI'
            except:
                continue
    return 'Helvetica'

# --- [데이터 분석 엔진] ---
@st.cache_data
def analyze_data(file_content):
    # io.BytesIO를 통해 메모리에서 직접 엑셀 읽기
    df = pd.read_excel(file_content)
    
    # 엑셀 시트명이나 컬럼명은 실제 파일에 맞춰 수정이 필요합니다.
    # 아래는 예시 계산 로직입니다.
    results = {
        'company_name': "주식회사 케이에이치오토",
        'growth': 15.7,
        'profitability': 8.4,
        'stability': 45.2,
        'valuation': 2450000000, # 24.5억
        'years': ['2023', '2024', '2025'],
        'revenues': [1000, 1150, 1320]
    }
    return results

# --- [차트 생성 엔진] ---
def create_report_chart(data):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(data['years'], data['revenues'], color='#2E5A88')
    ax.set_title('Revenue Trend')
    
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close(fig) # 중요: JavaScript 노드 충돌 방지
    return img_buf

# --- [메인 UI] ---
def main():
    st.set_page_config(page_title="CEO 리포트 생성기", layout="centered")
    font_name = get_font()

    st.title("📊 기업 재무경영진단 리포트")
    st.info("크레탑(CRETOP) 엑셀 자료를 업로드하면 분석이 시작됩니다.")

    # key를 부여하여 removeChild 오류 방지
    uploaded_file = st.file_uploader("재무 엑셀 파일 선택", type=['xlsx'], key="cre_file_up")

    if uploaded_file is not None:
        try:
            # 데이터 분석 실행
            analysis = analyze_data(uploaded_file)
            
            st.success(f"{analysis['company_name']} 데이터 분석 성공")
            
            # 요약 지표 표시 (Metric)
            col1, col2, col3 = st.columns(3)
            col1.metric("매출성장률", f"{analysis['growth']}%")
            col2.metric("순이익률", f"{analysis['profitability']}%")
            col3.metric("부채비율", f"{analysis['stability']}%")

            # 리포트 생성 버튼
            if st.button("📄 PDF 진단 리포트 생성", key="btn_generate"):
                with st.spinner("리포트 파일을 구성 중입니다..."):
                    # 1. 차트 준비
                    chart_img = create_report_chart(analysis)
                    
                    # 2. PDF 작성
                    pdf_buf = io.BytesIO()
                    c = canvas.Canvas(pdf_buf, pagesize=A4)
                    w, h = A4
                    
                    c.setFont(font_name, 20)
                    c.drawCentredString(w/2, h - 60, f"{analysis['company_name']} 경영진단 결과")
                    
                    c.setStrokeColor(colors.dodgerblue)
                    c.line(50, h - 80, w - 50, h - 80)
                    
                    c.setFont(font_name, 12)
                    c.drawString(70, h - 130, f"1. 성장성 지표: {analysis['growth']}%")
                    c.drawString(70, h - 150, f"2. 추정 기업가치: {analysis['valuation']:,}원")
                    
                    c.drawImage(ImageReader(chart_img), 70, h - 450, width=450, preserveAspectRatio=True)
                    
                    c.showPage()
                    c.save()
                    pdf_buf.seek(0)
                    
                    # 3. 다운로드 버튼 제공
                    st.download_button(
                        label="📥 리포트(PDF) 저장하기",
                        data=pdf_buf,
                        file_name=f"CEO_Report_{analysis['company_name']}.pdf",
                        mime="application/pdf",
                        key="btn_download"
                    )
        except Exception as e:
            st.error(f"파일 처리 오류: {e}")

if __name__ == "__main__":
    main()
