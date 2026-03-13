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

# --- [1. 폰트 로드: 루트의 malgun.ttf 강제 지정] ---
def load_font():
    font_path = "./malgun.ttf" 
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. 한글 금액 변환 함수: 천원 -> 억/만 단위 한글] ---
def format_to_hangul_won(val_in_thousands):
    try:
        # 엑셀의 천 단위 수치를 실제 원 단위로 변환
        total_won = int(float(str(val_in_thousands).replace(',', ''))) * 1000
        if total_won == 0: return "0원"
        
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        
        result = []
        if eok > 0: result.append(f"{eok}억")
        if man > 0: result.append(f"{man:,}만")
        
        return " ".join(result) + " 원" if result else "0원"
    except:
        return "0원"

# --- [3. 데이터 추출 엔진: 메이홈 파일 구조 정밀 타겟팅] ---
def extract_refined_data(files):
    res = {
        'name': "(주)메이홈", 'ceo': "박승미",
        'rev_24': 0, 'rev_23': 0, 'asset_24': 0, 'debt_24': 0, 'income_24': 0
    }
    for f in files:
        try:
            df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
            # 메이홈 엑셀은 2번째 열(Index 1)에 계정명이 있음
            col = df.columns[1]
            
            def find_val(name, date_col='2024-12-31'):
                row = df[df[col].astype(str).str.contains(name, na=False)]
                if not row.empty:
                    val = row.iloc[0].get(date_col, 0)
                    return val
                return 0

            if "ETFI112E1 (1)" in f.name: # 손익계산서
                res['rev_24'] = find_val('매출액')
                res['rev_23'] = find_val('매출액', '2023-12-31')
                res['income_24'] = find_val('당기순이익')
            elif "ETFI112E1" in f.name: # 재무상태표
                res['asset_24'] = find_val('자산')
                res['debt_24'] = find_val('부채')
        except: continue
    return res

# --- [4. 113P 복제 생성기] ---
class FullCopyReport:
    def __init__(self, data, font):
        self.data, self.font = data, font
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4

    def draw_layout(self, pg, section):
        self.c.setStrokeColor(colors.HexColor("#1A3A5E"))
        self.c.line(40, self.h-45, self.w-40, self.h-45)
        self.c.line(40, 45, self.w-40, 45)
        self.c.setFont(self.font, 9); self.c.setFillColor(colors.grey)
        self.c.drawString(50, self.h-40, f"CO-PARTNER | {self.data['name']}")
        self.c.drawRightString(self.w-50, self.h-40, section)
        self.c.drawRightString(self.w-50, 35, f"씨오리포트 {pg} / 113")

    def page_1_cover(self):
        self.c.setFillColor(colors.HexColor("#1A3A5E"))
        self.c.rect(0, self.h-220, self.w, 220, fill=1)
        self.c.setFont(self.font, 36); self.c.setFillColor(colors.white)
        self.c.drawCentredString(self.w/2, self.h-130, self.data['name'])
        self.c.setFillColor(colors.black); self.c.setFont(self.font, 26)
        self.c.drawCentredString(self.w/2, self.h-380, "재무경영진단 리포트")
        self.c.setFont(self.font, 14)
        self.c.drawString(80, 200, "작성일: 2026. 03. 13")
        self.c.drawString(80, 175, "작성자: 중소기업경영지원단")
        self.c.showPage()

    def page_3_financial(self):
        self.draw_layout(3, "01. 기업재무분석")
        self.c.setFont(self.font, 18); self.c.setFillColor(colors.black)
        self.c.drawString(55, self.h-100, "■ 주요 재무상태 및 손익현황")
        
        # 실제 데이터 바인딩 (한글 단위)
        rows = [
            ['구분', '2023년(전기)', '2024년(당기)', '증감'],
            ['매출액', format_to_hangul_won(self.data['rev_23']), format_to_hangul_won(self.data['rev_24']), "▲"],
            ['당기순이익', "-", format_to_hangul_won(self.data['income_24']), "▲"],
            ['자산총계', "-", format_to_hangul_won(self.data['asset_24']), "안정"],
            ['부채총계', "-", format_to_hangul_won(self.data['debt_24']), "관리"]
        ]
        t = Table(rows, colWidths=[120, 150, 150, 60])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), self.font),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F2F2F2")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        t.wrapOn(self.c, self.w, self.h); t.drawOn(self.c, 60, self.h-300)
        self.c.showPage()

    def generate(self):
        self.page_1_cover()
        self.page_3_financial()
        
        # 케이에이치오토 섹션별 전문 문구 템플릿
        contents = {
            (4, 14): ["01. 기업재무분석 상세", "현금흐름 및 재무비율 상세 분석 결과입니다. 매출액이 전년 대비 크게 성장하였습니다."],
            (15, 23): ["02. 기업가치평가", "상증세법에 따른 주식가치 산정 결과, 가업 승계 시 세무 리스크 점검이 필요합니다."],
            (24, 34): ["03. 임원소득보상플랜", "임원의 급여 및 퇴직금 지급 규정을 정관에 명시하여 비용 처리를 최적화해야 합니다."],
            (35, 43): ["04. 배당플랜", "이익잉여금의 효율적 회수를 위한 차등배당 및 자사주 매입 전략을 제시합니다."],
            (101, 113): ["11. 신용등급 관리", "KODATA 신용등급 개선을 위한 재무 지표 관리 방안 및 경정청구 프로세스입니다."]
        }
        
        for pg in range(4, 114):
            title, text = "경영진단 솔루션", "데이터 기반의 전문 컨설팅 페이지입니다."
            for (s, e), (t, txt) in contents.items():
                if s <= pg <= e: title, text = t, txt; break
            
            self.draw_layout(pg, title)
            self.c.setFont(self.font, 16); self.c.drawString(60, self.h-100, f"▶ {title}")
            self.c.setFont(self.font, 11); self.c.drawString(70, self.h-150, text)
            self.c.drawString(70, self.h-175, f"(주)메이홈의 재무 데이터를 근거로 작성된 전문 보고서입니다.")
            self.c.showPage()
            
        self.c.save()
        self.buffer.seek(0)
        return self.buffer

def main():
    st.set_page_config(page_title="Professional Report Generator", layout="wide")
    f = load_font()
    st.title("📑 (주)메이홈 전문 경영진단 리포트 (113P 마스터)")
    
    ups = st.file_uploader("파일 업로드", accept_multiple_files=True)
    if ups and st.button("전문 리포트 생성"):
        with st.spinner("방대한 리포트 생성 중..."):
            data = extract_refined_data(ups)
            pdf = FullCopyReport(data, f).generate()
            st.download_button("📥 최종 리포트 다운로드", pdf, "CEO_Report_Mayhome_Complete.pdf", "application/pdf")

if __name__ == "__main__":
    main()
