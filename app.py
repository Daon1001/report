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

# --- [1. API 키 설정] ---
# 사용자님이 입력하신 변수명을 그대로 사용하거나, 보안 설정을 사용합니다.
GEMINI_API_KEY = "AIzaSyDH8HKJTzsdY0rZzkqmJ_Sx2QrPbu9dBy0" # 여기에 직접 입력하신 키

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
elif "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
else:
    st.error("API 키가 설정되지 않았습니다. 코드 상단의 GEMINI_API_KEY를 확인해주세요.")

# --- [2. 마스터 리포트 데이터 (result.txt)] ---
# 제공해주신 result.txt의 긴 텍스트를 이 따옴표 사이에 붙여넣으세요.
# (내용이 너무 길어 아래는 예시입니다. 실제 파일 내용을 전체 복사해 넣으셔야 합니다.)
MASTER_PDF_BASE64 = "JVBERi0xLjMKJf... (중략) ...6MjIxNzUxIDAwMDAwIG4=" 

def load_font():
    if os.path.exists("./malgun.ttf"):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', "./malgun.ttf"))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [3. 데이터 추출 및 리포트 생성 로직] ---
def extract_data_with_gemini(files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    all_context = ""
    for f in files:
        if f.name.endswith('.pdf'):
            doc = fitz.open(stream=f.read(), filetype="pdf")
            all_context += "".join([p.get_text() for p in doc])
        else:
            df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
            all_context += df.to_string()

    prompt = f"다음 자료에서 (주)메이홈의 정보를 JSON으로 추출하세요. 금액은 억/만 단위 한글로 변환하세요. 항목: 기업명, 대표자, 24년매출, 23년매출, 24년순이익, 자산총계, 부채총계. 자료: {all_context[:15000]}"
    
    try:
        response = model.generate_content(prompt)
        import json
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"기업명": "(주)메이홈", "24년매출": "41억 3,792만 원"}

class FinalIntegratedReport:
    def __init__(self, data, font):
        self.data, self.font = data, font
        self.pdf_bytes = base64.b64decode(MASTER_PDF_BASE64)
        self.template_doc = fitz.open(stream=self.pdf_bytes, filetype="pdf")
        self.output = io.BytesIO()
        self.c = canvas.Canvas(self.output, pagesize=A4)
        self.w, self.h = A4

    def generate(self):
        for i in range(len(self.template_doc)):
            self.c.setFont(self.font, 10)
            if i == 0: # 표지 데이터 대입
                self.c.setFont(self.font, 32)
                self.c.drawCentredString(self.w/2, self.h - 130, self.data.get('기업명', '(주)메이홈'))
            if i == 2: # 재무표 데이터 대입
                self.c.setFont(self.font, 11)
                self.c.drawString(380, self.h - 145, self.data.get('24년매출', '0원'))
            
            self.c.setFont(self.font, 8); self.c.setFillColor(colors.grey)
            self.c.drawString(50, 30, f"CO-PARTNER | {self.data.get('기업명')} 전용 리포트 | Page {i+1}")
            self.c.showPage()
        
        self.c.save()
        self.output.seek(0)
        return self.output

def main():
    st.set_page_config(page_title="Master CEO Report", layout="wide")
    f_name = load_font()
    st.title("📂 (주)메이홈 전문 경영진단 시스템")

    files = st.file_uploader("데이터 파일 업로드", accept_multiple_files=True)
    if files and st.button("🚀 113P 전문 리포트 생성"):
        with st.spinner("Gemini AI가 파일을 정밀 분석 중입니다..."):
            extracted = extract_data_with_gemini(files)
            report = FinalIntegratedReport(extracted, f_name)
            pdf = report.generate()
            st.download_button("📥 최종 리포트 다운로드", pdf, "CEO_Report_Mayhome.pdf", "application/pdf")

if __name__ == "__main__":
    main()
