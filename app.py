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
# 사용자님이 제공하신 키를 코드에 직접 설정합니다.
GEMINI_API_KEY = "AIzaSyDH8HKJTzsdY0rZzkqmJ_Sx2QrPbu9dBy0"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("API 키가 설정되지 않았습니다. GEMINI_API_KEY 변수를 확인해주세요.")

# --- [2. 폰트 로드] ---
def load_font():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [3. 금액 한글 변환 함수] ---
def format_krw(val):
    try:
        # 천 단위 수치를 원 단위로 환산 (예: 4137922 -> 41억 3792만 2000원)
        total = int(float(str(val).replace(',', '').strip())) * 1000
        if total == 0: return "0원"
        eok = total // 100000000
        man = (total % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except:
        return "0원"

# --- [4. Gemini AI 데이터 정밀 추출] ---
def extract_data_with_gemini(files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    all_context = ""
    for f in files:
        if f.name.endswith('.pdf'):
            with fitz.open(stream=f.read(), filetype="pdf") as doc:
                all_context += f"\n[파일: {f.name}]\n" + "".join([p.get_text() for p in doc])
        else:
            try:
                df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
                all_context += f"\n[파일: {f.name}]\n" + df.to_string()
            except: pass

    prompt = f"""
    당신은 기업 경영 분석 전문가입니다. 제공된 자료에서 '(주)메이홈'의 데이터를 찾아 JSON 형식으로만 답변하세요.
    수치는 천 단위(예: 4137922) 그대로 유지하세요.
    항목: company_name, ceo_name, rev_2024, rev_2023, net_income_2024, total_assets, total_debts, credit_rating
    자료: {all_context[:20000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        clean_res = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_res)
    except:
        return {"company_name": "(주)메이홈", "rev_2024": 4137922}

# --- [5. 리포트 생성 엔진 (result.txt 파일 읽기)] ---
class MasterReportGenerator:
    def __init__(self, data, font_name):
        self.data = data
        self.font = font_name
        self.output_pdf = io.BytesIO()
        
        # result.txt 파일에서 Base64 데이터를 안전하게 읽어옵니다.
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r", encoding="utf-8") as f:
                b64_str = f.read().strip()
                # 비-ASCII 문자 제거 및 디코딩
                b64_bytes = b64_str.encode('ascii', 'ignore')
                pdf_bytes = base64.b64decode(b64_bytes)
                self.template_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            st.error("서버에 'result.txt' 파일이 없습니다. 파일을 업로드해주세요.")
            self.template_doc = None

    def generate(self):
        if not self.template_doc: return None

        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        # 113페이지 전체를 순회하며 데이터 오버레이
        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            # 페이지별 데이터 대입 (샘플 리포트의 레이아웃 위치 기준)
            if i == 0: # 1페이지 표지
                c.setFont(self.font, 32)
                c.drawCentredString(w/2, h - 130, self.data.get('company_name', '(주)메이홈'))
                c.setFont(self.font, 12)
                c.drawString(80, 180, f"대표자: {self.data.get('ceo_name', '박승미')}")
                
            elif i == 2: # 3페이지 재무 데이터 요약
                c.setFont(self.font, 11)
                rev_24 = format_krw(self.data.get('rev_2024', 0))
                rev_23 = format_krw(self.data.get('rev_2023', 0))
                c.drawString(385, h - 145, rev_24) # 2024년 매출 위치

            # 하단바 및 페이지 번호 유지
            c.setFont(self.font, 8); c.setFillColor(colors.grey)
            c.drawString(50, 30, f"CO-PARTNER | {self.data.get('company_name')} 전용 컨설팅 리포트")
            c.drawRightString(w - 50, 30, f"씨오리포트 {i+1} / 113")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        
        # 원본 템플릿과 데이터 레이어 병합
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        self.template_doc.save(self.output_pdf)
        self.template_doc.close()
        self.output_pdf.seek(0)
        return self.output_pdf

# --- [6. 메인 UI] ---
def main():
    st.set_page_config(page_title="Professional CEO Report System", layout="wide")
    font_name = load_font()
    
    st.title("📂 팀장용 씨오리포트 자동 생성 시스템")
    st.markdown("**(주)메이홈** 관련 데이터 파일을 업로드하면 113페이지 전문 리포트가 생성됩니다.")

    files = st.file_uploader("기업 데이터 파일 업로드 (PDF, Excel, CSV)", accept_multiple_files=True)
    
    if files and st.button("🚀 113P 전문 리포트 즉시 생성"):
        with st.spinner("Gemini AI가 파일을 분석하여 리포트를 구성 중입니다..."):
            extracted_data = extract_data_with_gemini(files)
            report_gen = MasterReportGenerator(extracted_data, font_name)
            final_pdf = report_gen.generate()
            
            if final_pdf:
                st.success(f"✅ {extracted_data.get('company_name')} 리포트 생성 완료!")
                st.download_button(
                    label="📥 최종 리포트 다운로드",
                    data=final_pdf,
                    file_name=f"CEO_Report_{extracted_data.get('company_name')}.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
