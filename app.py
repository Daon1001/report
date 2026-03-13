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

# --- [2. 한글 금액 변환 (천원 -> 억/만 단위)] ---
def format_currency_hangul(val):
    try:
        num = float(str(val).replace(',', '').strip())
        total_won = int(num * 1000)
        if total_won == 0: return "해당 없음"
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "0원"

# --- [3. Gemini AI: 파일 분석 및 실데이터/개요 추출] ---
def extract_smart_content(files):
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
    당신은 전문 경영 컨설턴트입니다. 아래 자료에서 '(주)메이홈'의 정보를 분석하여 JSON으로만 답변하세요.
    1. 'business_summary'는 제공된 파일(회사소개 등)을 읽고 이 회사의 핵심 사업(예: PVC 창호 제조, 가구 제작 등)을 30자 이내로 요약하세요.
    2. 'rev_24', 'rev_23', 'income_24', 'asset_24', 'debt_24'는 재무제표의 '천 단위' 수치를 정확히 찾아 숫자로만 추출하세요.
    
    JSON 예시:
    {{
        "company": "(주)메이홈",
        "ceo": "대표자 성명",
        "summary": "추출된 사업 개요 내용",
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
        return {"company": "(주)메이홈", "summary": "PVC 창호 제조 및 가구 생산", "rev_24": 4137922}

# --- [4. 지능형 스마트 리포트 생성기 (Find-Delete-Inject)] ---
class SmartInjectionEngine:
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
            st.error("마스터 템플릿(result.txt)이 없습니다.")
            return None

        # 1. 원본 샘플 데이터 삭제 (Redaction) 로직
        # 샘플에 포함된 낡은 텍스트를 찾아 아예 삭제합니다.
        for page in self.template_doc:
            targets = ["주식회사 케이에이치오토", "케이에이치오토", "0원", "재무 진단 분석"]
            for target in targets:
                insts = page.search_for(target)
                for inst in insts:
                    page.add_redact_annot(inst, fill=(1, 1, 1)) # 영역 삭제
            page.apply_redactions()

        # 2. 제미나이 데이터 주입 (Overlay)
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            # [1페이지: 표지 및 AI 요약 개요]
            if i == 0:
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('company'))
                c.setFont(self.font, 14); c.setFillColor(colors.black)
                c.drawString(100, 205, f"대표자: {self.data.get('ceo', '박승미')}")
                # AI가 추출한 사업 개요 삽입
                c.setFont(self.font, 12)
                c.drawString(100, 180, f"주요사업: {self.data.get('summary')}")
                c.drawString(100, 160, "작성자: 중소기업경영지원단")

            # [3페이지: 재무 지표 (샘플의 '0원' 자리에 실데이터 주입)]
            elif i == 2:
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                # 제미나이가 뽑아온 숫자를 억/만 단위로 변환해 정확한 칸에 삽입
                c.drawString(385, h - 145, format_currency_hangul(self.data.get('rev_24'))) # 당기매출
                c.drawString(235, h - 145, format_currency_hangul(self.data.get('rev_23'))) # 전기매출
                c.drawString(385, h - 172, format_currency_hangul(self.data.get('income_24'))) # 순이익
                c.drawString(385, h - 198, format_currency_hangul(self.data.get('asset_24')))  # 자산
                c.drawString(385, h - 225, format_currency_hangul(self.data.get('debt_24')))   # 부채

            # 하단바 회사명 업데이트
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('company')}")
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

# --- [5. 앱 실행 화면] ---
def main():
    st.set_page_config(page_title="Professional AI Report", layout="wide")
    f_name = load_font()
    st.title("📂 (주)메이홈 전문 경영진단 리포트 (지능형 데이터 치환)")
    
    st.markdown("**(주)메이홈**의 엑셀 데이터와 개요 파일을 업로드하세요. 제미나이 AI가 내용을 읽어 리포트의 낡은 데이터를 지우고 실데이터를 채워넣습니다.")

    files = st.file_uploader("메이홈 데이터 파일 업로드 (Excel, PDF)", accept_multiple_files=True)
    
    if files and st.button("🚀 AI 데이터 분석 및 리포트 생성"):
        with st.spinner("제미나이 AI가 파일의 맥락을 분석하여 데이터를 '추출 및 치환' 중입니다..."):
            # 1. Gemini를 통한 데이터 및 사업개요 추출
            smart_data = extract_smart_content(files)
            # 2. 스마트 엔진 가동 (찾기-지우기-입히기)
            engine = SmartInjectionEngine(smart_data, f_name)
            final_pdf = engine.generate()
            
            if final_pdf:
                st.success(f"✅ {smart_data.get('company')} 리포트가 성공적으로 생성되었습니다!")
                st.download_button("📥 최종 리포트(데이터 반영본) 다운로드", final_pdf, f"CEO_Report_Mayhome_AI_Final.pdf", "application/pdf")

if __name__ == "__main__":
    main()
