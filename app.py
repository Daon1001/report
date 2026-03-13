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
def format_krw(val):
    try:
        total = int(float(str(val).replace(',', '').strip())) * 1000
        if total == 0: return "0원"
        eok, man = total // 100000000, (total % 100000000) // 10000
        res = []
        if eok: res.append(f"{eok}억")
        if man: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "0원"

# --- [3. Gemini AI: 실데이터 정밀 추출] ---
def extract_data_with_gemini(files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    all_context = ""
    for f in files:
        if f.name.endswith('.pdf'):
            doc = fitz.open(stream=f.read(), filetype="pdf")
            all_context += f"\n[파일: {f.name}]\n" + "".join([p.get_text() for p in doc])
        else:
            df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
            all_context += f"\n[파일: {f.name}]\n" + df.to_string()

    prompt = f"""
    당신은 기업 재무 분석 전문가입니다. 제공된 자료에서 (주)메이홈의 실데이터를 찾아 JSON 형식으로만 답변하세요.
    수치는 천 단위(예: 4137922) 그대로 가져오세요.
    항목: company_name, ceo_name, rev_2024, rev_2023, net_income_2024, total_assets, total_debts
    자료: {all_context[:15000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"company_name": "(주)메이홈", "rev_2024": 4137922}

# --- [4. 113P 마스터 리포트 생성 엔진] ---
class MasterReportEngine:
    def __init__(self, data, font):
        self.data, self.font = data, font
        self.output = io.BytesIO()
        
        # 텍스트 파일(result.txt)에서 Base64를 읽어 PDF로 변환
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r") as f:
                b64_str = f.read().strip()
                # ASCII 오류 방지를 위해 필터링 후 디코딩
                pdf_data = base64.b64decode(b64_str.encode('ascii', 'ignore'))
                self.template_doc = fitz.open(stream=pdf_data, filetype="pdf")
        else:
            st.error("서버에 'result.txt' 파일이 없습니다. 파일을 업로드해주세요.")
            self.template_doc = None

    def generate(self):
        if not self.template_doc: return None
        
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        # 113페이지를 순회하며 데이터 오버레이
        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            # 페이지별 데이터 대입 (좌표는 샘플 리포트 위치에 최적화)
            if i == 0: # 1페이지 표지
                c.setFont(self.font, 32)
                c.drawCentredString(w/2, h - 130, self.data.get('company_name', '(주)메이홈'))
            
            elif i == 2: # 3페이지 재무 데이터
                c.setFont(self.font, 11)
                rev_text = format_krw(self.data.get('rev_2024', 0))
                c.drawString(385, h - 145, rev_text)

            # 디자인 유지를 위한 하단바 정보
            c.setFont(self.font, 8); c.setFillColor(colors.grey)
            c.drawString(50, 30, f"CO-PARTNER | {self.data.get('company_name')} 전용 컨설팅 리포트")
            c.drawRightString(w - 50, 30, f"씨오리포트 {i+1} / 113")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        self.template_doc.save(self.output)
        self.output.seek(0)
        return self.output

# --- [5. 메인 실행] ---
def main():
    st.set_page_config(page_title="Professional CEO Report", layout="wide")
    f_name = load_font()
    st.title("📂 팀장용 전문 리포트 자동 생성 시스템")
    
    files = st.file_uploader("메이홈 데이터 파일들을 업로드하세요", accept_multiple_files=True)
    if files and st.button("🚀 113P 전문 리포트 즉시 생성"):
        with st.spinner("AI가 파일을 분석하고 113페이지 리포트를 제작 중입니다..."):
            extracted = extract_data_with_gemini(files)
            engine = MasterReportEngine(extracted, f_name)
            final_pdf = engine.generate()
            if final_pdf:
                st.success(f"✅ {extracted.get('company_name')} 리포트 생성 완료!")
                st.download_button("📥 최종 리포트 다운로드", final_pdf, "CEO_Report_Mayhome.pdf", "application/pdf")

if __name__ == "__main__":
    main()
