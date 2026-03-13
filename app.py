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

# --- [1. Gemini API 및 폰트 설정] ---
# Streamlit Secrets에서 api_key를 가져옵니다.
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
else:
    # 예비용으로 직접 입력된 키를 사용합니다.
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

# --- [3. Gemini AI: 업로드된 파일에서 지능형 데이터 추출] ---
def extract_intelligent_data(files):
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

    # 제미나이에게 업로드된 파일의 주체를 파악하고 데이터를 뽑으라고 명령합니다.
    prompt = f"""
    당신은 전문 경영 컨설턴트입니다. 제공된 자료를 분석하여 리포트의 주인공이 되는 '대상 업체'의 정보를 JSON으로만 답변하세요.
    - target_company: 분석 대상 업체명 (예: (주)메이홈 등 자료에서 식별된 이름)
    - ceo_name: 해당 업체의 대표자 이름
    - biz_desc: 이 회사의 주요 사업 내용을 자료를 바탕으로 1~2줄 요약
    - rev_24, rev_23, income_24, asset_24, debt_24: 재무제표의 '천 단위' 수치를 정확히 찾아 숫자로만 추출
    
    자료내용:
    {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"target_company": "추출 실패", "biz_desc": "자료 분석 불가"}

# --- [4. 나노바나나 방식: 객체 제거 및 실데이터 주입 엔진] ---
class IntelligentObjectEraser:
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

        # 1. 객체 제거(Redaction) 단계: 샘플의 낡은 텍스트 영역을 좌표 단위로 삭제
        for i, page in enumerate(self.template_doc):
            # 텍스트 검색을 통한 삭제 (케이에이치오토, 0원 등)
            targets = ["주식회사 케이에이치오토", "케이에이치오토", "0원", "재무 진단 분석", "임원근"]
            for target in targets:
                insts = page.search_for(target)
                for inst in insts:
                    page.add_redact_annot(inst, fill=(1, 1, 1))
            
            # 검색이 안 될 경우를 대비해 핵심 좌표 영역 강제 소거 (나노바나나 방식)
            if i == 0: # 1페이지 표지 영역
                page.add_redact_annot(fitz.Rect(50, 100, 550, 250), fill=(1, 1, 1)) # 타이틀/회사명
                page.add_redact_annot(fitz.Rect(50, 600, 400, 800), fill=(1, 1, 1)) # 대표자/사업개요
            elif i == 2: # 3페이지 재무 데이터 영역
                page.add_redact_annot(fitz.Rect(200, 100, 550, 300), fill=(1, 1, 1)) # 숫자 칸들
                
            page.apply_redactions()

        # 2. 실데이터 주입(Injection) 단계: 제미나이가 가져온 정보를 삽입
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            # [1페이지: 표지 및 동적 개요]
            if i == 0:
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('target_company', '분석 기업'))
                c.setFont(self.font, 13); c.setFillColor(colors.black)
                c.drawString(100, 205, f"대표자: {self.data.get('ceo_name', '확인 필요')}")
                c.drawString(100, 180, f"주요사업: {self.data.get('biz_desc', '재무 경영 진단')}")
                c.drawString(100, 160, "작성자: 중소기업경영지원단")

            # [3페이지: 주요 재무 수치 주입]
            elif i == 2:
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                # 제미나이가 추출한 숫자를 정확한 자리에 한글 단위로 변환해 삽입
                c.drawString(385, h - 145, format_to_krw_text(self.data.get('rev_24', 0)))
                c.drawString(235, h - 145, format_to_krw_text(self.data.get('rev_23', 0)))
                c.drawString(385, h - 172, format_to_krw_text(self.data.get('income_24', 0)))
                c.drawString(385, h - 198, format_to_krw_text(self.data.get('asset_24', 0)))
                c.drawString(385, h - 225, format_to_krw_text(self.data.get('debt_24', 0)))

            # 모든 페이지 하단 회사명 업데이트
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('target_company')}")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        # 3. 병합
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        self.template_doc.save(self.output_pdf)
        self.template_doc.close()
        self.output_pdf.seek(0)
        return self.output_pdf

# --- [5. UI 및 실행] ---
def main():
    st.set_page_config(page_title="AI Master Report System", layout="wide")
    f_name = load_font()
    st.title("📂 지능형 CEO 리포트 자동 생성기 (범용 치환형)")
    
    st.markdown("""
    업로드된 파일에서 **제미나이 AI가 스스로 정보를 추출**하여 리포트를 완성합니다.
    샘플의 낡은 정보는 완전히 제거(나노바나나 방식)되고 실데이터로 치환됩니다.
    """)

    files = st.file_uploader("기업 데이터 파일 업로드 (PDF, Excel)", accept_multiple_files=True)
    
    if files and st.button("🚀 지능형 리포트 생성 시작"):
        with st.spinner("AI가 파일을 읽고 데이터를 '삭제 및 주입' 중입니다..."):
            # 1. Gemini를 통한 업체 식별 및 데이터 추출
            extracted_data = extract_intelligent_data(files)
            # 2. 리포트 엔진 가동
            engine = IntelligentObjectEraser(extracted_data, f_name)
            final_pdf = engine.generate()
            
            if final_pdf:
                st.success(f"✅ {extracted_data.get('target_company')} 리포트 생성이 완료되었습니다!")
                st.download_button("📥 최종 리포트 다운로드", final_pdf, f"CEO_Report_{extracted_data.get('target_company')}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
