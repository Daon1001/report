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
import fitz  # PyMuPDF

# --- [1. 폰트 설정] ---
def load_font():
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
            except: continue
    return 'Helvetica'

# --- [2. 분석 엔진] ---
class IntegratedAnalyzer:
    def __init__(self):
        self.company_info = ""
        self.financial_metrics = {}
        self.company_name = "미지정 기업"

    def process_pdf(self, file):
        """PDF에서 기업개요 텍스트 추출"""
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        self.company_info += text[:1000] # 핵심 내용 일부 저장
        if "주식회사" in text and self.company_name == "미지정 기업":
            try:
                self.company_name = text.split("주식회사")[1].split()[0]
            except: pass

    def process_excel(self, file):
        """엑셀에서 재무지표 추출"""
        df = pd.read_excel(file)
        # 실제 크레탑 엑셀의 항목명에 맞춰 매핑이 필요합니다.
        self.financial_metrics = {
            'growth': 15.8,   # 예시: 매출증가율
            'profit': 7.2,    # 예시: 영업이익률
            'stability': 38.5 # 예시: 부채비율
        }

    def create_chart(self):
        fig, ax = plt.subplots(figsize=(5, 3))
        labels = ['Growth', 'Profit', 'Stability']
        values = [self.financial_metrics.get('growth', 0), 
                  self.financial_metrics.get('profit', 0), 
                  self.financial_metrics.get('stability', 0)]
        ax.bar(labels, values, color=['#4F81BD', '#C0504D', '#9BBB59'])
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return buf

# --- [3. 메인 UI] ---
def main():
    st.set_page_config(page_title="통합 씨오리포트 생성기", layout="wide")
    font_name = load_font()
    
    st.title("📂 멀티 파일 통합 진단 시스템")
    st.write("기업개요 PDF들과 재무제표 엑셀을 모두 선택하여 업로드하세요.")

    uploaded_files = st.file_uploader(
        "파일 업로드 (PDF, XLSX)", 
        type=['pdf', 'xlsx'], 
        accept_multiple_files=True,
        key="multi_file_uploader"
    )

    if uploaded_files:
        analyzer = IntegratedAnalyzer()
        
        for f in uploaded_files:
            if f.name.endswith('.pdf'):
                analyzer.process_pdf(f)
            elif f.name.endswith('.xlsx'):
                analyzer.process_excel(f)

        st.success(f"✅ 분석 완료: {analyzer.company_name}")

        # 화면 요약
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 기업 개요 (PDF 추출)")
            st.write(analyzer.company_info[:300] + "...")
        with col2:
            st.subheader("📈 재무 지표 (Excel 분석)")
            st.json(analyzer.financial_metrics)

        # 리포트 생성
        if st.button("📄 통합 PDF 리포트 생성", key="gen_final_pdf"):
            pdf_buf = io.BytesIO()
            c = canvas.Canvas(pdf_buf, pagesize=A4)
            w, h = A4
            
            # 리포트 디자인
            c.setFont(font_name, 20)
            c.drawCentredString(w/2, h - 50, f"기업 경영진단 통합 보고서")
            
            c.setFont(font_name, 12)
            c.drawString(50, h - 100, f"기업명: {analyzer.company_name}")
            
            # 분석 내용 기록
            text_obj = c.beginText(50, h - 140)
            text_obj.setFont(font_name, 10)
            text_obj.textLine("[기업 개요 요약]")
            # 간단한 줄바꿈 처리
            summary = analyzer.company_info[:200].replace('\n', ' ')
            text_obj.textLine(summary[:70])
            text_obj.textLine(summary[70:140])
            c.drawText(text_obj)
            
            # 차트 삽입
            chart_img = analyzer.create_chart()
            c.drawImage(ImageReader(chart_img), 50, h - 450, width=400, preserveAspectRatio=True)
            
            c.showPage()
            c.save()
            pdf_buf.seek(0)

            st.download_button(
                label="📥 통합 리포트 다운로드",
                data=pdf_buf,
                file_name=f"Integrated_Report_{analyzer.company_name}.pdf",
                mime="application/pdf",
                key="last_down_btn"
            )

if __name__ == "__main__":
    main()
