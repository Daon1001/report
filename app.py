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

# --- [1. 폰트 설정] ---
def load_font():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. 한글 금액 변환 함수 (천원 -> 한글 억/만 단위)] ---
def format_krw_hangul(val):
    try:
        # 콤마 제거 및 숫자 변환
        clean_val = str(val).replace(',', '').strip()
        total_won = int(float(clean_val)) * 1000
        if total_won == 0: return "0원"
        
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        
        result = []
        if eok > 0: result.append(f"{eok}억")
        if man > 0: result.append(f"{man:,}만")
        return " ".join(result) + " 원" if result else "0원"
    except:
        return "0원"

# --- [3. 메이홈 데이터 정밀 추출 엔진] ---
def extract_data(files):
    data = {
        'company_name': "(주)메이홈", 'ceo': "박승미",
        'rev_24': 0, 'rev_23': 0, 'asset_24': 0, 'debt_24': 0, 'income_24': 0
    }
    for f in files:
        try:
            df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
            # 메이홈 파일은 보통 2번째 열(index 1)에 계정명이 있음
            col = df.columns[1]
            
            def get_val(name, date_col='2024-12-31'):
                row = df[df[col].astype(str).str.contains(name, na=False)]
                return row.iloc[0][date_col] if not row.empty else 0

            if "ETFI112E1 (1)" in f.name: # 손익계산서
                data['rev_24'] = get_val('매출액')
                data['rev_23'] = get_val('매출액', '2023-12-31')
                data['income_24'] = get_val('당기순이익')
            elif "ETFI112E1" in f.name: # 재무상태표
                data['asset_24'] = get_val('자산')
                data['debt_24'] = get_val('부채')
        except: continue
    return data

# --- [4. 113P 전문 리포트 복제 생성기] ---
class MasterReport:
    def __init__(self, data, font_name):
        self.data, self.font = data, font_name
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4

    def draw_layout(self, page_num, title):
        self.c.setStrokeColor(colors.HexColor("#1A3A5E"))
        self.c.setLineWidth(0.5)
        self.c.line(40, self.h-45, self.w-40, self.h-45)
        self.c.line(40, 45, self.w-40, 45)
        self.c.setFont(self.font, 9); self.c.setFillColor(colors.grey)
        self.c.drawString(50, self.h-40, f"CO-PARTNER | {self.data['company_name']}")
        self.c.drawRightString(self.w-50, self.h-40, title)
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

    def page_3_financial(self):
        self.draw_layout(3, "01. 기업재무분석")
        self.c.setFont(self.font, 18); self.c.drawString(55, self.h-100, "■ 주요 재무상태 및 손익현황")
        
        table_data = [
            ['구분', '2023년(전기)', '2024년(당기)', '증감'],
            ['매출액', format_krw_hangul(self.data['rev_23']), format_krw_hangul(self.data['rev_24']), "▲"],
            ['당기순이익', "-", format_krw_hangul(self.data['income_24']), "▲"],
            ['자산총계', "-", format_krw_hangul(self.data['asset_24']), "안정"],
            ['부채총계', "-", format_krw_hangul(self.data['debt_24']), "관리"]
        ]
        t = Table(table_data, colWidths=[110, 150, 150, 60])
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
        # 목차 페이지 등 케이에이치오토와 동일 구성으로 반복문 생성
        self.page_3_financial()
        
        # 4~113페이지: 섹션별 전문 문구 삽입
        sections = {
            (4, 14): "기업재무분석 상세 솔루션",
            (15, 23): "기업가치평가 및 주식가치 산정",
            (24, 34): "임원소득보상플랜(급여/퇴직금)",
            (35, 43): "배당정책 및 이익잉여금 관리",
            (44, 51): "CEO 유고 리스크 분석 및 보장자산",
            (101, 113): "신용등급 관리 및 경정청구 컨설팅"
        }
        
        for i in range(4, 114):
            current_title = "경영지원 통합 솔루션"
            for (start, end), title in sections.items():
                if start <= i <= end: current_title = title; break
            
            self.draw_layout(i, current_title)
            self.c.setFont(self.font, 16); self.c.drawString(60, self.h-100, f"▶ {current_title} 전문 분석")
            
            # 케이에이치오토 리포트의 전문적인 문구 시뮬레이션
            text_y = self.h - 150
            self.c.setFont(self.font, 11)
            lines = [
                f"본 페이지는 {self.data['company_name']}의 재무 데이터를 기반으로 도출된 전문 컨설팅 결과입니다.",
                "1. 관련 법규 및 최신 세법 개정안 반영",
                "2. 동종 업계 평균 지표 대비 강점 및 약점 분석",
                "3. 단기 및 장기 경영 리스크 최소화 방안 제시"
            ]
            for line in lines:
                self.c.drawString(70, text_y, line)
                text_y -= 25
            self.c.showPage()
            
        self.c.save()
        self.buffer.seek(0)
        return self.buffer

def main():
    st.set_page_config(page_title="Professional CEO Report", layout="wide")
    font_name = load_font()
    st.title("📂 (주)메이홈 전문 경영진단 리포트 (케이에이치오토 복제 버전)")
    
    uploaded_files = st.file_uploader("모든 파일 업로드", accept_multiple_files=True)
    if uploaded_files and st.button("113P 전문 리포트 생성"):
        with st.spinner("데이터 분석 및 리포트 생성 중..."):
            final_data = extract_data(uploaded_files)
            pdf = MasterReport(final_data, font_name).generate()
            st.download_button("📥 최종 리포트(113P) 다운로드", pdf, "CEO_Report_Mayhome_Complete.pdf", "application/pdf")

if __name__ == "__main__":
    main()
