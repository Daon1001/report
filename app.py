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

# --- [1. API 키 및 폰트 설정] ---
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

# --- [2. 수치 변환 함수 (천원 -> 억/만 단위)] ---
def format_to_krw_text(val):
    try:
        if not val: return "데이터 없음"
        clean_val = str(val).replace(',', '').strip()
        total_won = int(float(clean_val)) * 1000
        if total_won == 0: return "0원"
        eok, man = total_won // 100000000, (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "데이터 없음"

# --- [3. Gemini AI: 업로드된 파일에서 데이터 추출] ---
def extract_smart_data(files):
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
    당신은 기업 분석 전문가입니다. 업로드된 자료를 분석하여 리포트 템플릿에 채울 데이터를 JSON으로 답변하세요.
    - company_name: 업체명
    - ceo_name: 대표자 이름
    - biz_desc: 사업 내용 1줄 요약
    - rev_24, rev_23, income_24, asset_24, debt_24: 재무제표 천 단위 수치 그대로
    자료내용: {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return {"company_name": "분석 대상 기업", "biz_desc": "재무 경영 진단"}

# --- [4. 구조적 치환 엔진: 템플릿의 슬롯만 교체] ---
class StructuralMappingEngine:
    def __init__(self, data, font_name):
        self.data, self.font = data, font_name
        self.output_pdf = io.BytesIO()
        
        # result.txt 파일을 직접 읽어 인코딩 오류 방지
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r", encoding="utf-8") as f:
                b64_content = f.read().strip()
                # 텍스트 내 비ASCII 문자 제거 후 디코딩
                clean_b64 = re.sub(r'[^a-zA-Z0-9+/=]', '', b64_content)
                pdf_bytes = base64.b64decode(clean_b64)
                self.doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else: self.doc = None

    def process(self):
        if not self.doc: return None
        
        # 1. '슬롯 삭제': 데이터가 들어갈 위치를 깨끗이 비움
        for i, page in enumerate(self.doc):
            if i == 0: # 1P 표지 슬롯 (회사명, 대표자 등)
                page.add_redact_annot(fitz.Rect(50, 100, 550, 250), fill=(1, 1, 1))
                page.add_redact_annot(fitz.Rect(50, 150, 400, 220), fill=(1, 1, 1))
            elif i == 2: # 3P 재무표 슬롯 (숫자 칸)
                page.add_redact_annot(fitz.Rect(200, 120, 550, 280), fill=(1, 1, 1))
            
            # 하단 공통 회사명 삭제
            for inst in page.search_for("주식회사 케이에이치오토"):
                page.add_redact_annot(inst, fill=(1, 1, 1))
            page.apply_redactions()

        # 2. '데이터 주입': 비워진 슬롯에 실데이터 채우기
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.doc)):
            c.setFont(self.font, 10)
            if i == 0: # 표지 데이터
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('company_name'))
                c.setFont(self.font, 13); c.setFillColor(colors.black)
                c.drawString(100, 205, f"대표자: {self.data.get('ceo_name', '확인필요')}")
                c.drawString(100, 185, f"주요사업: {self.data.get('biz_desc')}")
                c.drawString(100, 165, "작성자: 중소기업경영지원단")
            elif i == 2: # 재무 데이터
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                c.drawString(385, h - 145, format_to_krw_text(self.data.get('rev_24')))
                c.drawString(235, h - 145, format_to_krw_text(self.data.get('rev_23')))
                c.drawString(385, h - 172, format_to_krw_text(self.data.get('income_24')))
            
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('company_name')}")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_pdf = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        for i in range(len(self.doc)):
            self.doc[i].show_pdf_page(self.doc[i].rect, overlay_pdf, i)
        
        # 3. 결과 반환
        final_buffer = io.BytesIO()
        self.doc.save(final_buffer)
        self.doc.close()
        final_buffer.seek(0)
        return final_buffer

# --- [5. 앱 실행 화면] ---
def main():
    st.set_page_config(page_title="AI Master Report System", layout="wide")
    f_name = load_font()
    st.title("📂 지능형 범용 CEO 리포트 시스템")
    st.write("샘플 양식(`result.txt`)의 113페이지 구조에 업로드된 실데이터를 채워넣습니다.")

    files = st.file_uploader("데이터 파일 업로드", accept_multiple_files=True)
    
    if files:
        if st.button("🚀 리포트 생성 및 데이터 치환"):
            with st.spinner("AI가 데이터를 분석하여 리포트 슬롯을 채우는 중..."):
                data = extract_smart_data(files)
                engine = StructuralMappingEngine(data, f_name)
                final_pdf = engine.process()
                
                if final_pdf:
                    st.session_state['pdf_ready'] = final_pdf
                    st.session_state['target_company'] = data.get('company_name')
                    st.success(f"✅ {data.get('company_name')} 리포트 생성 완료!")

    if 'pdf_ready' in st.session_state:
        st.download_button(
            label="📥 최종 리포트 다운로드",
            data=st.session_state['pdf_ready'],
            file_name=f"CEO_Report_{st.session_state['target_company']}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
