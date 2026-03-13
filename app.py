import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import os
import base64
import fitz  # PyMuPDF
import json
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# --- [1. API 및 환경 설정] ---
# 사용자님의 API 키 직접 설정
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

# --- [2. 수치 변환 함수 (천원 -> 억/만 단위)] ---
def format_to_krw(val):
    try:
        if not val or val == 0: return "데이터 없음"
        clean_val = str(val).replace(',', '').strip()
        total_won = int(float(clean_val)) * 1000
        eok, man = total_won // 100000000, (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원" if res else "0원"
    except: return "0원"

# --- [3. Gemini AI: 파일 구조 파악 및 실데이터 추출] ---
def extract_data_by_structure(files):
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

    # 제미나이에게 업로드된 파일이 어떤 회사의 것인지, 수치는 무엇인지 JSON으로 요구
    prompt = f"""
    당신은 기업 분석 AI입니다. 업로드된 자료를 분석하여 리포트 템플릿에 채울 데이터를 JSON으로만 답변하세요.
    - company_name: 업체명
    - ceo_name: 대표자 성명
    - biz_type: 주요 사업 내용 1줄 요약 (자료 근거)
    - rev_24, rev_23, income_24, asset_24, debt_24: 재무제표 천 단위 수치 그대로
    자료내용: {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return {"company_name": "분석 기업", "biz_type": "재무 경영 진단"}

# --- [4. 구조적 매핑 엔진 (템플릿 기반 데이터 채우기)] ---
class StructuralReportEngine:
    def __init__(self, data, font_name):
        self.data, self.font = data, font_name
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r", encoding="utf-8") as f:
                b64 = f.read().strip()
                pdf_bytes = base64.b64decode(b64.encode('ascii', 'ignore'))
                self.template = fitz.open(stream=pdf_bytes, filetype="pdf")
        else: self.template = None

    def build(self):
        if not self.template: return None
        
        # 1. '구조적 삭제': 템플릿에서 데이터가 들어갈 슬롯을 미리 비움
        for i, page in enumerate(self.template):
            # 모든 페이지 하단 회사명 삭제
            for inst in page.search_for("주식회사 케이에이치오토"):
                page.add_redact_annot(inst, fill=(1, 1, 1))
            
            # 1P, 3P 등 주요 데이터 슬롯 삭제 (나노바나나 방식)
            if i == 0: # 표지 슬롯
                page.add_redact_annot(fitz.Rect(50, 100, 550, 250), fill=(1, 1, 1))
                page.add_redact_annot(fitz.Rect(50, 150, 400, 220), fill=(1, 1, 1))
            elif i == 2: # 재무표 슬롯
                page.add_redact_annot(fitz.Rect(200, 120, 550, 280), fill=(1, 1, 1))
            
            page.apply_redactions()

        # 2. '데이터 채우기': 비워진 슬롯에 실데이터 주입
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template)):
            if i == 0: # 1페이지 데이터 채우기
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('company_name'))
                c.setFont(self.font, 13); c.setFillColor(colors.black)
                c.drawString(100, 205, f"대표자: {self.data.get('ceo_name', '확인필요')}")
                c.drawString(100, 185, f"주요사업: {self.data.get('biz_type')}")
                c.drawString(100, 165, "작성자: 중소기업경영지원단")
            elif i == 2: # 3페이지 재무 데이터 채우기
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                c.drawString(385, h - 145, format_to_krw(self.data.get('rev_24')))
                c.drawString(235, h - 145, format_to_krw(self.data.get('rev_23')))
                c.drawString(385, h - 172, format_to_krw(self.data.get('income_24')))
            
            # 하단 공통 정보 업데이트
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('company_name')}")
            c.showPage()
            
        c.save()
        overlay_buffer.seek(0)
        overlay_pdf = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        for i in range(len(self.template)):
            self.template[i].show_pdf_page(self.template[i].rect, overlay_pdf, i)
        
        # 3. 결과 반환 (메모리 버퍼)
        final_buffer = io.BytesIO()
        self.template.save(final_buffer)
        self.template.close()
        final_buffer.seek(0)
        return final_buffer

# --- [5. 메인 앱 화면] ---
def main():
    st.set_page_config(page_title="AI Master Report", layout="wide")
    f_name = load_font()
    st.title("📂 지능형 범용 CEO 리포트 생성기")
    st.write("샘플의 113페이지 구조를 그대로 유지하며, 업로드된 데이터로 핵심 내용을 채워넣습니다.")

    files = st.file_uploader("기업 데이터(Excel, PDF) 업로드", accept_multiple_files=True)
    
    if files:
        if st.button("🚀 리포트 생성 및 치환 시작"):
            with st.spinner("AI가 데이터를 분석하여 리포트 구조에 맞게 채워넣는 중입니다..."):
                extracted_data = extract_data_by_structure(files)
                engine = StructuralReportEngine(extracted_data, f_name)
                final_pdf = engine.build()
                
                if final_pdf:
                    st.session_state['pdf_result'] = final_pdf
                    st.session_state['target_name'] = extracted_data.get('company_name')
                    st.success(f"✅ {extracted_data.get('company_name')} 리포트 생성 완료!")

    # 다운로드 버튼 (세션 상태를 확인하여 표시)
    if 'pdf_result' in st.session_state:
        st.download_button(
            label="📥 최종 리포트 다운로드",
            data=st.session_state['pdf_result'],
            file_name=f"CEO_Report_{st.session_state.get('target_name', 'result')}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
