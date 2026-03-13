import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import os
import io

# 1. 폰트 설정 (에러 방지 로직 포함)
def load_korean_font():
    # 폰트 우선순위: 1. 로컬 fonts 폴더, 2. 시스템 경로, 3. 기본 폰트
    font_paths = [
        "./fonts/NanumGothic.ttf", 
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('HanguI', path))
                return 'HanguI'
            except:
                continue
    return 'Helvetica' # 한글 폰트 실패 시 기본 영문 폰트 사용

# 2. 분석 엔진 클래스
class CEOReporter:
    def __init__(self, dataframe):
        self.df = dataframe
        self.analysis = {}

    def run_process(self):
        # 예시 데이터 추출 (실제 엑셀 컬럼명에 맞게 수정 필요)
        # 엑셀 첫 번째 시트의 데이터를 기반으로 수치 계산
        try:
            self.analysis['name'] = "분석 대상 기업"
            self.analysis['rev_growth'] = 15.4  # 매출성장률 예시
            self.analysis['profit_idx'] = 8.2   # 수익성 지표 예시
            self.analysis['debt_idx'] = 42.1    # 부채비율 예시
        except:
            st.error("엑셀 데이터 구조가 리포트 양식과 맞지 않습니다.")

    def get_chart(self):
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(['Growth', 'Profit', 'Debt'], [self.analysis['rev_growth'], self.analysis['profit_idx'], self.analysis['debt_idx']])
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return buf

# 3. 메인 앱 화면
def main():
    st.set_page_config(page_title="씨오리포트 생성기", layout="wide")
    font_name = load_korean_font()

    st.title("🚀 기업분석 리포트 자동 생성기")
    st.info("크레탑에서 받은 엑셀 파일을 업로드하면 PDF 리포트가 즉시 생성됩니다.")

    uploaded_file = st.file_uploader("엑셀 파일 업로드", type=['xlsx'], key="uploader")

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        reporter = CEOReporter(df)
        reporter.run_process()

        # 분석 결과 미리보기
        st.subheader("📊 주요 분석 지표")
        cols = st.columns(3)
        cols[0].metric("성장성", f"{reporter.analysis['rev_growth']}%")
        cols[1].metric("수익성", f"{reporter.analysis['profit_idx']}%")
        cols[2].metric("안정성", f"{reporter.analysis['debt_idx']}%")

        # PDF 생성 및 다운로드
        if st.button("PDF 리포트 생성하기"):
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            w, h = A4
            
            c.setFont(font_name, 20)
            c.drawString(50, h - 50, f"기업 경영 진단 결과 보고서")
            c.setFont(font_name, 12)
            c.drawString(50, h - 100, f"성장성 지표: {reporter.analysis['rev_growth']}%")
            
            # 차트 삽입
            chart_buf = reporter.get_chart()
            c.drawImage(ImageReader(chart_buf), 50, h - 400, width=400, preserveAspectRatio=True)
            
            c.showPage()
            c.save()
            buf.seek(0)

            st.download_button(
                label="📥 리포트 다운로드",
                data=buf,
                file_name="CEO_Analysis_Report.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
