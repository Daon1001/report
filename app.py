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

# 1. 폰트 설정 (한글 깨짐 방지)
def setup_fonts():
    # 로컬 fonts 폴더에 폰트가 있거나 시스템 폰트를 사용하도록 설정
    # 배포 시 fonts/NanumGothic.ttf 파일을 포함하는 것이 가장 좋습니다.
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf", 
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "./fonts/NanumGothic.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('HanguFont', path))
                return 'HanguFont'
            except:
                continue
    return 'Helvetica'

# 2. 분석 엔진 클래스
class CorporateAnalyzer:
    def __init__(self, dataframe):
        self.df = dataframe
        self.results = {}

    def run_analysis(self):
        # 크레탑 엑셀 구조에서 데이터를 추출하는 로직 (예시 수치)
        # 실제 운영 시 df.loc 등을 사용하여 실제 데이터를 매핑하세요.
        try:
            self.results['company_name'] = "분석 대상 기업"
            self.results['growth_rate'] = 18.5  # 매출성장률
            self.results['profit_margin'] = 9.2 # 영업이익률
            self.results['debt_ratio'] = 35.0   # 부채비율
            self.results['years'] = ['2023', '2024', '2025']
            self.results['rev_trend'] = [100, 120, 150]
        except Exception as e:
            st.error(f"데이터 분석 중 오류 발생: {e}")

    def create_chart(self):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(self.results['years'], self.results['rev_trend'], marker='o', color='#1f77b4')
        ax.set_title('Revenue Growth Trend')
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig) # DOM 충돌 방지를 위한 리소스 해제
        return buf

# 3. PDF 리포트 생성 함수
def create_pdf(analyzer, font_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # 제목 및 기본 정보
    c.setFont(font_name, 22)
    c.setFillColor(colors.darkblue)
    c.drawCentredString(w/2, h - 60, f"씨오리포트: 경영 진단 보고서")
    
    c.setStrokeColor(colors.lightgrey)
    c.line(50, h - 80, w - 50, h - 80)

    # 분석 내용
    c.setFont(font_name, 14)
    c.setFillColor(colors.black)
    c.drawString(70, h - 120, f"• 기업명: {analyzer.results['company_name']}")
    c.drawString(70, h - 150, f"• 주요 지표 요약")
    c.setFont(font_name, 11)
    c.drawString(90, h - 180, f"- 매출성장률: {analyzer.results['growth_rate']}%")
    c.drawString(90, h - 200, f"- 수익성(이익률): {analyzer.results['profit_margin']}%")
    c.drawString(90, h - 220, f"- 재무안정성(부채비율): {analyzer.results['debt_ratio']}%")

    # 차트 삽입
    chart_buf = analyzer.create_chart()
    c.drawImage(ImageReader(chart_buf), 70, h - 500, width=450, preserveAspectRatio=True)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# 4. Streamlit UI 메인
def main():
    st.set_page_config(page_title="씨오리포트 생성기", layout="centered")
    font_name = setup_fonts()

    st.title("📑 씨오리포트 자동 생성기")
    st.markdown("---")

    uploaded_file = st.file_uploader("크레탑 재무 엑셀 파일을 업로드하세요", type=['xlsx'], key="cre_uploader")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            analyzer = CorporateAnalyzer(df)
            analyzer.run_analysis()

            st.success("데이터 분석 완료!")
            
            # 대시보드 미리보기
            m1, m2, m3 = st.columns(3)
            m1.metric("성장성", f"{analyzer.results['growth_rate']}%")
            m2.metric("수익성", f"{analyzer.results['profit_margin']}%")
            m3.metric("안정성", f"{analyzer.results['debt_ratio']}%")

            # 리포트 생성 및 다운로드
            if st.button("전문 PDF 리포트 생성", key="gen_pdf_btn"):
                with st.spinner("리포트를 생성 중입니다..."):
                    pdf_data = create_pdf(analyzer, font_name)
                    st.download_button(
                        label="📥 PDF 리포트 다운로드",
                        data=pdf_data,
                        file_name=f"CEO_Report_{analyzer.results['company_name']}.pdf",
                        mime="application/pdf",
                        key="download_pdf_final"
                    )
        except Exception as e:
            st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
