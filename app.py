import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import os
import base64
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# --- [1. Gemini API 설정] ---
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
else:
    # 예비용 직접 입력 (Secrets 미설정 시)
    genai.configure(api_key="AIzaSyDH8HKJTzsdY0rZzkqmJ_Sx2QrPbu9dBy0")

def load_font():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. 수치 한글 변환 함수] ---
def format_to_krw_text(val):
    try:
        clean_val = str(val).replace(',', '').strip()
        total_won = int(float(clean_val)) * 1000
        if total_won == 0: return "0원"
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "0원"

# --- [3. Gemini AI: 범용 업체 정보 및 수치 추출] ---
def extract_universal_data(files):
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
    당신은 전문 경영 분석가입니다. 제공된 자료에서 분석 대상 업체(메이홈 또는 다른 모든 기업)의 정보를 찾아 JSON으로만 답변하세요.
    - target_company: 업체명
    - ceo_name: 대표자 이름
    - biz_summary: 회사가 하는 일(예: PVC 창호 제조 등)을 문서 내용을 근거로 요약
    - rev_24, rev_23, income_24, asset_24, debt_24: 재무제표의 '천 단위' 수치 그대로 추출
    
    자료내용:
    {all_context[:28000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"target_company": "분석 대상 기업", "biz_summary": "재무 분석 및 경영 진단"}

# --- [4. 나노바나나 방식: 객체 제거 및 지능형 치환 엔진] ---
class SmartObjectEraserEngine:
    def __init__(self, data, font_name):
        self.data = data
        self.font = font_name
        self.output_pdf = io.BytesIO()
        
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r", encoding="utf-8") as f:
                b64_str = f.read().strip()
                pdf_bytes = base64.b64decode(b64_str.encode('ascii', 'ignore'))
                self.template_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            self.template_doc = None

    def generate(self):
        if not self.template_doc:
            return None

        # 1. 원본 샘플 데이터 삭제 (Redaction)
        # 나노바나나 기능처럼 기존의 불필요한 객체(글자)를 완전히 제거합니다.
        for page in self.template_doc:
            targets = ["주식회사 케이에이치오토", "케이에이치오토", "임원근", "0원", "재무 진단 분석"]
            for target in targets:
                insts = page.search_for(target)
                for inst in insts:
                    # 해당 영역을 PDF 구조상에서 완전히 삭제(흰색 소거)
                    page.add_redact_annot(inst, fill=(1, 1, 1))
            page.apply_redactions()

        # 2. 제거된 자리에 제미나이가 추출한 실데이터 주입
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            # [1페이지: 표지 및 개요 치환]
            if i == 0:
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('target_company'))
                c.setFont(self.font, 14); c.setFillColor(colors.black)
                c.drawString(100, 205, f"대표자: {self.data.get('ceo_name', '확인 필요')}")
                c.drawString(100, 180, f"주요사업: {self.data.get('biz_summary')}")
                c.drawString(100, 160, "작성자: 중소기업경영지원단")

            # [3페이지: 재무 지표 정밀 치환]
            elif i == 2:
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                # 제미나이가 뽑아온 실데이터를 억/만 단위로 변환해 삽입
                c.drawString(385, h - 145, format_to_krw_text(self.data.get('rev_24'))) # 당기매출
                c.drawString(235, h - 145, format_to_krw_text(self.data.get('rev_23'))) # 전기매출
                c.drawString(385, h - 172, format_to_krw_text(self.data.get('income_24'))) # 순이익
                c.drawString(385, h - 198, format_to_krw_text(self.data.get('asset_24')))  # 자산
                c.drawString(385, h - 225, format_to_krw_text(self.data.get('debt_24')))   # 부채

            # 하단 공통 회사명 업데이트
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('target_company')}")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        # 3. 레이어 병합
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        self.template_doc.save(self.output_pdf)
        self.template_doc.close()
        self.output_pdf.seek(0)
        return self.output_pdf

# --- [5. UI 메인] ---
def main():
    st.set_page_config(page_title="AI Master Report System", layout="wide")
    f_name = load_font()
    st.title("📂 지능형 범용 CEO 리포트 생성기")
    
    st.markdown("""
    분석하려는 **어떤 기업의 파일(엑셀, PDF)**이라도 업로드하세요. 
    제미나이 AI가 파일을 읽어 업체를 식별하고, 샘플의 낡은 정보를 제거한 뒤 실데이터로 채워넣습니다.
    """)

    files = st.file_uploader("기업 데이터 파일 업로드 (Excel, PDF 등)", accept_multiple_files=True)
    
    if files and st.button("🚀 지능형 리포트 생성 시작"):
        with st.spinner("AI가 파일의 맥락을 분석하고 데이터를 치환하는 중입니다..."):
            # 1. 제미나이를 통한 동적 데이터 추출
            extracted_data = extract_universal_data(files)
            # 2. 객체 제거 및 데이터 주입 엔진 가동
            engine = SmartObjectEraserEngine(extracted_data, f_name)
            final_pdf = engine.generate()
            
            if final_pdf:
                st.success(f"✅ {extracted_data.get('target_company')} 리포트 생성이 완료되었습니다!")
                st.download_button("📥 최종 리포트 다운로드", final_pdf, f"CEO_Report_{extracted_data.get('target_company')}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
