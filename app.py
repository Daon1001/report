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

# --- [1. API 키 및 폰트 설정] ---
# 사용자님이 제공하신 API 키를 직접 설정
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

# --- [2. 수치 한글 변환 함수 (천원 -> 억/만 단위)] ---
def format_to_krw_text(val):
    try:
        clean_val = str(val).replace(',', '').strip()
        total_won = int(float(clean_val)) * 1000
        if total_won == 0: return "해당 없음"
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "0원"

# --- [3. Gemini AI: 파일 분석 및 실데이터 추출] ---
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
    당신은 전문 경영 분석가입니다. 아래 자료에서 '분석 대상 업체'의 정보를 찾아 JSON으로만 답변하세요.
    1. 업체명을 가장 먼저 식별하세요.
    2. 재무수치는 자료 속 천 단위 수치를 찾아 숫자로만 추출하세요 (예: 4137922).
    3. 사업내용은 자료를 근거로 구체적으로(예: PVC 창호 제조 등) 1줄 요약하세요.
    
    JSON 형식:
    {{
        "company": "업체명",
        "ceo": "대표자명",
        "biz_desc": "사업내용 요약",
        "rev_24": 2024매출액,
        "rev_23": 2023매출액,
        "income_24": 2024순이익,
        "asset_24": 2024자산총계,
        "debt_24": 2024부채총계
    }}
    자료: {all_context[:28000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"company": "분석 대상 기업", "biz_desc": "재무 진단 분석"}

# --- [4. 나노바나나 방식: 지능형 객체 삭제 및 치환 엔진] ---
class NanoBananaReportEngine:
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

        # 1. 낡은 데이터 '삭제' 작업 (나노바나나 방식)
        # 샘플 템플릿의 특정 영역을 깨끗이 밀어버립니다.
        for i, page in enumerate(self.template_doc):
            if i == 0: # 1페이지 표지 영역 삭제
                page.add_redact_annot(fitz.Rect(50, 100, 550, 250), fill=(1, 1, 1)) # 회사명/제목
                page.add_redact_annot(fitz.Rect(50, 150, 400, 220), fill=(1, 1, 1)) # 대표자/사업내용
            elif i == 2: # 3페이지 재무 데이터 영역 삭제
                page.add_redact_annot(fitz.Rect(200, 120, 550, 280), fill=(1, 1, 1)) 
            
            # 하단바 회사명 삭제
            for inst in page.search_for("주식회사 케이에이치오토"):
                page.add_redact_annot(inst, fill=(1, 1, 1))
            
            page.apply_redactions()

        # 2. 새로운 데이터 '주입' 작업 (치환)
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            if i == 0: # 표지 데이터 입히기
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('company'))
                c.setFont(self.font, 13); c.setFillColor(colors.black)
                c.drawString(80, 205, f"대표자: {self.data.get('ceo', '확인필요')}")
                c.drawString(80, 185, f"주요사업: {self.data.get('biz_desc')}")
                c.drawString(80, 165, "작성자: 중소기업경영지원단")

            elif i == 2: # 재무 수치 대입
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                c.drawString(385, h - 145, format_to_krw_text(self.data.get('rev_24')))
                c.drawString(235, h - 145, format_to_krw_text(self.data.get('rev_23')))
                c.drawString(385, h - 172, format_to_krw_text(self.data.get('income_24')))
                c.drawString(385, h - 198, format_to_krw_text(self.data.get('asset_24')))
                c.drawString(385, h - 225, format_to_krw_text(self.data.get('debt_24')))

            # 모든 페이지 하단에 현재 업체명 표시
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('company')}")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        self.template_doc.save(self.output_pdf)
        self.template_doc.close()
        self.output_pdf.seek(0)
        return self.output_pdf

# --- [5. UI 및 실행부] ---
def main():
    st.set_page_config(page_title="AI Master Report System", layout="wide")
    f_name = load_font()
    st.title("📂 지능형 범용 CEO 리포트 시스템 (나노바나나 방식)")
    
    st.write("샘플 양식(`result.txt`)을 기반으로, 업로드된 파일의 실데이터를 지능적으로 채워넣습니다.")

    files = st.file_uploader("기업 데이터 파일 업로드 (Excel, PDF)", accept_multiple_files=True)
    
    if files and st.button("🚀 리포트 생성"):
        with st.spinner("AI가 데이터를 분석하여 템플릿을 수정 중입니다..."):
            smart_data = extract_smart_data(files)
            engine = NanoBananaReportEngine(smart_data, f_name)
            final_pdf = engine.generate()
            
            if final_pdf:
                st.success(f"✅ {smart_data.get('company')} 리포트 생성 완료!")
                st.download_button("📥 리포트 다운로드", final_pdf, f"CEO_Report_{smart_data.get('company')}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
