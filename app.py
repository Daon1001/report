import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import os

# 1. 환경 설정
INPUT_FILE = "cretop_data.xlsx"  # 크레탑에서 다운로드한 파일명으로 변경
OUTPUT_DIR = "output"
FONT_PATH = "C:/Windows/Fonts/malgun.ttf"  # Windows 기준, 맥/리눅스는 해당 경로 폰트로 수정

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('HanguI', FONT_PATH))

class CEOReportGenerator:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.data = {}
        self.analysis = {}

    def load_data(self):
        """크레탑 엑셀 시트 분석 및 데이터 추출"""
        # 실제 엑셀의 컬럼명에 맞춰 조정이 필요합니다.
        df = pd.read_excel(self.excel_path)
        
        # 샘플 로직: 항목명과 연도별 수치 추출
        # 예: df.loc[df['항목'] == '매출액', '2025'].values[0]
        try:
            self.data['company_name'] = "주식회사 케이에이치오토" # 예시
            self.data['revenue'] = [1000, 1200, 1500] # 최근 3개년 매출 예시
            self.data['net_income'] = [100, 120, 180] # 최근 3개년 순이익 예시
            self.data['total_assets'] = 5000
            self.data['total_debt'] = 2000
        except Exception as e:
            print(f"데이터 파싱 오류: {e}. 엑셀 형식을 확인하세요.")

    def run_analysis(self):
        """재무 및 기업가치 분석 엔진"""
        # 1. 성장성 (매출증가율)
        rev = self.data['revenue']
        self.analysis['growth'] = ((rev[-1] - rev[-2]) / rev[-2]) * 100
        
        # 2. 수익성 (영업이익률 - 순이익으로 대체 예시)
        self.analysis['profitability'] = (self.data['net_income'][-1] / rev[-1]) * 100
        
        # 3. 안정성 (부채비율)
        self.analysis['stability'] = (self.data['total_debt'] / self.data['total_assets']) * 100
        
        # 4. 기업가치평가 (간이 상증세법 로직)
        # (순손익가치 * 0.6) + (순자산가치 * 0.4) - 매우 간소화된 버전
        avg_income = sum(self.data['net_income']) / len(self.data['net_income'])
        self.analysis['stock_value'] = (avg_income / 0.1) * 0.6 + (self.data['total_assets'] - self.data['total_debt']) * 0.4

    def create_visuals(self):
        """차트 생성"""
        plt.figure(figsize=(6, 4))
        plt.plot(['2023', '2024', '2025'], self.data['revenue'], marker='o', label='Revenue')
        plt.plot(['2023', '2024', '2025'], self.data['net_income'], marker='s', label='Net Income')
        plt.title('Financial Trend')
        plt.legend()
        chart_path = os.path.join(OUTPUT_DIR, 'trend_chart.png')
        plt.savefig(chart_path)
        plt.close()
        return chart_path

    def generate_pdf(self):
        """PDF 리포트 생성"""
        chart_path = self.create_visuals()
        file_path = os.path.join(OUTPUT_DIR, f"CEO_Report_{self.data['company_name']}.pdf")
        
        c = canvas.Canvas(file_path, pagesize=A4)
        w, h = A4

        # 헤더
        c.setFont('HanguI', 20)
        c.drawCentredString(w/2, h - 50, f"{self.data['company_name']} 재무경영진단 리포트")
        
        c.setStrokeColor(colors.blue)
        c.line(50, h - 70, w - 50, h - 70)

        # 주요 지표 섹션
        c.setFont('HanguI', 14)
        c.drawString(50, h - 110, "[1. 핵심 재무 지표]")
        c.setFont('HanguI', 11)
        c.drawString(70, h - 140, f"• 매출성장율: {self.analysis['growth']:.2f}%")
        c.drawString(70, h - 160, f"• 순이익률: {self.analysis['profitability']:.2f}%")
        c.drawString(70, h - 180, f"• 부채비율: {self.analysis['stability']:.2f}%")

        # 기업가치 섹션
        c.setFont('HanguI', 14)
        c.drawString(50, h - 230, "[2. 기업가치 추정]")
        c.setFont('HanguI', 11)
        c.drawString(70, h - 260, f"• 추정 기업가치: 약 {self.analysis['stock_value']:,.0f} 만원")
        c.drawString(70, h - 280, "  (상증세법 보충적 평가방법 간이 계산 결과)")

        # 차트 삽입
        c.drawImage(chart_path, 50, h - 550, width=450, preserveAspectRatio=True)

        # 하단 푸터
        c.setFont('HanguI', 9)
        c.setStrokeColor(colors.lightgrey)
        c.line(50, 50, w - 50, 50)
        c.drawString(50, 40, "본 리포트는 크레탑 데이터를 바탕으로 자동 생성되었습니다.")

        c.showPage()
        c.save()
        print(f"리포트 생성 완료: {file_path}")

# 실행부
if __name__ == "__main__":
    # 1. 엑셀 파일이 있는지 확인 (실제 크레탑 파일명으로 교체 필요)
    if os.path.exists(INPUT_FILE):
        gen = CEOReportGenerator(INPUT_FILE)
        gen.load_data()
        gen.run_analysis()
        gen.generate_pdf()
    else:
        # 파일이 없을 경우 테스트용 가상 데이터 생성 로직을 넣거나 안내 메시지 출력
        print(f"'{INPUT_FILE}' 파일이 없습니다. 크레탑 엑셀 파일을 준비해주세요.")
