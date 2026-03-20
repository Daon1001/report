"""
HTML 템플릿 기반 리포트 생성 (WeasyPrint로 PDF 변환)
sample.pdf의 디자인을 재현
"""

def format_number(val, unit="천원") -> str:
    """숫자를 포맷팅"""
    if val is None:
        return "-"
    val = float(val)
    if unit == "천원":
        return f"{val:,.0f}"
    elif unit == "백만원":
        return f"{val/1000:,.0f}"
    elif unit == "억원":
        v = val / 100000
        return f"{v:,.1f}억원"
    elif unit == "%":
        return f"{val:.1f}%"
    elif unit == "원":
        return f"{val:,.0f}원"
    return f"{val:,.0f}"


def fn(val) -> str:
    """천원 단위 숫자 포맷"""
    return format_number(val, "천원")


def fp(val) -> str:
    """퍼센트 포맷"""
    if val is None:
        return "-"
    return f"{val:.2f}%"


def generate_report_html(company: dict, bs: dict, isc: dict, mfg: dict, 
                          ratios: dict, valuation: dict, credit: dict,
                          author_name: str = "", author_org: str = "", 
                          author_phone: str = "") -> str:
    """전체 리포트 HTML 생성"""
    
    company_name = company.get("기업명", "기업명")
    years = bs.get("years", [])
    
    # 연도 표시
    year_labels = [y.replace("-12-31", "년") for y in years]
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
{get_css()}
</style>
</head>
<body>

{_cover_page(company_name, author_name, author_org, author_phone)}

{_toc_page()}

{_section_divider("기업재무분석")}

{_company_overview_page(company)}

{_balance_sheet_page(bs, years, year_labels)}

{_income_statement_page(isc, years, year_labels)}

{_financial_summary_page(bs, isc, years, year_labels)}

{_ratio_analysis_page(ratios, years, year_labels)}

{_ratio_analysis_page2(ratios, years, year_labels)}

{_expense_analysis_page(isc, years, year_labels)}

{_section_divider("신용등급 관리")}

{_credit_page(company, credit)}

{_section_divider("기업가치평가")}

{_valuation_page(valuation, company)}

{_tax_reference_page()}

{_section_divider("임원소득보상플랜")}

{_compensation_plan_overview_page()}

{_salary_tax_simulation_page(isc, company, years)}

{_retirement_plan_page(isc, bs, company, years, year_labels)}

{_section_divider("배당플랜")}

{_dividend_strategy_page()}

{_retained_earnings_page(bs, isc, years, year_labels)}

{_section_divider("기업제도정비")}

{_corporate_governance_page(company)}

{_certification_strategy_page(company)}

{_certification_detail_page()}

{_stock_option_page()}

{_section_divider("노무 컨설팅")}

{_labor_checklist_page(company)}

{_employment_subsidy_page(company)}

</body>
</html>"""
    
    return html


def _cover_page(company_name, author_name, author_org, author_phone) -> str:
    import datetime
    today = datetime.date.today().strftime("%Y-%m-%d")
    return f"""
<div class="page cover-page">
    <div class="cover-bg">
        <div class="cover-content">
            <div class="cover-company">{company_name}</div>
            <h1 class="cover-title">재무경영진단 리포트</h1>
            <div class="cover-line"></div>
            <div class="cover-info">
                <div class="cover-info-row"><span class="cover-label">작성일</span><span>{today}</span></div>
                <div class="cover-info-row"><span class="cover-label">작성자</span><span>{author_name} / {author_org}</span></div>
                <div class="cover-info-row"><span class="cover-label">연락처</span><span>{author_phone}</span></div>
            </div>
        </div>
    </div>
    <div class="cover-footer">
        <div class="cover-disclaimer">본 자료는 고객님의 기업경영에 도움을 드리고자 제작된 참고자료입니다.</div>
    </div>
</div>
"""


def _toc_page() -> str:
    return """
<div class="page toc-page">
    <div class="toc-header">CONTENTS</div>
    <div class="toc-grid">
        <div class="toc-row">
            <div class="toc-item"><span class="toc-icon">📊</span><span class="toc-text">기업재무분석</span><span class="toc-dots"></span><span class="toc-page-num">P03</span></div>
            <div class="toc-item"><span class="toc-icon">🏦</span><span class="toc-text">신용등급 관리</span><span class="toc-dots"></span><span class="toc-page-num">P11</span></div>
        </div>
        <div class="toc-row">
            <div class="toc-item"><span class="toc-icon">📈</span><span class="toc-text">기업가치평가</span><span class="toc-dots"></span><span class="toc-page-num">P13</span></div>
            <div class="toc-item"><span class="toc-icon">👔</span><span class="toc-text">임원소득보상플랜</span><span class="toc-dots"></span><span class="toc-page-num">P16</span></div>
        </div>
        <div class="toc-row">
            <div class="toc-item"><span class="toc-icon">💰</span><span class="toc-text">배당플랜</span><span class="toc-dots"></span><span class="toc-page-num">P20</span></div>
            <div class="toc-item"><span class="toc-icon">📋</span><span class="toc-text">기업제도정비</span><span class="toc-dots"></span><span class="toc-page-num">P23</span></div>
        </div>
        <div class="toc-row">
            <div class="toc-item"><span class="toc-icon">⚖️</span><span class="toc-text">노무 컨설팅</span><span class="toc-dots"></span><span class="toc-page-num">P28</span></div>
        </div>
    </div>
</div>
"""


def _section_divider(title: str) -> str:
    return f"""
<div class="page section-divider">
    <div class="divider-left"></div>
    <div class="divider-right">
        <div class="divider-line"></div>
        <h2 class="divider-title">{title}</h2>
    </div>
</div>
"""


def _company_overview_page(company: dict) -> str:
    # 신용등급 이미지 또는 텍스트
    grade_img = company.get('신용등급_이미지', '')
    if grade_img:
        grade_html = f'<img src="data:image/png;base64,{grade_img}" style="max-height:120px;"/>'
    else:
        grade_html = f'<div style="font-size:36px;font-weight:800;color:#4A5FC1;">{company.get("기업신용등급") or "-"}</div>'
    
    ew_img = company.get('EW등급_이미지', '')
    if ew_img:
        ew_html = f'<img src="data:image/png;base64,{ew_img}" style="max-height:120px;"/>'
    else:
        ew_html = f'<div style="font-size:36px;font-weight:800;color:#4A5FC1;">{company.get("EW등급") or "-"}</div>'
    
    # 재무진단 항목
    diag_items = ["성장성", "수익성", "재무구조", "부채상환능력", "활동성"]
    diag_images = company.get("재무진단_이미지", {})
    diag_text = company.get("재무진단", {})
    diag_html = ""
    for dk in diag_items:
        if dk in diag_images:
            diag_html += f'''
            <div class="diag-item">
                <div class="diag-label">{dk}</div>
                <img src="data:image/png;base64,{diag_images[dk]}" style="max-height:100px;max-width:100px;"/>
            </div>'''
        else:
            val = diag_text.get(dk, '-')
            diag_html += f'''
            <div class="diag-item">
                <div class="diag-label">{dk}</div>
                <div class="diag-value diag-{val}">{val}</div>
            </div>'''
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📊 기업재무분석</span>
        <span class="page-title-main">기업개요</span>
    </div>
    <div class="page-body">
        <h3 class="subsection-title">◆ 기업일반</h3>
        <table class="data-table company-table">
            <tr><td class="label-cell">기업명</td><td>{company.get('기업명', '-')}</td>
                <td class="label-cell">설립일자</td><td>{company.get('설립일자', '-')}</td></tr>
            <tr><td class="label-cell">대표자명</td><td>{company.get('대표자명', '-')}</td>
                <td class="label-cell">종업원수</td><td>{company.get('종업원수', '-')}</td></tr>
            <tr><td class="label-cell">기업유형</td><td>{company.get('기업유형', '-')}</td>
                <td class="label-cell">기업규모</td><td>{company.get('기업규모', '-')}</td></tr>
            <tr><td class="label-cell">사업자번호</td><td>{company.get('사업자번호', '-')}</td>
                <td class="label-cell">전화번호</td><td>{company.get('전화번호', '-')}</td></tr>
            <tr><td class="label-cell">주소</td><td colspan="3">{company.get('주소', '-')}</td></tr>
            <tr><td class="label-cell">업종</td><td colspan="3">{company.get('표준산업분류', '-')}</td></tr>
            <tr><td class="label-cell">주요제품</td><td colspan="3">{company.get('주요제품', '-')}</td></tr>
        </table>
        
        <h3 class="subsection-title" style="margin-top:20px;">◆ 기업신용등급 / EW등급</h3>
        <div style="display:flex;gap:30px;margin-bottom:20px;">
            <div style="flex:1;text-align:center;padding:16px;background:#F8F9FC;border-radius:12px;border:1px solid #E5E7EB;">
                <div style="font-size:14px;color:#666;margin-bottom:8px;">기업신용등급</div>
                {grade_html}
            </div>
            <div style="flex:1;text-align:center;padding:16px;background:#F8F9FC;border-radius:12px;border:1px solid #E5E7EB;">
                <div style="font-size:14px;color:#666;margin-bottom:8px;">EW 등급</div>
                {ew_html}
            </div>
        </div>
        
        <h3 class="subsection-title">◆ 재무진단 결과</h3>
        <div class="diagnosis-grid">
            {diag_html}
        </div>
    </div>
</div>
"""


def _balance_sheet_page(bs: dict, years: list, year_labels: list) -> str:
    def row(label, key, indent=False):
        cls = ' class="indent"' if indent else ''
        cells = "".join(f"<td class='num'>{fn(bs.get(key, {}).get(y))}</td>" for y in years)
        return f"<tr><td{cls}>{label}</td>{cells}</tr>"
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📊 기업재무분석</span>
        <span class="page-title-main">요약 재무상태표</span>
    </div>
    <div class="page-body">
        <p class="unit-label">(단위: 천원)</p>
        <div class="two-col-tables">
            <div class="half-table">
                <table class="data-table financial-table">
                    <thead>
                        <tr><th class="col-label">자산</th>{"".join(f'<th class="col-year">{yl}</th>' for yl in year_labels)}</tr>
                    </thead>
                    <tbody>
                        {row("자산", "자산")}
                        {row("유동자산", "유동자산", True)}
                        {row("현금및현금성자산", "현금및현금성자산", True)}
                        {row("매출채권", "매출채권", True)}
                        {row("재고자산", "재고자산", True)}
                        {row("비유동자산", "비유동자산", True)}
                        {row("유형자산", "유형자산", True)}
                    </tbody>
                </table>
            </div>
            <div class="half-table">
                <table class="data-table financial-table">
                    <thead>
                        <tr><th class="col-label">부채 및 자본</th>{"".join(f'<th class="col-year">{yl}</th>' for yl in year_labels)}</tr>
                    </thead>
                    <tbody>
                        {row("부채", "부채")}
                        {row("유동부채", "유동부채", True)}
                        {row("매입채무", "매입채무", True)}
                        {row("비유동부채", "비유동부채", True)}
                        {row("자본", "자본")}
                        {row("자본금", "자본금", True)}
                        {row("이익잉여금", "이익잉여금", True)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
"""


def _income_statement_page(isc: dict, years: list, year_labels: list) -> str:
    def row(label, key, indent=False, bold=False):
        cls_parts = []
        if indent: cls_parts.append("indent")
        if bold: cls_parts.append("bold-row")
        cls = f' class="{" ".join(cls_parts)}"' if cls_parts else ''
        cells = "".join(f"<td class='num'>{fn(isc.get(key, {}).get(y))}</td>" for y in years)
        return f"<tr><td{cls}>{label}</td>{cells}</tr>"
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📊 기업재무분석</span>
        <span class="page-title-main">요약 손익계산서</span>
    </div>
    <div class="page-body">
        <p class="unit-label">(단위: 천원)</p>
        <div class="two-col-tables">
            <div class="half-table">
                <table class="data-table financial-table">
                    <thead>
                        <tr><th class="col-label">손익계정</th>{"".join(f'<th class="col-year">{yl}</th>' for yl in year_labels)}</tr>
                    </thead>
                    <tbody>
                        {row("매출액", "매출액", bold=True)}
                        {row("매출원가", "매출원가", True)}
                        {row("매출총이익(손실)", "매출총이익")}
                        {row("판매비와관리비", "판관비", True)}
                        {row("급여", "급여", True)}
                        {row("퇴직급여", "퇴직급여", True)}
                        {row("복리후생비", "복리후생비", True)}
                        {row("지급수수료", "지급수수료", True)}
                        {row("감가상각비", "감가상각비", True)}
                        {row("운반비", "운반비", True)}
                        {row("영업이익(손실)", "영업이익", bold=True)}
                    </tbody>
                </table>
            </div>
            <div class="half-table">
                <table class="data-table financial-table">
                    <thead>
                        <tr><th class="col-label">손익계정</th>{"".join(f'<th class="col-year">{yl}</th>' for yl in year_labels)}</tr>
                    </thead>
                    <tbody>
                        {row("영업외수익", "영업외수익")}
                        {row("영업외비용", "영업외비용")}
                        {row("법인세차감전순이익", "법인세차감전순이익", bold=True)}
                        {row("법인세비용", "법인세비용", True)}
                        {row("당기순이익(순손실)", "당기순이익", bold=True)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
"""


def _financial_summary_page(bs: dict, isc: dict, years: list, year_labels: list) -> str:
    """재무현황 개요 - 차트 느낌의 요약 테이블"""
    rows = ""
    items = [
        ("자산", "자산", bs), ("부채", "부채", bs), ("자본", "자본", bs),
        ("매출액", "매출액", isc), ("영업이익", "영업이익", isc), ("당기순이익", "당기순이익", isc),
    ]
    for label, key, src in items:
        cells = "".join(f"<td class='num'>{format_number(src.get(key, {}).get(y), '억원')}</td>" for y in years)
        rows += f"<tr><td class='bold-row'>{label}</td>{cells}</tr>\n"
    
    # 증가율 행
    for label, key, src in [("매출액증가율%", "매출액", isc), ("영업이익률%", "영업이익", isc)]:
        cells = ""
        for i, y in enumerate(years):
            if "증가율" in label and i > 0:
                curr = src.get(key.replace("증가율", ""), {}).get(y)
                prev = src.get(key.replace("증가율", ""), {}).get(years[i-1])
                if curr and prev and prev != 0:
                    val = (curr - prev) / abs(prev) * 100
                    cells += f"<td class='num'>{val:.1f}%</td>"
                else:
                    cells += "<td class='num'>-</td>"
            elif "이익률" in label:
                rev = isc.get("매출액", {}).get(y)
                op = isc.get("영업이익", {}).get(y)
                if rev and op and rev != 0:
                    cells += f"<td class='num'>{op/rev*100:.1f}%</td>"
                else:
                    cells += "<td class='num'>-</td>"
            else:
                cells += "<td class='num'>-</td>"
        rows += f"<tr><td>{label}</td>{cells}</tr>\n"
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📊 기업재무분석</span>
        <span class="page-title-main">재무현황 개요</span>
    </div>
    <div class="page-body">
        <p class="unit-label">(단위: 천원)</p>
        <table class="data-table financial-table full-width">
            <thead>
                <tr><th class="col-label">구분</th>{"".join(f'<th class="col-year">{yl}</th>' for yl in year_labels)}</tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
</div>
"""


def _ratio_analysis_page(ratios: dict, years: list, year_labels: list) -> str:
    """재무비율 분석 (1) - 안정성/수익성"""
    from parsers.financial_ratios import evaluate_ratio
    
    def ratio_row(label, key):
        cells = ""
        for y in years:
            val = ratios.get(key, {}).get(y)
            grade = evaluate_ratio(key, val)
            grade_cls = {"우수": "grade-good", "양호": "grade-ok", "위험": "grade-bad"}.get(grade, "")
            cells += f"<td class='num'>{fp(val)}</td><td class='grade {grade_cls}'>{grade}</td>"
        return f"<tr><td class='ratio-name'>{label}</td>{cells}</tr>"
    
    yr_heads = ""
    for yl in year_labels:
        yr_heads += f'<th class="col-year" colspan="2">{yl}</th>'
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📊 기업재무분석</span>
        <span class="page-title-main">재무비율 분석 (1)</span>
    </div>
    <div class="page-body">
        <h3 class="subsection-title">◆ 안정성 지표</h3>
        <table class="data-table ratio-table">
            <thead>
                <tr><th class="col-label">재무비율</th>{yr_heads}</tr>
                <tr><th></th>{"".join('<th>값</th><th>평가</th>' for _ in years)}</tr>
            </thead>
            <tbody>
                {ratio_row("부채비율", "부채비율")}
                {ratio_row("유동비율", "유동비율")}
                {ratio_row("차입금의존도", "차입금의존도")}
            </tbody>
        </table>
        
        <h3 class="subsection-title" style="margin-top:30px;">◆ 수익성 지표</h3>
        <table class="data-table ratio-table">
            <thead>
                <tr><th class="col-label">재무비율</th>{yr_heads}</tr>
                <tr><th></th>{"".join('<th>값</th><th>평가</th>' for _ in years)}</tr>
            </thead>
            <tbody>
                {ratio_row("매출총이익률", "매출총이익률")}
                {ratio_row("영업이익률", "영업이익률")}
                {ratio_row("매출순이익률", "매출순이익률")}
                {ratio_row("ROE (자기자본이익률)", "ROE")}
                {ratio_row("ROA (총자산이익률)", "ROA")}
            </tbody>
        </table>
    </div>
</div>
"""


def _ratio_analysis_page2(ratios: dict, years: list, year_labels: list) -> str:
    """재무비율 분석 (2) - 성장성/활동성"""
    from parsers.financial_ratios import evaluate_ratio
    
    def ratio_row(label, key):
        cells = ""
        for y in years:
            val = ratios.get(key, {}).get(y)
            grade = evaluate_ratio(key, val)
            grade_cls = {"우수": "grade-good", "양호": "grade-ok", "위험": "grade-bad"}.get(grade, "")
            cells += f"<td class='num'>{fp(val)}</td><td class='grade {grade_cls}'>{grade}</td>"
        return f"<tr><td class='ratio-name'>{label}</td>{cells}</tr>"
    
    def ratio_row_plain(label, key):
        cells = ""
        for y in years:
            val = ratios.get(key, {}).get(y)
            if val is not None:
                cells += f"<td class='num'>{val:.2f}회전</td>"
            else:
                cells += "<td class='num'>-</td>"
            cells += "<td></td>"
        return f"<tr><td class='ratio-name'>{label}</td>{cells}</tr>"
    
    yr_heads = ""
    for yl in year_labels:
        yr_heads += f'<th class="col-year" colspan="2">{yl}</th>'
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📊 기업재무분석</span>
        <span class="page-title-main">재무비율 분석 (2)</span>
    </div>
    <div class="page-body">
        <h3 class="subsection-title">◆ 성장성 지표</h3>
        <table class="data-table ratio-table">
            <thead>
                <tr><th class="col-label">재무비율</th>{yr_heads}</tr>
                <tr><th></th>{"".join('<th>값</th><th>평가</th>' for _ in years)}</tr>
            </thead>
            <tbody>
                {ratio_row("총자산증가율", "총자산증가율")}
                {ratio_row("매출액증가율", "매출액증가율")}
                {ratio_row("자기자본증가율", "자기자본증가율")}
            </tbody>
        </table>
        
        <h3 class="subsection-title" style="margin-top:30px;">◆ 활동성 지표</h3>
        <table class="data-table ratio-table">
            <thead>
                <tr><th class="col-label">재무비율</th>{yr_heads}</tr>
                <tr><th></th>{"".join('<th>값</th><th>평가</th>' for _ in years)}</tr>
            </thead>
            <tbody>
                {ratio_row_plain("총자산회전율", "총자산회전율")}
                {ratio_row_plain("재고자산회전율", "재고자산회전율")}
                {ratio_row_plain("매출채권회전율", "매출채권회전율")}
            </tbody>
        </table>
    </div>
</div>
"""


def _expense_analysis_page(isc: dict, years: list, year_labels: list) -> str:
    """주요 경비율 분석"""
    rows = ""
    items = [
        ("매출원가", "매출원가"), ("급여", "급여"), ("임차료", "임차료"), ("보험료", "보험료"),
    ]
    for label, key in items:
        row = f"<tr><td class='bold-row'>{label}</td>"
        for y in years:
            val = isc.get(key, {}).get(y)
            row += f"<td class='num'>{fn(val)}</td>"
        row += "</tr>\n"
        # 비율 행
        row += f"<tr><td class='indent'>({label}/매출액)</td>"
        for y in years:
            val = isc.get(key, {}).get(y)
            rev = isc.get("매출액", {}).get(y)
            if val and rev and rev != 0:
                row += f"<td class='num'>{val/rev*100:.1f}%</td>"
            else:
                row += "<td class='num'>-</td>"
        row += "</tr>\n"
        rows += row
    
    # 매출액 행
    rows += f"<tr class='total-row'><td class='bold-row'>매출액</td>"
    for y in years:
        rows += f"<td class='num'>{fn(isc.get('매출액', {}).get(y))}</td>"
    rows += "</tr>"
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📊 기업재무분석</span>
        <span class="page-title-main">주요 경비율 분석</span>
    </div>
    <div class="page-body">
        <div class="info-box">
            주요 경비는 매출원가, 인건비, 임차료로 구성됩니다. 최근 결산 기준 매출액 대비 주요 경비율을 분석합니다.
        </div>
        <p class="unit-label">(단위: 천원)</p>
        <table class="data-table financial-table full-width">
            <thead>
                <tr><th class="col-label">계정명</th>{"".join(f'<th class="col-year">{yl}</th>' for yl in year_labels)}</tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
</div>
"""


def _valuation_page(valuation: dict, company: dict) -> str:
    """기업가치평가 페이지"""
    if not valuation:
        return ""
    
    total_val = valuation.get("기업가치", 0)
    per_share = valuation.get("1주당평가액", 0)
    shares = valuation.get("주식수", 0)
    
    # 미래 가치 예측 (연 5% 성장 가정)
    future_rows = ""
    base_val = total_val
    for i, yr_offset in enumerate([0, 2, 3, 5, 7, 12, 17, 22]):
        import datetime
        base_year = int(valuation.get("기준일", "2024")[:4])
        future_year = base_year + yr_offset
        future_val = base_val * (1.05 ** yr_offset)
        future_per = future_val / shares if shares else 0
        future_rows += f"""
        <tr>
            <td>{future_year}년</td>
            <td class="num">{format_number(future_val / 1000, '억원')}</td>
            <td class="num">{format_number(future_per, '원')}</td>
        </tr>"""
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📈 기업가치평가</span>
        <span class="page-title-main">비상장주식 가치평가</span>
    </div>
    <div class="page-body">
        <div class="valuation-summary">
            <div class="val-box">
                <div class="val-label">기업가치</div>
                <div class="val-amount">{format_number(total_val / 1000, '억원')}</div>
            </div>
            <div class="val-box">
                <div class="val-label">1주당 주식가액</div>
                <div class="val-amount">{format_number(per_share, '원')}</div>
            </div>
        </div>
        <p class="val-basis">평가기준일 {valuation.get('기준일', '')}</p>
        
        <h3 class="subsection-title">◆ 연도별 기업가치 예상 추이</h3>
        <p class="val-note">※ 연 5% 성장률 가정 (상증세법상 보충적 평가방법 기준)</p>
        <table class="data-table financial-table">
            <thead>
                <tr><th>연도</th><th>기업가치</th><th>1주당 주식가액</th></tr>
            </thead>
            <tbody>{future_rows}</tbody>
        </table>
        
        <div class="info-box" style="margin-top:20px;">
            <strong>산출 근거</strong><br>
            순자산가치(1주당): {format_number(valuation.get('순자산가치_1주당', 0), '원')}<br>
            순손익가치(1주당): {format_number(valuation.get('순손익가치_1주당', 0), '원')}<br>
            1주당 평가액 = (순자산가치 × 2 + 순손익가치 × 3) ÷ 5
        </div>
    </div>
</div>
"""


def _credit_page(company: dict, credit: dict) -> str:
    """신용등급 관리 페이지"""
    grade = credit.get("현재등급", company.get("기업신용등급", "-"))
    ew = company.get("EW등급", "-")
    
    history_rows = ""
    for item in credit.get("등급이력", []):
        history_rows += f"<tr><td>{item.get('등급', '-')}</td><td>{item.get('평가일자', '-')}</td><td>{item.get('재무기준일자', '-')}</td></tr>"
    
    cr_rows = ""
    for item in credit.get("현금흐름등급", []):
        cr_rows += f"<tr><td>{item.get('기준일자', '-')}</td><td>{item.get('등급', '-')}</td></tr>"
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">🏦 신용등급 관리</span>
        <span class="page-title-main">기업 신용등급 현황</span>
    </div>
    <div class="page-body">
        <div class="credit-summary">
            <div class="credit-box">
                <div class="credit-label">기업신용등급</div>
                <div class="credit-grade">{grade}</div>
            </div>
            <div class="credit-box">
                <div class="credit-label">EW 등급</div>
                <div class="credit-grade ew-{ew}">{ew}</div>
            </div>
        </div>
        
        <div class="info-box">
            {credit.get('등급설명', '채무상환능력이 우량하나, 상위등급에 비해 경기침체 및 환경악화의 영향을 받기 쉬움')}
        </div>
        
        {f'''<h3 class="subsection-title" style="margin-top:20px;">◆ 현금흐름등급 이력</h3>
        <table class="data-table financial-table">
            <thead><tr><th>재무기준일자</th><th>등급</th></tr></thead>
            <tbody>{cr_rows}</tbody>
        </table>''' if cr_rows else ''}
    </div>
</div>
"""


def get_css() -> str:
    """리포트 CSS - sample.pdf 스타일 재현"""
    return """
@page {
    size: 1330px 940px;
    margin: 0;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    font-size: 13px;
    color: #333;
    line-height: 1.5;
    background: #E0E0E0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 0;
}

.page {
    width: 1330px;
    height: 940px;
    page-break-after: always;
    page-break-inside: avoid;
    position: relative;
    overflow: hidden;
    background: white;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12);
}

@media print {
    .page { 
        height: 940px; 
        overflow: hidden; 
        margin-bottom: 0; 
        box-shadow: none; 
    }
}

/* ── Cover Page ── */
.cover-page { background: linear-gradient(135deg, #4A5FC1 0%, #3B4CA8 50%, #2D3D8F 100%); }
.cover-bg { padding: 120px 100px; color: white; height: 85%; }
.cover-company { font-size: 28px; margin-bottom: 10px; font-weight: 400; }
.cover-title { font-size: 56px; font-weight: 800; margin-bottom: 30px; }
.cover-line { width: 80px; height: 4px; background: white; margin-bottom: 40px; }
.cover-info { font-size: 18px; }
.cover-info-row { margin-bottom: 8px; }
.cover-label { display: inline-block; width: 80px; color: rgba(255,255,255,0.8); }
.cover-footer { position: absolute; bottom: 0; width: 100%; padding: 20px 100px; background: white; }
.cover-disclaimer { font-size: 10px; color: #999; }

/* ── TOC Page ── */
.toc-page { padding: 60px 100px; }
.toc-header { font-size: 36px; font-weight: 800; color: #4A5FC1; margin-bottom: 60px; border-top: 3px solid #4A5FC1; padding-top: 20px; }
.toc-grid { display: flex; flex-direction: column; gap: 30px; max-width: 600px; }
.toc-item { display: flex; align-items: center; gap: 15px; font-size: 20px; }
.toc-icon { font-size: 28px; }
.toc-text { flex: 1; font-weight: 600; }
.toc-page-num { color: #999; }

/* ── Section Divider ── */
.section-divider { display: flex; }
.divider-left { width: 45%; background: #F0F2F8; }
.divider-right { width: 55%; display: flex; flex-direction: column; justify-content: center; padding-left: 60px; }
.divider-line { width: 100%; height: 2px; background: #4A5FC1; margin-bottom: 30px; }
.divider-title { font-size: 48px; font-weight: 800; color: #4A5FC1; }

/* ── Content Pages ── */
.content-page { padding: 40px 60px; }
.page-header { display: flex; align-items: baseline; gap: 20px; margin-bottom: 30px; border-bottom: 2px solid #E5E7EB; padding-bottom: 15px; }
.section-badge { font-size: 14px; color: #666; }
.page-title-main { font-size: 28px; font-weight: 800; color: #333; }

.page-body { }
.subsection-title { font-size: 16px; font-weight: 700; color: #333; margin-bottom: 15px; }
.unit-label { text-align: right; font-size: 12px; color: #999; margin-bottom: 8px; }
.info-box { background: #F8F9FC; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; font-size: 13px; color: #555; line-height: 1.7; }

/* ── Tables ── */
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { background: #4A5FC1; color: white; padding: 10px 12px; text-align: center; font-weight: 600; }
.data-table td { padding: 8px 12px; border-bottom: 1px solid #E5E7EB; }
.data-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.data-table td.indent { padding-left: 30px; color: #555; }
.data-table td.bold-row, .data-table .bold-row td { font-weight: 700; }
.data-table .total-row td { border-top: 2px solid #333; font-weight: 700; }
.data-table td.label-cell { background: #F8F9FC; font-weight: 600; width: 120px; color: #555; }

.company-table td { padding: 10px 15px; }
.col-label { text-align: left !important; }
.col-year { text-align: center; }

.two-col-tables { display: flex; gap: 30px; }
.half-table { flex: 1; }
.full-width { width: 100%; }

/* ── Ratio Table ── */
.ratio-table td.grade { text-align: center; font-weight: 700; font-size: 12px; }
.grade-good { color: #2E7D32; }
.grade-ok { color: #F57F17; }
.grade-bad { color: #C62828; }
.ratio-name { font-weight: 600; }

/* ── Diagnosis Grid ── */
.diagnosis-grid { display: flex; gap: 20px; margin-top: 10px; }
.diag-item { flex: 1; text-align: center; padding: 20px; border-radius: 12px; border: 2px solid #E5E7EB; }
.diag-label { font-size: 14px; color: #666; margin-bottom: 10px; }
.diag-value { font-size: 22px; font-weight: 800; }
.diag-우수 { color: #2E7D32; }
.diag-양호 { color: #4A5FC1; }
.diag-보통 { color: #F57F17; }
.diag-미흡 { color: #E65100; }
.diag-열위 { color: #C62828; }

/* ── Valuation ── */
.valuation-summary { display: flex; gap: 30px; margin-bottom: 20px; }
.val-box { flex: 1; text-align: center; padding: 30px; background: #F8F9FC; border-radius: 12px; border: 1px solid #E5E7EB; }
.val-label { font-size: 14px; color: #666; margin-bottom: 8px; }
.val-amount { font-size: 32px; font-weight: 800; color: #4A5FC1; }
.val-basis { font-size: 12px; color: #999; margin-bottom: 20px; }
.val-note { font-size: 12px; color: #999; margin-bottom: 10px; }

/* ── Credit ── */
.credit-summary { display: flex; gap: 30px; margin-bottom: 20px; }
.credit-box { flex: 1; text-align: center; padding: 30px; background: #F8F9FC; border-radius: 12px; }
.credit-label { font-size: 14px; color: #666; margin-bottom: 10px; }
.credit-grade { font-size: 48px; font-weight: 800; color: #4A5FC1; }
.ew-정상 { color: #2E7D32; }
.ew-주의 { color: #F57F17; }
.ew-경고 { color: #E65100; }
.ew-위험 { color: #C62828; }

/* ── Footer ── */
.page-footer { position: absolute; bottom: 20px; left: 60px; right: 60px; display: flex; justify-content: space-between; font-size: 11px; color: #999; }

/* ── TOC Enhanced ── */
.toc-row { display: flex; gap: 60px; margin-bottom: 25px; }
.toc-row .toc-item { flex: 1; display: flex; align-items: center; gap: 12px; }
.toc-dots { flex: 1; border-bottom: 2px dotted #ccc; margin: 0 8px; min-width: 30px; }

/* ── Card Layouts ── */
.card-grid { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }
.card { flex: 1; min-width: 280px; background: #F8F9FC; border-radius: 12px; padding: 24px; border: 1px solid #E5E7EB; }
.card-title { font-size: 16px; font-weight: 700; color: #4A5FC1; margin-bottom: 10px; }
.card-desc { font-size: 13px; color: #555; line-height: 1.7; }
.card-icon { font-size: 32px; margin-bottom: 10px; }

.highlight-box { background: #4A5FC1; color: white; border-radius: 12px; padding: 20px 28px; margin-bottom: 20px; }
.highlight-box .hl-title { font-size: 18px; font-weight: 700; margin-bottom: 6px; }
.highlight-box .hl-desc { font-size: 13px; opacity: 0.9; line-height: 1.6; }

.step-list { margin: 16px 0; }
.step-item { display: flex; gap: 14px; margin-bottom: 14px; align-items: flex-start; }
.step-num { background: #4A5FC1; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.step-content { font-size: 13px; color: #333; line-height: 1.6; padding-top: 3px; }

.check-grid { display: flex; gap: 16px; flex-wrap: wrap; }
.check-item { display: flex; gap: 8px; align-items: center; font-size: 13px; color: #333; }
.check-icon { color: #4A5FC1; font-weight: 700; }

.two-col { display: flex; gap: 30px; }
.two-col > div { flex: 1; }

.warning-box { background: #FFF3E0; border: 1px solid #FFB74D; border-radius: 8px; padding: 14px 18px; margin: 16px 0; font-size: 13px; color: #E65100; }

/* ── Labor Table ── */
.labor-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.labor-table th { background: #F0F2F8; padding: 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #4A5FC1; }
.labor-table td { padding: 10px; border-bottom: 1px solid #E5E7EB; vertical-align: top; }
.labor-table .category { background: #F8F9FC; font-weight: 600; width: 80px; }
.labor-table .item-name { font-weight: 600; color: #4A5FC1; width: 100px; }
.badge { display: inline-block; background: #E8EAF6; color: #4A5FC1; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }

/* ── Subsidy Cards ── */
.subsidy-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.subsidy-title { font-size: 16px; font-weight: 700; color: #333; margin-bottom: 12px; }
.subsidy-row { display: flex; gap: 20px; margin-bottom: 8px; }
.subsidy-label { font-weight: 600; color: #4A5FC1; width: 70px; flex-shrink: 0; }
.subsidy-value { font-size: 13px; color: #333; line-height: 1.6; }
"""


# ════════════════════════════════════════════════════════
# 신규 섹션 함수들
# ════════════════════════════════════════════════════════

def _tax_reference_page() -> str:
    """[참고] 비상장주식 양도 및 증여 시 세금"""
    return """
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📈 기업가치평가</span>
        <span class="page-title-main">[참고] 비상장주식 양도 및 증여 시 세금</span>
    </div>
    <div class="page-body">
        <div class="two-col">
            <div>
                <h3 class="subsection-title">◆ 주식 양도소득 세율</h3>
                <table class="data-table financial-table">
                    <thead><tr><th>비상장주식</th><th>세율</th></tr></thead>
                    <tbody>
                        <tr><td>대주주 이외</td><td class="num">10%</td></tr>
                        <tr><td>대주주 (과표 3억 이하)</td><td class="num">20%</td></tr>
                        <tr><td>대주주 (과표 3억 초과)</td><td class="num">25%</td></tr>
                        <tr><td>중견기업 대주주 1년 미만 보유</td><td class="num">30%</td></tr>
                    </tbody>
                </table>
                <p style="font-size:11px;color:#999;margin-top:8px;">※ 주식양도소득공제 연 250만원 (해외주식 합산)<br>※ 양도소득세의 10%를 지방소득세로 별도 납부</p>
                
                <h3 class="subsection-title" style="margin-top:24px;">◆ 대주주 구분</h3>
                <table class="data-table financial-table">
                    <thead><tr><th>비상장주식</th><th>구분조건</th></tr></thead>
                    <tbody>
                        <tr><td>지분율</td><td class="num">4% 이상</td></tr>
                        <tr><td>또는 주식가치</td><td class="num">10억원 이상</td></tr>
                    </tbody>
                </table>
            </div>
            <div>
                <h3 class="subsection-title">◆ 상속·증여세율</h3>
                <table class="data-table financial-table">
                    <thead><tr><th>과세표준</th><th>세율</th><th>누진공제액</th></tr></thead>
                    <tbody>
                        <tr><td>1억원 이하</td><td class="num">10%</td><td class="num">-</td></tr>
                        <tr><td>1억원 초과 ~ 5억원 이하</td><td class="num">20%</td><td class="num">1,000만원</td></tr>
                        <tr><td>5억원 초과 ~ 10억원 이하</td><td class="num">30%</td><td class="num">6,000만원</td></tr>
                        <tr><td>10억원 초과 ~ 30억원 이하</td><td class="num">40%</td><td class="num">1억 6,000만원</td></tr>
                        <tr><td>30억원 초과</td><td class="num">50%</td><td class="num">4억 6,000만원</td></tr>
                    </tbody>
                </table>
                <p style="font-size:11px;color:#999;margin-top:8px;">※ 세대 생략 시(조부→손자) 30% 할증과세, 신고세액공제 3%</p>

                <h3 class="subsection-title" style="margin-top:24px;">◆ 증여재산공제액</h3>
                <table class="data-table financial-table">
                    <thead><tr><th>구분</th><th>10년 단위 공제액</th></tr></thead>
                    <tbody>
                        <tr><td>배우자</td><td class="num">6억원</td></tr>
                        <tr><td>직계비속(미성년자)</td><td class="num">2,000만원</td></tr>
                        <tr><td>직계비속(성인)</td><td class="num">5,000만원</td></tr>
                        <tr><td>직계존속</td><td class="num">5,000만원</td></tr>
                        <tr><td>기타친족(사위, 며느리 등)</td><td class="num">1,000만원</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
"""


def _compensation_plan_overview_page() -> str:
    """임원소득보상플랜 필요성"""
    return """
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">👔 임원소득보상플랜</span>
        <span class="page-title-main">임원소득보상플랜 필요성</span>
    </div>
    <div class="page-body">
        <div class="highlight-box">
            <div class="hl-title">" 급여 + 배당 + 퇴직금의 황금비율을 찾으세요 "</div>
            <div class="hl-desc">급여, 배당, 퇴직금을 적절히 배분하면 충분한 보상과 함께 절세효과까지 누릴 수 있습니다.</div>
        </div>

        <div class="info-box" style="margin-bottom:24px;">
            <strong>◆ 임원소득보상플랜이란</strong><br>
            임원이자 주주인 대표이사가 법인으로부터 보상받을 수 있는 급여, 퇴직금, 배당 소득을 절세 및 리스크 차원에서 적절하게 설계합니다.
        </div>

        <div class="card-grid">
            <div class="card">
                <div class="card-icon">💵</div>
                <div class="card-title">임원 급여/상여</div>
                <div class="card-desc">
                    <strong>(근로소득세)</strong><br>
                    임원보수규정 제정<br>
                    급여 수준 적정성 검토를 통한 최적 급여 설계
                </div>
            </div>
            <div class="card">
                <div class="card-icon">🏦</div>
                <div class="card-title">주주배당</div>
                <div class="card-desc">
                    <strong>(배당소득세)</strong><br>
                    정관 중간배당 규정 + 배당정책 수립<br>
                    가족주주 지분설계를 통한 절세 방안
                </div>
            </div>
            <div class="card">
                <div class="card-icon">🎯</div>
                <div class="card-title">임원 퇴직금</div>
                <div class="card-desc">
                    <strong>(퇴직소득세)</strong><br>
                    임원퇴직금규정 제정<br>
                    보험상품 활용 시 법인자금 효율적 운영
                </div>
            </div>
        </div>

        <div class="highlight-box" style="background:#F8F9FC;border:2px solid #4A5FC1;color:#333;">
            <div class="hl-title" style="color:#4A5FC1;">" 임원 퇴직금, 실행을 위해서는 규정 정비와 재원 마련이 필요합니다 "</div>
        </div>

        <div class="two-col">
            <div>
                <h3 class="subsection-title">퇴직소득 인정요건</h3>
                <p class="card-desc">(임원퇴직금규정 정비)</p>
                <div class="step-list">
                    <div class="step-item"><div class="step-num">1</div><div class="step-content">정관변경 및 임원퇴직급여규정 제정<br><span style="color:#999;">지급 규정은 반드시 임원 전체에 적용되어야 함</span></div></div>
                    <div class="step-item"><div class="step-num">2</div><div class="step-content">주주총회의사록 작성 및 공증업무<br><span style="color:#999;">공증은 필수사항은 아니지만 1인주주·가족주주일 경우 권장</span></div></div>
                </div>
            </div>
            <div>
                <h3 class="subsection-title">퇴직금 재원마련</h3>
                <p class="card-desc">(보험상품 활용 시 장점)</p>
                <div class="step-list">
                    <div class="step-item"><div class="step-num">1</div><div class="step-content"><strong>법인자금 효율적 운영</strong><br>퇴직전까지 보험계약대출 가능(유동성 확보 가능)</div></div>
                    <div class="step-item"><div class="step-num">2</div><div class="step-content"><strong>부족한 은퇴자금을 법인에서 준비</strong><br>계약자 변경 통해 보험계약으로 퇴직금 지급 가능</div></div>
                    <div class="step-item"><div class="step-num">3</div><div class="step-content"><strong>CEO 유고 시 리스크 대비</strong><br>보장성 보험 활용 시 CEO 유고 시 리스크 헷지 가능</div></div>
                </div>
            </div>
        </div>
    </div>
</div>
"""


def _retirement_plan_page(isc: dict, bs: dict, company: dict, years: list, year_labels: list) -> str:
    """예상 퇴직금 및 퇴직소득세 검토"""
    # 최근 급여 데이터에서 연봉 추정
    latest = years[-1] if years else ""
    salary = isc.get("급여", {}).get(latest)
    employees = company.get("종업원수", "10명")
    try:
        emp_num = int(''.join(filter(str.isdigit, str(employees)))) or 10
    except:
        emp_num = 10

    avg_salary = (salary * 1000 / emp_num / 10000) if salary else 0  # 만원 단위
    
    # 대표이사 연봉 가정 (전체 인건비의 대표이사 비중 가정)
    ceo_salary_est = max(avg_salary * 1.5, 5000)  # 최소 5천만원

    # 퇴직금 = 연평균급여 × 1/12 × 근속기간 × 지급배수
    tenure_years = 10  # 가정
    severance_1x = ceo_salary_est / 12 * tenure_years
    severance_3x = severance_1x * 3
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">👔 임원소득보상플랜</span>
        <span class="page-title-main">예상 퇴직금 및 퇴직소득세 검토</span>
    </div>
    <div class="page-body">
        <div class="info-box">
            대표이사에게 퇴직금은 현재 회사에 기여한 만큼 급여로 충분히 보상받지 못한 부분을 퇴직 시라도 일정 부분 가져갈 수 있도록 도와주는 장치입니다.
            <strong>퇴직금은 퇴직 시점 기준 직전 3년 연평균 급여에 비례하여 계산</strong>되기 때문에, 은퇴 시 충분한 퇴직금 확보를 위해서는 사전에 <strong>적정한 규모의 급여 설계가 함께 수반</strong>되어야 합니다.
        </div>

        <h3 class="subsection-title">◆ 퇴직금 시뮬레이션</h3>
        <p style="font-size:12px;color:#999;margin-bottom:12px;">※ 대표이사 추정 연봉 기준, 지급배수별 예상 퇴직금(세전)</p>
        
        <table class="data-table financial-table">
            <thead>
                <tr><th>구분</th><th>지급배수 1배</th><th>지급배수 2배</th><th>지급배수 3배</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td class="bold-row">추정 연봉</td>
                    <td class="num" colspan="3">{ceo_salary_est:,.0f}만원</td>
                </tr>
                <tr>
                    <td class="bold-row">근속기간 (가정)</td>
                    <td class="num" colspan="3">{tenure_years}년</td>
                </tr>
                <tr>
                    <td class="bold-row">예상 퇴직금 (세전)</td>
                    <td class="num">{severance_1x:,.0f}만원</td>
                    <td class="num">{severance_1x*2:,.0f}만원</td>
                    <td class="num">{severance_3x:,.0f}만원</td>
                </tr>
                <tr>
                    <td class="bold-row">퇴직소득세 (약 15%)</td>
                    <td class="num">{severance_1x*0.15:,.0f}만원</td>
                    <td class="num">{severance_1x*2*0.15:,.0f}만원</td>
                    <td class="num">{severance_3x*0.15:,.0f}만원</td>
                </tr>
                <tr class="total-row">
                    <td class="bold-row">예상 퇴직금 (세후)</td>
                    <td class="num">{severance_1x*0.85:,.0f}만원</td>
                    <td class="num">{severance_1x*2*0.85:,.0f}만원</td>
                    <td class="num">{severance_3x*0.85:,.0f}만원</td>
                </tr>
            </tbody>
        </table>
        
        <div class="warning-box" style="margin-top:20px;">
            ⚠️ <strong>임원퇴직금규정</strong>이 없다면, 임원이 퇴직하는 날로부터 소급하여 1년 총급여액의 1/10 × 근속기간으로 계산한 퇴직금에 대해 세법상 손금산입 가능합니다.
            규정이 있으면 <strong>지급배수를 최대 3배까지 적용</strong>하여 전액 비용처리가 가능합니다.
        </div>

        <h3 class="subsection-title" style="margin-top:20px;">◆ 연봉가정별 예상 퇴직금(세전) 비교</h3>
        <table class="data-table financial-table">
            <thead><tr><th>연봉 가정</th><th>당해연도 말 (1배)</th><th>10년 후 (3배)</th></tr></thead>
            <tbody>
                <tr><td>연봉 1.00억원</td><td class="num">{10000/12*tenure_years:,.0f}만원</td><td class="num">{10000/12*tenure_years*3:,.0f}만원</td></tr>
                <tr><td>연봉 1.50억원</td><td class="num">{15000/12*tenure_years:,.0f}만원</td><td class="num">{15000/12*tenure_years*3:,.0f}만원</td></tr>
                <tr><td>연봉 2.50억원</td><td class="num">{25000/12*tenure_years:,.0f}만원</td><td class="num">{25000/12*tenure_years*3:,.0f}만원</td></tr>
            </tbody>
        </table>
    </div>
</div>
"""


def _dividend_strategy_page() -> str:
    """배당을 통한 CEO 자산관리 전략"""
    return """
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">💰 배당플랜</span>
        <span class="page-title-main">배당을 통한 CEO 자산관리 전략</span>
    </div>
    <div class="page-body">
        <div class="highlight-box">
            <div class="hl-title">가족주주 지분설계와 배당정책이 왜 필요할까요?</div>
        </div>

        <div class="info-box">
            <strong>◆ 배당(Dividend)</strong>이란 기업이 일정 기간 동안 영업활동을 해 발생한 이익 중 일부를 주주들에게 나눠주는 것을 말합니다.
            배당은 미처분이익잉여금 한도 내에서 지급할 수 있으며, 금전뿐만 아니라 현물 또는 주식 배당도 가능합니다.
        </div>

        <div class="card-grid">
            <div class="card">
                <div class="card-icon">1️⃣</div>
                <div class="card-title">대표이사의 세부담 경감</div>
                <div class="card-desc">대표이사의 급여와 배당을 적절하게 혼합설계하면 개인의 세금부담을 줄일 수 있으며, 절세 금액 만큼 개인의 재투자 자산을 만들 수 있습니다.</div>
            </div>
            <div class="card">
                <div class="card-icon">2️⃣</div>
                <div class="card-title">자녀의 자금출처 재원 마련</div>
                <div class="card-desc">소득 없는 자녀명의의 부동산을 구매하거나, 자녀를 계약자·수익자로 하는 종신보험계약을 체결할 수 있습니다. (상속세 제외자산)</div>
            </div>
        </div>
        <div class="card-grid">
            <div class="card">
                <div class="card-icon">3️⃣</div>
                <div class="card-title">미처분이익잉여금 진단·관리</div>
                <div class="card-desc">정기적인 배당을 통해 매년 미처분이익잉여금 적정성을 진단하고, 주식가치 평가를 통해 향후 주식이동, 기업정리 시 등의 문제들을 미리 준비할 수 있습니다.</div>
            </div>
            <div class="card">
                <div class="card-icon">4️⃣</div>
                <div class="card-title">자산배분차원에서 필요성</div>
                <div class="card-desc">현재 경영하고 있는 기업 주식에 몰빵투자되어 있는 중소기업 CEO의 자산구조를 현금화된 배당을 통해 안전자산으로 분산투자 할 수 있습니다.</div>
            </div>
        </div>

        <div class="info-box" style="background:#E8EAF6;">
            <strong>배당 정책의 주요전략</strong><br>
            ✅ 배우자, 자녀 등 <strong>가족주주를 고려한 지분설계</strong>를 진행합니다.<br>
            ✅ 매년 법인의 <strong>미처분이익잉여금을 진단</strong>하고 배당정책을 수립합니다.<br>
            ✅ 정기배당 이외에도 <strong>중간배당</strong>을 통해 탄력적인 배당을 실행합니다.<br>
            ✅ 필요시 <strong>현물배당과 차등(초과)배당</strong>을 적절히 혼합설계하여 실행합니다.
        </div>
    </div>
</div>
"""


def _retained_earnings_page(bs: dict, isc: dict, years: list, year_labels: list) -> str:
    """미처분이익잉여금 분석"""
    rows = ""
    for y, yl in zip(years, year_labels):
        ni = isc.get("당기순이익", {}).get(y)
        re = bs.get("미처분이익잉여금", {}).get(y)
        ni_str = format_number(ni, "억원") if ni else "-"
        re_str = format_number(re, "억원") if re else "-"
        rows += f"<tr><td class='bold-row'>{yl}</td><td class='num'>{ni_str}</td><td class='num'>{re_str}</td></tr>\n"
    
    # 미래 예측 (미처분이익잉여금 증가 추이)
    latest_re = bs.get("미처분이익잉여금", {}).get(years[-1]) if years else 0
    latest_ni = isc.get("당기순이익", {}).get(years[-1]) if years else 0
    if latest_re is None: latest_re = 0
    if latest_ni is None: latest_ni = 0
    
    future_rows = ""
    base_year = int(years[-1][:4]) if years else 2024
    accumulated = latest_re
    for offset in [2, 3, 5, 7]:
        accumulated += latest_ni * offset / 5  # 간이 추정
        fy = base_year + offset
        future_rows += f"<tr><td>{fy}년</td><td class='num'>{format_number(accumulated, '억원')}</td></tr>\n"
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">💰 배당플랜</span>
        <span class="page-title-main">미처분이익잉여금 분석</span>
    </div>
    <div class="page-body">
        <div class="info-box">
            대다수 중소기업은 <strong>매출채권, 재고자산, 시설투자 등의 형태로 이익잉여금을 유보</strong>하고 현금성 자산이 아니라는 이유로 
            <strong>매년 증가하는 미처분이익잉여금을 인식하지 못하고</strong> 있습니다.
            미처분이익잉여금의 과도한 증가는 주식가치를 높여 기업의 청산, 양도, 증여, 상속 시 세부담을 높이는 원인이 되므로 적정 수준으로 관리해야 합니다.
        </div>

        <h3 class="subsection-title">◆ 직전 3년 미처분이익잉여금 현황</h3>
        <table class="data-table financial-table">
            <thead><tr><th>구분</th><th>당기순이익</th><th>미처분이익잉여금(결손금)</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>

        <h3 class="subsection-title" style="margin-top:24px;">◆ 미처분이익잉여금 증가 예상 추이</h3>
        <p style="font-size:12px;color:#999;">※ 현재 수준의 당기순이익 지속 가정</p>
        <table class="data-table financial-table" style="max-width:400px;">
            <thead><tr><th>연도</th><th>미처분이익잉여금 (예상)</th></tr></thead>
            <tbody>{future_rows}</tbody>
        </table>

        <div class="warning-box">
            <strong>" 미처분이익잉여금이 쌓이면 어떤 문제가 생기나요? "</strong><br><br>
            ✅ 기업가치를 상승시켜 <strong>상속세 부담 증가</strong><br>
            ✅ 이익잉여금 일시에 처분 시 <strong>종합소득세 부담</strong><br>
            ✅ 기업 청산 시 의제배당으로 <strong>배당소득세 부담 증가</strong>
        </div>
    </div>
</div>
"""


def _corporate_governance_page(company: dict) -> str:
    """기업제도정비 - 정관개정 주요 확인사항"""
    # 기업인증 정보
    cert_venture = company.get("기업인증", {}).get("벤처", "미인증") if isinstance(company.get("기업인증"), dict) else "-"
    
    return """
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📋 기업제도정비</span>
        <span class="page-title-main">정관전면 개정 주요 확인사항</span>
    </div>
    <div class="page-body">
        <div class="highlight-box">
            <div class="hl-title">" 법인 이익에 대한 Tax Consulting은 정관의 정비부터 출발합니다. "</div>
        </div>
        
        <div class="two-col" style="margin-bottom:20px;">
            <div class="info-box">
                비상장법인의 경우 회사의 설립 시 작성되었던 <strong>오래된 과거의 원시정관이 한번도 개정되지 않고 그대로인 상태</strong>가 많습니다.
            </div>
            <div class="info-box">
                이 경우 <strong>개정된 상법의 규정이 반영 되지 않는</strong> 것은 물론이고 효율적인 Tax Consulting을 수행할 수 없게 됩니다.
            </div>
        </div>

        <h3 class="subsection-title">◆ 정관컨설팅 주요내용</h3>
        <div class="card-grid">
            <div class="card">
                <div class="card-icon">💰</div>
                <div class="card-title">임원의 보수 및 퇴직금 규정</div>
                <div class="card-desc">주주총회결의를 통한 임원보수 및 퇴직금지급규정 제정 목적</div>
            </div>
            <div class="card">
                <div class="card-icon">💵</div>
                <div class="card-title">이익배당 및 중간배당 규정</div>
                <div class="card-desc">현금배당 이외 현물배당, 주식배당 및 중간배당 설계 목적</div>
            </div>
        </div>
        <div class="card-grid">
            <div class="card">
                <div class="card-icon">🔒</div>
                <div class="card-title">주식양도 제한 규정 <span class="badge">등기</span></div>
                <div class="card-desc">주주 이외 제3자에게 주식양도 제한 (비상장법인 경영권 보호)</div>
            </div>
            <div class="card">
                <div class="card-icon">⭐</div>
                <div class="card-title">주식매수선택권 (스톡옵션) <span class="badge">등기</span></div>
                <div class="card-desc">핵심인재 로열티 제고 목적, 일정기간 재직 후 주주로 참여 가능</div>
            </div>
        </div>
        <div class="card-grid">
            <div class="card">
                <div class="card-icon">📄</div>
                <div class="card-title">신주인수권 (주식의 발행과 배정)</div>
                <div class="card-desc">신주 발행 시 기존 주주 이외 자(외부 투자자)에게 주식 배정 시</div>
            </div>
            <div class="card">
                <div class="card-icon">🏢</div>
                <div class="card-title">자기주식취득 / 자기주식 이익소각</div>
                <div class="card-desc">회사가 주주로부터 자기주식 취득 시 상법 절차 (정관 필수 x)<br>자기주식 이익소각 시에는 정관에 관련 규정이 있어야 함</div>
            </div>
        </div>
    </div>
</div>
"""


def _stock_option_page() -> str:
    """주식매수선택권(스톡옵션) 안내"""
    return """
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📋 기업제도정비</span>
        <span class="page-title-main">주식매수선택권(스톡옵션)</span>
    </div>
    <div class="page-body">
        <div class="highlight-box">
            <div class="hl-title">" 주식매수선택권(스톡옵션)은 핵심인재 로열티 제고를 위한 보상제도의 일환입니다. "</div>
        </div>

        <div class="info-box">
            주식매수선택권은 회사가 정관의 규정에 따라 주주총회의 특별결의로 회사의 설립, 경영과 기술혁신 등에 기여하거나, 기여할 수 있는 회사의
            임직원에게 <strong>일정한 기간(행사기간) 내에 미리 정하여진 유리한 가격(행사가격)으로 일정 수량의 자기회사의 주식을 취득할 수 있는 권리</strong>를 부여하는 제도입니다.
        </div>

        <h3 class="subsection-title">◆ 주식매수선택권 부여</h3>
        <div class="two-col">
            <div>
                <table class="data-table financial-table">
                    <thead><tr><th>구분</th><th>내용</th></tr></thead>
                    <tbody>
                        <tr><td>한도</td><td>발행 주식 수 10% 한도</td></tr>
                        <tr><td>행사조건</td><td>최소 2년 재직 후</td></tr>
                        <tr><td>교부방법</td><td>신주발행 또는 자기주식으로 교부</td></tr>
                        <tr><td>과세</td><td>(행사시점 시가 – 행사가액) 차액에 대해 근로소득으로 과세</td></tr>
                    </tbody>
                </table>
            </div>
            <div>
                <h3 class="subsection-title">부여대상</h3>
                <div class="info-box">
                    • 회사 임직원, 협업기관(벤처기업)<br>
                    • 단, 최대주주, 주요주주(지분율 10% 이상) 및 그 특수관계인에게는 부여 불가
                </div>
                <div class="info-box" style="background:#E8F5E9;">
                    <strong>🏷 벤처기업 세제혜택</strong><br>
                    • 스톡옵션 행사차액 비과세 한도 <strong>2억원</strong><br>
                    • 비과세 한도 초과하는 행사이익에 대한 소득세를 양도시점에 양도소득세로 납부
                </div>
            </div>
        </div>

        <h3 class="subsection-title" style="margin-top:20px;">◆ 주식매수선택권 행사 프로세스</h3>
        <div class="step-list">
            <div class="step-item"><div class="step-num">1</div><div class="step-content">행사시점 시가 > 행사가격, 스톡옵션 행사 (실무적으로 3년 ~ 5년 사이 분할 행사하도록 함, 원칙은 행사 기한 없음)</div></div>
            <div class="step-item"><div class="step-num">2</div><div class="step-content">주식매수선택권 행사 시 회사는 일반적으로 <strong>신주발행 또는 자기주식으로 교부</strong></div></div>
            <div class="step-item"><div class="step-num">3</div><div class="step-content">(행사시점 시가 – 행사가액) 차액에 대하여 <strong>근로소득으로 과세</strong> (퇴직 후 행사 시 기타소득)</div></div>
        </div>
    </div>
</div>
"""


def _labor_checklist_page(company: dict) -> str:
    """사업장 규모별 노무이슈 체크리스트"""
    emp = company.get("종업원수", "10명")
    industry = company.get("표준산업분류", "")
    
    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">⚖️ 노무 컨설팅</span>
        <span class="page-title-main">사업장 규모별 노무이슈</span>
    </div>
    <div class="page-body">
        <div class="two-col" style="margin-bottom:16px;">
            <div class="info-box">
                <strong>◆ 사업장 현황</strong><br>
                상시근로자수: <strong>{emp}</strong><br>
                업종: {industry if industry else '-'}
            </div>
            <div class="info-box">
                상시근로자 수 상관없이 모든 사업장이 기본적으로 지켜야 하는 기업 노무 규정을 제대로 갖추고 있는지 확인이 필요합니다.
            </div>
        </div>

        <h3 class="subsection-title">◆ 기업노무 체크사항</h3>
        <table class="labor-table">
            <thead>
                <tr><th style="width:80px;">분류</th><th style="width:100px;">항목</th><th>주요 내용</th><th style="width:130px;">위반 시</th><th style="width:50px;">적용</th></tr>
            </thead>
            <tbody>
                <tr><td class="category" rowspan="4">규정</td><td class="item-name">근로계약서</td>
                    <td>• 근로계약서 교부 의무<br>• 근로자명부 함께 작성, 포괄임금 근로계약서 적용<br>• 노동청 근로감독시 가장 먼저 체크하는 규정서식</td>
                    <td>미작성, 미교부시 500만원 벌금</td><td>공통</td></tr>
                <tr><td class="item-name">임금대장</td>
                    <td>• 근로일수, 기본근로시간, 연장·야간·휴일근로시간<br>• 임금구성항목, 임금수준이 체크되어야 함</td>
                    <td>임금체불시 노동청 제출자료</td><td>공통</td></tr>
                <tr><td class="item-name">급여명세서</td>
                    <td>• 급여명세서 교부 의무 (전자문서 교부 가능)<br>• 임금구성항목, 계산방법, 임금공제내역 기재</td>
                    <td>미교부시 500만원 이하 과태료</td><td>공통</td></tr>
                <tr><td class="item-name">평가규정</td>
                    <td>• 부당해고 판단시 가장 이슈가 되는 규정<br>• 수습직, 계약직, 정규직 인사처분시 중요 근거 규정<br>• 회사의 상황에 적합한 평가규정 정립 필수</td>
                    <td>-</td><td>공통</td></tr>
                <tr><td class="category" rowspan="2">임금</td><td class="item-name">최저임금 준수</td>
                    <td>• 2026년 최저시급 10,320원(월급여 2,156,800원)</td>
                    <td>-</td><td>공통</td></tr>
                <tr><td class="item-name">주휴수당</td>
                    <td>• 주 15시간 이상 근무 시</td>
                    <td>-</td><td>공통</td></tr>
                <tr><td class="category" rowspan="2">근로시간</td><td class="item-name">주52시간제</td>
                    <td>• 주52시간제 준수, 출근기록부 작성<br>• 휴게시간(8시간 근로 시 1시간 부여)</td>
                    <td>-</td><td>공통</td></tr>
                <tr><td class="item-name">출산·육아휴직</td>
                    <td>• 임신근로자 육아휴직 및 출퇴근시간 조정 신청 가능<br>• 임신여성 출산전후 90일(다태아 120일) 휴가 부여</td>
                    <td>-</td><td>공통</td></tr>
                <tr><td class="category" rowspan="2">계약종료</td><td class="item-name">퇴직금 지급의무</td>
                    <td>• 1년 이상 근로 시, 14일 이내 지급<br>• 초단시간(주 15시간 미만) 근로자 지급 의무 면제</td>
                    <td>-</td><td>공통</td></tr>
                <tr><td class="item-name">해고예고 필수</td>
                    <td>• 해고 30일 전 예고, 30일분 통상임금 지급</td>
                    <td>-</td><td>공통</td></tr>
            </tbody>
        </table>
    </div>
</div>
"""


def _employment_subsidy_page(company: dict) -> str:
    """신청 가능한 고용지원금 — 전체 목록 + 기업규모별 신청 가능 여부"""
    emp_str = company.get("종업원수", "10명")
    try:
        emp_num = int(''.join(filter(str.isdigit, str(emp_str)))) or 10
    except:
        emp_num = 10

    # ── 전체 고용지원금 데이터베이스 ──
    subsidies = [
        # (분류, 지원금명, 지원내용 요약, 지원금액, 대상 최소인원, 대상 최대인원(None=무제한), 비고)
        ("고용창출", "고용촉진장려금", "취업취약계층(장기실업자, 여성가장, 장애인 등)을 고용한 사업주 지원", "월 60만원 (1년간)", 0, None, ""),
        ("고용창출", "신중년 적합직무 고용장려금", "만 50세 이상 구직자를 신중년 적합직무에 채용한 사업주 지원", "월 80만원 (1년간)", 0, None, "우선지원대상기업"),
        ("고용창출", "국내복귀기업 고용지원금", "해외사업장을 축소·청산하고 국내로 복귀한 기업의 신규 채용 지원", "월 60~110만원 (2년간)", 0, None, ""),
        ("고용안정", "고용유지지원금", "경영악화로 고용조정이 불가피한 사업주가 휴업·휴직·훈련 등으로 고용 유지 시 지원", "인건비의 2/3~3/4 (최대 240일)", 0, None, "경영악화 입증 필요"),
        ("고용안정", "고용안정장려금 (워라밸 일자리)", "주 15~30시간 단축근무 전환 시 사업주 및 근로자 지원", "임금감소 보전금 월 40만원 + 사업주 월 30만원", 0, None, ""),
        ("고용안정", "고용안정장려금 (시차출퇴근제)", "시차출퇴근, 선택근무 등 유연근무제 도입 사업주 지원", "월 10~30만원 (1년간)", 0, None, ""),
        ("일·생활균형", "육아휴직 지원금", "30일 이상 육아휴직 허용한 경우 인건비 지원", "월 30만원 (1년간, 최대 360만원)", 0, None, "추가: 첫3개월 월200만원(12개월이내 자녀)"),
        ("일·생활균형", "육아기 근로시간 단축 지원금", "육아기 근로시간 단축을 30일 이상 허용한 경우 지원", "월 30만원 (1년간, 최대 360만원)", 0, None, "최초 도입 시 추가 월10만원"),
        ("일·생활균형", "대체인력 지원금", "육아휴직·근로시간 단축 시 대체인력 채용 사업주 지원", "월 140만원 (2026년 기준)", 0, None, "업무부담자 금전보상시 월20만원"),
        ("일·생활균형", "가족돌봄휴직 지원금", "근로자에게 가족돌봄휴직을 30일 이상 허용한 사업주 지원", "월 30만원 (최대 1년)", 0, None, ""),
        ("직업능력개발", "사업주 직업훈련 지원", "사업주가 근로자에게 직업훈련을 실시하는 경우 훈련비 지원", "훈련비의 60~100% 지원", 0, None, "우선지원대상기업 100%"),
        ("직업능력개발", "국가인적자원개발 컨소시엄", "중소기업 공동훈련을 위한 컨소시엄 참여 시 훈련비 전액 지원", "훈련비 전액 (근로자 무료)", 0, None, ""),
        ("직업능력개발", "일학습병행 지원", "기업이 NCS 기반으로 체계적 OJT를 실시하는 경우 지원", "훈련비 + 기업지원금 월 40~80만원", 0, None, "5인 이상 사업장"),
        ("청년고용", "청년일자리도약장려금", "취업애로청년(만15~34세)을 정규직 채용한 5인 이상 중소기업 지원", "월 60만원 (최대 1년, 720만원)", 5, None, "6개월 이상 고용유지"),
        ("청년고용", "청년내일채움공제", "중소기업 정규직 청년 근로자의 자산형성 지원", "2년간 1,200만원 (기업+정부 적립)", 5, None, "5인 이상 중소기업"),
        ("장애인고용", "장애인 고용장려금", "의무고용률 이상 장애인을 고용한 사업주에게 초과 인원에 대해 지원", "월 30~80만원 (장애 정도별)", 0, None, ""),
        ("장애인고용", "장애인 고용시설·장비 지원", "장애인 근로자를 위한 편의시설 설치, 장비 구입비 지원", "시설 최대 1.5억원, 장비 최대 3천만원", 0, None, ""),
        ("고령자고용", "60세 이상 고령자 고용지원금", "만 60세 이상 근로자를 업종별 고령자 기준고용률 초과 고용 시 지원", "분기당 18만원 (초과 인원당)", 0, None, ""),
        ("고령자고용", "고령자 계속고용장려금", "정년에 도달한 근로자를 정년 이후에도 계속 고용하는 사업주 지원", "월 30만원 (최대 2년)", 0, None, "정년제도 운영 기업"),
        ("사회보험", "두루누리 사회보험 지원", "10인 미만 사업장 사업주 및 근로자 부담 사회보험료 지원", "고용보험+국민연금 보험료 80% 지원", 0, 9, "월보수 270만원 미만 신규가입자"),
    ]

    # 신청 가능 여부 판단
    def is_eligible(min_emp, max_emp):
        if min_emp > emp_num:
            return False
        if max_emp is not None and emp_num > max_emp:
            return False
        return True

    eligible_count = sum(1 for s in subsidies if is_eligible(s[4], s[5]))
    
    # 테이블 행 생성 함수
    def build_rows(sub_list):
        rows = ""
        prev_cat = ""
        cat_counts = {}
        for s in sub_list:
            cat_counts[s[0]] = cat_counts.get(s[0], 0) + 1
        cat_used = {}
        for s in sub_list:
            cat, name, desc, amount, min_e, max_e, note = s
            eligible = is_eligible(min_e, max_e)
            eligible_badge = '<span style="background:#2E7D32;color:white;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">신청가능</span>' if eligible else '<span style="background:#9E9E9E;color:white;padding:2px 8px;border-radius:4px;font-size:11px;">대상외</span>'
            cat_cell = ""
            if cat not in cat_used:
                cat_cell = f'<td class="category" rowspan="{cat_counts[cat]}">{cat}</td>'
                cat_used[cat] = True
            note_str = f'<br><span style="font-size:10px;color:#999;">{note}</span>' if note else ''
            rows += f"""<tr>{cat_cell}<td class="item-name">{name}</td>
                <td>{desc}{note_str}</td>
                <td style="font-size:12px;">{amount}</td>
                <td style="text-align:center;">{eligible_badge}</td></tr>\n"""
        return rows

    # 10개씩 분할
    page1_subs = subsidies[:10]
    page2_subs = subsidies[10:]
    
    table_head = """<table class="labor-table" style="font-size:11px;">
            <thead>
                <tr><th style="width:75px;">분류</th><th style="width:110px;">지원금명</th><th>지원내용 / 조건</th><th style="width:140px;">지원금액</th><th style="width:60px;">신청여부</th></tr>
            </thead>"""

    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">⚖️ 노무 컨설팅</span>
        <span class="page-title-main">신청 가능한 고용지원금 (1/2)</span>
    </div>
    <div class="page-body">
        <div class="two-col" style="margin-bottom:12px;">
            <div class="info-box">
                <strong>◆ 사업장 현황</strong> &nbsp; 상시근로자수: <strong>{emp_str}</strong>
            </div>
            <div class="info-box" style="background:#E8F5E9;border:1px solid #66BB6A;">
                <strong>신청 가능 지원금: {eligible_count}건</strong> / 전체 {len(subsidies)}건
            </div>
        </div>
        {table_head}
            <tbody>{build_rows(page1_subs)}</tbody>
        </table>
    </div>
</div>

<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">⚖️ 노무 컨설팅</span>
        <span class="page-title-main">신청 가능한 고용지원금 (2/2)</span>
    </div>
    <div class="page-body">
        {table_head}
            <tbody>{build_rows(page2_subs)}</tbody>
        </table>
        <p style="font-size:10px;color:#999;margin-top:10px;">※ 모든 고용지원금은 최저임금 준수, 4대보험 가입, 임금체불·중대재해 미발생 기업 대상. 세부 요건은 고용노동부(☎ 1350) 확인 필요.</p>
    </div>
</div>

{_employment_subsidy_detail_page(company)}
"""


def _employment_subsidy_detail_page(company: dict) -> str:
    """고용지원금 상세 — 3페이지로 분할 (카드 2개씩)"""
    emp_str = company.get("종업원수", "10명")
    try:
        emp_num = int(''.join(filter(str.isdigit, str(emp_str)))) or 10
    except:
        emp_num = 10

    durumuri_eligible = "✅ 신청 가능" if emp_num < 10 else "❌ 10인 이상 사업장 (대상 외)"
    youth_eligible = "✅ 신청 가능" if emp_num >= 5 else "❌ 5인 미만 사업장 (대상 외)"

    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">⚖️ 노무 컨설팅</span>
        <span class="page-title-main">주요 고용지원금 상세 (1) — 육아휴직·대체인력</span>
    </div>
    <div class="page-body">
        <div class="subsidy-card">
            <div class="subsidy-title">🍼 육아휴직 지원금</div>
            <div class="info-box" style="margin-bottom:12px;"><strong>30일 이상 육아휴직 허용</strong>한 경우 인건비 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• <strong>(1년간) 인당 최대 360만원 (월 30만원 × 12개월)</strong><br>• (추가지원금) 첫 3개월 월 200만원 * 만 12개월 이내 자녀 육아휴직 신청시 첫 3개월(연속)</div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 육아휴직 종료 후 6개월 이상 계속 고용 후 12개월 이내 신청<br>• 남성육아휴직 1~3호 허용사례까지 월 10만원 인센티브 장려금 추가 지원 (월 40만원 × 12개월)</div></div>
            <div class="subsidy-row"><div class="subsidy-label">2026년<br>변경사항</div><div class="subsidy-value" style="color:#C62828;">• 육아휴직 기간 중 50% 지급 → <strong>100% 지급</strong><br>• 월 120만원 → 30인 미만 사업장 월 <strong>140만원</strong> (30인 이상 사업장 월 130만원)<br>• 복직 후 최대 1개월간 인건비도 지원</div></div>
        </div>

        <div class="subsidy-card">
            <div class="subsidy-title">👶 대체인력 지원금</div>
            <div class="info-box" style="margin-bottom:12px;"><strong>육아휴직, 육아기근로시간 단축을 허용</strong>한 경우 대체인력 지원금 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• <strong>(대체인력 고용기간) 월 120만원 → 월 140만원 (2026년)</strong><br>• (업무부담자에게 금전보상시) 월 20만원 지원</div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 해당 기간동안 대체인력을 30일 이상 고용한 사업주에 지급<br>• 파견근로자를 사용한 경우에도 지원 (임금의 80% 한도)<br>• <strong>업무인수인계 기간</strong>도 지원 (출산휴가 시작일 전 최대 2개월)</div></div>
        </div>
    </div>
</div>

<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">⚖️ 노무 컨설팅</span>
        <span class="page-title-main">주요 고용지원금 상세 (2) — 청년고용·고용촉진</span>
    </div>
    <div class="page-body">
        <div class="subsidy-card">
            <div class="subsidy-title">🧑‍💼 청년일자리도약장려금 &nbsp; <span style="font-size:12px;">{youth_eligible}</span></div>
            <div class="info-box" style="margin-bottom:12px;">취업애로청년(만15~34세)을 정규직으로 채용한 <strong>5인 이상 중소기업</strong> 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• <strong>월 60만원 × 최대 12개월 = 최대 720만원</strong></div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 5인 이상 중소기업 (성장유망업종 등은 5인 미만도 가능)<br>• 6개월 이상 고용유지 필수<br>• 최저임금 이상, 주 30시간 이상 근로</div></div>
        </div>

        <div class="subsidy-card">
            <div class="subsidy-title">💼 고용촉진장려금</div>
            <div class="info-box" style="margin-bottom:12px;">취업취약계층(장기실업자, 여성가장, 장애인, 국가유공자 등)을 채용한 사업주 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• <strong>월 60만원 × 최대 12개월 = 최대 720만원</strong></div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 직업안정기관 등에서 직업소개를 받아 채용<br>• 6개월 이상 고용유지 후 신청</div></div>
        </div>

        <div class="subsidy-card">
            <div class="subsidy-title">🏢 청년내일채움공제 &nbsp; <span style="font-size:12px;">{youth_eligible}</span></div>
            <div class="info-box" style="margin-bottom:12px;">중소기업 정규직 청년(만15~34세) 근로자의 <strong>자산형성</strong> 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• <strong>2년간 1,200만원</strong> (청년 본인 300만원 + 기업 300만원 + 정부 600만원 적립)</div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 5인 이상 중소기업 정규직 채용<br>• 2년 이상 고용유지</div></div>
        </div>
    </div>
</div>

<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">⚖️ 노무 컨설팅</span>
        <span class="page-title-main">주요 고용지원금 상세 (3) — 사회보험·직업훈련</span>
    </div>
    <div class="page-body">
        <div class="subsidy-card">
            <div class="subsidy-title">🛡️ 두루누리 사회보험 지원 &nbsp; <span style="font-size:12px;">{durumuri_eligible}</span></div>
            <div class="info-box" style="margin-bottom:12px;"><strong>10인 미만 사업장</strong> 사업주 및 근로자 부담 사회보험료 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• <strong>사업주 및 근로자 부담 고용보험 및 국민연금 보험료 80% 지원</strong></div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 월보수 270만원 미만 신규 가입자<br>• 지원 신청일 직전 <strong>6개월간 피보험자격 취득이력이 없는</strong> 근로자와 그 사업주<br>• 직전 3개월 연속 상시근로자 <strong>10인 미만</strong> 사업장</div></div>
        </div>

        <div class="subsidy-card">
            <div class="subsidy-title">📚 사업주 직업훈련 지원</div>
            <div class="info-box" style="margin-bottom:12px;">사업주가 소속 근로자에게 직무관련 직업훈련을 실시하는 경우 훈련비 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• 우선지원대상기업: 훈련비의 <strong>최대 100%</strong><br>• 대규모기업: 훈련비의 40~60%<br>• 유급휴가훈련: 임금의 100% + 훈련비 전액</div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 고용보험 가입 사업주<br>• HRD-Net 훈련과정 인정 필요<br>• 훈련 종료 후 1개월 이내 신청</div></div>
        </div>

        <div class="subsidy-card">
            <div class="subsidy-title">👴 고령자 계속고용장려금</div>
            <div class="info-box" style="margin-bottom:12px;">정년에 도달한 근로자를 정년 이후에도 <strong>계속 고용</strong>하는 사업주 지원</div>
            <div class="subsidy-row"><div class="subsidy-label">지원내용</div><div class="subsidy-value">• <strong>월 30만원 × 최대 2년 = 최대 720만원</strong></div></div>
            <div class="subsidy-row"><div class="subsidy-label">지원조건</div><div class="subsidy-value">• 정년제도를 운영하는 기업<br>• 정년에 도달한 근로자를 재고용, 정년연장, 정년폐지 중 하나로 계속 고용</div></div>
        </div>

        <p style="font-size:10px;color:#999;margin-top:8px;">※ 지원금 세부 요건 및 금액은 정책 변경에 따라 달라질 수 있습니다. 정확한 사항은 고용노동부(☎ 1350) 또는 고용보험 홈페이지를 참고하세요.</p>
    </div>
</div>
"""


def _salary_tax_simulation_page(isc: dict, company: dict, years: list) -> str:
    """임원 급여 수준별 세금 시뮬레이션 + 법인세 절감 효과"""

    def calc_income_tax(annual_salary_man):
        """근로소득세 간이 계산 (만원 단위 입력, 만원 단위 출력)"""
        # 근로소득공제
        sal = annual_salary_man
        if sal <= 500:
            deduction = sal * 0.70
        elif sal <= 1500:
            deduction = 350 + (sal - 500) * 0.40
        elif sal <= 4500:
            deduction = 750 + (sal - 1500) * 0.15
        elif sal <= 10000:
            deduction = 1200 + (sal - 4500) * 0.05
        else:
            deduction = 1475 + (sal - 10000) * 0.02
        taxable = sal - deduction
        # 인적공제 등 기본공제 (본인 150만원)
        taxable = max(taxable - 150, 0)
        # 종합소득세율 적용
        if taxable <= 1400:
            tax = taxable * 0.06
        elif taxable <= 5000:
            tax = 84 + (taxable - 1400) * 0.15
        elif taxable <= 8800:
            tax = 624 + (taxable - 5000) * 0.24
        elif taxable <= 15000:
            tax = 1536 + (taxable - 8800) * 0.35
        elif taxable <= 30000:
            tax = 3706 + (taxable - 15000) * 0.38
        elif taxable <= 50000:
            tax = 9406 + (taxable - 30000) * 0.40
        elif taxable <= 100000:
            tax = 17406 + (taxable - 50000) * 0.42
        else:
            tax = 38406 + (taxable - 100000) * 0.45
        local_tax = tax * 0.10  # 지방소득세
        return round(tax), round(local_tax), round(tax + local_tax)

    def calc_4대보험_company(monthly_man):
        """4대보험 사업주 부담분 (만원 단위)"""
        annual = monthly_man * 12
        national_pension = min(monthly_man, 590) * 0.045 * 12  # 국민연금 4.5%
        health = monthly_man * 0.03545 * 12  # 건강보험 3.545%
        long_care = health * 0.1295  # 장기요양 12.95%
        employ = monthly_man * 0.009 * 12  # 고용보험 0.9%
        industrial = annual * 0.007  # 산재보험 ~0.7% (업종별 상이)
        return round(national_pension + health + long_care + employ + industrial)

    # 시나리오: 월 500만, 1000만, 1500만
    scenarios = [
        {"월급": 500, "연봉": 6000},
        {"월급": 1000, "연봉": 12000},
        {"월급": 1500, "연봉": 18000},
    ]

    # 최근 영업이익
    latest = years[-1] if years else ""
    op_income = isc.get("영업이익", {}).get(latest, 0) or 0
    op_income_man = op_income / 10  # 천원 → 만원

    rows = ""
    for s in scenarios:
        tax, local, total_tax = calc_income_tax(s["연봉"])
        insurance_co = calc_4대보험_company(s["월급"])
        total_cost = s["연봉"] + insurance_co  # 법인 총 부담
        # 법인세 절감 = 총비용 × 법인세율(약 10~20%, 소기업 기준 10% 가정)
        corp_tax_saved = round(total_cost * 0.10)  # 과세표준 2억 이하 → 9%(+지방세=~10%)
        net_salary = s["연봉"] - total_tax
        rows += f"""
        <tr>
            <td class="bold-row" style="text-align:center;">월 {s['월급']:,}만원</td>
            <td class="num">{s['연봉']:,}만원</td>
            <td class="num">{tax:,}만원</td>
            <td class="num">{local:,}만원</td>
            <td class="num">{total_tax:,}만원</td>
            <td class="num">{net_salary:,}만원</td>
            <td class="num">{insurance_co:,}만원</td>
            <td class="num">{total_cost:,}만원</td>
            <td class="num" style="color:#2E7D32;font-weight:700;">△{corp_tax_saved:,}만원</td>
        </tr>"""

    # 비교표: 급여 0일 때 vs 급여 지급 시
    no_salary_corp_tax = round(op_income_man * 0.10)  # 법인세 10% 가정
    compare_rows = ""
    for s in scenarios:
        tax, local, total_tax = calc_income_tax(s["연봉"])
        insurance_co = calc_4대보험_company(s["월급"])
        total_cost = s["연봉"] + insurance_co
        new_taxable = op_income_man - total_cost
        new_corp_tax = round(max(new_taxable, 0) * 0.10)
        saved = no_salary_corp_tax - new_corp_tax
        individual_tax = total_tax
        net_effect = saved - individual_tax
        compare_rows += f"""
        <tr>
            <td class="bold-row" style="text-align:center;">월 {s['월급']:,}만원</td>
            <td class="num">{total_cost:,}만원</td>
            <td class="num" style="color:#2E7D32;">△{saved:,}만원</td>
            <td class="num" style="color:#C62828;">{individual_tax:,}만원</td>
            <td class="num {'grade-good' if net_effect > 0 else 'grade-bad'}" style="font-weight:700;">{'+' if net_effect > 0 else ''}{net_effect:,}만원</td>
        </tr>"""

    return f"""
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">👔 임원소득보상플랜</span>
        <span class="page-title-main">임원 급여 수준별 세금 시뮬레이션</span>
    </div>
    <div class="page-body">
        <div class="info-box">
            임원 급여를 높이면 <strong>개인 소득세는 증가</strong>하지만, 법인 입장에서는 <strong>급여가 비용(손금)으로 처리</strong>되어 
            <strong>법인세가 줄어드는 효과</strong>가 있습니다. 급여, 4대보험, 소득세, 법인세를 종합적으로 비교하여 최적의 급여 수준을 설계해야 합니다.
        </div>

        <h3 class="subsection-title">◆ 급여 수준별 세금 비교</h3>
        <p class="unit-label">(단위: 만원, 연간 기준)</p>
        <table class="data-table financial-table" style="font-size:12px;">
            <thead>
                <tr>
                    <th rowspan="2">월급여</th>
                    <th rowspan="2">연봉</th>
                    <th colspan="3">개인 세금</th>
                    <th rowspan="2">세후<br>수령액</th>
                    <th colspan="2">법인 부담</th>
                    <th rowspan="2">법인세<br>절감효과</th>
                </tr>
                <tr>
                    <th>소득세</th>
                    <th>지방세</th>
                    <th>합계</th>
                    <th>4대보험<br>(사업주)</th>
                    <th>총 비용</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        <h3 class="subsection-title" style="margin-top:28px;">◆ 급여 지급에 따른 법인세 절감 vs 개인 소득세 비교</h3>
        <div class="info-box" style="background:#E8F5E9;border:1px solid #66BB6A;">
            <strong>핵심 포인트:</strong> 임원 급여는 법인의 <strong>손금(비용)</strong>으로 인정되어 <strong>과세소득이 감소</strong>합니다.
            법인세율(소기업 과세표준 2억 이하: 9%) 대비 개인 소득세 실효세율이 낮은 구간에서는 
            <strong>급여를 지급하는 것이 총 세금 부담을 줄이는 효과</strong>가 있습니다.
        </div>
        <p class="unit-label">현재 영업이익 기준: {op_income_man:,.0f}만원 ({format_number(op_income, '억원')}) | 법인세율 10% 가정</p>
        <table class="data-table financial-table">
            <thead>
                <tr>
                    <th>급여 수준</th>
                    <th>법인 총 비용<br>(급여+4대보험)</th>
                    <th>법인세 절감액</th>
                    <th>개인 소득세</th>
                    <th>순 절세효과<br>(법인세절감-소득세)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="bold-row" style="text-align:center;">급여 미지급시</td>
                    <td class="num">-</td>
                    <td class="num">-</td>
                    <td class="num">-</td>
                    <td class="num">법인세 {no_salary_corp_tax:,}만원</td>
                </tr>
                {compare_rows}
            </tbody>
        </table>
        
        <div class="warning-box" style="margin-top:16px;">
            ⚠️ 위 시뮬레이션은 <strong>간이 계산</strong>이며, 실제 세금은 각종 공제·감면에 따라 달라집니다. 정확한 세금 계산은 세무사와 상담하시기 바랍니다.
        </div>
    </div>
</div>
"""


def _certification_strategy_page(company: dict) -> str:
    """업종별 인증전략 + 개별 인증 안내 (공장등록, 연구부서, 벤처, 뿌리기업, 여성기업, 메인비즈, 이노비즈)"""
    return """
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📋 기업제도정비</span>
        <span class="page-title-main">업종별 인증전략</span>
    </div>
    <div class="page-body">
        <div class="info-box">
            업종별 경영 사이클 단계별로 도입 가능한 <strong>인증제도를 이해</strong>하고, 순차적으로 확보해 나간다면 각종 <strong>세제혜택과 우대혜택</strong>은 물론 
            <strong>정부지원사업, 정책자금 융자</strong> 등을 지원할 때 유리하게 활용할 수 있습니다.
        </div>

        <h3 class="subsection-title">◆ 기업 사이클 단계별 권장 인증 프로세스</h3>
        <div style="display:flex;align-items:center;gap:8px;margin:20px 0 30px 0;flex-wrap:wrap;">
            <div style="background:#F0F2F8;padding:14px 18px;border-radius:10px;text-align:center;min-width:120px;">
                <div style="font-size:24px;">🏭</div>
                <div style="font-weight:700;font-size:13px;margin-top:4px;">공장등록</div>
            </div>
            <div style="font-size:24px;color:#4A5FC1;">→</div>
            <div style="background:#F0F2F8;padding:14px 18px;border-radius:10px;text-align:center;min-width:120px;">
                <div style="font-size:24px;">🔬</div>
                <div style="font-weight:700;font-size:13px;margin-top:4px;">연구부서<br><span style="font-size:11px;color:#999;">(전담부서)</span></div>
            </div>
            <div style="font-size:24px;color:#4A5FC1;">→</div>
            <div style="background:#E8EAF6;padding:14px 18px;border-radius:10px;text-align:center;min-width:120px;border:2px solid #4A5FC1;">
                <div style="font-size:24px;">🚀</div>
                <div style="font-weight:700;font-size:13px;margin-top:4px;color:#4A5FC1;">벤처인증</div>
            </div>
            <div style="font-size:24px;color:#4A5FC1;">→</div>
            <div style="background:#F0F2F8;padding:14px 18px;border-radius:10px;text-align:center;min-width:120px;">
                <div style="font-size:24px;">🏅</div>
                <div style="font-weight:700;font-size:13px;margin-top:4px;">이노비즈<br><span style="font-size:11px;color:#999;">(기술제조업)</span></div>
            </div>
            <div style="font-size:24px;color:#4A5FC1;">or</div>
            <div style="background:#F0F2F8;padding:14px 18px;border-radius:10px;text-align:center;min-width:120px;">
                <div style="font-size:24px;">📊</div>
                <div style="font-weight:700;font-size:13px;margin-top:4px;">메인비즈<br><span style="font-size:11px;color:#999;">(서비스/유통)</span></div>
            </div>
        </div>

        <h3 class="subsection-title">◆ 주요 기업인증 요약</h3>
        <table class="data-table financial-table" style="font-size:12px;">
            <thead>
                <tr><th style="width:100px;">인증</th><th>개요</th><th style="width:180px;">주요 혜택</th><th style="width:100px;">발급기관</th></tr>
            </thead>
            <tbody>
                <tr><td class="bold-row">공장등록</td>
                    <td>제조업 영위 시 공장설립 완료 후 등록. 제조시설 및 생산설비를 갖추고 지자체에 공장등록 신청</td>
                    <td>• 세제감면(취득세, 재산세)<br>• 정책자금 신청 기본요건</td>
                    <td>지자체</td></tr>
                <tr><td class="bold-row">연구전담부서<br>(기업부설연구소)</td>
                    <td>과학기술분야 또는 서비스분야의 연구개발활동을 수행하는 조직.<br>연구전담요원 1명 이상(전담부서), 소기업 3명 이상(연구소)</td>
                    <td>• 연구개발비 <strong>25% 세액공제</strong><br>• 이노비즈·벤처인증 가점<br>• 기업신용등급 상승</td>
                    <td>한국산업기술<br>진흥협회</td></tr>
                <tr><td class="bold-row">벤처인증</td>
                    <td>벤처투자유형, 연구개발유형, 혁신성장유형, 예비벤처기업 등 4가지 유형.<br>최초 인증 이후 3년마다 갱신</td>
                    <td>• 법인세·소득세 <strong>50% 감면</strong><br>• 취득세 75% 감면<br>• 재산세 면제<br>• 스톡옵션 비과세 2억</td>
                    <td>벤처확인기관<br>(기보, 중진공 등)</td></tr>
                <tr><td class="bold-row">뿌리기업</td>
                    <td>주조, 금형, 용접, 표면처리, 소성가공, 열처리 등 6대 뿌리기술을 활용하는 기업</td>
                    <td>• 뿌리기술 전문기업 인증<br>• 정책자금 우대<br>• 기술개발 지원사업 가점</td>
                    <td>뿌리산업<br>진흥센터</td></tr>
                <tr><td class="bold-row">여성기업</td>
                    <td>여성이 소유하고 경영하는 기업 (대표이사가 여성, 지분 30% 이상 보유)</td>
                    <td>• 공공기관 물품구매 <strong>5% 우선구매</strong><br>• 여성기업 전용 정책자금<br>• 각종 지원사업 가점</td>
                    <td>여성기업<br>종합지원센터</td></tr>
                <tr><td class="bold-row">이노비즈<br>(INNOBIZ)</td>
                    <td>기술혁신형 중소기업 인증. 기술 우위를 바탕으로 경쟁력을 확보한 <strong>기술제조업</strong> 대상.</br>기술혁신시스템(경영, 기술, 사업화) 평가 700점 이상</td>
                    <td>• 정책자금 <strong>우대금리</strong><br>• 기술보증기금 우대<br>• 병역특례 지정업체 가점<br>• 공공구매 우대</td>
                    <td>중소벤처기업부<br>(기술보증기금)</td></tr>
                <tr><td class="bold-row">메인비즈<br>(MAINBIZ)</td>
                    <td>경영혁신형 중소기업 인증. 경영혁신 활동으로 경쟁력을 확보한 <strong>서비스/유통업</strong> 대상.<br>경영혁신 역량 평가</td>
                    <td>• 정책자금 우대금리<br>• 신용보증기금 우대<br>• 공공구매 우대<br>• 수출지원 우대</td>
                    <td>중소벤처기업부<br>(신용보증기금)</td></tr>
            </tbody>
        </table>
    </div>
</div>
"""


def _certification_detail_page() -> str:
    """주요 인증 상세 - 벤처인증 + 연구소 설립 혜택"""
    return """
<div class="page content-page">
    <div class="page-header">
        <span class="section-badge">📋 기업제도정비</span>
        <span class="page-title-main">벤처인증 및 기업부설연구소 상세</span>
    </div>
    <div class="page-body">
        <h3 class="subsection-title">◆ 벤처기업 인증 유형별 기준요건</h3>
        <table class="data-table financial-table" style="font-size:12px;">
            <thead><tr><th style="width:120px;">유형</th><th>기준요건</th><th style="width:130px;">확인기관</th></tr></thead>
            <tbody>
                <tr><td class="bold-row">벤처투자유형</td>
                    <td>• 투자금의 총 합계가 <strong>5천만원 이상</strong>일 것<br>• 기업의 자본금 중 투자금액의 합계가 차지하는 비율이 <strong>10% 이상</strong>일 것</td>
                    <td>한국벤처캐피탈협회</td></tr>
                <tr><td class="bold-row">연구개발유형</td>
                    <td>• <strong>기업부설연구소를 보유</strong>할 것 (필수)<br>• 직전 4분기 연간 연구개발비가 <strong>5천만원 이상</strong>이고, 연간 총매출액에 대한 연구개발비의 합계가 차지하는 비율이 <strong>5% 이상</strong></td>
                    <td>신용보증기금<br>중소벤처기업진흥공단</td></tr>
                <tr><td class="bold-row">혁신성장유형</td>
                    <td>• 기술보증기금과 중소벤처기업진흥공단으로부터 기술의 <strong>혁신성과 사업의 성장성이 우수</strong>한 것으로 평가받은 기업</td>
                    <td>기술보증기금외</td></tr>
                <tr><td class="bold-row">예비벤처기업</td>
                    <td>• 법인설립 또는 사업자등록을 준비중인 자<br>• 벤처기업확인기관으로부터 기술의 혁신성과 사업의 성장성이 <strong>우수한 것으로 평가</strong>받은 기업</td>
                    <td>기술보증기금</td></tr>
            </tbody>
        </table>

        <div class="warning-box" style="margin-top:16px;">
            ⚠️ <strong>창업 후 3년 이내 인증받아야</strong> 세제혜택을 받을 수 있습니다. 벤처기업 인증 시 가장 흔히 적용 받는 세제 혜택으로 법인세·소득세 50% 감면 제도, 취득세 75% 감면 제도, 재산세 면제 제도 등이 있습니다.
        </div>

        <h3 class="subsection-title" style="margin-top:24px;">◆ 기업부설연구소 설립 혜택</h3>
        <div class="highlight-box" style="background:#F8F9FC;border:2px solid #4A5FC1;color:#333;">
            <div class="hl-title" style="color:#4A5FC1;">" 연구소를 설립하면 어떤 점이 좋을까요? "</div>
        </div>
        <div class="card-grid">
            <div class="card">
                <div class="card-icon">🏅</div>
                <div class="card-title">이노비즈인증, 벤처인증 가점</div>
                <div class="card-desc">기업부설연구소 보유 시 벤처인증(연구개발유형) 필수요건 충족, 이노비즈 인증에도 유리</div>
            </div>
            <div class="card">
                <div class="card-icon">👥</div>
                <div class="card-title">인력지원, 관세감면</div>
                <div class="card-desc">연구인력 채용 지원, 연구용 장비·재료 관세 감면 혜택</div>
            </div>
            <div class="card">
                <div class="card-icon">📈</div>
                <div class="card-title">기업신용등급 상승</div>
                <div class="card-desc">연구소 설립 기업은 기업 기술력 평가에서 가점 부여, 신용등급 향상에 기여</div>
            </div>
            <div class="card">
                <div class="card-icon">💰</div>
                <div class="card-title">세제혜택 (법인세 절감, 세액공제)</div>
                <div class="card-desc">중소기업의 경우 매년 <strong>연구개발비 발생액의 25% 세액공제</strong><br>① 연구요원 및 연구보조원의 인건비<br>② 연구용 견본품·부품·원재료와 시약류 구입비<br>③ 연구·시험용 시설의 이용에 필요한 비용</div>
            </div>
        </div>

        <h3 class="subsection-title" style="margin-top:16px;">◆ 연구소 및 전담부서 인정 요건</h3>
        <table class="data-table financial-table" style="font-size:12px;">
            <thead><tr><th>구분</th><th>기업규모</th><th>신고 요건</th></tr></thead>
            <tbody>
                <tr><td class="bold-row" rowspan="3">연구소 (인적요건)</td><td>벤처기업/연구원창업 중소기업</td><td>연구전담요원 <strong>2명</strong> 이상</td></tr>
                <tr><td>소기업</td><td>연구전담요원 <strong>3명</strong> 이상 (단, 창업일로부터 3년까지는 2명 이상)</td></tr>
                <tr><td>중기업/해외소재연구소</td><td>연구전담요원 <strong>5명</strong> 이상</td></tr>
                <tr><td class="bold-row">연구개발전담부서</td><td>기업규모 무관</td><td>연구전담요원 <strong>1명</strong> 이상</td></tr>
                <tr><td class="bold-row">물적요건</td><td colspan="2">독립된 연구공간과 연구시설 보유. 단, 소기업의 경우 파티션 공간처리도 인정</td></tr>
            </tbody>
        </table>
    </div>
</div>
"""
