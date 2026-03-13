import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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

# --- [2. 한글 단위 변환 함수] ---
def format_krw(val_in_thousands):
    """천 단위 숫자를 억, 만 단위 한글로 변환"""
    try:
        total_won = int(float(val_in_thousands)) * 1000
        if total_won == 0: return "0원"
        
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        
        result = ""
        if eok > 0: result += f"{eok}억 "
        if man > 0: result += f"{man:,}만 "
        return result + "원"
    except:
        return "데이터 없음"

# --- [3. 데이터 추출 엔진] ---
def extract_data(files):
    data = {
        'company_name': "(주)메이홈", 'ceo': "박승미",
        'rev_24': 0, 'rev_23': 0, 'asset_24': 0, 'debt_24': 0
    }
    for f in files:
        try:
            df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
            # 계정명 열 찾기 (2번째 열)
            col = df.columns[1]
            if any(df[col].astype(str).str.contains('매출액', na=False)):
                row = df[df[col].astype(str).str.contains('매출액', na=False)].iloc[0]
                data['rev_24'] = row.get('2024-12-31', 0)
                data['rev_23'] = row.get('2023-12-31', 0)
            if any(df[col].astype(str).str.contains('자산', na=False)):
                data['asset_24'] = df[df[col].astype(str).str.contains('자산', na=False)].iloc[0].get('2024-12-31', 0)
            if any(df[col].astype(str).str.contains('부채', na=False)):
                data['debt_24'] = df[df[col].astype(str).str.contains('부채', na=False)].iloc[0].get('2024-12-31', 0)
        except: continue
    return data

# --- [4. 113P 고도화 리포트 생성기] ---
class FinalReport:
    def __init__(self, data, font_name):
        self.data, self.font = data, font_name
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4

    def draw_frame(self, page_num, title):
        self.c.setStrokeColor(colors.HexColor("#1A3A5E"))
        self.c.line(40, self.h-45, self.w-40, self.h-45)
        self.c.line(40, 45, self.w-40, 45)
        self.c.setFont(self.font, 9)
        self.c.setFillColor(colors.grey)
        self.c.drawString(50, self.h-40, f"CO-PARTNER | {self.data['company_name']}")
        self.c.drawRightString(self.w-50, self.h-40, title)
        self.c.drawRightString(self.w-50, 35, f"씨오리포트 {page_num} / 113")

    def page_cover(self):
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

    def page_financial(self):
        self.draw_frame(3, "01. 기업재무분석")
        self.c.setFont(self.font, 18); self.c.setFillColor(colors.black)
        self.c.drawString(55, self.h-100, "■ 주요 재무상태 및 손익현황")
        
        # 한글 단위 적용 데이터
        table_data = [
            ['구분', '2023년(전기)', '2024년(당기)', '비고'],
            ['매출액', format_krw(self.data['rev_23']), format_krw(self.data['rev_24']), "성장"],
            ['자산총계', "-", format_krw(self.data['asset_24']), "안정"],
            ['부채총계', "-", format_krw(self.data['debt_24']), "관리"]
        ]
        t = Table(table_data, colWidths=[120, 140, 140, 60])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), self.font),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F2F2F2")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        t.wrapOn(self.c, self.w, self.h)
        t.drawOn(self.c, 70, self.h-280)
        self.c.showPage()

    def page_solutions(self, start, end, section_title, content_list):
        """상세 솔루션 페이지 컨텐츠 삽입"""
        for i in range(start, end + 1):
            self.draw_frame(i, section_title)
            self.c.setFont(self.font, 16)
            self.c.drawString(60, self.h-100, f"▶ {section_title} 상세 분석")
            
            # 실제 솔루션 텍스트 (content_list에서 순차적으로 가져오거나 반복)
            idx = (i - start) % len(content_list)
            text_lines = content_list[idx]
            
            y_text = self.h - 150
            self.c.setFont(self.font, 11)
            for line in text_lines:
                self.c.drawString(70, y_text, line)
                y_text -= 25
            self.c.showPage()

    def generate(self):
        self.page_cover()
        # 목차 등 생략...
        self.page_financial()
        
        # 전문 솔루션 컨텐츠 예시 (이 내용을 늘리면 리포트가 꽉 찹니다)
        tax_content = [
            ["1. 법인세 절세 전략 수립", "- 기업부설연구소 설립을 통한 세액공제 극대화", "- 고용증대 세액공제 및 사회보험료 세액공제 검토"],
            ["2. 미처분이익잉여금 관리", "- 과도한 이익잉여금은 기업가치 상승으로 상속/증여세 부담 가중", "- 자사주 매입 및 배당을 통한 전략적 회수 필요"]
        ]
        ceo_content = [
            ["1. CEO 유고 시 긴급 자금 확보", "- 경영진 유고 시 대출금 즉시 상환 압박 대비", "- 가업 승계 시 상속세 재원 마련 전략"]
        ]
        
        self.page_solutions(4, 50, "기업 경영 전략 솔루션", tax_content)
        self.page_solutions(51, 100, "CEO 리스크 관리", ceo_content)
        self.page_solutions(101, 113, "신용등급 및 경정청구", [["- 국세청 환급금 추적 및 경정청구권 행사"]])
        
        self.c.save()
        self.buffer.seek(0)
        return self.buffer

def main():
    st.set_page_config(page_title="Professional CEO Report", layout="wide")
    font_name = load_font()
    st.title("📂 (주)메이홈 전문 경영지원 시스템")
    
    uploaded_files = st.file_uploader("파일 업로드", accept_multiple_files=True)
    if uploaded_files and st.button("113P 전문 리포트 생성"):
        final_data = extract_data(uploaded_files)
        pdf = FinalReport(final_data, font_name).generate()
        st.download_button("📥 최종 리포트 다운로드", pdf, f"CEO_Report_Mayhome_Full.pdf", "application/pdf")

if __name__ == "__main__":
    main()
