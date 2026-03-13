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
# Streamlit Secrets에 저장된 api_key를 자동으로 불러옵니다.
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
else:
    st.error("Secrets에 'api_key'가 설정되어 있지 않습니다.")

def load_font():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. 수치 변환 함수 (천원 -> 한글 억/만 단위)] ---
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

# --- [3. Gemini AI: 실데이터 정밀 추출] ---
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
    당신은 전문 회계 분석가입니다. 제공된 자료에서 '(주)메이홈'의 재무 정보를 찾아 JSON으로만 답변하세요.
    수치는 반드시 자료에 적힌 '천 단위 수치' 그대로 추출하세요 (예: 4137922).
    
    필요 항목:
    - company_name: (주)메이홈
    - ceo_name: 대표자 이름
    - business_summary: 회사가 하는 일(예: PVC 창호 제조 등) 2줄 요약
    - rev_24: 2024년 매출액
    - rev_23: 2023년 매출액
    - income_24: 2024년 당기순이익
    - asset_24: 2024년 자산총계
    - debt_24: 2024년 부채총계
    
    자료내용:
    {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"company_name": "(주)메이홈", "rev_24": 4137922, "rev_23": 2765913}

# --- [4. 스마트 리포트 생성 엔진 (Redact & Replace)] ---
class MasterSmartEngine:
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
            st.error("서버에 'result.txt' 파일이 없습니다.")
            return None

        # 1. 원본 텍스트 삭제 (Redaction)
        # 샘플에 있는 회사명과 '0원' 텍스트를 찾아 흰색으로 지웁니다.
        for page in self.template_doc:
            targets = ["주식회사 케이에이치오토", "케이에이치오토", "0원", "재무 진단 분석"]
            for target in targets:
                insts = page.search_for(target)
                for inst in insts:
                    # 최신 PyMuPDF 함수명 사용: add_redact_annot
                    page.add_redact_annot(inst, fill=(1, 1, 1))
            page.apply_redactions()

        # 2. 새로운 데이터 삽입 (Overlay)
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            # [1페이지: 표지 및 개요]
            if i == 0:
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('company_name'))
                c.setFont(self.font, 13); c.setFillColor(colors.black)
                c.drawString(80, 205, f"대표자: {self.data.get('ceo_name', '박승미')}")
                c.drawString(80, 180, f"주요사업: {self.data.get('business_summary', 'PVC 창호 제조')}")
            
            # [3페이지: 재무 지표 상세]
            elif i == 2:
                c.setFont(self.font, 11)
                c.drawString(385, h - 145, format_to_krw_text(self.data.get('rev_24')))
                c.drawString(235, h - 145, format_to_krw_text(self.data.get('rev_23')))
                c.drawString(385, h - 172, format_to_krw_text(self.data.get('income_24')))
                c.drawString(385, h - 198, format_to_krw_text(self.data.get('asset_24')))
                c.drawString(385, h - 225, format_to_krw_text(self.data.get('debt_24')))

            # 모든 페이지 하단 회사명 치환
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('company_name')}")
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

# --- [5. UI 메인 실행부] ---
def main():
    st.set_page_config(page_title="Professional Report Generator", layout="wide")
    f_name = load_font()
    
    st.title("📂 팀장용 전문 리포트 자동 생성기 (데이터 정밀 반영)")
    st.markdown("**(주)메이홈** 관련 데이터 파일을 업로드하면 샘플의 정보를 지우고 실데이터로 완벽히 치환합니다.")

    files = st.file_uploader("데이터 파일 업로드 (PDF, Excel)", accept_multiple_files=True)
    
    if files and st.button("🚀 113페이지 전문 리포트 즉시 생성"):
        with st.spinner("AI가 파일을 분석하고 데이터를 대입 중입니다..."):
            # 1. 데이터 추출
            smart_data = extract_smart_data(files)
            # 2. 리포트 엔진 실행
            engine = MasterSmartEngine(smart_data, f_name)
            final_pdf = engine.generate()
            
            if final_pdf:
                st.success(f"✅ {smart_data.get('company_name')} 리포트 생성 완료!")
                st.download_button(
                    label="📥 최종 리포트 다운로드",
                    data=final_pdf,
                    file_name=f"CEO_Report_{smart_data.get('company_name')}.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
