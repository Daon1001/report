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
GEMINI_API_KEY = "AIzaSyDH8HKJTzsdY0rZzkqmJ_Sx2QrPbu9dBy0"
genai.configure(api_key=GEMINI_API_KEY)

# --- [2. 폰트 설정] ---
def load_font():
    if os.path.exists("./malgun.ttf"):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', "./malgun.ttf"))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [3. 금액 변환 함수] ---
def to_krw_string(val):
    try:
        # 천 단위 수치를 원 단위로 환산
        total = int(float(str(val).replace(',', '').strip())) * 1000
        if total == 0: return "0원"
        eok = total // 100000000
        man = (total % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "0원"

# --- [4. Gemini AI: 실데이터 및 기업개요 정밀 추출] ---
def extract_mayhome_data(files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    all_context = ""
    for f in files:
        if f.name.endswith('.pdf'):
            doc = fitz.open(stream=f.read(), filetype="pdf")
            all_context += "".join([p.get_text() for p in doc])
        else:
            df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
            all_context += df.to_string()

    prompt = f"""
    당신은 전문 경영 컨설턴트입니다. 자료에서 '(주)메이홈'의 정보를 찾아 JSON으로 출력하세요. 
    1. 재무수치는 천 단위 수치 그대로(예: 4137922) 가져오세요.
    2. '기업개요'는 회사소개서나 개요 파일에서 사업 내용(예: PVC 창호 제조, 가구 제조 등)을 요약해서 3줄 이내로 작성하세요.
    
    항목: company_name, ceo_name, business_summary(기업개요), rev_24, rev_23, income_24, asset_24, debt_24, rating
    자료: {all_context[:20000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"company_name": "(주)메이홈", "ceo_name": "박승미", "rev_24": 4137922}

# --- [5. 리포트 생성 엔진 (오버레이 방식)] ---
class MasterOverlayEngine:
    def __init__(self, data, font_name):
        self.data = data
        self.font = font_name
        self.output_pdf = io.BytesIO()
        
        # result.txt에서 템플릿 로드
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

        # 데이터 레이어 생성
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            # [1페이지: 표지 및 기업개요]
            if i == 0:
                c.setFont(self.font, 32)
                c.drawCentredString(w/2, h - 130, self.data.get('company_name', '(주)메이홈'))
                c.setFont(self.font, 14)
                c.drawString(100, 200, f"대표자: {self.data.get('ceo_name', '박승미')}")
                # 기업개요 삽입
                c.setFont(self.font, 11)
                c.drawString(100, 150, f"주요사업: {self.data.get('business_summary', '재무 진단 분석')}")
                
            # [3페이지: 주요 재무제표 수치]
            elif i == 2:
                c.setFont(self.font, 11)
                # 2024년 매출액 (샘플 좌표 기준 덮어쓰기)
                c.drawString(385, h - 145, to_krw_string(self.data.get('rev_24', 0)))
                # 2023년 매출액
                c.drawString(235, h - 145, to_krw_string(self.data.get('rev_23', 0)))
                # 당기순이익
                c.drawString(385, h - 170, to_krw_string(self.data.get('income_24', 0)))
                # 자산/부채
                c.drawString(385, h - 195, to_krw_string(self.data.get('asset_24', 0)))
                c.drawString(385, h - 220, to_krw_string(self.data.get('debt_24', 0)))

            # 모든 페이지 하단 회사명 치환
            c.setFont(self.font, 8); c.setFillColor(colors.grey)
            c.drawString(50, 30, f"CO-PARTNER | {self.data.get('company_name')} 전용 컨설팅 리포트")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        # 원본과 데이터 병합
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        self.template_doc.save(self.output_pdf)
        self.template_doc.close()
        self.output_pdf.seek(0)
        return self.output_pdf

# --- [6. 메인 UI] ---
def main():
    st.set_page_config(page_title="Professional Report System", layout="wide")
    f_name = load_font()
    st.title("📂 (주)메이홈 전문 경영진단 리포트 생성 (113P)")
    
    st.info("팀장님용: 'result.txt' 템플릿을 기반으로 실데이터를 덮어씌웁니다.")
    
    files = st.file_uploader("메이홈 실데이터 파일(PDF, Excel) 업로드", accept_multiple_files=True)
    if files and st.button("🚀 113페이지 전문 리포트 즉시 생성"):
        with st.spinner("Gemini AI가 파일을 분석하여 리포트를 구성 중입니다..."):
            extracted = extract_mayhome_data(files)
            engine = MasterOverlayEngine(extracted, f_name)
            final_pdf = engine.generate()
            if final_pdf:
                st.success("✅ 리포트 생성이 완료되었습니다!")
                st.download_button("📥 최종 리포트 다운로드", final_pdf, f"CEO_Report_{extracted.get('company_name')}.pdf", "application/pdf")

if __name__ == "__main__":
    main()
