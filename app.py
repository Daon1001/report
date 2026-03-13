import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import os
import base64
import fitz  # PyMuPDF
import json
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# --- [1. 설정 및 폰트] ---
GEMINI_API_KEY = "AIzaSyDH8HKJTzsdY0rZzkqmJ_Sx2QrPbu9dBy0"
genai.configure(api_key=GEMINI_API_KEY)

def load_font():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. 수치 변환 함수] ---
def to_krw_text(val):
    try:
        if not val or val == 0: return "데이터 없음"
        clean_val = str(val).replace(',', '').strip()
        total_won = int(float(clean_val)) * 1000
        eok, man = total_won // 100000000, (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원" if res else "0원"
    except: return "데이터 없음"

# --- [3. Gemini AI: 업체 식별 및 데이터 추출] ---
def extract_company_data(files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    all_context = ""
    for f in files:
        if f.name.endswith('.pdf'):
            with fitz.open(stream=f.read(), filetype="pdf") as doc:
                all_context += "".join([p.get_text() for p in doc])
        else:
            try:
                df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
                all_context += df.to_string()
            except: pass

    prompt = f"""
    당신은 경영 분석 전문가입니다. 업로드된 자료를 분석하여 리포트 대상 업체의 정보를 JSON으로 답변하세요.
    - target_company: 업체명
    - ceo_name: 대표자 이름
    - biz_summary: 사업 내용 1줄 요약
    - rev_24, rev_23, income_24, asset_24, debt_24: 재무제표 천 단위 수치 그대로
    자료내용: {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return {"target_company": "분석 대상 기업", "biz_summary": "재무 분석"}

# --- [4. 나노바나나 엔진: 삭제 후 주입] ---
class NanoBananaEngine:
    def __init__(self, data, font_name):
        self.data, self.font = data, font_name
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r", encoding="utf-8") as f:
                b64 = f.read().strip()
                pdf_bytes = base64.b64decode(b64.encode('ascii', 'ignore'))
                self.doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else: self.doc = None

    def process(self):
        if not self.doc: return None
        
        # 1. 낡은 객체 삭제 (나노바나나)
        for i, page in enumerate(self.doc):
            # 텍스트 기반 삭제
            for t in ["주식회사 케이에이치오토", "케이에이치오토", "임원근", "0원"]:
                for inst in page.search_for(t):
                    page.add_redact_annot(inst, fill=(1, 1, 1))
            # 영역 기반 강제 삭제
            if i == 0:
                page.add_redact_annot(fitz.Rect(50, 100, 550, 250), fill=(1, 1, 1))
                page.add_redact_annot(fitz.Rect(50, 150, 400, 220), fill=(1, 1, 1))
            elif i == 2:
                page.add_redact_annot(fitz.Rect(200, 120, 550, 280), fill=(1, 1, 1))
            page.apply_redactions()

        # 2. 새 데이터 주입
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4
        for i in range(len(self.doc)):
            if i == 0:
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('target_company'))
                c.setFont(self.font, 13); c.setFillColor(colors.black)
                c.drawString(100, 205, f"대표자: {self.data.get('ceo_name', '확인필요')}")
                c.drawString(100, 185, f"주요사업: {self.data.get('biz_summary')}")
            elif i == 2:
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                c.drawString(385, h - 145, to_krw_text(self.data.get('rev_24')))
                c.drawString(235, h - 145, to_krw_text(self.data.get('rev_23')))
                c.drawString(385, h - 172, to_krw_text(self.data.get('income_24')))
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('target_company')}")
            c.showPage()
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        for i in range(len(self.doc)):
            self.doc[i].show_pdf_page(self.doc[i].rect, overlay_doc, i)
        
        final_buffer = io.BytesIO()
        self.doc.save(final_buffer)
        self.doc.close()
        final_buffer.seek(0)
        return final_buffer

# --- [5. 실행 UI] ---
def main():
    st.set_page_config(page_title="Universal CEO Report", layout="wide")
    f_name = load_font()
    st.title("📂 지능형 범용 CEO 리포트 생성기")

    files = st.file_uploader("기업 데이터 업로드", accept_multiple_files=True)
    
    if files:
        if st.button("🚀 리포트 생성"):
            with st.spinner("AI 분석 및 치환 중..."):
                data = extract_company_data(files)
                engine = NanoBananaEngine(data, f_name)
                final_pdf = engine.process()
                if final_pdf:
                    st.session_state['pdf_buffer'] = final_pdf
                    st.session_state['company_name'] = data.get('target_company')
                    st.success(f"✅ {data.get('target_company')} 리포트 생성 완료!")

    if 'pdf_buffer' in st.session_state:
        st.download_button(
            label="📥 최종 리포트 다운로드",
            data=st.session_state['pdf_buffer'],
            file_name=f"CEO_Report_{st.session_state['company_name']}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
