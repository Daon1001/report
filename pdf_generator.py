"""
PDF 생성 모듈 - WeasyPrint 사용
"""
import os
import tempfile
from typing import Optional


def generate_pdf(html_content: str, output_path: str) -> str:
    """HTML을 PDF로 변환"""
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)
        return output_path
    except ImportError:
        # WeasyPrint 미설치시 HTML 파일로 저장
        html_path = output_path.replace('.pdf', '.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return html_path


def generate_report(
    bs_file: str, 
    is_file: str, 
    mfg_file: str,
    overview_pdf: Optional[str] = None,
    credit_pdf: Optional[str] = None,
    output_path: str = "report.pdf",
    author_name: str = "",
    author_org: str = "",
    author_phone: str = "",
    shares: Optional[int] = None,
    par_value: Optional[int] = None,
) -> str:
    """전체 리포트 생성 파이프라인"""
    from parsers.excel_parser import parse_balance_sheet, parse_income_statement, parse_manufacturing_cost
    from parsers.pdf_parser import parse_company_overview, parse_credit_report
    from parsers.financial_ratios import calculate_ratios, calculate_valuation
    from report.html_template import generate_report_html
    
    # 1. 데이터 파싱
    bs = parse_balance_sheet(bs_file)
    isc = parse_income_statement(is_file)
    mfg = parse_manufacturing_cost(mfg_file)
    
    company = {}
    if overview_pdf:
        company = parse_company_overview(overview_pdf)
    
    credit = {}
    if credit_pdf:
        credit = parse_credit_report(credit_pdf)
    
    # 2. 재무비율 계산
    ratios = calculate_ratios(bs, isc)
    
    # 3. 기업가치 평가
    valuation = calculate_valuation(bs, isc, shares=shares, par_value=par_value)
    
    # 4. HTML 생성
    html = generate_report_html(
        company=company, bs=bs, isc=isc, mfg=mfg,
        ratios=ratios, valuation=valuation, credit=credit,
        author_name=author_name, author_org=author_org, author_phone=author_phone,
    )
    
    # 5. PDF 변환
    result_path = generate_pdf(html, output_path)
    
    return result_path
