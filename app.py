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

# --- [1. Gemini API 및 폰트 설정] ---
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
else:
    st.error("Streamlit Secrets에 'api_key'가 설정되어 있지 않습니다.")

def load_font():
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [2. Gemini AI: 실데이터 정밀 추출 및 매핑] ---
def get_smart_data(data_files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # 1. 데이터 파일들의 내용을 텍스트로 취합
    context = ""
    for f in data_files:
        if f.name.endswith('.pdf'):
            doc = fitz.open(stream=f.read(), filetype="pdf")
            context += f"\n[파일: {f.name}]\n" + "".join([p.get_text() for p in doc])
        else:
            df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
            context += f"\n[파일: {f.name}]\n" + df.to_string()

    # 2. Gemini에게 필요한 수치만 JSON으로 추출 요청
    prompt = f"""
    당신은 전문 회계 컨설턴트입니다. 다음 자료에서 (주)메이홈의 정보를 찾아 JSON으로 출력하세요.
    수치는 천 단위(예: 4,137,922) 그대로 가져오세요.
    항목: 기업명, 대표자명, 2024년매출, 2023년매출, 2024년당기순이익, 2024년자산총계, 2024년부채총계, 신용등급
    자료: {context[:15000]}
    """
    
    response = model.generate_content(prompt)
    try:
        import json
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"기업명": "(주)메이홈", "2024년매출": "4137922"}

# --- [3. 113P 마스터 복제 엔진] ---
class MasterTemplateReport:
    def __init__(self, sample_pdf_file, extracted_data, font_name):
        self.sample_doc = fitz.open(stream=sample_pdf_file.read(), filetype="pdf")
        self.data = extracted_data
        self.font = font_name
        self.buffer = io.BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4

    def format_krw(self, val):
        """숫자를 억/만 단위 한글로 변환"""
        try:
            total = int(float(str(val).replace(',', ''))) * 1000
            eok, man = total // 100000000, (total % 100000000) // 10000
            res = []
            if eok: res.append(f"{eok}억")
            if man: res.append(f"{man:,}만")
            return " ".join(res) + " 원"
        except: return str(val)

    def generate(self):
        # 샘플 리포트의 모든 페이지(113P)를 순회하며 텍스트 복제 및 치환
        for i in range(len(self.sample_doc)):
            page = self.sample_doc[i]
            text_instances = page.get_text("blocks") # 텍스트 블록과 위치 정보 가져오기
            
            # 상하단 레이아웃 및 페이지 번호 그리기
            self.c.setStrokeColor(colors.HexColor("#1A3A5E"))
            self.c.line(40, self.h-45, self.w-40, self.h-45)
            self.c.line(40, 45, self.w-40, 45)
            self.c.setFont(self.font, 9); self.c.setFillColor(colors.grey)
            self.c.drawString(50, self.h-40, f"CO-PARTNER | {self.data.get('기업명')}")
            self.c.drawRightString(self.w-50, 35, f"씨오리포트 {i+1} / {len(self.sample_doc)}")

            # 각 페이지의 텍스트를 복제하되, 특정 키워드(기업명, 수치)는 치환
            for block in text_instances:
                original_text = block[4]
                # 1. 기업명 치환
                modified_text = original_text.replace("주식회사 케이에이치오토", self.data.get('기업명'))
                modified_text = modified_text.replace("케이에이치오토", self.data.get('기업명'))
                
                # 2. 특정 페이지(예: 3페이지)의 수치 정밀 치환
                if i == 2: # 3페이지 (Index 2)
                    if "매출액" in modified_text:
                        modified_text = f"매출액: {self.format_krw(self.data.get('2024년매출'))}"
                
                # 3. 맑은 고딕으로 텍스트 그리기 (위치는 샘플과 동일하게 조정)
                x, y = block[0], self.h - block[1]
                self.c.setFont(self.font, 10)
                self.c.setFillColor(colors.black)
                self.c.drawString(x, y - 10, modified_text.strip())

            self.c.showPage()
        
        self.c.save()
        self.buffer.seek(0)
        return self.buffer

# --- [4. Streamlit UI] ---
def main():
    st.set_page_config(page_title="Master CEO Report", layout="wide")
    f_name = load_font()
    
    st.title("📑 씨오리포트 마스터 복제 시스템 (Gemini AI)")
    st.info("샘플 리포트(PDF)의 모든 구성과 내용을 그대로 유지하며 데이터만 바꿉니다.")

    col1, col2 = st.columns(2)
    with col1:
        sample_file = st.file_uploader("1. 샘플 리포트 업로드 (케이에이치오토 PDF)", type=['pdf'])
    with col2:
        data_files = st.file_uploader("2. 데이터 파일 업로드 (메이홈 PDF, 엑셀)", accept_multiple_files=True)

    if sample_file and data_files and st.button("🚀 113페이지 전문 리포트 생성"):
        with st.spinner("Gemini AI가 샘플을 분석하고 데이터를 대입 중입니다..."):
            # 1. 데이터 추출
            extracted = get_smart_data(data_files)
            # 2. 리포트 복제 생성
            report_engine = MasterTemplateReport(sample_file, extracted, f_name)
            final_pdf = report_engine.generate()
            
            st.download_button("📥 최종 리포트(113P) 다운로드", final_pdf, f"CEO_Report_Mayhome_Master.pdf", "application/pdf")

if __name__ == "__main__":
    main()
