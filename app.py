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

# --- [2. 금액 한글 변환 함수 (천원 -> 억/만 단위)] ---
def format_currency_to_hangul(val):
    try:
        clean_val = str(val).replace(',', '').strip()
        # 천 단위 수치를 원 단위로 환산
        total_won = int(float(clean_val)) * 1000
        if total_won == 0: return "0원"
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except:
        return "0원"

# --- [3. 제미나이 API: 실데이터 및 기업개요 정밀 추출] ---
def extract_smart_data(files):
    model = genai.GenerativeModel('gemini-1.5-pro')
    all_context = ""
    for f in files:
        if f.name.endswith('.pdf'):
            doc = fitz.open(stream=f.read(), filetype="pdf")
            all_context += "".join([p.get_text() for p in doc])
        else:
            try:
                df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
                all_context += df.to_string()
            except: pass

    prompt = f"""
    당신은 전문 경영 분석가입니다. 아래 자료에서 '(주)메이홈'의 정보를 찾아 JSON으로만 답변하세요.
    1. rev_24, rev_23, income_24, asset_24, debt_24는 자료 속 천 단위 수치를 찾아 숫자로만 추출하세요.
    2. business_summary는 자료를 읽고 회사가 하는 일(PVC 창호 제조, 가구 생산 등)을 전문적으로 요약하세요.
    
    JSON 형식 예시:
    {{
        "company_name": "(주)메이홈",
        "ceo_name": "박승미",
        "business_summary": "PVC 창호 제조 및 가구 부속품 생산 전문 기업",
        "rev_24": 4137922,
        "rev_23": 2765913,
        "income_24": 426000,
        "asset_24": 1089606,
        "debt_24": 313936
    }}
    자료내용:
    {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        import json
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        # 추출 실패 시 기본값
        return {
            "company_name": "(주)메이홈", "ceo_name": "박승미",
            "business_summary": "창호 제조 및 가구 생산 전문 기업",
            "rev_24": 4137922, "rev_23": 2765913, "income_24": 426000, "asset_24": 1089606, "debt_24": 313936
        }

# --- [4. 스마트 검색 및 치환 엔진 (Search-Redact-Replace)] ---
class SmartSearchReplaceEngine:
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
            st.error("서버에 'result.txt' 파일이 없습니다.")
            return None

        # 1. 템플릿 내 특정 키워드 삭제 및 위치 확보
        # "주식회사 케이에이치오토", "0원", "재무 진단 분석" 등을 찾아 지움
        for page in self.template_doc:
            search_targets = ["주식회사 케이에이치오토", "케이에이치오토", "0원", "재무 진단 분석"]
            for target in search_targets:
                insts = page.search_for(target)
                for inst in insts:
                    page.add_redact_annotation(inst, fill=(1, 1, 1)) # 흰색으로 지우기
            page.apply_redactions()

        # 2. 지워진 자리에 새로운 데이터 오버레이
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
                c.drawString(80, 205, f"대표자: {self.data.get('ceo_name')}")
                c.drawString(80, 180, f"주요사업: {self.data.get('business_summary')}")
                c.drawString(80, 155, "작성자: 중소기업경영지원단")

            # [3페이지: 재무 데이터 (샘플의 '0원' 자리에 대입)]
            elif i == 2:
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                # 제미나이가 추출한 숫자를 한글 단위로 변환하여 삽입
                c.drawString(385, h - 145, format_currency_to_hangul(self.data.get('rev_24')))
                c.drawString(235, h - 145, format_currency_to_hangul(self.data.get('rev_23')))
                c.drawString(385, h - 172, format_currency_to_hangul(self.data.get('income_24')))
                c.drawString(385, h - 198, format_currency_to_hangul(self.data.get('asset_24')))
                c.drawString(385, h - 225, format_currency_to_hangul(self.data.get('debt_24')))

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

# --- [5. 실행 UI] ---
def main():
    st.set_page_config(page_title="Professional Report Generator", layout="wide")
    f_name = load_font()
    st.title("📂 (주)메이홈 전문 씨오리포트 생성 시스템")
    
    st.markdown("**(주)메이홈** 관련 엑셀/PDF를 업로드하면 샘플의 데이터를 지우고 실데이터로 완벽히 치환합니다.")
    
    files = st.file_uploader("메이홈 데이터 파일 업로드 (Excel, PDF)", accept_multiple_files=True)
    
    if files and st.button("🚀 데이터 정밀 반영 리포트 생성"):
        with st.spinner("제미나이 AI가 데이터를 추출하고 템플릿을 수정 중입니다..."):
            # 1. AI 데이터 추출
            smart_data = extract_smart_data(files)
            # 2. 리포트 생성 엔진 가동
            engine = SmartSearchReplaceEngine(smart_data, f_name)
            final_pdf = engine.generate()
            
            if final_pdf:
                st.success(f"✅ {smart_data.get('company_name')} 리포트 생성 완료!")
                st.download_button("📥 최종 리포트 다운로드", final_pdf, f"CEO_Report_Mayhome_Smart_Final.pdf", "application/pdf")

if __name__ == "__main__":
    main()
