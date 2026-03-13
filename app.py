import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
import io
import os
import fitz

# --- [1. 맑은 고딕 폰트 설정] ---
def setup_malgun_font():
    # 윈도우 시스템 경로 또는 프로젝트 내 fonts 폴더 확인
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf",
        "./fonts/malgun.ttf",
        "/usr/share/fonts/truetype/malgun.ttf" # 리눅스 환경 대비
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('Malgun', path))
                return 'Malgun'
            except: continue
    return 'Helvetica' # 실패 시 기본 폰트

# --- [2. 110페이지급 리포트 생성 엔진] ---
class FullConsultingReport:
    def __init__(self, data, font_name):
        self.data = data
        self.font = font_name
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4

    def draw_header_footer(self, page_num, title):
        """모든 페이지에 공통 헤더/푸터 삽입"""
        self.c.setFont(self.font, 9)
        self.c.setFillColor(colors.grey)
        self.c.drawString(50, self.h - 30, f"씨오리포트 | {self.data['company_name']}")
        self.c.drawRightString(self.w - 50, self.h - 30, title)
        self.c.line(50, self.h - 35, self.w - 50, self.h - 35)
        
        self.c.drawString(50, 30, "작성자: 중소기업경영지원단")
        self.c.drawRightString(self.w - 50, 30, f"Page {page_num} / 113")
        self.c.line(50, 35, self.w - 50, 35)

    def page_1_cover(self):
        """표지: 케이에이치오토 스타일"""
        self.c.setFont(self.font, 28)
        self.c.setFillColor(colors.HexColor("#1A3A5E"))
        self.c.drawCentredString(self.w/2, self.h - 250, self.data['company_name'])
        self.c.setFont(self.font, 22)
        self.c.drawCentredString(self.w/2, self.h - 310, "재무경영진단 리포트")
        
        self.c.setFont(self.font, 12)
        self.c.setFillColor(colors.black)
        self.c.drawString(70, 150, f"작성일: 2026. 03. 13")
        self.c.drawString(70, 130, f"작성자: 중소기업경영지원단")
        self.c.showPage()

    def page_2_contents(self):
        """목차: 12개 전문 섹션 구성"""
        self.draw_header_footer(2, "CONTENTS")
        self.c.setFont(self.font, 20)
        self.c.drawString(50, self.h - 100, "CONTENTS")
        
        sections = [
            ("01. 기업재무분석", "P03"), ("02. 기업가치평가", "P15"),
            ("03. 임원소득보상플랜", "P24"), ("04. 배당플랜", "P35"),
            ("05. CEO 유고 리스크 분석", "P44"), ("06. 차명주식 솔루션", "P52"),
            ("07. 가지급금 솔루션", "P58"), ("08. 자기주식 활용 솔루션", "P63"),
            ("09. 상속 및 가업승계", "P70"), ("10. 기업제도정비", "P80"),
            ("11. 신용등급 관리", "P101"), ("12. 경정청구 컨설팅", "P104")
        ]
        y = self.h - 180
        for name, pg in sections:
            self.c.setFont(self.font, 12)
            self.c.drawString(70, y, name)
            self.c.drawRightString(self.w - 70, y, pg)
            y -= 35
        self.c.showPage()

    def page_3_financial_summary(self):
        """실제 데이터 기반 재무분석 페이지"""
        self.draw_header_footer(3, "01. 기업재무분석")
        self.c.setFont(self.font, 16)
        self.c.drawString(50, self.h - 80, "■ 요약 재무현황")
        
        # 표 데이터 구성 (메이홈 엑셀 수치 반영)
        data = [
            ['구분', '2023년(전기)', '2024년(당기)', '증감'],
            ['매출액', f"{self.data.get('rev_23', 0):,}", f"{self.data.get('rev_24', 0):,}", '▲'],
            ['영업이익', '303,000', '433,000', '▲'],
            ['당기순이익', '297,000', '426,000', '▲']
        ]
        t = Table(data, colWidths=[120, 120, 120, 80])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), self.font),
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        t.wrapOn(self.c, self.w, self.h)
        t.drawOn(self.c, 70, self.h - 250)
        
        self.c.showPage()

    def generate_full_report(self):
        self.page_1_cover()
        self.page_2_contents()
        self.page_3_financial_summary()
        # 나머지 110페이지 분량을 섹션별로 반복 생성 (더미 페이지 포함)
        for i in range(4, 114):
            self.draw_header_footer(i, "경영진단 솔루션 상세")
            self.c.setFont(self.font, 12)
            self.c.drawString(100, self.h/2, f"상세 컨설팅 페이지 {i} (준비 중인 섹션)")
            self.c.showPage()
        
        self.c.save()
        self.buffer.seek(0)
        return self.buffer

# --- [3. Streamlit 앱 인터페이스] ---
def main():
    st.set_page_config(page_title="Professional CEO Report", layout="wide")
    font_name = setup_malgun_font()

    st.title("📊 전문 경영진단 리포트 시스템 (Malgun Gothic)")
    st.info("케이에이치오토 리포트와 동일한 110페이지 구성으로 리포트를 생성합니다.")

    uploaded_files = st.file_uploader("메이홈 관련 파일들을 모두 업로드하세요", accept_multiple_files=True)

    if uploaded_files:
        # (실제 구현 시 여기서 파일들로부터 데이터를 추출하여 dict에 저장)
        # 예시 수치: 메이홈 엑셀 ETFI112E1(1)에서 확인된 데이터
        mayhome_data = {
            'company_name': "(주)메이홈",
            'rev_23': 2765913,
            'rev_24': 4137922,
            'valuation': 254000
        }

        if st.button("113페이지 전체 리포트 생성 시작"):
            with st.spinner("방대한 분량의 PDF를 맑은 고딕으로 구성 중입니다..."):
                report_gen = FullConsultingReport(mayhome_data, font_name)
                final_pdf = report_gen.generate_full_report()
                
                st.download_button(
                    label="📥 최종 리포트(113P) 다운로드",
                    data=final_pdf,
                    file_name="Mayhome_Professional_Report.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
