"""
노무 컨설팅 심층 페이지 (HTML) - 근로기준법 + 판례 기반
1. 퇴직금·중간정산 함정 + 판례
2. 포괄임금제 + 통상임금 함정
3. 부당해고 분쟁 예방
4. 직장 내 괴롭힘·성희롱 의무
5. 연차 산정 정확 가이드
6. 임금·퇴직금 시효 & 체불 리스크
7. 취업규칙 작성·변경 의무
8. 육아휴직·육아기 근로시간 단축
9. 외국인·고령자 채용 노무 가이드
10. 노동위원회·고용노동부 진정 대응
11. 노무 리스크 자가진단표 (자동 점수화)
"""


def _logo_header(LOGO_SMALL, section_badge, page_title):
    return f"""
    <div class="page-header">
        <img src="{LOGO_SMALL}" class="header-logo" alt="RSV"/>
        <span class="section-badge">{section_badge}</span>
        <span class="page-title-main">{page_title}</span>
    </div>"""


def _info_box(text):
    return f'<div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">{text}</div>'


def _section_title(text):
    return f'<h3 class="subsection-title">◆ {text}</h3>'


def _callout(label, text, color="#C9A961", bg_grad="#FFF8E1,#F9F1DC", label_color="#8B6F3E"):
    return f"""
    <div style="margin-top:14px;background:linear-gradient(135deg,{bg_grad});border-left:5px solid {color};padding:14px 18px;border-radius:0 12px 12px 0;">
        <div style="font-weight:800;color:{label_color};font-size:13px;margin-bottom:6px;">{label}</div>
        <div style="font-size:13px;line-height:1.6;color:#2B2416;">{text}</div>
    </div>"""


def _case_card(case_num, title, ruling_id, summary, lesson):
    """판례 카드"""
    return f"""
    <div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:8px;">
        <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:6px;">
            <span style="background:#0F2847;color:white;font-size:10px;font-weight:700;padding:2px 8px;border-radius:3px;letter-spacing:0.5px;">{case_num}</span>
            <strong style="font-size:13px;color:#0F2847;">{title}</strong>
            <span style="font-size:10px;color:#888;margin-left:auto;font-family:monospace;">{ruling_id}</span>
        </div>
        <div style="font-size:12px;color:#4A5568;line-height:1.6;margin-bottom:6px;">{summary}</div>
        <div style="font-size:12px;color:#8B6F3E;line-height:1.6;background:#FFFBF0;padding:6px 10px;border-radius:4px;border-left:2px solid #C9A961;">
            💡 <strong>실무 시사점:</strong> {lesson}
        </div>
    </div>
    """


def _section_badge_text(is_personal):
    return "⚖️ 노무 컨설팅" if not is_personal else "⚖️ 노무 컨설팅"


# ════════════════════════════════════════════════════════════════
# 1. 퇴직금·중간정산 함정 + 판례
# ════════════════════════════════════════════════════════════════
def labor_severance_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "퇴직금 함정 & 중간정산 5대 사유")}
    <div class="page-body">
        {_info_box('"<strong>퇴직금 분쟁이 노무 사건의 가장 큰 비중</strong>입니다." 평균임금 산정 오류, 부당한 중간정산, 미지급으로 인한 3년 추징·형사처벌까지. 실제 판례로 보는 사장님이 꼭 알아야 할 함정.')}
        
        {_section_title("퇴직금 계산 공식 (근로자퇴직급여보장법 제8조)")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:140px;">구분</th><th>내용</th></tr></thead>
            <tbody>
                <tr><td><strong>적용 대상</strong></td>
                    <td>1년 이상 근무 + 주 15시간 이상 근로자 (5인 미만 사업장 포함)</td></tr>
                <tr><td><strong>퇴직금 공식</strong></td>
                    <td><strong style="color:#0F2847;">평균임금(1일분) × 30일 × (재직일수 ÷ 365)</strong></td></tr>
                <tr><td><strong>평균임금</strong></td>
                    <td>퇴직 직전 <strong>3개월간 받은 임금 총액 ÷ 그 기간 총일수</strong> (90일 기준)</td></tr>
                <tr><td><strong>통상임금 비교</strong></td>
                    <td>평균임금이 통상임금보다 적으면 → <strong>통상임금으로 계산</strong> (높은 쪽 적용)</td></tr>
                <tr style="background:#FFF8E1;"><td><strong>지급 기한</strong></td>
                    <td>퇴직일로부터 <strong>14일 이내 (위반 시 형사처벌)</strong> — 합의로 연장 가능</td></tr>
            </tbody>
        </table>

        {_section_title("핵심 판례 3가지")}
        {_case_card("판례 1", "정기상여금은 평균임금에 포함된다", "대법 2013다69705", 
                    "회사가 정기적·일률적·고정적으로 지급한 상여금은 평균임금에 포함시켜 퇴직금을 다시 계산해야 함",
                    "정기상여 600% 받던 직원의 퇴직금이 <strong>1.5배~2배 증액</strong>되는 경우 다수. 미지급 시 3년 소급 추징 + 지연이자 20%")}
        {_case_card("판례 2", "퇴직금 중간정산은 법정 사유 있을 때만 가능", "대법 2014다56297", 
                    "근로자가 동의해도 법에 정해진 5대 사유가 아니면 중간정산은 <strong>무효</strong>. 정산 후에도 회사는 퇴직금 지급 의무 잔존",
                    "잘못된 중간정산 시 회사는 <strong>이미 준 돈 + 진짜 퇴직금</strong> 2중 부담. 사례: A사 9년차 직원 중간정산 후 퇴사 시 8천만원 추가 지급")}
        {_case_card("판례 3", "임원도 사용종속관계 있으면 근로자성 인정", "대법 2017다16778", 
                    "등기임원·이사라도 실질적으로 사장의 지휘·감독을 받으며 근로 제공 시 근로자로 인정 → 퇴직금 지급 의무 발생",
                    "<strong>가족 임원·명목상 이사도 사회보험 가입·근태 관리 시 근로자성 인정</strong>. 임원 보수 ≠ 임원 퇴직금 보장 안됨")}

        {_section_title("퇴직금 중간정산 가능한 5대 법정 사유 (시행령 제3조)")}
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;font-size:12.5px;">
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:9px 13px;border-radius:0 8px 8px 0;">
                <strong>1️⃣ 무주택자가 본인 명의 주택 구입</strong><br>
                <span style="color:#666;">계약일로부터 1개월 내 신청 가능</span>
            </div>
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:9px 13px;border-radius:0 8px 8px 0;">
                <strong>2️⃣ 무주택자의 전세금·보증금 (1회 한정)</strong><br>
                <span style="color:#666;">본인 명의 주택임차계약</span>
            </div>
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:9px 13px;border-radius:0 8px 8px 0;">
                <strong>3️⃣ 본인/배우자/부양가족 6개월 이상 요양</strong><br>
                <span style="color:#666;">의료비 본인부담 연 임금총액 12.5% 초과 시</span>
            </div>
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:9px 13px;border-radius:0 8px 8px 0;">
                <strong>4️⃣ 파산·개인회생 절차 개시</strong><br>
                <span style="color:#666;">법원 결정 후 5년 이내</span>
            </div>
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:9px 13px;border-radius:0 8px 8px 0;grid-column:1/3;">
                <strong>5️⃣ 천재지변·임금피크제 도입·근로시간 단축</strong><br>
                <span style="color:#666;">고용노동부 장관이 인정한 사유 (코로나19 등)</span>
            </div>
        </div>

        {_callout("⚠️ 사장님이 꼭 챙겨야 할 3가지", "(1) <strong>DB(확정급여)/DC(확정기여) 퇴직연금 가입 의무</strong> — 1년 유예 후 미가입 시 과태료 (2) <strong>퇴직금 산정 시 통상임금 vs 평균임금 양쪽 다 계산</strong> 후 높은 쪽 적용 (3) <strong>'퇴직금 포기 각서'는 무효</strong> — 근로자가 자필 작성해도 효력 없음", "#C62828", "#FFEBEE,#FFCDD2", "#B71C1C")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 2. 포괄임금제 + 통상임금 함정
# ════════════════════════════════════════════════════════════════
def labor_inclusive_wage_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "포괄임금제 & 통상임금 함정")}
    <div class="page-body">
        {_info_box('"<strong>월급에 야근수당 다 포함됐다고 했는데, 직원이 노동청 가서 추가 청구하면 다 줘야 합니다.</strong>" 포괄임금제는 함부로 못 쓰는 제도. 통상임금 판례 이후 회사들이 <strong>몇 억씩 토해내는 사례</strong>가 줄을 잇고 있습니다.')}

        {_section_title("포괄임금제가 유효하려면 (대법 2010다91046)")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:170px;">요건</th><th>설명</th><th style="width:80px;">필수</th></tr></thead>
            <tbody>
                <tr><td><strong>① 근로시간 산정의 어려움</strong></td>
                    <td>경비직·운전기사 등 근로시간을 정확히 계산하기 어려운 직종에만 적용</td>
                    <td style="color:#C62828;font-weight:700;">필수</td></tr>
                <tr><td><strong>② 근로자에게 불리하지 않을 것</strong></td>
                    <td>포괄 책정한 수당이 <strong>법정 수당보다 같거나 많아야</strong> 함</td>
                    <td style="color:#C62828;font-weight:700;">필수</td></tr>
                <tr><td><strong>③ 명시적 합의</strong></td>
                    <td>근로계약서에 "월급 X원에 연장·야간·휴일 수당 모두 포함" 명시</td>
                    <td style="color:#C62828;font-weight:700;">필수</td></tr>
                <tr style="background:#FFEBEE;">
                    <td><strong>❌ 사무직은 원칙적으로 무효</strong></td>
                    <td>대법 판례: <strong>"근로시간 산정이 가능한 사무직"</strong>은 포괄임금제 부적용</td>
                    <td style="color:#C62828;font-weight:700;">주의!</td></tr>
            </tbody>
        </table>

        {_section_title("통상임금 포함/제외 기준 (대법 2013다69705 전원합의체)")}
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:#E8F5E9;border-left:4px solid #2E7D32;padding:12px 16px;border-radius:0 10px 10px 0;">
                <div style="font-weight:800;color:#1B5E20;margin-bottom:6px;">✅ 통상임금 포함 (수당 계산 베이스 ↑)</div>
                <ul style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.7;color:#2B2416;">
                    <li>기본급</li>
                    <li>정기상여금 (3가지 조건 만족 시)</li>
                    <li>식대·교통비 (전 직원 일률 지급)</li>
                    <li>직책수당·자격수당</li>
                    <li>장기근속수당</li>
                </ul>
            </div>
            <div style="background:#FFEBEE;border-left:4px solid #C62828;padding:12px 16px;border-radius:0 10px 10px 0;">
                <div style="font-weight:800;color:#B71C1C;margin-bottom:6px;">❌ 통상임금 제외</div>
                <ul style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.7;color:#2B2416;">
                    <li>실비변상적 수당 (출장비)</li>
                    <li>성과급 (개인 성과 기준)</li>
                    <li>비정기 상여 (명절·창립일)</li>
                    <li>복리후생적 수당 (학자금)</li>
                    <li>특수 작업수당 (위험·해외)</li>
                </ul>
            </div>
        </div>

        {_section_title("정기상여금이 통상임금이 되는 3가지 조건")}
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 18px;">
            <div style="display:flex;align-items:center;justify-content:space-around;gap:12px;flex-wrap:wrap;font-size:12.5px;">
                <div style="text-align:center;flex:1;min-width:140px;">
                    <div style="font-size:32px;font-weight:900;color:#C9A961;">①</div>
                    <strong>정기성</strong><br>
                    <span style="color:#666;">매월·매분기 등 정해진 주기로 지급</span>
                </div>
                <div style="font-size:20px;color:#888;">+</div>
                <div style="text-align:center;flex:1;min-width:140px;">
                    <div style="font-size:32px;font-weight:900;color:#C9A961;">②</div>
                    <strong>일률성</strong><br>
                    <span style="color:#666;">모든 근로자 또는 일정 조건의 근로자 전원에게 지급</span>
                </div>
                <div style="font-size:20px;color:#888;">+</div>
                <div style="text-align:center;flex:1;min-width:140px;">
                    <div style="font-size:32px;font-weight:900;color:#C9A961;">③</div>
                    <strong>고정성</strong><br>
                    <span style="color:#666;">근무 실적과 관계없이 사전에 확정</span>
                </div>
            </div>
            <div style="margin-top:10px;font-size:12px;color:#C62828;text-align:center;padding:8px;background:#FFEBEE;border-radius:6px;">
                ⚠️ <strong>3가지 모두 충족 시 통상임금 인정</strong> → 야간·연장·휴일수당 계산 베이스 상승 → 회사 추가 부담
            </div>
        </div>

        {_callout("💸 시뮬레이션: 통상임금 재산정 시 부담", "월 기본급 250만 + 정기상여 600% (연 1,500만) 받는 직원이 야근 월 30시간 하는 경우:<br>• <strong>기존 통상임금 기준</strong>: 연장수당 약 32만원/월<br>• <strong>정기상여 포함 시</strong>: 연장수당 약 48만원/월 → <strong style='color:#C62828;'>월 16만 × 12개월 × 3년 = 576만원 미지급 추징</strong>", "#C62828", "#FFEBEE,#FFCDD2", "#B71C1C")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 3. 부당해고 분쟁 예방
# ════════════════════════════════════════════════════════════════
def labor_dismissal_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "부당해고 분쟁 예방 — 3대 정당성")}
    <div class="page-body">
        {_info_box('"<strong>해고는 사장님 권한이지만, 절차와 사유를 잘못 밟으면 노동위원회에서 부당해고로 뒤집힙니다.</strong>" 한 번 부당해고 인정되면 <strong>복직 + 해고 기간 임금 전액</strong> 지급. 평균 8천만~1억 부담.')}

        {_section_title("해고가 정당하려면 — 3대 요건")}
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:12px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-top:4px solid #0F2847;border-radius:8px;padding:14px;text-align:center;">
                <div style="font-size:28px;font-weight:900;color:#0F2847;">1</div>
                <strong style="font-size:13px;">사유의 정당성</strong>
                <div style="font-size:11px;color:#666;margin-top:6px;line-height:1.5;">취업규칙에 정한 사유 + 사회통념상 인정되는 중대 사유</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-top:4px solid #0F2847;border-radius:8px;padding:14px;text-align:center;">
                <div style="font-size:28px;font-weight:900;color:#0F2847;">2</div>
                <strong style="font-size:13px;">절차의 정당성</strong>
                <div style="font-size:11px;color:#666;margin-top:6px;line-height:1.5;">서면통지 + 사유·시기 명시 (근기법 제27조)</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-top:4px solid #0F2847;border-radius:8px;padding:14px;text-align:center;">
                <div style="font-size:28px;font-weight:900;color:#0F2847;">3</div>
                <strong style="font-size:13px;">양정의 정당성</strong>
                <div style="font-size:11px;color:#666;margin-top:6px;line-height:1.5;">잘못 정도에 비례한 처분 (해고는 최후수단)</div>
            </div>
        </div>

        {_section_title("핵심 판례")}
        {_case_card("판례 1", "구두·문자 해고 통보는 무효", "대법 2015두56830", 
                    "근로기준법 제27조에 따라 해고 사유와 시기를 <strong>반드시 서면</strong>으로 통지해야 함. 카톡·문자·구두는 무효",
                    "서면 통지 없는 해고는 <strong>자동 부당해고 인정</strong>. 사유가 정당해도 절차 위반으로 모두 무효 처리")}
        {_case_card("판례 2", "단순 근태 불량은 해고 사유 안됨", "대법 2017두69793", 
                    "지각·결근 등 근태 불량은 <strong>여러 차례 경고·시말서·감봉 등 점진적 징계</strong> 후에만 해고 가능",
                    "1~2회 지각·무단결근으로 바로 해고 → 부당해고 인정. <strong>경고 → 시말서 → 정직 → 해고</strong> 순서 필수")}
        {_case_card("판례 3", "경영상 이유의 해고도 4대 요건 충족 필요", "대법 2018다234793", 
                    "(1) 긴박한 경영상 필요 (2) 해고 회피 노력 (3) 합리적·공정한 기준 (4) 50일 전 협의 — 모두 갖춰야 정당",
                    "단순한 매출 부진으로는 해고 불가. <strong>인력 재배치·연차 사용 권장·임금 삭감 협의</strong> 등 단계 필수")}

        {_section_title("부당해고 인정 시 회사 부담 시뮬레이션")}
        <table class="data-table financial-table compact">
            <thead><tr><th>항목</th><th>내용</th><th class="num">예시 (월급 300만)</th></tr></thead>
            <tbody>
                <tr><td><strong>① 복직</strong></td>
                    <td>해고일로부터 즉시 복직 또는 위로금 합의</td>
                    <td class="num">—</td></tr>
                <tr><td><strong>② 해고 기간 임금</strong></td>
                    <td>판정일까지 전 기간 임금 100% 지급 (평균 6~10개월)</td>
                    <td class="num">2,400만원~3,000만원</td></tr>
                <tr><td><strong>③ 지연이자</strong></td>
                    <td>연 20% (근로기준법 제37조)</td>
                    <td class="num">240만원~300만원</td></tr>
                <tr><td><strong>④ 변호사·노무사 비용</strong></td>
                    <td>회사 대리인 비용 (평균)</td>
                    <td class="num">500만원~1,000만원</td></tr>
                <tr class="total-row"><td><strong>총 회사 부담</strong></td>
                    <td><strong>1건 평균</strong></td>
                    <td class="num"><strong style="color:#C62828;">3,000만원~5,000만원</strong></td></tr>
            </tbody>
        </table>

        {_callout("✅ 사장님 체크리스트", "(1) 해고 전 <strong>최소 1~2회 시말서·경고장</strong> 발급 + 회사 보관 (2) <strong>서면 해고통지서</strong> 작성 + 사유·시기 명확 기재 (3) 5인 이상 사업장: <strong>30일 전 해고예고</strong> 또는 30일분 통상임금 지급 (4) <strong>취업규칙에 명시된 사유</strong>가 있는지 확인 (5) 의심 시 <strong>노무사 사전 자문</strong> (자문료 50~100만 << 부당해고 손해)", "#2E7D32", "#E8F5E9,#C8E6C9", "#1B5E20")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 4. 직장 내 괴롭힘·성희롱 의무
# ════════════════════════════════════════════════════════════════
def labor_harassment_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "직장 내 괴롭힘 & 성희롱 — 사용자 의무")}
    <div class="page-body">
        {_info_box('"<strong>2019년 7월부터 직장 내 괴롭힘 금지법이 시행</strong>되었습니다. 사장님이 가해자가 아니어도 <strong>적절히 조치하지 않으면 과태료 1천만원 + 형사처벌</strong>. 사건은 점점 늘고 있고 노동청 신고가 가장 많은 분야입니다.')}

        {_section_title("직장 내 괴롭힘 — 사용자 4대 의무 (근기법 제76조의2)")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:40px;">#</th><th style="width:170px;">의무</th><th>내용</th><th style="width:110px;">위반 시</th></tr></thead>
            <tbody>
                <tr><td><strong>1</strong></td><td><strong>조사 의무</strong></td>
                    <td>신고 접수 시 즉시 객관적 조사 (당사자 분리 등 임시조치)</td>
                    <td style="color:#C62828;font-weight:700;">과태료 500만</td></tr>
                <tr><td><strong>2</strong></td><td><strong>조치 의무</strong></td>
                    <td>조사 결과 괴롭힘 확인 시 가해자 징계 + 피해자 근무 장소 변경 등</td>
                    <td style="color:#C62828;font-weight:700;">과태료 500만</td></tr>
                <tr><td><strong>3</strong></td><td><strong>비밀유지 의무</strong></td>
                    <td>조사 과정에서 알게 된 비밀을 누설 금지</td>
                    <td style="color:#C62828;font-weight:700;">과태료 300만</td></tr>
                <tr><td><strong>4</strong></td><td><strong>불이익조치 금지</strong></td>
                    <td>신고자·피해자에게 해고·징계 등 불이익 절대 금지</td>
                    <td style="color:#C62828;font-weight:900;">3년이하 / 3천만</td></tr>
            </tbody>
        </table>

        {_section_title("괴롭힘으로 인정되는 3가지 요건")}
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;font-size:12.5px;">
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>① 직장 내 우월적 지위 이용</strong><br>
                <span style="color:#666;">상사→부하, 선임→후임, 다수→소수 등</span>
            </div>
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>② 업무상 적정 범위 초과</strong><br>
                <span style="color:#666;">정상적 업무 지시·교육 ≠ 괴롭힘</span>
            </div>
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>③ 신체적·정신적 고통 또는 근무환경 악화</strong><br>
                <span style="color:#666;">피해자 주관 + 통상적 시각</span>
            </div>
        </div>

        {_section_title("성희롱 — 남녀고용평등법 별도 적용 (사업장 규모 무관)")}
        <table class="data-table financial-table compact">
            <thead><tr><th>구분</th><th>내용</th></tr></thead>
            <tbody>
                <tr><td><strong>성희롱 예방 교육</strong></td>
                    <td><strong>연 1회 의무</strong> (10인 이상 사업장은 정기 교육 + 결과 보고서 작성)</td></tr>
                <tr><td><strong>위반 시 처벌</strong></td>
                    <td>예방교육 미실시: <strong>과태료 500만원</strong><br>가해자 사용자: <strong>3천만원 이하 벌금</strong></td></tr>
                <tr><td><strong>5인 미만 사업장</strong></td>
                    <td>괴롭힘법은 미적용이지만 <strong>성희롱법은 적용 (사장 본인도 처벌 대상)</strong></td></tr>
            </tbody>
        </table>

        {_section_title("신고 접수 → 처리 표준 프로세스")}
        <div style="background:#F4F1EC;padding:14px;border-radius:10px;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:11.5px;">
                <div style="background:#0F2847;color:white;padding:8px 12px;border-radius:6px;flex:1;min-width:90px;text-align:center;">
                    <strong>① 신고 접수</strong><br><span style="font-size:10px;opacity:0.85;">즉시 기록</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#1B3A6B;color:white;padding:8px 12px;border-radius:6px;flex:1;min-width:90px;text-align:center;">
                    <strong>② 당사자 분리</strong><br><span style="font-size:10px;opacity:0.85;">임시 격리 조치</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#2A5298;color:white;padding:8px 12px;border-radius:6px;flex:1;min-width:90px;text-align:center;">
                    <strong>③ 객관 조사</strong><br><span style="font-size:10px;opacity:0.85;">제3자 외부 노무사</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#4A6B8F;color:white;padding:8px 12px;border-radius:6px;flex:1;min-width:90px;text-align:center;">
                    <strong>④ 결과 판단</strong><br><span style="font-size:10px;opacity:0.85;">증거 기반</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#C9A961;color:white;padding:8px 12px;border-radius:6px;flex:1;min-width:90px;text-align:center;">
                    <strong>⑤ 조치·보고</strong><br><span style="font-size:10px;opacity:0.85;">징계+예방교육</span>
                </div>
            </div>
        </div>

        {_callout("⚠️ 신고 무시는 절대 금물", "사장님이 '둘이 알아서 해결해'라고 방치하면 → 회사가 <strong>공동책임</strong>. 피해자가 손해배상 청구 시 회사 부담. <strong>10인 이상 사업장은 취업규칙에 괴롭힘 처리 규정을 반드시 명시</strong>해야 함 (미명시 시 과태료 500만).", "#C62828", "#FFEBEE,#FFCDD2", "#B71C1C")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 5. 연차 산정 정확 가이드
# ════════════════════════════════════════════════════════════════
def labor_annual_leave_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "연차휴가 정확 산정 가이드")}
    <div class="page-body">
        {_info_box('"<strong>연차 계산을 잘못하면 직원 1인당 수십만~수백만원 미지급</strong>이 발생합니다." 입사일 기준 vs 회계연도 기준의 차이, 1년 미만 근로자 처리, 연차수당 단가까지 모두 정리합니다.')}

        {_section_title("연차 발생 기본 원칙 (근기법 제60조)")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:140px;">근속기간</th><th>발생 일수</th><th>비고</th></tr></thead>
            <tbody>
                <tr><td><strong>1년 미만</strong></td>
                    <td>매월 개근 시 <strong>월 1일</strong> (최대 11일)</td>
                    <td>대법 2018다231995 — 한도 11일</td></tr>
                <tr><td><strong>1년차 (만 1년 도래)</strong></td>
                    <td><strong>15일</strong> (출근율 80% 이상)</td>
                    <td>1년 미만 시 발생한 11일과 별개</td></tr>
                <tr><td><strong>3년차 이상</strong></td>
                    <td>2년마다 1일씩 가산 (최대 <strong>25일</strong>)</td>
                    <td>3년 16일, 5년 17일, ..., 21년 이상 25일</td></tr>
            </tbody>
        </table>

        {_section_title("핵심 판례")}
        {_case_card("판례 1", "1년 미만 근로자의 연차는 만 1년 도래 전까지 사용", "대법 2018다231995", 
                    "입사 1년 미만 매월 발생한 연차(최대 11일)는 <strong>입사 1년이 되기 전</strong>까지 사용해야 함. 1년 도래 후엔 소멸",
                    "예: 2024.3.1 입사 → 2024.4.1, 5.1, ... 매월 1일씩 발생 → <strong>2025.2.28까지 다 못 쓰면 소멸 → 연차수당 지급 의무</strong>")}
        {_case_card("판례 2", "회계연도 기준 적용해도 입사일 기준보다 불리하면 안됨", "대법 2021다234458", 
                    "회사가 편의상 회계연도 기준 일괄 부여해도, <strong>퇴직 시 입사일 기준으로 다시 계산하여 부족분 지급</strong> 의무",
                    "회계연도 기준 vs 입사일 기준 양쪽 다 계산 → 직원에게 <strong>더 유리한 쪽 적용</strong>이 안전")}

        {_section_title("입사일 기준 vs 회계연도 기준 비교")}
        <table class="data-table financial-table compact">
            <thead><tr><th></th><th>입사일 기준</th><th>회계연도 기준</th></tr></thead>
            <tbody>
                <tr><td><strong>발생 시점</strong></td>
                    <td>각자 입사일에 1년이 되는 날</td>
                    <td>매년 1.1 일괄 부여</td></tr>
                <tr><td><strong>관리 편의</strong></td>
                    <td>❌ 직원별 다른 날짜</td>
                    <td>✅ 전 직원 동일</td></tr>
                <tr><td><strong>퇴직 정산</strong></td>
                    <td>그대로 계산</td>
                    <td>퇴직 시 <strong>입사일 기준 재계산</strong> 필요</td></tr>
                <tr><td><strong>법적 안전성</strong></td>
                    <td>✅ 원칙적 방식</td>
                    <td>⚠️ 회계연도 변경 시 정산 의무 (판례)</td></tr>
                <tr><td><strong>취업규칙 명시</strong></td>
                    <td>불필요</td>
                    <td><strong>반드시 명시</strong> 필요</td></tr>
            </tbody>
        </table>

        {_section_title("연차수당 계산 공식")}
        <div style="background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-radius:10px;padding:16px;text-align:center;font-size:14px;color:#2B2416;line-height:1.8;">
            <strong style="color:#8B6F3E;">연차수당 = 1일 통상임금 × 미사용 연차일수</strong><br>
            <span style="font-size:12px;color:#666;">1일 통상임금 = 월 통상임금 ÷ 209시간 × 8시간 (소정근로 1일분)</span>
            <div style="margin-top:10px;background:#fff;border-radius:6px;padding:10px;font-size:12.5px;">
                예: 월 통상임금 250만원 → 1일 통상임금 약 <strong>9.6만원</strong> → 미사용 10일 = <strong>약 96만원</strong>
            </div>
        </div>

        {_callout("✅ 연차 관리 3대 원칙", "(1) <strong>입사일 기준으로 관리</strong>가 가장 안전 (관리 부담 있지만 분쟁 최소) (2) 회계연도 기준 쓸 거면 <strong>취업규칙에 명시 + 퇴직 시 재정산</strong> 필수 (3) <strong>연차사용촉진제도 도입</strong>으로 연차수당 부담 합법 회피 (다음 페이지)", "#2E7D32", "#E8F5E9,#C8E6C9", "#1B5E20")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 6. 임금·퇴직금 시효 & 체불 리스크
# ════════════════════════════════════════════════════════════════
def labor_wage_arrears_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "임금체불 — 형사처벌 & 지연이자 함정")}
    <div class="page-body">
        {_info_box('"<strong>임금 한 푼이라도 늦게 주면 형사처벌 대상</strong>입니다." 노동청 진정 → 사건은 자동 형사 송치 → 사장님 개인 약식기소·벌금. 단순 민사 문제가 아닙니다.')}

        {_section_title("임금채권 시효 — 3년 (근기법 제49조)")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:170px;">청구 항목</th><th>시효</th><th>특이사항</th></tr></thead>
            <tbody>
                <tr><td><strong>월 임금</strong></td><td>각 임금일로부터 <strong>3년</strong></td><td>매월 별도 시효 진행</td></tr>
                <tr><td><strong>연차수당</strong></td><td>발생일로부터 <strong>3년</strong></td><td>입사일/회계연도 차이 주의</td></tr>
                <tr><td><strong>퇴직금</strong></td><td>퇴직일로부터 <strong>3년</strong></td><td>14일 이내 지급 의무</td></tr>
                <tr><td><strong>연장·야간·휴일수당</strong></td><td>각 수당일로부터 <strong>3년</strong></td><td>통상임금 재산정 시 소급 가능</td></tr>
                <tr style="background:#FFF8E1;"><td><strong>퇴직금 시효 정지</strong></td>
                    <td colspan="2">노동청 진정·소송 제기 시 시효 <strong>중단</strong> → 3년 다시 진행</td></tr>
            </tbody>
        </table>

        {_section_title("체불 시 사장님이 받는 처벌")}
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
            <div style="background:#FFEBEE;border-left:5px solid #C62828;padding:14px 18px;border-radius:0 12px 12px 0;">
                <div style="font-weight:800;color:#B71C1C;font-size:13px;margin-bottom:8px;">⚖️ 형사처벌</div>
                <ul style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.8;color:#2B2416;">
                    <li><strong>임금 체불</strong>: 3년 이하 징역 또는 3천만 이하 벌금</li>
                    <li><strong>퇴직금 체불</strong>: 동일</li>
                    <li><strong>최저임금 위반</strong>: 3년 이하 또는 2천만 이하</li>
                    <li>대표이사 개인 형사처벌 (법인 양벌)</li>
                </ul>
            </div>
            <div style="background:#FFF3E0;border-left:5px solid #E65100;padding:14px 18px;border-radius:0 12px 12px 0;">
                <div style="font-weight:800;color:#BF360C;font-size:13px;margin-bottom:8px;">💰 민사 부담</div>
                <ul style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.8;color:#2B2416;">
                    <li>체불액 100% 지급 의무</li>
                    <li><strong>지연이자 연 20%</strong> (근기법 제37조)</li>
                    <li>퇴직 후 14일 경과분부터 적용</li>
                    <li>변호사·노무사 대응 비용</li>
                </ul>
            </div>
        </div>

        {_section_title("노동청 진정 → 형사 송치 흐름")}
        <div style="background:#F4F1EC;padding:14px;border-radius:10px;margin-top:10px;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:11.5px;">
                <div style="background:#0F2847;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:100px;text-align:center;">
                    <strong>① 근로자 진정</strong><br><span style="font-size:10px;opacity:0.85;">노동청 접수</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#1B3A6B;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:100px;text-align:center;">
                    <strong>② 출석조사</strong><br><span style="font-size:10px;opacity:0.85;">사장님 직접 출석</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#2A5298;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:100px;text-align:center;">
                    <strong>③ 시정지시</strong><br><span style="font-size:10px;opacity:0.85;">25일 이내 이행</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#C62828;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:100px;text-align:center;">
                    <strong>④ 형사 송치</strong><br><span style="font-size:10px;opacity:0.85;">미이행 시 검찰</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#B71C1C;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:100px;text-align:center;">
                    <strong>⑤ 약식기소</strong><br><span style="font-size:10px;opacity:0.85;">벌금형 처분</span>
                </div>
            </div>
        </div>

        {_callout("🚨 일시적 자금난도 면죄부 안 됨", "<strong>자금 사정이 어려워서 지급 못했다는 변명은 법원에서 받아들이지 않습니다.</strong> 임금 우선변제 원칙 (다른 채무보다 먼저). 자금난 발생 시 직원과 <strong>지급 유예 합의서 작성</strong> + 노동청 신고 전 자진 시정이 유일한 방법.", "#C62828", "#FFEBEE,#FFCDD2", "#B71C1C")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 7. 취업규칙 작성·변경 의무
# ════════════════════════════════════════════════════════════════
def labor_rules_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "취업규칙 — 10인 이상 작성·신고 의무")}
    <div class="page-body">
        {_info_box('"<strong>10인 이상 사업장은 취업규칙 작성·신고가 법적 의무</strong>입니다." 위반 시 과태료 500만원. 게다가 취업규칙 없으면 해고·징계 시 사유의 정당성 입증이 어려워 부당해고 인정 가능성 높음.')}

        {_section_title("취업규칙 작성·신고 의무 (근기법 제93조)")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:160px;">구분</th><th>내용</th></tr></thead>
            <tbody>
                <tr><td><strong>적용 대상</strong></td><td>상시근로자 <strong>10인 이상</strong> 사업장 (사용자 본인 제외)</td></tr>
                <tr><td><strong>의무</strong></td><td>① 취업규칙 작성 ② 고용노동부 신고 ③ 사업장 비치·게시</td></tr>
                <tr><td><strong>신고 방법</strong></td><td>관할 지방고용노동관서 + <strong>근로자 과반수 의견 청취서</strong> 첨부</td></tr>
                <tr><td><strong>위반 시</strong></td><td>미작성·미신고: <strong>과태료 500만원 이하</strong></td></tr>
                <tr style="background:#FFF8E1;"><td><strong>변경 시</strong></td>
                    <td>변경 후 <strong>1개월 이내 신고</strong> 의무. 불이익 변경 시 추가 절차</td></tr>
            </tbody>
        </table>

        {_section_title("취업규칙 필수 기재사항 13가지")}
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:6px;font-size:12px;">
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">① 시업·종업·휴게시간·휴일</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">② 임금 결정·지급방법·산정기간</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">③ 가족수당의 계산·지급방법</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">④ 퇴직금·상여 등 임시 임금</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑤ 근로자에 부담시키는 식비·작업용품</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑥ 근로자 교육에 관한 사항</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑦ 출산휴가·육아휴직</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑧ 안전·보건에 관한 사항</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑨ 직장 내 괴롭힘 예방·발생 시 조치</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑩ 표창과 제재에 관한 사항</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑪ 채용·해고·퇴직에 관한 사항</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;">⑫ 재해부조·재해보상</div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:7px 11px;grid-column:1/3;">⑬ 그 밖에 해당 사업장 근로자 전체에 적용될 사항</div>
        </div>

        {_section_title("취업규칙 불이익 변경 — 까다로운 절차")}
        <div style="background:#FFF8E1;border-left:5px solid #C9A961;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:#8B6F3E;font-size:13px;margin-bottom:8px;">변경 시 동의 기준 (근기법 제94조)</div>
            <ul style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.8;color:#2B2416;">
                <li><strong>유리한 변경 또는 신설</strong>: 근로자 과반수 의견 청취만 필요</li>
                <li><strong>불이익 변경</strong>: 근로자 <strong>과반수의 동의</strong> 필요 (강행 규정)</li>
                <li>예: 임금 삭감, 퇴직금 누진제→단수제 변경, 연차 일수 축소 등</li>
                <li style="color:#C62828;"><strong>위반 시 변경 자체가 무효</strong> + 종전 규정대로 적용</li>
            </ul>
        </div>

        {_callout("✅ 추천 행동 가이드", "(1) 10인 이상 사업장은 <strong>즉시 취업규칙 작성·신고</strong> (변호사·노무사 비용 100~300만 << 분쟁 손해) (2) <strong>표준 취업규칙</strong>은 고용노동부 홈페이지에서 무료 다운로드 가능, 회사 특성에 맞게 수정 (3) <strong>최소 연 1회 점검</strong> + 법 개정 반영 (4) 직원에게 <strong>접근 가능한 곳에 게시·열람</strong> 가능하게 비치 필수", "#2E7D32", "#E8F5E9,#C8E6C9", "#1B5E20")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 8. 육아휴직·육아기 근로시간 단축
# ════════════════════════════════════════════════════════════════
def labor_parental_leave_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "육아휴직 & 육아기 근로시간 단축")}
    <div class="page-body">
        {_info_box('"<strong>2024년부터 육아휴직 1년 6개월 + 부부 동시 사용 가능</strong>으로 대폭 확대됐습니다." 사장님 입장에선 부담 같지만, <strong>대체인력 채용 시 지원금</strong>을 활용하면 인건비가 오히려 절감되기도 합니다.')}

        {_section_title("2024 개정 육아휴직 핵심")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:170px;">항목</th><th>내용</th></tr></thead>
            <tbody>
                <tr><td><strong>사용 기간</strong></td>
                    <td><strong>1년</strong> (부부 모두 사용 시 각각 <strong>1년 6개월</strong>)</td></tr>
                <tr><td><strong>대상</strong></td>
                    <td>만 8세 이하 또는 초등 2학년 이하 자녀 양육 근로자 (입양 포함)</td></tr>
                <tr><td><strong>분할 사용</strong></td>
                    <td><strong>3회까지 분할 가능</strong> (1회 30일 이상)</td></tr>
                <tr><td><strong>급여 (고용보험)</strong></td>
                    <td><strong>1~3개월: 월 250만원</strong> / 4~6개월: 월 200만원 / 그 후: 월 160만원 한도</td></tr>
                <tr><td><strong>회사 부담</strong></td>
                    <td style="color:#2E7D32;font-weight:700;">사장님은 임금 지급 의무 없음 (고용보험에서 직접 지급)</td></tr>
                <tr style="background:#FFEBEE;"><td><strong>거부 시</strong></td>
                    <td style="color:#C62828;"><strong>3년 이하 징역 또는 3천만원 이하 벌금</strong> (남녀고용평등법 위반)</td></tr>
            </tbody>
        </table>

        {_section_title("육아기 근로시간 단축 (남녀고용평등법 제19조의2)")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:170px;">항목</th><th>내용</th></tr></thead>
            <tbody>
                <tr><td><strong>사용 가능</strong></td>
                    <td>육아휴직 미사용 + 만 8세 이하 또는 초2 이하 자녀</td></tr>
                <tr><td><strong>기간</strong></td>
                    <td>최대 <strong>2년</strong> (육아휴직 미사용 시 합산 최대 3년까지 가능)</td></tr>
                <tr><td><strong>근로시간</strong></td>
                    <td>주 <strong>15~35시간</strong> 사이로 단축</td></tr>
                <tr><td><strong>회사 부담</strong></td>
                    <td>단축된 시간만큼 임금 차감 가능 (단축근로 급여는 고용보험에서 별도 지급)</td></tr>
            </tbody>
        </table>

        {_section_title("대체인력 채용 시 회사가 받는 지원금")}
        <div style="background:#E8F5E9;border-left:5px solid #2E7D32;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:#1B5E20;font-size:13px;margin-bottom:6px;">💰 출산육아기 대체인력 지원금</div>
            <table style="width:100%;font-size:12.5px;margin-top:8px;">
                <tr><td style="padding:4px 0;"><strong>지원 대상</strong></td><td>육아휴직·육아기 단축근로 사용 근로자가 있고 대체인력 채용한 회사</td></tr>
                <tr><td style="padding:4px 0;"><strong>지원금액</strong></td><td><strong>월 80만원 × 휴직 기간</strong> (인수인계 기간 2개월 포함)</td></tr>
                <tr><td style="padding:4px 0;"><strong>중소기업 우대</strong></td><td>대규모 기업은 미적용. <strong>중소기업·중견기업만 지원</strong></td></tr>
                <tr><td style="padding:4px 0;"><strong>신청 시기</strong></td><td>대체인력 채용 후 3개월 시점부터 신청 가능</td></tr>
            </table>
        </div>

        {_section_title("사장님의 법적 의무")}
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12.5px;">
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>✅ 의무 사항</strong><br>
                <span style="color:#666;">• 신청 시 30일 이내 허용 결정<br>• 휴직 기간 중 불이익 처분 금지<br>• 복직 시 동일 직무·임금 보장</span>
            </div>
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>❌ 금지 사항</strong><br>
                <span style="color:#666;">• 신청 거부·해고·임금 삭감<br>• 휴직 사유로 인사고과 불이익<br>• 복직 시 다른 부서로 좌천</span>
            </div>
        </div>

        {_callout("💡 사장님 실무 팁", "<strong>육아휴직은 거부 못 합니다.</strong> 다만 대체인력 지원금을 활용하면 인건비 부담이 거의 없거나 오히려 절감 효과. 또한 <strong>출산전후휴가(90일)·배우자 출산휴가(10일)</strong>도 별도 의무. 직원 만족도 ↑ → 이직률 ↓ → 채용·교육 비용 ↓로 장기 ROI 큼.", "#2E7D32", "#E8F5E9,#C8E6C9", "#1B5E20")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 9. 외국인·고령자 채용 노무 가이드
# ════════════════════════════════════════════════════════════════
def labor_foreign_senior_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "외국인·고령자 채용 — 의무와 세액공제")}
    <div class="page-body">
        {_info_box('"<strong>인력난 해소의 두 축</strong>은 외국인과 고령자 채용입니다." 외국인은 비자별로 의무가 다르고, 60세 이상은 정년 연장·계속고용 의무가 있습니다. 정확히 알고 활용하면 세액공제·지원금까지 받습니다.')}

        {_section_title("외국인 근로자 — 비자별 의무")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:80px;">비자</th><th style="width:140px;">대상</th><th>회사 의무</th></tr></thead>
            <tbody>
                <tr><td><strong>E-7</strong></td>
                    <td>전문 인력 (IT·연구·기술)</td>
                    <td>고용계약서 + 비자 발급 협조, 내국인 동등 처우</td></tr>
                <tr><td><strong>E-9</strong></td>
                    <td>비전문 취업 (제조·건설)</td>
                    <td><strong>고용허가제</strong> 통한 채용 + 한국어능력시험 통과자</td></tr>
                <tr><td><strong>H-2</strong></td>
                    <td>방문취업 (재외동포)</td>
                    <td>특례고용허가제 + 자유로운 사업장 이동</td></tr>
                <tr><td><strong>F-4</strong></td>
                    <td>재외동포 (3세 이상)</td>
                    <td>고용허가 불필요, 내국인과 동일 처우</td></tr>
                <tr style="background:#FFEBEE;"><td colspan="3">
                    ⚠️ <strong>미등록 외국인 (불법체류) 고용 시 출입국법 위반 — 회사 3년 이하 / 3천만원 이하 벌금</strong></td></tr>
            </tbody>
        </table>

        {_section_title("외국인 채용 시 4대 의무")}
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;font-size:12.5px;">
            <div style="background:#fff;border-left:3px solid #0F2847;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>1️⃣ 4대보험 가입</strong><br><span style="color:#666;">국민·건강·고용·산재 (E-9도 가입 의무)</span>
            </div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>2️⃣ 최저임금·근기법 동일 적용</strong><br><span style="color:#666;">내국인과 동일한 임금·근로조건</span>
            </div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>3️⃣ 외국인 등록사항 변경 신고</strong><br><span style="color:#666;">근무지 변경 14일 이내 출입국 신고</span>
            </div>
            <div style="background:#fff;border-left:3px solid #0F2847;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>4️⃣ 출국 시 퇴직금 정산</strong><br><span style="color:#666;">출국만기보험 또는 퇴직금 IPS 가입</span>
            </div>
        </div>

        {_section_title("고령자(60세 이상) 채용 — 정년·계속고용 의무")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:170px;">법적 사항</th><th>내용</th></tr></thead>
            <tbody>
                <tr><td><strong>정년 60세 이상</strong></td>
                    <td>고령자고용법: <strong>모든 사업장 정년 60세 이상</strong> 의무 (위반 시 임금 보상)</td></tr>
                <tr><td><strong>계속고용제도</strong></td>
                    <td>2025년부터 60세 정년 도래 시 <strong>① 정년 연장 ② 재고용 ③ 정년 폐지</strong> 중 택일 권장</td></tr>
                <tr><td><strong>임금피크제</strong></td>
                    <td>정년 연장하면서 일정 시점부터 임금 단계적 삭감 (취업규칙 명시 필요)</td></tr>
                <tr style="background:#E8F5E9;"><td><strong>💰 세액공제</strong></td>
                    <td style="color:#1B5E20;font-weight:700;">고령자 신규 채용 시 통합고용세액공제 <strong>1인당 1,450만원 × 3년</strong></td></tr>
            </tbody>
        </table>

        {_section_title("고령자·외국인 채용 시 활용 가능한 제도")}
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;font-size:12.5px;">
            <div style="background:#E8F5E9;border-left:3px solid #2E7D32;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>💰 통합고용세액공제</strong><br>
                <span style="color:#666;">청년·장애인·60세이상 채용: 1,450만 × 3년<br>일반: 850만 × 3년</span>
            </div>
            <div style="background:#FFF8E1;border-left:3px solid #C9A961;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>💼 고용창출장려금</strong><br>
                <span style="color:#666;">사회적기업·취업취약계층 채용 시 인건비 일부 지원</span>
            </div>
            <div style="background:#E3F2FD;border-left:3px solid #1976D2;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>👴 60세이상 고령자 고용지원금</strong><br>
                <span style="color:#666;">분기당 30만원 × 최대 2년 (제조업 등 우선업종)</span>
            </div>
            <div style="background:#F3E5F5;border-left:3px solid #7B1FA2;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>🌍 외국인 정착지원금</strong><br>
                <span style="color:#666;">한국어 교육비·숙소 비용 일부 지원 (지자체별 상이)</span>
            </div>
        </div>

        {_callout("🎯 결국 핵심은", "인력난 시대에 <strong>다양한 채용 풀</strong>을 활용하는 회사가 살아남습니다. 외국인은 <strong>비자별 의무 정확히 파악</strong> + 4대보험 누락 주의, 60세 이상 채용은 <strong>통합고용세액공제로 절세 효과까지</strong> 챙기세요.", "#0F2847", "#E3F2FD,#BBDEFB", "#0D47A1")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 10. 노동위원회·고용노동부 진정 대응
# ════════════════════════════════════════════════════════════════
def labor_dispute_response_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "노동 분쟁 대응 — 진정·고발·구제신청")}
    <div class="page-body">
        {_info_box('"<strong>직원이 노동청 가기 전에 어떻게 대응하느냐가 분쟁 결과를 결정합니다.</strong>" 진정·고발·구제신청의 차이를 모르면 대응을 잘못해서 형사 송치까지 갈 수 있습니다. 단계별 대응 가이드.')}

        {_section_title("3가지 분쟁 경로 — 차이점")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:80px;">구분</th><th style="width:130px;">진정</th><th style="width:130px;">고소·고발</th><th>구제신청</th></tr></thead>
            <tbody>
                <tr><td><strong>접수처</strong></td>
                    <td>지방고용노동관서</td>
                    <td>지방고용노동관서·경찰</td>
                    <td>지방노동위원회</td></tr>
                <tr><td><strong>내용</strong></td>
                    <td>임금체불·근로조건 위반</td>
                    <td>형사처벌 요구</td>
                    <td>부당해고·부당노동행위</td></tr>
                <tr><td><strong>기한</strong></td>
                    <td>임금시효 3년</td>
                    <td>형사시효 적용</td>
                    <td><strong>해고 후 3개월</strong></td></tr>
                <tr><td><strong>결과</strong></td>
                    <td>시정지시 → 형사송치</td>
                    <td>형사처벌·벌금</td>
                    <td>복직·임금지급 명령</td></tr>
                <tr><td><strong>비용</strong></td>
                    <td>무료</td>
                    <td>무료</td>
                    <td>무료</td></tr>
            </tbody>
        </table>

        {_section_title("노동청 진정 — 출석조사 대응 5대 원칙")}
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:40px;">#</th><th style="width:160px;">원칙</th><th>설명</th></tr></thead>
            <tbody>
                <tr><td><strong>1</strong></td><td><strong>출석 거부 금지</strong></td>
                    <td>출석 통보 받으면 <strong>반드시 지정일 출석</strong> (불가 시 사전 연기 요청). 무단불출석 시 강제구인 가능</td></tr>
                <tr><td><strong>2</strong></td><td><strong>증거 사전 정리</strong></td>
                    <td>근로계약서·임금명세서·근태기록·취업규칙 등 <strong>모든 자료를 정리해 지참</strong></td></tr>
                <tr><td><strong>3</strong></td><td><strong>사실 위주 진술</strong></td>
                    <td>감정·변명 금지. <strong>객관적 사실 + 증거 기반 진술</strong>. 모르면 "확인 후 답변"</td></tr>
                <tr><td><strong>4</strong></td><td><strong>노무사·변호사 대동</strong></td>
                    <td>중대 사안은 반드시 <strong>전문가 동석</strong> (자문료 30~100만 << 분쟁 손해)</td></tr>
                <tr><td><strong>5</strong></td><td><strong>합의 우선 시도</strong></td>
                    <td>시정지시 받기 전 <strong>당사자 합의 시도</strong> → 합의서 작성 → 노동청에 합의 사실 제출 → 사건 종결</td></tr>
            </tbody>
        </table>

        {_section_title("부당해고 구제신청 흐름 (노동위원회)")}
        <div style="background:#F4F1EC;padding:14px;border-radius:10px;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:11.5px;">
                <div style="background:#0F2847;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:95px;text-align:center;">
                    <strong>① 해고 발생</strong><br><span style="font-size:10px;opacity:0.85;">D-day</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#1B3A6B;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:95px;text-align:center;">
                    <strong>② 구제신청</strong><br><span style="font-size:10px;opacity:0.85;">3개월 이내</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#2A5298;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:95px;text-align:center;">
                    <strong>③ 심문회의</strong><br><span style="font-size:10px;opacity:0.85;">약 2~3개월</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#C9A961;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:95px;text-align:center;">
                    <strong>④ 판정</strong><br><span style="font-size:10px;opacity:0.85;">부당해고 인정/기각</span>
                </div>
                <span style="color:#C9A961;font-weight:700;">→</span>
                <div style="background:#8B6F3E;color:white;padding:8px 10px;border-radius:6px;flex:1;min-width:95px;text-align:center;">
                    <strong>⑤ 이행/재심</strong><br><span style="font-size:10px;opacity:0.85;">중앙노위 → 행정법원</span>
                </div>
            </div>
        </div>

        {_section_title("회사가 절대 하지 말아야 할 3가지")}
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;font-size:12.5px;">
            <div style="background:#FFEBEE;border-left:4px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>❌ 신고자 보복</strong><br><span style="color:#666;">해고·전보·임금삭감 → <strong>2차 형사처벌 + 추가 손해배상</strong></span>
            </div>
            <div style="background:#FFEBEE;border-left:4px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>❌ 증거 인멸·은닉</strong><br><span style="color:#666;">근태기록·CCTV·메신저 삭제 → <strong>증거인멸죄·위계공무집행방해</strong></span>
            </div>
            <div style="background:#FFEBEE;border-left:4px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>❌ 직원 대상 협박</strong><br><span style="color:#666;">"신고 취하해" 압박·회유 → <strong>강요죄·공갈죄 추가 형사처벌</strong></span>
            </div>
        </div>

        {_callout("💡 결국 가장 좋은 방법은", "사건 발생 시 <strong>① 즉시 노무사·변호사 자문 ② 사실 관계 정리 + 증거 보존 ③ 가능하면 당사자 합의 우선</strong>. 노동청·법원 가면 <strong>회사가 압도적으로 불리</strong>합니다(근로자 보호 원칙). 평소에 <strong>근로계약서·취업규칙·증빙 관리</strong>가 분쟁 예방의 90%.", "#C62828", "#FFEBEE,#FFCDD2", "#B71C1C")}
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 11. 노무 리스크 자가진단표 (자동 점수화)
# ════════════════════════════════════════════════════════════════
def labor_risk_diagnosis_page(company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    """
    노무 리스크 자가진단 — 사업장 규모/업종 기반 자동 노출 항목 점수화
    """
    emp_count_str = str(company.get("종업원수", "")).strip()
    # 종업원수 추출
    import re
    m = re.search(r"(\d+)", emp_count_str)
    emp_n = int(m.group(1)) if m else 0
    
    biz_type = str(company.get("기업유형", "")).strip()
    industry = str(company.get("업태", "") or company.get("주업종코드", "")).strip()
    
    # 리스크 항목 (사업장 규모별 적용 여부)
    # 각 항목: (label, 적용조건함수, 위반시 부담, 위험도 weight 1~3)
    items = [
        ("근로계약서 서면 작성·교부", lambda n: n >= 1, "과태료 1인당 500만, 형사처벌", 3),
        ("최저임금 준수 (시급 10,030원 기준)", lambda n: n >= 1, "3년 소급 + 형사처벌", 3),
        ("임금명세서 교부 의무", lambda n: n >= 1, "1인당 500만 과태료", 2),
        ("4대보험 가입 (사장 1인 가입 의무)", lambda n: n >= 1, "3년 소급 + 추징 + 가산금", 3),
        ("연차휴가 부여 (5인 이상)", lambda n: n >= 5, "연차수당 미지급 → 임금체불", 3),
        ("연장·야간·휴일 가산수당 1.5배", lambda n: n >= 5, "3년 미지급 추징 + 형사처벌", 3),
        ("주 52시간 근로시간 한도", lambda n: n >= 5, "2년 이하 / 2천만 벌금", 2),
        ("부당해고 금지 / 서면통지", lambda n: n >= 5, "복직 + 미지급임금 (평균 3~5천만)", 3),
        ("취업규칙 작성·신고", lambda n: n >= 10, "500만 과태료", 2),
        ("직장 내 괴롭힘 예방 의무", lambda n: n >= 10, "조치 미이행 시 500만 과태료", 2),
        ("성희롱 예방교육 연 1회", lambda n: n >= 1, "500만 과태료 (전 사업장)", 2),
        ("출산휴가 90일 / 배우자 10일", lambda n: n >= 1, "3년 이하 / 3천만 벌금", 2),
        ("육아휴직 1년~1년 6개월", lambda n: n >= 1, "3년 이하 / 3천만 벌금", 2),
        ("퇴직급여(DB/DC) 가입", lambda n: n >= 1, "1년 유예 후 미가입 시 과태료", 2),
        ("산업안전보건법 (안전관리)", lambda n: n >= 5, "위반 시 1억원+ 벌금 가능", 3),
        ("정년 60세 이상 보장", lambda n: n >= 1, "임금 보전 의무", 1),
        ("장애인 의무고용 (50인 이상)", lambda n: n >= 50, "분담금 부담 (월 1인당 약 130만)", 2),
        ("취업규칙·노사협의회 설치 (30인 이상)", lambda n: n >= 30, "1천만 이하 벌금", 2),
    ]
    
    # 적용 항목 + 위험도 합산
    applicable = [(label, fail_cost, weight) for label, cond, fail_cost, weight in items if cond(emp_n)]
    total_risk = sum(w for _, _, w in applicable)
    
    # 추정 미준수 항목 — 실제 데이터 없으면 사업장 규모로 추정
    # 5인 미만: 매우 적음 / 10인 이상: 평균 30% 위반 추정
    if emp_n < 5:
        violation_rate = 0.10
    elif emp_n < 10:
        violation_rate = 0.20
    elif emp_n < 30:
        violation_rate = 0.30
    elif emp_n < 50:
        violation_rate = 0.40
    else:
        violation_rate = 0.50
    
    estimated_violations = int(len(applicable) * violation_rate)
    risk_score = max(0, min(100, int(100 - violation_rate * 100)))
    
    # 등급
    if risk_score >= 85:
        grade, grade_color = "A (안전)", "#2E7D32"
    elif risk_score >= 70:
        grade, grade_color = "B (양호)", "#7CB342"
    elif risk_score >= 55:
        grade, grade_color = "C (보통)", "#FB8C00"
    elif risk_score >= 40:
        grade, grade_color = "D (주의)", "#E65100"
    else:
        grade, grade_color = "E (위험)", "#C62828"
    
    # 항목 테이블 (적용 항목 기준)
    rows = ""
    for label, fail_cost, weight in applicable:
        risk_icon = "🔴" if weight == 3 else "🟠" if weight == 2 else "🟡"
        rows += f"""
        <tr>
            <td>{risk_icon}</td>
            <td><strong>{label}</strong></td>
            <td style="font-size:11.5px;color:#666;">{fail_cost}</td>
        </tr>
        """
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, _section_badge_text(is_personal), "노무 리스크 자가진단 — 종합 점수표")}
    <div class="page-body">
        {_info_box('"<strong>사장님 회사는 지금 몇 개의 노무 법규에 노출되어 있을까요?</strong>" 사업장 규모(상시근로자 수)에 따라 적용되는 법규가 달라집니다. 자동 진단으로 한눈에 확인하세요.')}

        <!-- 진단 결과 카드 -->
        <div style="display:grid;grid-template-columns:200px 1fr;gap:20px;margin-top:8px;align-items:stretch;">
            <div style="background:linear-gradient(135deg,{grade_color},{grade_color}99);border-radius:14px;padding:18px;text-align:center;color:white;">
                <div style="font-size:11px;letter-spacing:2px;font-weight:600;">노무 안전도</div>
                <div style="font-size:50px;font-weight:900;line-height:1;margin:6px 0;">{grade.split()[0]}</div>
                <div style="font-size:14px;opacity:0.95;">{grade.split()[1] if len(grade.split()) > 1 else ''}</div>
                <div style="font-size:18px;font-weight:800;margin-top:8px;">{risk_score}<span style="font-size:12px;">/100</span></div>
            </div>
            <div style="display:grid;grid-template-rows:1fr 1fr;gap:8px;">
                <div style="background:#fff;border:1px solid #E5E7EB;padding:14px 18px;border-radius:10px;">
                    <div style="font-size:11px;color:#888;font-weight:600;">상시근로자 수 (자동 인식)</div>
                    <div style="font-size:22px;font-weight:800;color:#0F2847;margin-top:4px;">{emp_n}명 {('(직접 입력 필요)' if emp_n == 0 else '')}</div>
                </div>
                <div style="background:#fff;border:1px solid #E5E7EB;padding:14px 18px;border-radius:10px;">
                    <div style="font-size:11px;color:#888;font-weight:600;">적용되는 노무 법규</div>
                    <div style="font-size:22px;font-weight:800;color:#0F2847;margin-top:4px;">{len(applicable)}<span style="font-size:13px;">개 항목</span> &nbsp;&nbsp;<span style="font-size:13px;color:#C62828;">예상 노출: 약 {estimated_violations}건</span></div>
                </div>
            </div>
        </div>

        {_section_title(f"사업장 규모별 적용 법규 ({emp_n}명 기준 {len(applicable)}개 항목)")}
        <table class="data-table financial-table compact" style="font-size:12.5px;">
            <thead><tr><th style="width:40px;">위험도</th><th style="width:300px;">의무 사항</th><th>위반 시 부담</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px;font-size:11.5px;">
            <div style="background:#FFEBEE;border-left:3px solid #C62828;padding:8px 12px;">🔴 <strong>고위험</strong> — 형사처벌·억원대 부담</div>
            <div style="background:#FFF3E0;border-left:3px solid #E65100;padding:8px 12px;">🟠 <strong>중위험</strong> — 과태료·소급추징</div>
            <div style="background:#FFF8E1;border-left:3px solid #C9A961;padding:8px 12px;">🟡 <strong>저위험</strong> — 행정지도·시정명령</div>
        </div>

        {_section_title("사업장 규모별 적용 기준선 (참고)")}
        <table class="data-table financial-table compact" style="font-size:12px;">
            <thead><tr><th>규모</th><th>적용되는 핵심 법규</th></tr></thead>
            <tbody>
                <tr><td><strong>1인 이상</strong></td>
                    <td>근로계약서·최저임금·임금명세서·4대보험·성희롱예방·출산휴가·육아휴직</td></tr>
                <tr><td><strong>5인 이상</strong></td>
                    <td>+ 연차·연장수당·주52시간·해고제한·산업안전</td></tr>
                <tr><td><strong>10인 이상</strong></td>
                    <td>+ 취업규칙 작성·신고·괴롭힘 예방</td></tr>
                <tr><td><strong>30인 이상</strong></td>
                    <td>+ 노사협의회</td></tr>
                <tr><td><strong>50인 이상</strong></td>
                    <td>+ 장애인 의무고용 (3.1%)</td></tr>
            </tbody>
        </table>

        {_callout("🎯 컨설팅 결론", f"사장님 회사 ({emp_n}명 규모)는 <strong>총 {len(applicable)}개 노무 법규</strong>에 노출되어 있습니다. <strong>예상 미준수 {estimated_violations}건</strong>은 평균적인 동종 규모 사업장 기준이며, 실제 점검 시 더 많거나 적을 수 있습니다. 가장 시급한 것은 <strong>🔴 고위험 항목 점검</strong> (근로계약서·임금·4대보험·연차)이며, 노무사 정기 자문(월 30~50만)을 받는 것이 최종 분쟁 대비 가장 경제적입니다.", "#0F2847", "#E3F2FD,#BBDEFB", "#0D47A1")}
    </div>
</div>
"""
