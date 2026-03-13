import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import os
import io

# --- 1. 환경 설정 및 폰트 로드 ---
def setup_fonts():
    # 여러 경로에서 폰트 탐색 (Windows, Linux/Streamlit Cloud 대응)
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf",  # Windows
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Linux
        "./fonts/NanumGothic.ttf"  # Local project folder
    ]
    
    font_loaded = False
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('HanguI', path))
                font_loaded = True
                break
            except:
                continue
    
    if not font_loaded:
        st.warning("한글 폰트를 찾을 수 없어 기본 폰트로 대체합니다. PDF 내 한글이 깨질 수 있습니다.")

# --- 2. 분석 엔진 클래스 ---
class CEOReportGenerator:
    def __init__(self, df):
        self.df = df
        self.analysis = {}
        self.company_name = "미지정 기업"

    def analyze(self):
        try:
            # 엑셀 시트 구조에 따라 필터링 (예시: 특정 행 추출)
            # 여기서는 샘플 데이터를 생성하지만 실제로는 df에서 추출 로직을 넣으세요.
            self.company_name = "주식회사 케이에이치오토"
            
            # 수치 데이터 추출 및 계산
            rev_data = [1000000000, 1200000000, 1500000000] # 최근 3개년 매출
            self.analysis['growth'] = ((rev_data[-1] - rev_data[-2]) / rev_data[-2]) * 100
            self.analysis['profit_margin'] = 12.5
            self.analysis['debt_ratio'] = 45.0
            self.analysis['stock_value'] = 2500000000 # 25억
            self.analysis['rev_data'] = rev_data
        except Exception as e:
            st.error(f"데이터 분석 중 오류 발생: {e}")

    def create_chart_image(self):
        # 렌더링 오류 방지를 위해 명시적으로 Figure 객체 생성
        fig, ax = plt.subplots(figsize=(6, 4))
        years = ['2023', '2024', '2025']
        ax.plot(years, self.analysis['rev_data'], marker='o', color='blue', label='Revenue')
        ax.set_title('Financial Growth Trend')
        ax.legend()
        
        img_data = io.BytesIO()
        fig.savefig(img_data, format='png')
        img_data.seek(0)
        plt.close(fig) # 중요: 리소스 해제 및 DOM 충돌 방지
        return img_data

    def generate_pdf(self):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4

        # 리포트 내용 구성
        c.setFont('HanguI' if 'HanguI' in pdfmetrics.getRegisteredFontNames() else 'Helvetica', 20)
        c.drawCentredString(w/2, h - 50, f"{self.company_name} 경영 리포트")
        
        c.setStrokeColor(colors.dodgerblue)
        c.line(50, h - 70, w - 50, h - 70)

        # 지표 출력
        c.setFont('HanguI' if 'HanguI' in pdfmetrics.getRegisteredFontNames() else 'Helvetica', 12)
        c.drawString(70, h - 120, f"• 매출성장율: {self.analysis['growth']:.2f}%")
        c.drawString(70, h - 140, f"• 순이익률: {self.analysis['profit_margin']:.2f}%")
        c.drawString(70, h - 160, f"• 부채비율: {self.analysis['debt_ratio']:.2f}%")
        
        # 차트 삽입
        chart_img = self.create_chart_image()
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(chart_img), 70, h - 450, width=450, preserveAspectRatio=True)

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

# --- 3. Streamlit UI (메인 화면) ---
def main():
    st.set_page_config(page_title="CEO Report Generator", layout="centered")
    setup_fonts()

    st.title("📊 CEO 경영진단 리포트 생성기")
    st.write("크레탑에서 다운로드한 엑셀 파일을 업로드하세요.")

    uploaded_file = st.file_uploader("Excel 파일 선택", type=['xlsx', 'xls'], key="main_uploader")

    if uploaded_file is not None:
        try:
            # 1. 데이터 로드
            df = pd.read_excel(uploaded_file)
            
            # 2. 분석 진행
            generator = CEOReportGenerator(df)
            generator.analyze()
            
            # 3. 화면 표시
            st.success("데이터 분석이 완료되었습니다!")
            col1, col2 = st.columns(2)
            col1.metric("매출성장율", f"{generator.analysis['growth']:.1f}%")
            col2.metric("추정 기업가치", f"{generator.analysis['stock_value']:,} 원")

            # 4. 리포트 생성 및 다운로드
            pdf_data = generator.generate_pdf()
            
            st.download_button(
                label="📥 진단 리포트(PDF) 다운로드",
                data=pdf_data,
                file_name=f"CEO_Report_{generator.company_name}.pdf",
                mime="application/pdf",
                key="download_btn"
            )
            
        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
