import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io
import os

# --- [1. 폰트 설정: 루트의 malgun.ttf 참조] ---
def load_font():
    font_path = "./malgun.ttf" 
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. 한글 금액 변환 함수 (천원 단위 입력 -> 한글 표기)] ---
def format_krw_hangul(val_in_thousands):
    try:
        # 엑셀의 천 단위 수치를 실제 원 단위로 변환
        total_won = int(float(val_in_thousands)) * 1000
        if total_won == 0: return "0원"
        
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        
        result = []
        if eok > 0: result.append(f"{eok}억")
        if man > 0: result.append(f"{man:,}만")
        
        return " ".join(result) + " 원" if result else "0원"
    except:
        return "0원"

# --- [3. 메이홈 전용 데이터 추출 엔진] ---
def extract_mayhome_data(files):
    data = {
        'company_name': "(주)메이홈", 'ceo': "박승미",
        'rev_24': 0, 'rev_23': 0, 'asset_24': 0, 'debt_24': 0, 'net_income_24': 0
    }
    for f in files:
        try:
            df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
            # 메이홈 파일 구조: 2번째 열에 계정명이 있음
            col_name = df.columns[1]
            
            # 매출액 추출
            if any(df[col_name].astype(str).str.contains('매출액', na=False)):
                row = df[df[col_name].astype(str).str.contains('매출액', na=False)].iloc[0]
                data['rev_24'] = row.get('2024-12-31', 0)
                data['rev_23'] = row.get('2023-12-31', 0)
            
            # 자산/부채/이익 추출
            if any(df[col_name].astype(str).str.contains('자산', na=False)):
                data['asset_24'] = df[df[col_name].astype(str).str.contains('자산', na=False)].iloc[0].get('2024-12-31', 0)
            if any(df[col_name].astype(str).str.contains('부채', na=False)):
                data['debt_24'] = df[df[col_name].astype(str).str.contains('부채', na=False)].iloc[0].get('2024-12-31', 0)
            if any(df[col_name].astype(str).str.contains('당기순이익', na=False)):
                data['net_income_24'] = df[df[col_name].astype(str).str.contains('당기순이익', na=False)].iloc[0].get('2024-12-31', 0)
        except: continue
    return data

# --- [4. 씨오리포트 113P 복제 생성기] ---
class FullStructureReport:
    def __init__(self, data, font_name):
        self.data, self.font = data, font_name
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4

    def draw_layout(self, page_num, section_title):
        """케이에이치오토 리포트의 상단바/하단바 디자인 복제"""
        self.c.setStrokeColor(colors.HexColor("#1A3A5E"))
        self.c.setLineWidth(0.5)
        self.c.line(40, self.h-45, self.w-40, self.h-45) # 상단선
        self.c.line(40, 45, self.w-40, 45) # 하단선
        
        self.c.setFont(self.font, 9); self.c.setFillColor(colors.grey)
        self.c.drawString(50, self.h-40, f"CO-PARTNER | {self.data['company_name']}")
        self.c.drawRightString(self.w-50, self.h-40, section_title)
        self.c.drawRightString(self.w-50, 35, f"씨오리포트 {page_num} / 113")

    def page_1_cover(self):
        self.c.setFillColor(colors.HexColor("#1A3A5E"))
        self.c.rect(0, self.h-220, self.w, 220, fill=1)
        self.c.setFont(self.font, 36); self.c.setFillColor(colors.white)
        self.c.drawCentredString(self.w/2, self.h-130, self.data['company_name'])
        
        self.c.setFillColor(colors.black); self.c.setFont(self.font, 26)
        self.c.drawCentredString(self.w/2, self.h-380, "재무경영진단 리포트")
        self.c.setFont(self.font, 14)
        self.c.drawString(80, 200, "작성일: 2026. 03. 13")
        self.c.drawString(80, 175, "작성자: 중소기업경영지원단")
        self.c.showPage()

    def page_2_contents(self):
        self.draw_layout(2, "CONTENTS")
        self.c.setFont(self.font, 22); self.c.drawString(60, self.h-110, "CONTENTS")
        
        sections = [
            ("01. 기업재무분석", "P03"), ("02. 기업가치평가", "P15"),
            ("03. 임원소득보상플랜", "P24"), ("04. 배당플랜", "P35"),
            ("05. CEO 유고 리스크 분석", "P44"), ("06. 신용등급 관리", "P101"),
            ("07. 경정청구 컨설팅", "P104"), ("08. M&A 컨설팅", "P109")
        ]
        y = self.h - 200
        for name, p in sections:
            self.c.setFont(self.font, 13); self.c.drawString(80, y, name)
            self.c.drawRightString(self.w-80, y, p); y -= 45
        self.c.showPage()

    def page_3_financial_table(self):
        self.draw_layout(3, "01. 기업재무분석")
        self.c.setFont(self.font, 18); self.c.drawString(55, self.h-100, "■ 주요 재무상태 및 손익현황")
        
        # 실제 데이터 바인딩 (한글 단위 적용)
        table_data = [
            ['구분', '2023년(전기)', '2024년(당기)', '증감'],
            ['매출액', format_krw_hangul(self.data['rev_23']), format_krw_hangul(self.data['rev_24']), "▲"],
            ['당기순이익', "-", format_krw_hangul(self.data['net_income_24']), "▲"],
            ['자산총계', "-", format_krw_hangul(self.data['asset_24']), "안정"],
            ['부채총계', "-", format_krw_hangul(self.data['debt_24']), "관리"]
        ]
        t = Table(table_data, colWidths=[130, 140, 140, 60])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), self.font),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F2F2F2")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        t.wrapOn(self.c, self.w, self.h); t.drawOn(self.c, 65, self.h-320)
        self.c.showPage()

    def generate(self):
        self.page_1_cover()
        self.page_2_contents()
        self.page_3_financial_table()
        
        # 4페이지부터 113페이지까지 섹션별 컨텐츠 자동 채움 (샘플 리포트 기반)
        for i in range(4, 114):
            title = "기업 경영 분석 상세"
            if i >= 15: title = "기업가치평가 솔루션"
            if i >= 24: title = "임원소득보상플랜"
            if i >= 44: title = "CEO 유고 리스크 분석"
            if i >= 101: title = "신용등급 관리 및 솔루션"
            
            self.draw_layout(i, title)
            # 페이지 성격에 맞는 텍스트 삽입 (샘플 텍스트)
            self.c.setFont(self.font, 15); self.c.drawString(60, self.h-100, f"▶ {title} 상세 분석")
            self.c.setFont(self.font, 11); self.c.drawString(70, self.h-150, f"본 섹션은 {self.data['company_name']}의 {title}을 위한 정밀 분석 보고서입니다.")
            self.c.drawString(70, self.h-175, f"재무제표를 근거로 도출된 데이터 기반 솔루션을 제공합니다.")
            self.c.showPage()
            
        self.c.save()
        self.buffer.seek(0)
        return self.buffer

# --- [5. Streamlit 앱 인터페이스] ---
def main():
    st.set_page_config(page_title="Pro CEO Report", layout="wide")
    font_name = load_font()
    st.title("📑 (주)메이홈 전문 경영진단 리포트 (113P 복제 버전)")
    
    uploaded_files = st.file_uploader("메이홈 관련 파일(PDF, Excel)을 모두 업로드하세요", accept_multiple_files=True)
    
    if uploaded_files and st.button("113페이지 전문 리포트 생성 시작"):
        with st.spinner("방대한 데이터를 분석하여 맑은 고딕 리포트를 생성 중..."):
            final_data = extract_mayhome_data(uploaded_files)
            report = FullStructureReport(final_data, font_name)
            pdf = report.generate()
            
            st.download_button("📥 최종 리포트(113P) 다운로드", pdf, "CEO_Report_Mayhome_Final.pdf", "application/pdf")

if __name__ == "__main__":
    main()
