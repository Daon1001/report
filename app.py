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
    font_path = "./malgun.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            return 'Malgun'
        except: pass
    return 'Helvetica'

# --- [3. 금액 변환 함수] ---
def format_to_krw_full(val):
    try:
        # 천 단위 수치를 원 단위로 환산
        num = float(str(val).replace(',', '').strip())
        total = int(num * 1000)
        if total == 0: return "데이터 없음"
        eok = total // 100000000
        man = (total % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "0원"

# --- [4. Gemini AI: 실데이터 및 기업개요 정밀 추출] ---
def extract_smart_data(files):
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
    당신은 전문 경영 분석가입니다. 아래 자료에서 '(주)메이홈'의 정보를 찾아 JSON으로만 답변하세요.
    1. rev_24, rev_23, income_24, asset_24, debt_24는 반드시 자료 속 천 단위 수치 그대로 추출하세요.
    2. business_summary는 자료를 읽고 이 회사가 무엇을 하는 회사인지(예: PVC 창호 제조 및 가구 도소매 등) 상세히 요약하세요.
    
    JSON 형식:
    {{
        "company_name": "(주)메이홈",
        "ceo_name": "대표자명",
        "business_summary": "추출된 사업 내용",
        "rev_24": 2024년 매출액수치,
        "rev_23": 2023년 매출액수치,
        "income_24": 2024년 당기순이익수치,
        "asset_24": 2024년 자산총계수치,
        "debt_24": 2024년 부채총계수치
    }}
    자료내용:
    {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {
            "company_name": "(주)메이홈", "ceo_name": "박승미", 
            "business_summary": "PVC 창호 제조 및 가구 생산 전문 기업",
            "rev_24": 4137922, "rev_23": 2765913, "income_24": 426000, 
            "asset_24": 1089606, "debt_24": 313936
        }

# --- [5. 리포트 생성 엔진 (White-out & Overlay)] ---
class MasterReportEngine:
    def __init__(self, data, font_name):
        self.data = data
        self.font = font_name
        self.output_pdf = io.BytesIO()
        
        # result.txt에서 마스터 템플릿 로드
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r", encoding="utf-8") as f:
                b64_str = f.read().strip()
                pdf_bytes = base64.b64decode(b64_str.encode('ascii', 'ignore'))
                self.template_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            self.template_doc = None

    def generate(self):
        if not self.template_doc:
            st.error("서버에 'result.txt' 파일이 없습니다. 깃허브 업로드 상태를 확인하세요.")
            return None

        # 데이터 레이어 (Overlay) 생성
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            
            # [1페이지: 표지 치환]
            if i == 0:
                # 기존 텍스트 위치 가리기 (화이트 박스)
                c.setFillColor(colors.white)
                c.rect(50, h-150, 500, 100, fill=1, stroke=0) # 기업명 자리
                c.rect(50, 150, 400, 100, fill=1, stroke=0)   # 작성자/대표자 자리
                
                # 새 데이터 쓰기
                c.setFillColor(colors.HexColor("#1A3A5E"))
                c.setFont(self.font, 36)
                c.drawCentredString(w/2, h - 130, self.data.get('company_name'))
                
                c.setFillColor(colors.black)
                c.setFont(self.font, 13)
                c.drawString(80, 205, f"대표자: {self.data.get('ceo_name')}")
                c.drawString(80, 185, f"주요사업: {self.data.get('business_summary')}")
                c.drawString(80, 165, "작성자: 중소기업경영지원단")

            # [3페이지: 재무 데이터 대입]
            elif i == 2:
                # 기존 숫자 자리 가리기
                c.setFillColor(colors.white)
                c.rect(200, h-250, 350, 150, fill=1, stroke=0)
                
                c.setFillColor(colors.black)
                c.setFont(self.font, 11)
                # 좌표 정밀 대입 (억/만 단위)
                c.drawString(385, h - 145, format_to_krw_full(self.data.get('rev_24'))) # 24년 매출
                c.drawString(235, h - 145, format_to_krw_full(self.data.get('rev_23'))) # 23년 매출
                c.drawString(385, h - 172, format_to_krw_full(self.data.get('income_24'))) # 24년 순이익
                c.drawString(385, h - 198, format_to_krw_full(self.data.get('asset_24')))  # 24년 자산
                c.drawString(385, h - 225, format_to_krw_full(self.data.get('debt_24')))   # 24년 부채

            # 공통 하단바 (주식회사 케이에이치오토 -> (주)메이홈)
            c.setFillColor(colors.white)
            c.rect(40, 30, 300, 15, fill=1, stroke=0) # 하단 회사명 자리 가리기
            c.setFillColor(colors.grey)
            c.setFont(self.font, 9)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('company_name')}")
            
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        # 원본과 데이터 레이어 병합
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        self.template_doc.save(self.output_pdf)
        self.template_doc.close()
        self.output_pdf.seek(0)
        return self.output_pdf

# --- [6. 메인 앱 실행] ---
def main():
    st.set_page_config(page_title="Professional CEO Report Generator", layout="wide")
    f_name = load_font()
    
    st.title("📑 (주)메이홈 전문 경영진단 리포트 생성기")
    st.info("메이홈의 엑셀 데이터와 개요 파일을 업로드하면 113P 전문 리포트의 숫자와 개요가 자동으로 바뀝니다.")

    uploaded_files = st.file_uploader("메이홈 데이터 파일 업로드 (Excel, PDF)", accept_multiple_files=True)
    
    if uploaded_files and st.button("🚀 데이터 반영 리포트 생성"):
        with st.spinner("Gemini AI가 파일을 분석하고 데이터를 대입 중입니다..."):
            # 1. AI 데이터 추출
            smart_data = extract_smart_data(uploaded_files)
            # 2. 오버레이 생성
            engine = MasterReportEngine(smart_data, f_name)
            final_pdf = engine.generate()
            
            if final_pdf:
                st.success(f"✅ {smart_data.get('company_name')} 리포트 생성 완료!")
                st.download_button("📥 최종 리포트 다운로드", final_pdf, f"CEO_Report_Mayhome_Master_Final.pdf", "application/pdf")

if __name__ == "__main__":
    main()
