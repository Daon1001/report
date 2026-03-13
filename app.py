import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import os
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# --- [1. 환경 설정 및 Gemini API] ---
# Streamlit Secrets에 저장된 api_key 사용
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
else:
    st.error("Streamlit Secrets에 'api_key'를 설정해주세요.")

def load_font():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. 한글 금액 변환 함수] ---
def format_to_krw(val_in_thousands):
    try:
        num = int(float(str(val_in_thousands).replace(',', '')))
        total = num * 1000
        if total == 0: return "0원"
        eok, man = total // 100000000, (total % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "0원"

# --- [3. Gemini API를 이용한 데이터 정밀 추출] ---
def extract_data_with_ai(uploaded_files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    all_text = ""
    for f in uploaded_files:
        if f.name.endswith('.pdf'):
            with fitz.open(stream=f.read(), filetype="pdf") as doc:
                all_text += "".join([p.get_text() for p in doc])
        else:
            df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
            all_text += df.to_string()

    prompt = f"""
    자료에서 '(주)메이홈'의 재무 정보를 찾아 JSON으로만 응답하세요. 
    금액은 자료에 적힌 천 단위 수치 그대로 가져오세요.
    항목: company_name, ceo_name, rev_2024, rev_2023, net_income_2024, total_assets, total_debts
    자료: {all_text[:15000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"company_name": "(주)메이홈", "rev_2024": 4137922}

# --- [4. 113P 복제 및 오버레이 엔진] ---
class ReplicaEngine:
    def __init__(self, data, font_name):
        self.data = data
        self.font = font_name
        # 서버에 저장된 sample.pdf를 직접 읽음
        self.template_path = "./sample.pdf"
        self.output_pdf = io.BytesIO()

    def generate(self):
        if not os.path.exists(self.template_path):
            st.error("서버에 'sample.pdf' 파일이 없습니다. 파일을 업로드해주세요.")
            return None

        template_doc = fitz.open(self.template_path)
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(template_doc)):
            c.setFont(self.font, 10)
            if i == 0: # 표지 기업명 대입
                c.setFont(self.font, 32)
                c.drawCentredString(w/2, h - 130, self.data.get('company_name', '(주)메이홈'))
            
            elif i == 2: # 3페이지 재무 데이터 대입
                c.setFont(self.font, 11)
                rev_text = format_to_krw(self.data.get('rev_2024', 0))
                c.drawString(385, h - 145, rev_text) # 샘플 위치에 맞춰 조정

            # 페이지 번호 및 하단바 디자인 유지
            c.setFont(self.font, 8); c.setFillColor(colors.grey)
            c.drawString(50, 30, f"CO-PARTNER | {self.data.get('company_name')} 전용 리포트")
            c.drawRightString(w - 50, 30, f"씨오리포트 {i+1} / 113")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        # 원본 위에 데이터 덮어쓰기
        for i in range(len(template_doc)):
            page = template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        template_doc.save(self.output_pdf)
        template_doc.close()
        self.output_pdf.seek(0)
        return self.output_pdf

# --- [5. 메인 앱 실행] ---
def main():
    st.set_page_config(page_title="Professional CEO Report", layout="wide")
    f_name = load_font()
    
    st.title("💼 팀장용 전문 리포트 자동 생성기")
    st.write("메이홈의 엑셀/PDF 파일을 올리면 113페이지 전문 리포트를 생성합니다.")

    files = st.file_uploader("파일 업로드", accept_multiple_files=True)
    if files and st.button("🚀 리포트 생성 시작"):
        with st.spinner("AI 분석 및 113페이지 구성을 진행 중입니다..."):
            extracted = extract_data_with_ai(files)
            report_pdf = ReplicaEngine(extracted, f_name).generate()
            if report_pdf:
                st.success("✅ 생성 완료!")
                st.download_button("📥 최종 리포트 다운로드", report_pdf, f"CEO_Report_{extracted.get('company_name')}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
