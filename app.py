import streamlit as st
import pandas as pd
import io
import os
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# --- [1. 폰트 설정] ---
def load_malgun():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Malgun', font_path))
        return 'Malgun'
    return 'Helvetica'

# --- [2. 한글 금액 변환 (100000 -> 1억 원)] ---
def won_to_hangul(val_in_thousands):
    try:
        # 콤마 제거 및 숫자로 변환
        num = str(val_in_thousands).replace(',', '').strip()
        total_won = int(float(num)) * 1000
        if total_won == 0: return "0원"
        
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except:
        return "0원"

# --- [3. 메이홈 전용 데이터 정밀 추출] ---
def extract_all_data(files):
    data = {
        'company': "(주)메이홈", 'ceo': "박승미", 'rating': "a",
        'rev_24': 0, 'rev_23': 0, 'asset_24': 0, 'debt_24': 0, 'income_24': 0
    }
    for f in files:
        if f.name.endswith('.pdf'):
            doc = fitz.open(stream=f.read(), filetype="pdf")
            text = "".join([page.get_text() for page in doc])
            if "박승미" in text: data['ceo'] = "박승미"
            if "신용등급" in text and "a" in text.lower(): data['rating'] = "a"
        else:
            try:
                # 엑셀/CSV 정밀 읽기: 2번째 열에서 계정명 확인
                df = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
                col = df.columns[1]
                
                def get_v(name, date='2024-12-31'):
                    row = df[df[col].astype(str).str.contains(name, na=False)]
                    if not row.empty: return row.iloc[0].get(date, 0)
                    return 0

                if "ETFI112E1 (1)" in f.name:
                    data['rev_24'] = get_v('매출액')
                    data['rev_23'] = get_v('매출액', '2023-12-31')
                    data['income_24'] = get_v('당기순이익')
                elif "ETFI112E1" in f.name:
                    data['asset_24'] = get_v('자산')
                    data['debt_24'] = get_v('부채')
            except: continue
    return data

# --- [4. 113P 케이에이치오토 복제 생성기] ---
class ReplicaReport:
    def __init__(self, data, font):
        self.data, self.font = data, font
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4

    def draw_layout(self, pg, title):
        """케이에이치오토 상하단 디자인 그대로 복제"""
        self.c.setStrokeColor(colors.HexColor("#1A3A5E"))
        self.c.setLineWidth(0.5)
        self.c.line(40, self.h-45, self.w-40, self.h-45)
        self.c.line(40, 45, self.w-40, 45)
        self.c.setFont(self.font, 9); self.c.setFillColor(colors.grey)
        self.c.drawString(50, self.h-40, f"CO-PARTNER | {self.data['company']}")
        self.c.drawRightString(self.w-50, self.h-40, title)
        self.c.drawRightString(self.w-50, 35, f"씨오리포트 {pg} / 113")

    def page_1_cover(self):
        """표지 디자인 복제"""
        self.c.setFillColor(colors.HexColor("#1A3A5E"))
        self.c.rect(0, self.h-220, self.w, 220, fill=1)
        self.c.setFont(self.font, 36); self.c.setFillColor(colors.white)
        self.c.drawCentredString(self.w/2, self.h-130, self.data['company'])
        self.c.setFillColor(colors.black); self.c.setFont(self.font, 26)
        self.c.drawCentredString(self.w/2, self.h-380, "재무경영진단 리포트")
        self.c.setFont(self.font, 12)
        self.c.drawString(80, 200, f"작성일: 2026. 03. 13")
        self.c.drawString(80, 180, f"대표자: {self.data['ceo']}")
        self.c.drawString(80, 160, f"작성자: 중소기업경영지원단")
        self.c.showPage()

    def page_3_financial(self):
        """3페이지 재무표: 실데이터 대입"""
        self.draw_layout(3, "01. 기업재무분석")
        self.c.setFont(self.font, 18); self.c.drawString(55, self.h-100, "■ 주요 재무상태 및 손익현황")
        
        table_data = [
            ['구분', '2023년(전기)', '2024년(당기)', '상태'],
            ['매출액', won_to_hangul(self.data['rev_23']), won_to_hangul(self.data['rev_24']), "상승"],
            ['당기순이익', "-", won_to_hangul(self.data['income_24']), "양호"],
            ['자산총계', "-", won_to_hangul(self.data['asset_24']), "안정"],
            ['부채총계', "-", won_to_hangul(self.data['debt_24']), "관리"]
        ]
        t = Table(table_data, colWidths=[120, 150, 150, 60])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), self.font),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F2F2F2")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        t.wrapOn(self.c, self.w, self.h); t.drawOn(self.c, 65, self.h-300)
        self.c.showPage()

    def generate(self):
        self.page_1_cover()
        # 2페이지 목차 (생략 가능하나 구조상 추가)
        self.draw_layout(2, "CONTENTS")
        self.c.showPage()
        
        self.page_3_financial()
        
        # 4~113페이지: 케이에이치오토 샘플의 실제 전문 문구들 대입
        contents = {
            (4, 14): ["01. 기업재무분석 상세", "현금흐름등급 관리 및 재무지표 안정화 전략을 제시합니다.", "매출액 대비 매출원가 비중을 분석하여 수익성을 점검합니다."],
            (15, 23): ["02. 기업가치평가", "상증세법상 보충적 평가방법을 적용한 기업가치 산정 페이지입니다.", "현 시점의 주식가치를 파악하여 가업승계 전략을 수립합니다."],
            (24, 34): ["03. 임원소득보상플랜", "임원 급여 및 퇴직금 지급규정의 세무적 적정성을 검토합니다.", "정관 변경을 통한 법적 보호 장치 마련이 필요합니다."],
            (101, 113): ["11. 신용등급 및 경정청구", "KODATA 신용등급 개선 솔루션 및 경정청구 안내입니다.", "환급 예상액 확인 후 경정청구 프로세스를 진행합니다."]
        }
        
        for pg in range(4, 114):
            title, desc1, desc2 = "종합 컨설팅 솔루션", "데이터 기반 전문 분석 내용입니다.", ""
            for (s, e), text_list in contents.items():
                if s <= pg <= e:
                    title, desc1, desc2 = text_list[0], text_list[1], text_list[2] if len(text_list)>2 else ""
                    break
            
            self.draw_layout(pg, title)
            self.c.setFont(self.font, 18); self.c.drawString(60, self.h-100, f"▶ {title}")
            self.c.setFont(self.font, 11); self.c.drawString(70, self.h-160, desc1)
            self.c.drawString(70, self.h-185, desc2)
            self.c.drawString(70, self.h-210, f"대상기업: {self.data['company']} / 기준일: 2024년 12월 31일")
            self.c.showPage()
            
        self.c.save()
        self.buffer.seek(0)
        return self.buffer

def main():
    st.set_page_config(page_title="Pro Consulting Report", layout="wide")
    f = load_malgun()
    st.title("📑 (주)메이홈 전문 씨오리포트 생성기 (KH복제형)")
    
    files = st.file_uploader("모든 파일을 올려주세요", accept_multiple_files=True)
    if files and st.button("전문 113P 리포트 생성"):
        with st.spinner("메이홈 데이터를 읽어 113페이지 리포트를 제작 중입니다..."):
            res = extract_all_data(files)
            pdf = ReplicaReport(res, f).generate()
            st.download_button("📥 최종 리포트 다운로드", pdf, "CEO_Report_Mayhome_Final_v2.pdf", "application/pdf")

if __name__ == "__main__":
    main()
