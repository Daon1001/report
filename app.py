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

# --- [1. API 키 및 폰트 설정] ---
# 사용자님께서 제공해주신 키를 직접 사용합니다.
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

# --- [2. 수치 변환 함수 (천원 -> 한글 억/만 단위)] ---
def format_to_krw_text(val):
    try:
        if not val: return "데이터 없음"
        clean_val = str(val).replace(',', '').strip()
        total_won = int(float(clean_val)) * 1000
        if total_won == 0: return "0원"
        eok = total_won // 100000000
        man = (total_won % 100000000) // 10000
        res = []
        if eok > 0: res.append(f"{eok}억")
        if man > 0: res.append(f"{man:,}만")
        return " ".join(res) + " 원"
    except: return "데이터 없음"

# --- [3. Gemini AI: 파일 분석 및 실데이터/개요 추출] ---
def extract_smart_data(files):
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
    당신은 전문 경영 분석가입니다. 제공된 자료를 분석하여 리포트 대상 업체의 정보를 JSON으로 답변하세요.
    - target_company: 분석 대상 업체명
    - ceo_name: 대표자 성명
    - biz_desc: 이 회사가 무엇을 하는지(예: PVC 창호 제조 등) 자료를 근거로 1줄 요약
    - rev_24, rev_23, income_24, asset_24, debt_24: 재무제표의 '천 단위' 수치 그대로 추출
    
    자료내용:
    {all_context[:25000]}
    """
    try:
        response = model.generate_content(prompt)
        # JSON 형식만 골라내기
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return {"target_company": "분석 대상 기업", "ceo_name": "확인 필요", "biz_desc": "재무 경영 분석"}

# --- [4. 나노바나나 방식: 객체 제거 및 데이터 주입 엔진] ---
class NanoBananaReportEngine:
    def __init__(self, data, font_name):
        self.data = data
        self.font = font_name
        self.output_pdf = io.BytesIO()
        
        # 1. result.txt에서 템플릿 로드
        if os.path.exists("./result.txt"):
            with open("./result.txt", "r", encoding="utf-8") as f:
                b64_str = f.read().strip()
                pdf_bytes = base64.b64decode(b64_str.encode('ascii', 'ignore'))
                self.template_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            self.template_doc = None

    def generate(self):
        if not self.template_doc:
            return None

        # 2. 기존 데이터 '나노바나나'식 삭제 (Redaction)
        for i, page in enumerate(self.template_doc):
            # 텍스트 검색 삭제
            for target in ["주식회사 케이에이치오토", "케이에이치오토", "임원근", "0원"]:
                for inst in page.search_for(target):
                    page.add_redact_annot(inst, fill=(1, 1, 1))
            
            # 특정 영역 강제 삭제 (검색 실패 대비)
            if i == 0: # 표지
                page.add_redact_annot(fitz.Rect(50, 100, 550, 250), fill=(1, 1, 1)) # 회사명
                page.add_redact_annot(fitz.Rect(50, 150, 400, 220), fill=(1, 1, 1)) # 대표/사업개요
            elif i == 2: # 재무표
                page.add_redact_annot(fitz.Rect(200, 120, 550, 280), fill=(1, 1, 1)) # 숫자 칸
            
            page.apply_redactions()

        # 3. 데이터 삽입용 레이어 생성
        overlay_buffer = io.BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        w, h = A4

        for i in range(len(self.template_doc)):
            c.setFont(self.font, 10)
            
            if i == 0: # 표지 데이터 주입
                c.setFont(self.font, 36); c.setFillColor(colors.HexColor("#1A3A5E"))
                c.drawCentredString(w/2, h - 130, self.data.get('target_company'))
                c.setFont(self.font, 14); c.setFillColor(colors.black)
                c.drawString(100, 205, f"대표자: {self.data.get('ceo_name')}")
                c.drawString(100, 180, f"주요사업: {self.data.get('biz_desc')}")
                c.drawString(100, 160, "작성자: 중소기업경영지원단")

            elif i == 2: # 재무 데이터 주입
                c.setFont(self.font, 11); c.setFillColor(colors.black)
                c.drawString(385, h - 145, format_to_krw_text(self.data.get('rev_24')))
                c.drawString(235, h - 145, format_to_krw_text(self.data.get('rev_23')))
                c.drawString(385, h - 172, format_to_krw_text(self.data.get('income_24')))
                c.drawString(385, h - 198, format_to_krw_text(self.data.get('asset_24')))
                c.drawString(385, h - 225, format_to_krw_text(self.data.get('debt_24')))

            # 하단 회사명 치환
            c.setFont(self.font, 9); c.setFillColor(colors.grey)
            c.drawString(50, 35, f"CO-PARTNER | {self.data.get('target_company')}")
            c.showPage()
        
        c.save()
        overlay_buffer.seek(0)
        overlay_doc = fitz.open(stream=overlay_buffer.read(), filetype="pdf")
        
        # 4. 레이어 병합 및 버퍼 저장
        for i in range(len(self.template_doc)):
            page = self.template_doc[i]
            page.show_pdf_page(page.rect, overlay_doc, i)
        
        # 최종 PDF를 메모리 버퍼에 씀
        self.template_doc.save(self.output_pdf)
        self.template_doc.close()
        self.output_pdf.seek(0) # 버퍼 포인터를 시작점으로 이동 (다운로드 가능하게 함)
        return self.output_pdf

# --- [5. UI 및 실행] ---
def main():
    st.set_page_config(page_title="AI Master CEO Report", layout="wide")
    f_name = load_font()
    st.title("📂 지능형 범용 CEO 리포트 생성 시스템")
    
    st.markdown("""
    분석하려는 **기업의 파일(엑셀, PDF)**을 업로드하세요. 
    제미나이 AI가 파일을 분석하여 샘플의 낡은 정보를 제거(나노바나나 방식)한 뒤 실데이터로 완벽히 치환합니다.
    """)

    files = st.file_uploader("기업 데이터 파일 업로드 (Excel, PDF 등)", accept_multiple_files=True)
    
    if files and st.button("🚀 지능형 리포트 생성 시작"):
        with st.spinner("AI가 데이터를 분석하고 113페이지 리포트를 제작 중입니다..."):
            # 1. 데이터 추출
            extracted_data = extract_smart_data(files)
            
            # 2. 리포트 생성
            engine = NanoBananaReportEngine(extracted_data, f_name)
            final_pdf_buffer = engine.generate()
            
            if final_pdf_buffer:
                st.success(f"✅ {extracted_data.get('target_company')} 리포트 생성 완료!")
                # 다운로드 버튼
                st.download_button(
                    label="📥 최종 리포트 다운로드",
                    data=final_pdf_buffer,
                    file_name=f"CEO_Report_{extracted_data.get('target_company')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("리포트 생성 중 오류가 발생했습니다. result.txt 파일을 확인하세요.")

if __name__ == "__main__":
    main()
