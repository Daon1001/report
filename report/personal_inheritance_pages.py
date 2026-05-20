"""
개인사업자 상속세 컨설팅 페이지
- 사업용 자산 기반 상속세 시뮬레이션
- 가업상속공제 (개인사업자도 적용 가능)
- 종신보험 재원 마련 전략 (기존 페이지와 별도 - 개인사업자 맞춤)
"""


def _logo_header(LOGO_SMALL, section_badge, page_title):
    return f"""
    <div class="page-header">
        <img src="{LOGO_SMALL}" class="header-logo" alt="RSV"/>
        <span class="section-badge">{section_badge}</span>
        <span class="page-title-main">{page_title}</span>
    </div>"""


def _fmt(v, unit="원", placeholder="—"):
    if v is None:
        return placeholder
    # float이지만 실제로는 정수값이면 정수처럼 표시
    if isinstance(v, float):
        if v == 0:
            return f"0{unit}"
        if v.is_integer():
            return f"{int(v):,}{unit}"
        return f"{v:,.0f}{unit}"
    if v == 0:
        return f"0{unit}"
    return f"{v:,}{unit}"


def _calc_inheritance_tax(taxable):
    """상속세 누진세율 계산 (원 단위)"""
    if taxable <= 0:
        return 0
    if taxable <= 100_000_000:        # 1억 이하
        return taxable * 0.10
    elif taxable <= 500_000_000:      # 5억 이하
        return 10_000_000 + (taxable - 100_000_000) * 0.20
    elif taxable <= 1_000_000_000:    # 10억 이하
        return 90_000_000 + (taxable - 500_000_000) * 0.30
    elif taxable <= 3_000_000_000:    # 30억 이하
        return 240_000_000 + (taxable - 1_000_000_000) * 0.40
    else:
        return 1_040_000_000 + (taxable - 3_000_000_000) * 0.50


# ════════════════════════════════════════════════════════════════
# 1. 개인사업자 상속세 시뮬레이션 (사업용 자산 기준)
# ════════════════════════════════════════════════════════════════
def personal_inheritance_tax_page(bs: dict, company: dict, LOGO_SMALL: str) -> str:
    """
    개인사업자의 상속재산 = 사업용 자산 + 개인 자산
    여기선 사업용 자산만 기준으로 시뮬레이션 (개인 자산은 별도 정보 필요)
    """
    company_name = company.get("기업명", "사업체")
    
    # 가장 최근 연도의 자산 추출
    years = bs.get("years", [])
    if not years:
        return ""
    latest = years[-1]
    bs_data = bs.get(latest, {}) if latest in bs else {}
    
    total_asset = bs_data.get("자산총계") or bs_data.get("자산") or 0
    cur_asset = bs_data.get("유동자산") or 0
    fixed_asset = bs_data.get("비유동자산") or bs_data.get("고정자산") or 0
    # 부채는 상속재산에서 차감
    total_liab = bs_data.get("부채총계") or bs_data.get("부채") or 0
    capital = bs_data.get("자본총계") or bs_data.get("자본") or 0
    
    # 순상속재산 = 자산 - 부채 (자본총계)
    net_estate = capital if capital > 0 else (total_asset - total_liab)
    
    # 시나리오: 100% 상속 (자녀 1인) / 가업상속공제 적용 / 미적용 비교
    deduction_base = 1_000_000_000  # 일괄공제 5억 + 배우자공제 5억
    
    # 가업상속공제 (개인사업자도 일정 요건 충족 시 가능)
    # 10년 이상 영위 + 사업자 본인 직접 경영 + 상속인 사업 승계 조건
    gauk_max = min(net_estate * 0.5, 30_000_000_000)  # 최대 300억 (10년 사업)
    
    # 시나리오 1: 공제 없음 (일반 상속)
    taxable_normal = max(net_estate - deduction_base, 0)
    tax_normal = _calc_inheritance_tax(taxable_normal)
    
    # 시나리오 2: 가업상속공제 적용
    taxable_with_gauk = max(net_estate - deduction_base - gauk_max, 0)
    tax_with_gauk = _calc_inheritance_tax(taxable_with_gauk)
    
    # 시나리오 3: 종신보험 활용 (보험금 5억 가정)
    insurance_amount = 500_000_000
    
    saved = tax_normal - tax_with_gauk
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, "💰 상속세 플랜", "개인사업자 상속세 시뮬레이션")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            "<strong>개인사업자도 상속세는 똑같이 발생합니다.</strong>" 사업용 자산(부동산·기계장치·재고)이 그대로 상속재산이 되며,
            준비 없이 사망 시 <strong>거액의 상속세를 6개월 내 현금으로 일시납</strong>해야 합니다.
        </div>

        <!-- 현재 사업 자산 현황 -->
        <h3 class="subsection-title">◆ 현재 사업 자산 현황 (재무상태표 기준)</h3>
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:200px;">구분</th><th class="num">금액</th><th>비고</th></tr></thead>
            <tbody>
                <tr><td><strong>자산총계</strong></td>
                    <td class="num">{_fmt(total_asset)}</td>
                    <td style="text-align:left;font-size:12px;">사업용 모든 자산</td></tr>
                <tr><td>　유동자산</td>
                    <td class="num">{_fmt(cur_asset)}</td>
                    <td style="text-align:left;font-size:12px;">현금·매출채권·재고</td></tr>
                <tr><td>　비유동자산</td>
                    <td class="num">{_fmt(fixed_asset)}</td>
                    <td style="text-align:left;font-size:12px;">건물·기계장치·차량 등</td></tr>
                <tr><td><strong>부채총계</strong></td>
                    <td class="num" style="color:#C62828;">{_fmt(total_liab)}</td>
                    <td style="text-align:left;font-size:12px;">은행 차입금·매입채무</td></tr>
                <tr class="total-row"><td><strong>순상속재산 (자본총계)</strong></td>
                    <td class="num"><strong style="color:#0F2847;">{_fmt(net_estate)}</strong></td>
                    <td style="text-align:left;font-size:12px;"><strong>실제 상속될 자산 가치</strong></td></tr>
            </tbody>
        </table>
        
        <div style="background:#FFF8E1;padding:10px 14px;border-radius:8px;margin-top:8px;font-size:12px;color:#3A2F1E;">
            💡 <strong>실제 상속재산</strong>은 위 사업용 자산에 <strong>개인 부동산·예금·차량·금융자산 등을 모두 합산</strong>하여 계산됩니다.
            아래는 사업용 자산만 기준으로 한 <strong>최소 추정치</strong>입니다.
        </div>

        <!-- 시나리오 비교 -->
        <h3 class="subsection-title" style="margin-top:16px;">◆ 상속세 시뮬레이션 - 3가지 시나리오</h3>
        <table class="data-table financial-table compact">
            <thead>
                <tr style="background:#0F2847;color:white;">
                    <th style="width:180px;background:#0F2847;color:white;padding:10px 12px;">시나리오</th>
                    <th class="num" style="background:#0F2847;color:white;padding:10px 12px;">상속재산</th>
                    <th class="num" style="background:#0F2847;color:white;padding:10px 12px;">공제액</th>
                    <th class="num" style="background:#0F2847;color:white;padding:10px 12px;">과세표준</th>
                    <th class="num" style="background:#0F2847;color:white;padding:10px 12px;">상속세</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>① 일반 상속</strong><br><span style="font-size:11px;color:#888;">기본공제만 적용</span></td>
                    <td class="num">{_fmt(net_estate)}</td>
                    <td class="num">{_fmt(deduction_base)}<br><span style="font-size:10px;color:#888;">(기본공제)</span></td>
                    <td class="num">{_fmt(taxable_normal)}</td>
                    <td class="num" style="color:#C62828;font-weight:800;">{_fmt(tax_normal)}</td>
                </tr>
                <tr style="background:#E8F5E9;">
                    <td><strong>② 가업상속공제 적용</strong><br><span style="font-size:11px;color:#2E7D32;">10년+ 사업 영위 + 승계 시</span></td>
                    <td class="num">{_fmt(net_estate)}</td>
                    <td class="num">{_fmt(deduction_base + gauk_max)}<br><span style="font-size:10px;color:#2E7D32;">(기본 {deduction_base/100_000_000:.0f}억 + 가업 {gauk_max/100_000_000:.1f}억)</span></td>
                    <td class="num">{'<span style="color:#2E7D32;font-weight:700;">전액 공제</span>' if taxable_with_gauk == 0 else _fmt(taxable_with_gauk)}</td>
                    <td class="num" style="color:#2E7D32;font-weight:800;">{'<span style="font-size:13px;">면제</span>' if tax_with_gauk == 0 else _fmt(tax_with_gauk)}</td>
                </tr>
                <tr style="background:#FFF8E1;">
                    <td><strong>③ ②+종신보험 재원</strong><br><span style="font-size:11px;color:#8B6F3E;">납부재원 부족 해결</span></td>
                    <td class="num">{_fmt(net_estate)}</td>
                    <td class="num">{_fmt(deduction_base + gauk_max)}<br><span style="font-size:10px;color:#8B6F3E;">(공제 + 보험금 활용)</span></td>
                    <td class="num">{'<span style="color:#8B6F3E;font-weight:700;">전액 공제</span>' if taxable_with_gauk == 0 else _fmt(taxable_with_gauk)}</td>
                    <td class="num" style="color:#8B6F3E;font-weight:800;">{'<span style="font-size:13px;">면제</span>' if tax_with_gauk == 0 else _fmt(tax_with_gauk)}<br><span style="font-size:10px;font-weight:600;">(보험금 {insurance_amount/100_000_000:.0f}억 재원 확보)</span></td>
                </tr>
            </tbody>
        </table>

        <!-- 절세 효과 강조 -->
        {f'''<div style="margin-top:14px;background:linear-gradient(135deg,#E8F5E9,#C8E6C9);border-left:5px solid #2E7D32;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:#1B5E20;font-size:13px;margin-bottom:6px;">💰 가업상속공제 적용 시 절세 효과</div>
            <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:14px;font-size:13px;color:#2B2416;line-height:1.6;">
                <div><div style="font-size:11px;color:#666;">일반 상속세</div><div style="font-size:18px;font-weight:900;color:#C62828;">{tax_normal/100_000_000:.2f}억</div></div>
                <div style="font-size:24px;color:#666;align-self:center;">→</div>
                <div><div style="font-size:11px;color:#666;">가업상속공제 후</div><div style="font-size:18px;font-weight:900;color:#2E7D32;">{tax_with_gauk/100_000_000:.2f}억</div></div>
                <div style="font-size:24px;color:#666;align-self:center;">=</div>
                <div><div style="font-size:11px;color:#666;">절세액</div><div style="font-size:20px;font-weight:900;color:#0F2847;">{saved/100_000_000:.2f}억</div></div>
            </div>
        </div>''' if saved > 0 else ''}

        <!-- 컨설팅 메시지 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-left:5px solid #C9A961;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:#8B6F3E;font-size:13px;margin-bottom:6px;">💡 컨설턴트의 시각</div>
            <div style="font-size:13px;line-height:1.6;color:#2B2416;">
                개인사업자 사장님도 사망 시 <strong>{net_estate/100_000_000:.1f}억원 규모의 상속재산</strong>이 발생할 수 있습니다.
                가업상속공제 요건(10년 이상 직접 경영 + 자녀 승계)을 충족하면 <strong>{saved/100_000_000:.2f}억원 절세</strong> 가능하지만,
                <strong>승계 후 7년간 사업 유지·고용 유지 의무</strong>가 있어 사전 설계가 필수입니다.
                다음 페이지에서 <strong>종신보험을 활용한 납부재원 마련</strong> 전략을 안내합니다.
            </div>
        </div>

        <div style="margin-top:12px;font-size:11.5px;color:#888;padding:8px 14px;background:#F4F1EC;border-radius:6px;">
            ⚠️ <strong>본 시뮬레이션은 사업용 자산만 기준</strong>으로 한 추정치입니다. 실제 상속세는 개인 부동산·예금·금융자산을 모두 합산하여 계산되며,
            상속인 구성·공제 항목에 따라 달라질 수 있습니다. 정확한 산정은 세무사 상담 필수.
        </div>
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 2. 개인사업자 가업상속공제 + 사업승계 가이드
# ════════════════════════════════════════════════════════════════
def personal_business_succession_page(company: dict, LOGO_SMALL: str) -> str:
    """가업상속공제 요건 + 사업 승계 전략"""
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, "💰 상속세 플랜", "가업상속공제 & 사업 승계 전략")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            "<strong>가업상속공제는 개인사업자도 적용 가능합니다.</strong>" 최대 600억까지 공제되는 강력한 절세 도구지만,
            요건이 까다롭고 <strong>승계 후 7년 사후관리 의무</strong>가 있어 신중한 사전 설계가 필요합니다.
        </div>

        <!-- 가업상속공제 핵심 -->
        <h3 class="subsection-title">◆ 가업상속공제 - 개인사업자 적용 요건</h3>
        <table class="data-table financial-table compact">
            <thead><tr><th style="width:140px;">구분</th><th>요건</th></tr></thead>
            <tbody>
                <tr><td><strong>사업 영위 기간</strong></td>
                    <td>피상속인이 <strong>10년 이상</strong> 계속하여 경영</td></tr>
                <tr><td><strong>경영 형태</strong></td>
                    <td>피상속인이 <strong>대표자로서 사업을 직접 영위</strong> (명의대여·휴업 기간 제외)</td></tr>
                <tr><td><strong>업종</strong></td>
                    <td>제조업·도소매업·서비스업 등 <strong>대부분 업종 가능</strong> (부동산 임대업·금융업 등 일부 제외)</td></tr>
                <tr><td><strong>매출액</strong></td>
                    <td>중소·중견기업 (직전 3개 사업연도 평균 매출액 5,000억 미만)</td></tr>
                <tr><td><strong>상속인</strong></td>
                    <td>상속개시일 현재 <strong>18세 이상 + 2년 이상 가업 종사 + 상속개시 전 동거</strong></td></tr>
                <tr><td><strong>승계 기간</strong></td>
                    <td>상속세 신고기한 내 가업 인수 + 등록 (개인사업자: 사업자등록 명의 변경)</td></tr>
                <tr style="background:#FFF8E1;"><td><strong>공제 한도</strong></td>
                    <td><strong>10~20년</strong>: 200억 / <strong>20~30년</strong>: 300억 / <strong>30년+</strong>: 600억</td></tr>
            </tbody>
        </table>

        <!-- 사후관리 의무 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 사후관리 의무 - 7년간 (위반 시 공제액 추징)</h3>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;font-size:12.5px;">
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>📍 사업 유지 의무</strong><br>
                <span style="color:#666;">상속개시 후 7년간 가업 계속 영위. <strong>폐업·휴업 시 추징</strong></span>
            </div>
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>👥 고용 유지 의무</strong><br>
                <span style="color:#666;">7년간 정규직 고용 인원 <strong>80% 이상 유지</strong></span>
            </div>
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>💰 자산 처분 제한</strong><br>
                <span style="color:#666;">가업용 자산의 <strong>20% 이상 처분 금지</strong> (5년간)</span>
            </div>
            <div style="background:#fff;border-left:3px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;">
                <strong>📊 매출액 유지</strong><br>
                <span style="color:#666;">상속개시일 직전 사업연도 매출액의 <strong>일정 수준 유지</strong></span>
            </div>
        </div>
        
        <div style="background:#FFEBEE;border-left:4px solid #C62828;padding:11px 14px;border-radius:0 8px 8px 0;margin-top:10px;">
            <strong style="color:#B71C1C;font-size:12.5px;">⚠️ 사후관리 위반 시</strong>
            <div style="font-size:12px;color:#2B2416;margin-top:4px;line-height:1.5;">
                감면받은 상속세 + <strong>이자상당액 추징</strong>. 7년 사후관리 의무 부담이 커서 <strong>승계 의사가 명확한 경우에만 활용</strong> 권장.
            </div>
        </div>

        <!-- 개인 vs 법인 비교 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 사업 승계 시 개인사업자 vs 법인전환 비교</h3>
        <table class="data-table financial-table compact">
            <thead><tr><th></th><th>개인사업자 그대로 승계</th><th>법인전환 후 승계</th></tr></thead>
            <tbody>
                <tr><td><strong>승계 절차</strong></td>
                    <td>사업자등록 명의변경 (간단)</td>
                    <td>주식 양도 또는 상속 (간단)</td></tr>
                <tr><td><strong>상속세 부담</strong></td>
                    <td>사업용 자산 전체 시가 기준</td>
                    <td>비상장주식 가치 기준 (보충적 평가)</td></tr>
                <tr><td><strong>가업상속공제</strong></td>
                    <td>최대 600억</td>
                    <td>최대 600억 (동일)</td></tr>
                <tr><td><strong>법인전환 비용</strong></td>
                    <td>해당없음</td>
                    <td>설립·자본금·이전등록 등 부담</td></tr>
                <tr><td><strong>임원퇴직금</strong></td>
                    <td>❌ 해당없음 (대표 본인)</td>
                    <td>✅ 임원퇴직금 활용 가능</td></tr>
                <tr><td><strong>배당</strong></td>
                    <td>❌ 해당없음</td>
                    <td>✅ 배당 통한 가족 소득 분산</td></tr>
                <tr style="background:#FFF8E1;"><td><strong>적합 케이스</strong></td>
                    <td>매출 10억 이하 + 자녀 단독 승계</td>
                    <td>매출 30억+ 또는 가족 분산 승계</td></tr>
            </tbody>
        </table>

        <!-- 컨설팅 메시지 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;border-radius:12px;padding:16px 20px;">
            <div style="font-weight:800;font-size:14px;margin-bottom:8px;color:#C9A961;">🎯 사장님께 드리는 3가지 핵심 조언</div>
            <ol style="margin:0;padding-left:22px;font-size:13px;line-height:1.8;">
                <li><strong>가업 승계 의사가 명확</strong>하다면 → 가업상속공제 적극 활용 (10년 이상 영위 요건 충족 확인)</li>
                <li><strong>매출 규모가 커지고 가족 여러 명에게 승계</strong>한다면 → 법인전환 검토 (배당·임원퇴직금 활용)</li>
                <li><strong>승계가 불확실</strong>하다면 → 종신보험으로 상속세 재원 마련 (다음 페이지)</li>
            </ol>
        </div>
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 3. 개인사업자 종신보험 활용 상속세 재원 마련
# ════════════════════════════════════════════════════════════════
def personal_inheritance_insurance_page(LOGO_SMALL: str) -> str:
    """종신보험 활용 상속세 재원 마련 - 개인사업자 맞춤"""
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, "💰 상속세 플랜", "종신보험을 통한 상속세 재원 마련")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            <div style="font-weight:800;color:#0F2847;margin-bottom:4px;">국세청 공식 입장 · 상속세 안내자료</div>
            <div>"<strong>종신보험은 상속세 납부재원 마련의 가장 효과적 수단</strong>"</div>
            <div style="font-size:12px;color:#666;margin-top:4px;">국세청은 「상속·증여세 안내」를 통해 종신보험 활용을 공식 권장 (출처: 국세청 상속세 절세 가이드북)</div>
        </div>

        <!-- 왜 종신보험인가 -->
        <h3 class="subsection-title">◆ 상속세 납부 현실 - 왜 종신보험이 필수인가?</h3>
        <div style="background:#FFEBEE;border-left:5px solid #C62828;padding:12px 18px;border-radius:0 10px 10px 0;font-size:13px;line-height:1.6;color:#2B2416;">
            ⚠️ <strong>개인사업자의 상속재산 80% 이상이 즉시 현금화 곤란한 사업용 자산</strong>(부동산·기계·재고).
            상속세는 <strong>현금 일시납 원칙</strong>으로 6개월 내 납부 필요 →
            <strong>현금 부족으로 사업체 매각 또는 부동산 헐값 처분</strong> 사례 빈발
        </div>

        <h3 class="subsection-title" style="margin-top:14px;">◆ 종신보험 활용 3대 효과</h3>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-top:4px solid #2E7D32;border-radius:8px;padding:14px;">
                <div style="font-size:24px;text-align:center;">💵</div>
                <div style="font-weight:800;color:#0F2847;font-size:13px;text-align:center;margin:6px 0;">현금 부족 해결</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">사망 즉시 거액의 보험금이 상속인에게 지급되어 <strong>상속세 일시납 가능</strong></div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-top:4px solid #2E7D32;border-radius:8px;padding:14px;">
                <div style="font-size:24px;text-align:center;">🏭</div>
                <div style="font-weight:800;color:#0F2847;font-size:13px;text-align:center;margin:6px 0;">사업 유지</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">사업용 자산·부동산을 <strong>매각하지 않고 사업 계속</strong> 가능. 가업상속공제 사후관리 의무도 충족</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-top:4px solid #2E7D32;border-radius:8px;padding:14px;">
                <div style="font-size:24px;text-align:center;">📊</div>
                <div style="font-weight:800;color:#0F2847;font-size:13px;text-align:center;margin:6px 0;">금융재산 공제</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">상속세 신고 시 <strong>최대 2억원 공제</strong> (순금융재산의 20%)</div>
            </div>
        </div>

        <!-- 계약 구조 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 종신보험 계약 구조 - 절세 효과 극대화</h3>
        <table class="data-table financial-table compact">
            <thead>
                <tr>
                    <th style="width:90px;">유형</th>
                    <th>계약자 / 피보험자 / 수익자</th>
                    <th style="width:160px;">상속세 처리</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background:#E8F5E9;">
                    <td><strong>✅ 권장</strong></td>
                    <td>
                        <strong>계약자: 자녀 (상속인)</strong><br>
                        피보험자: 사장님 (피상속인)<br>
                        수익자: 자녀
                    </td>
                    <td style="color:#2E7D32;font-weight:700;">상속세 대상 아님<br><span style="font-size:11px;">(자녀 본인의 재산)</span></td>
                </tr>
                <tr>
                    <td><strong>△ 일반</strong></td>
                    <td>
                        계약자: 사장님<br>
                        피보험자: 사장님<br>
                        수익자: 자녀
                    </td>
                    <td style="color:#E65100;">상속세 대상<br><span style="font-size:11px;">(보험금 = 상속재산)</span></td>
                </tr>
                <tr style="background:#FFEBEE;">
                    <td><strong>❌ 비권장</strong></td>
                    <td>
                        계약자: 사장님<br>
                        피보험자: 사장님<br>
                        수익자: 사장님 본인
                    </td>
                    <td style="color:#C62828;font-weight:800;">최대 50% 상속세<br><span style="font-size:11px;">(과세 + 일시납 부담)</span></td>
                </tr>
            </tbody>
        </table>
        
        <div style="background:#FFF8E1;padding:12px 16px;border-radius:8px;margin-top:8px;font-size:12.5px;color:#3A2F1E;line-height:1.6;">
            💡 <strong>핵심 포인트:</strong> 계약자를 <strong>자녀(상속인)</strong>로 설정하면 보험금은 자녀의 고유 재산이 되어 
            <strong>상속세 과세 대상에서 제외</strong>됩니다. 단, 자녀가 보험료를 자기 소득으로 납입할 수 있어야 인정되므로 
            <strong>증여세 신고 + 자녀 명의 통장에서 자동이체</strong>가 필수.
        </div>

        <!-- 시뮬레이션 예시 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 보험금 5억 가정 - 절세 시뮬레이션</h3>
        <table class="data-table financial-table compact">
            <thead><tr><th></th><th class="num">보험금 받기 전</th><th class="num">보험금 받은 후</th></tr></thead>
            <tbody>
                <tr><td><strong>상속세 예상액</strong></td>
                    <td class="num">5억원</td>
                    <td class="num">5억원 (변동없음)</td></tr>
                <tr><td><strong>현금 보유 자금</strong></td>
                    <td class="num" style="color:#C62828;">2천만원 (예금)</td>
                    <td class="num" style="color:#2E7D32;">5억 + α (보험금)</td></tr>
                <tr><td><strong>부동산·사업체 매각 필요</strong></td>
                    <td class="num" style="color:#C62828;">⚠️ 필수 (4.8억 매각)</td>
                    <td class="num" style="color:#2E7D32;">✅ 불필요</td></tr>
                <tr><td><strong>사업 유지 가능 여부</strong></td>
                    <td class="num" style="color:#C62828;">❌ 중단 위험</td>
                    <td class="num" style="color:#2E7D32;">✅ 정상 운영</td></tr>
                <tr style="background:#FFF8E1;"><td><strong>가업상속공제 사후관리</strong></td>
                    <td class="num" style="color:#C62828;">❌ 자산 처분으로 위반</td>
                    <td class="num" style="color:#2E7D32;">✅ 유지 가능</td></tr>
            </tbody>
        </table>

        <!-- 컨설팅 마무리 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-left:5px solid #C9A961;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:#8B6F3E;font-size:13px;margin-bottom:6px;">💡 RSV 컨설턴트가 함께 설계합니다</div>
            <div style="font-size:13px;line-height:1.7;color:#2B2416;">
                <strong>"보험 가입 자체가 목적이 아닙니다."</strong> 
                개인사업자 사장님의 자산 규모·상속인 구성·승계 계획을 종합적으로 분석하여
                <strong>가업상속공제 활용 + 종신보험 재원 마련 + (필요 시) 법인전환까지 통합 설계</strong>합니다.
                상속이라는 한 번뿐인 사건에 사장님의 평생 사업이 무너지지 않도록 사전 준비가 필수입니다.
            </div>
        </div>
    </div>
</div>
"""
