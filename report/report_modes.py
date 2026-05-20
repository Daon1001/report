"""
보고서 모드별 페이지 생성
- 샘플링 모드: 영업용 티저 페이지 (각 챕터 미리보기 + 잠긴 페이지 + CTA)
- 심플 모드: 한 페이지 종합 진단 + 핵심 페이지만
"""


def _logo_header(LOGO_SMALL, section_badge, page_title):
    return f"""
    <div class="page-header">
        <img src="{LOGO_SMALL}" class="header-logo" alt="RSV"/>
        <span class="section-badge">{section_badge}</span>
        <span class="page-title-main">{page_title}</span>
    </div>"""


# ════════════════════════════════════════════════════════════════
# 샘플링 모드 — 워터마크 CSS + 잠긴 페이지
# ════════════════════════════════════════════════════════════════
def sampling_watermark_css() -> str:
    """샘플링 모드 전용 CSS - 대각선 워터마크 + 모서리 SAMPLE 배지"""
    return """
    <style>
        /* 샘플링 모드 워터마크 */
        .content-page::before {
            content: "SAMPLE";
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%) rotate(-30deg);
            font-size: 130px;
            font-weight: 900;
            color: rgba(201, 169, 97, 0.10);
            pointer-events: none;
            z-index: 1;
            letter-spacing: 8px;
            font-family: 'Noto Sans KR', sans-serif;
            white-space: nowrap;
        }
        .content-page > * { position: relative; z-index: 2; }
        
        /* 우측 상단 SAMPLE 배지 */
        .content-page::after {
            content: "📄 SAMPLE · 영업용 미리보기";
            position: absolute;
            top: 16px; right: 16px;
            background: linear-gradient(135deg, #C9A961, #8B6F3E);
            color: white;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 5px 12px;
            border-radius: 14px;
            z-index: 3;
            box-shadow: 0 2px 8px rgba(139, 111, 62, 0.3);
        }
    </style>
    """


def locked_chapter_teaser(chapter_name: str, chapter_icon: str, hidden_pages: int, 
                          highlights: list, LOGO_SMALL: str) -> str:
    """잠긴 챕터 안내 페이지 - 정식 계약 시 제공되는 내용 미리보기"""
    highlight_html = ""
    for h in highlights:
        highlight_html += f"""
        <div style='background:#fff;border:1px solid rgba(201,169,97,0.3);border-radius:8px;padding:11px 16px;margin-bottom:8px;display:flex;gap:10px;align-items:center;'>
            <div style='width:24px;height:24px;background:linear-gradient(135deg,#C9A961,#8B6F3E);color:white;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;flex-shrink:0;'>🔒</div>
            <div style='font-size:13px;color:#3A2F1E;line-height:1.5;'>{h}</div>
        </div>
        """
    
    return f"""
<div class="page content-page" style="background:linear-gradient(135deg,#F4F1EC,#E8E2D5);">
    {_logo_header(LOGO_SMALL, "🔒 정식 계약 시 제공", f"{chapter_icon} {chapter_name}")}
    <div class="page-body" style="padding-top:30px;">
        <!-- 잠금 아이콘 영역 -->
        <div style="text-align:center;margin:30px 0 40px;">
            <div style="display:inline-block;width:90px;height:90px;background:linear-gradient(135deg,#0F2847,#1B3A6B);border-radius:50%;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(15,40,71,0.2);">
                <span style="font-size:42px;">🔐</span>
            </div>
            <h2 style="margin-top:18px;color:#0F2847;font-size:22px;font-weight:900;">
                {chapter_name} <span style="color:#C9A961;font-size:16px;font-weight:700;">+{hidden_pages}페이지</span>
            </h2>
            <p style="color:#666;font-size:13px;margin-top:8px;">
                이 챕터의 상세 분석은 <strong style="color:#0F2847;">정식 계약 후 제공</strong>됩니다
            </p>
        </div>

        <!-- 미리보기 -->
        <div style="background:#fff;border-radius:14px;padding:24px 28px;border:2px dashed rgba(201,169,97,0.5);">
            <div style="font-weight:800;color:#8B6F3E;font-size:14px;margin-bottom:14px;letter-spacing:1px;">
                ✨ 정식 보고서에 포함되는 내용
            </div>
            {highlight_html}
        </div>

        <!-- CTA 영역 -->
        <div style="margin-top:24px;background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;border-radius:12px;padding:18px 24px;text-align:center;">
            <div style="font-size:13px;color:#C9A961;font-weight:700;letter-spacing:1px;margin-bottom:6px;">📞 계약 문의</div>
            <div style="font-size:14px;line-height:1.7;">
                정식 컨설팅 계약 시 <strong style="color:#C9A961;">총 40~50페이지 풀 리포트</strong>가 제공됩니다.<br>
                담당 컨설턴트에게 문의하시면 상세 안내드립니다.
            </div>
        </div>
    </div>
</div>
"""


def sampling_cta_final_page(LOGO_SMALL: str, author_name: str = "", 
                            author_org: str = "", author_phone: str = "") -> str:
    """샘플링 마지막 페이지 - 정식 계약 CTA"""
    contact_html = ""
    if author_name:
        contact_html += f"<div style='font-size:14px;'>👤 <strong>{author_name}</strong></div>"
    if author_org:
        contact_html += f"<div style='font-size:13px;opacity:0.9;'>🏢 {author_org}</div>"
    if author_phone:
        contact_html += f"<div style='font-size:14px;color:#C9A961;font-weight:700;margin-top:4px;'>📞 {author_phone}</div>"
    
    return f"""
<div class="page content-page" style="background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;">
    <div class="page-body" style="text-align:center;padding:60px 40px;">
        <div style="font-size:14px;color:#C9A961;letter-spacing:4px;font-weight:700;margin-bottom:12px;">
            RSV · RICH SECRET VAULT
        </div>
        <h1 style="font-size:34px;font-weight:900;margin-bottom:24px;">
            지금 본 것은 <span style="color:#C9A961;">10%</span>입니다
        </h1>
        <p style="font-size:15px;line-height:1.8;opacity:0.95;max-width:560px;margin:0 auto;">
            정식 컨설팅 계약 시<br>
            <strong style="color:#C9A961;font-size:20px;">총 40~50페이지 풀 리포트</strong>와 함께<br>
            <strong>맞춤형 컨설팅</strong>이 제공됩니다.
        </p>
        
        <!-- 제공 내용 요약 -->
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;max-width:600px;margin:40px auto 0;">
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(201,169,97,0.3);border-radius:10px;padding:14px;">
                <div style="font-size:24px;margin-bottom:4px;">📊</div>
                <div style="font-weight:700;font-size:13px;">기업재무 심층분석</div>
                <div style="font-size:11px;opacity:0.85;margin-top:2px;">재무비율·EW등급·진단</div>
            </div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(201,169,97,0.3);border-radius:10px;padding:14px;">
                <div style="font-size:24px;margin-bottom:4px;">💼</div>
                <div style="font-weight:700;font-size:13px;">세무 심층진단</div>
                <div style="font-size:11px;opacity:0.85;margin-top:2px;">접대비·차량·고용공제</div>
            </div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(201,169,97,0.3);border-radius:10px;padding:14px;">
                <div style="font-size:24px;margin-bottom:4px;">⚖️</div>
                <div style="font-weight:700;font-size:13px;">노무 컨설팅</div>
                <div style="font-size:11px;opacity:0.85;margin-top:2px;">판례 기반·리스크 진단</div>
            </div>
            <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(201,169,97,0.3);border-radius:10px;padding:14px;">
                <div style="font-size:24px;margin-bottom:4px;">💰</div>
                <div style="font-weight:700;font-size:13px;">상속세·승계 플랜</div>
                <div style="font-size:11px;opacity:0.85;margin-top:2px;">맞춤 시뮬레이션</div>
            </div>
        </div>
        
        <!-- 연락처 -->
        {f'''<div style="margin-top:40px;background:rgba(201,169,97,0.15);border:1px solid rgba(201,169,97,0.4);border-radius:12px;padding:20px 28px;display:inline-block;text-align:left;">
            <div style="font-size:12px;color:#C9A961;font-weight:700;letter-spacing:1px;margin-bottom:10px;">📞 담당 컨설턴트</div>
            {contact_html}
        </div>''' if contact_html else ''}
        
        <div style="margin-top:36px;font-size:11px;opacity:0.6;letter-spacing:2px;">
            본 문서는 영업용 샘플로, 정식 계약 시 맞춤형 분석이 제공됩니다
        </div>
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 심플 모드 — 한 페이지 종합 진단 + 핵심 페이지
# ════════════════════════════════════════════════════════════════
def simple_dashboard_page(company: dict, bs: dict, isc: dict, ratios: dict, 
                          credit: dict, tax_deep: dict, is_personal: bool,
                          LOGO_SMALL: str) -> str:
    """심플 모드 - 한 페이지 종합 대시보드"""
    
    company_name = company.get("기업명", "기업")
    years = bs.get("years", [])
    latest = years[-1] if years else None
    
    # 핵심 지표 추출 - 양방향 형태 지원 (bs[year][key] / bs[key][year] 둘 다)
    def _gv(data, key, year):
        """양방향 데이터 접근 헬퍼"""
        if not isinstance(data, dict) or year is None:
            return 0
        # 형태 1: data[year][key]
        v = data.get(year)
        if isinstance(v, dict):
            r = v.get(key)
            if r is not None and not isinstance(r, dict):
                return r
        # 형태 2: data[key][year]
        v = data.get(key)
        if isinstance(v, dict):
            return v.get(year, 0) or 0
        return 0
    
    rev = _gv(isc, "매출액", latest)
    net = _gv(isc, "당기순이익", latest)
    asset = _gv(bs, "자산총계", latest) or _gv(bs, "자산", latest)
    debt = _gv(bs, "부채총계", latest) or _gv(bs, "부채", latest)
    capital = _gv(bs, "자본총계", latest) or _gv(bs, "자본", latest)
    
    # 비율
    debt_ratio = (debt / capital * 100) if capital > 0 else 0
    profit_margin = (net / rev * 100) if rev > 0 else 0
    
    # 신용등급
    credit_grade = credit.get("기업신용등급", "—") if credit else "—"
    ew_grade = credit.get("EW등급", "—") if credit else "—"
    
    # 세무 컨설팅 데이터
    consulting = (tax_deep or {}).get("consulting", {}) or {}
    tax_score = consulting.get("절세진단", {}).get("절세여력_점수")
    emp = consulting.get("고용", {})
    cur_emp = emp.get("당기_상시근로자수", 0) or 0
    inc_emp = emp.get("증가인원", 0) or 0
    
    # 추천 액션 자동 생성
    actions = []
    if debt_ratio > 200:
        actions.append(("⚠️ 부채비율 200% 초과", "재무구조 개선 시급 — 자본 확충 또는 차입 축소 검토"))
    if profit_margin < 3 and rev > 0:
        actions.append(("📉 영업이익률 저조", "원가 구조 분석 + 비과세 수당 활용으로 실효 절감"))
    if tax_score and tax_score < 60:
        actions.append(("💸 절세 활용도 미흡", "통합고용세액공제·중소기업 특별감면 등 미활용 항목 점검"))
    if inc_emp > 0:
        actions.append(("✅ 고용 증가", f"통합고용세액공제 {int(inc_emp * 850)}만원 × 3년 활용 가능"))
    if cur_emp >= 10:
        actions.append(("⚖️ 노무 리스크", "10인 이상 사업장 — 취업규칙·괴롭힘 예방 의무 확인"))
    # 최소 3개 확보
    while len(actions) < 3:
        actions.append(("💡 정밀 진단 필요", "정식 컨설팅으로 맞춤 절세·노무·상속 분석 권장"))
    actions = actions[:5]
    
    actions_html = ""
    for title, desc in actions:
        actions_html += f"""
        <div style='background:#fff;border-left:4px solid #C9A961;border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:8px;'>
            <div style='font-weight:800;color:#0F2847;font-size:13px;'>{title}</div>
            <div style='font-size:12px;color:#555;margin-top:3px;'>{desc}</div>
        </div>
        """
    
    biz_type = "개인사업자" if is_personal else "법인"
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, "⚡ Quick Diagnosis", f"{company_name} 종합 진단")}
    <div class="page-body">
        <div style="background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-left:5px solid #C9A961;padding:12px 18px;border-radius:0 12px 12px 0;margin-bottom:14px;font-size:13px;">
            <strong style="color:#8B6F3E;">⚡ 빠른 진단 리포트</strong> · 사장님의 회사를 핵심 지표만 모아 한눈에 진단합니다. 정식 컨설팅 시 풀버전 50페이지 분석 제공.
        </div>

        <!-- 상단 KPI 4개 -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;">
            <div style="background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;padding:12px;border-radius:10px;">
                <div style="font-size:10px;opacity:0.8;font-weight:600;letter-spacing:0.5px;">매출액 (당기)</div>
                <div style="font-size:18px;font-weight:900;margin-top:2px;">{rev/100_000_000:.1f}<span style="font-size:11px;">억</span></div>
            </div>
            <div style="background:linear-gradient(135deg,#1B3A6B,#2A5298);color:white;padding:12px;border-radius:10px;">
                <div style="font-size:10px;opacity:0.8;font-weight:600;letter-spacing:0.5px;">당기순이익</div>
                <div style="font-size:18px;font-weight:900;margin-top:2px;color:{'#C9A961' if net > 0 else '#FFC107'};">{net/100_000_000:.2f}<span style="font-size:11px;">억</span></div>
            </div>
            <div style="background:linear-gradient(135deg,#C9A961,#8B6F3E);color:white;padding:12px;border-radius:10px;">
                <div style="font-size:10px;opacity:0.85;font-weight:600;letter-spacing:0.5px;">자산총계</div>
                <div style="font-size:18px;font-weight:900;margin-top:2px;">{asset/100_000_000:.1f}<span style="font-size:11px;">억</span></div>
            </div>
            <div style="background:linear-gradient(135deg,#8B6F3E,#6D5530);color:white;padding:12px;border-radius:10px;">
                <div style="font-size:10px;opacity:0.85;font-weight:600;letter-spacing:0.5px;">자본총계</div>
                <div style="font-size:18px;font-weight:900;margin-top:2px;">{capital/100_000_000:.1f}<span style="font-size:11px;">억</span></div>
            </div>
        </div>

        <!-- 핵심 비율·신용·노무·세무 -->
        <h3 class="subsection-title" style="margin-top:0;">◆ 핵심 진단 지표</h3>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">부채비율</div>
                <div style="font-size:20px;font-weight:900;color:{'#C62828' if debt_ratio > 200 else '#E65100' if debt_ratio > 100 else '#2E7D32'};margin-top:3px;">{debt_ratio:.0f}%</div>
                <div style="font-size:10px;color:#888;margin-top:1px;">{'위험' if debt_ratio > 200 else '주의' if debt_ratio > 100 else '안정'}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">순이익률</div>
                <div style="font-size:20px;font-weight:900;color:{'#2E7D32' if profit_margin >= 10 else '#E65100' if profit_margin >= 3 else '#C62828'};margin-top:3px;">{profit_margin:.1f}%</div>
                <div style="font-size:10px;color:#888;margin-top:1px;">{'우수' if profit_margin >= 10 else '보통' if profit_margin >= 3 else '낮음'}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">신용등급</div>
                <div style="font-size:18px;font-weight:900;color:#0F2847;margin-top:3px;">{credit_grade}</div>
                <div style="font-size:10px;color:#888;margin-top:1px;">EW: {ew_grade}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">절세 활용도</div>
                <div style="font-size:20px;font-weight:900;color:{'#2E7D32' if (tax_score or 0) >= 70 else '#E65100' if (tax_score or 0) >= 50 else '#C62828'};margin-top:3px;">{tax_score if tax_score else '—'}<span style="font-size:11px;">{f'/100' if tax_score else ''}</span></div>
                <div style="font-size:10px;color:#888;margin-top:1px;">{('A' if (tax_score or 0) >= 80 else 'B' if (tax_score or 0) >= 65 else 'C' if (tax_score or 0) >= 50 else 'D') if tax_score else '평가 미진행'}</div>
            </div>
        </div>

        <!-- 시급 액션 -->
        <h3 class="subsection-title">◆ 사장님께 시급한 액션 {len(actions)}가지</h3>
        {actions_html}

        <!-- 결론 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;border-radius:12px;padding:14px 20px;">
            <div style="font-weight:800;font-size:13px;margin-bottom:6px;color:#C9A961;">🎯 한 줄 진단</div>
            <div style="font-size:13px;line-height:1.6;">
                {biz_type} <strong>{company_name}</strong>는 매출 {rev/100_000_000:.1f}억 / 자산 {asset/100_000_000:.1f}억 규모로,
                현재 <strong style="color:#C9A961;">{('재무 안정' if debt_ratio < 100 else '재무 관리 필요')} · {('절세 우수' if (tax_score or 0) >= 70 else '절세 개선 여지')}</strong> 상태입니다.
                정식 컨설팅에서 위 {len(actions)}가지 액션의 <strong>구체적 실행 방안</strong>을 제공해드립니다.
            </div>
        </div>
    </div>
</div>
"""


def simple_action_summary_page(company: dict, tax_deep: dict, is_personal: bool, 
                                LOGO_SMALL: str, author_name: str = "", 
                                author_phone: str = "") -> str:
    """심플 모드 마지막 - 추천 액션 + 다음 미팅 안내"""
    
    biz_type = "개인사업자" if is_personal else "법인"
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, "⚡ Quick Diagnosis", "다음 단계 — 정식 컨설팅 안내")}
    <div class="page-body">
        <div style="background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-left:5px solid #C9A961;padding:14px 18px;border-radius:0 12px 12px 0;margin-bottom:18px;">
            <div style="font-weight:800;color:#8B6F3E;font-size:14px;margin-bottom:4px;">📌 빠른 진단 결과 요약</div>
            <div style="font-size:13px;color:#3A2F1E;">
                오늘 보여드린 진단은 <strong>핵심만 추려낸 빠른 진단</strong>입니다. 
                정밀한 컨설팅을 원하시면 정식 컨설팅을 통해 풀버전 분석을 받아보세요.
            </div>
        </div>

        <!-- 정식 컨설팅에서 제공되는 내용 -->
        <h3 class="subsection-title">◆ 정식 컨설팅에서 제공되는 내용</h3>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;">
                <div style="font-weight:800;color:#0F2847;font-size:13px;margin-bottom:4px;">📊 기업재무 심층분석 (7페이지)</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">3개년 BS/IS·재무비율 22종·산업 평균 비교·EW등급 진단</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;">
                <div style="font-weight:800;color:#0F2847;font-size:13px;margin-bottom:4px;">💼 세무 심층진단 (7페이지)</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">접대비·차량·감가상각·고용공제·절세 마스터리 등급</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;">
                <div style="font-weight:800;color:#0F2847;font-size:13px;margin-bottom:4px;">🏦 신용등급·재무진단 (3페이지)</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">신용등급 변동·등급별 가이드·수익성·현금흐름</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;">
                <div style="font-weight:800;color:#0F2847;font-size:13px;margin-bottom:4px;">⚖️ 노무 컨설팅 (16페이지)</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">판례 기반 11페이지 + 자가진단표 + 비과세 활용</div>
            </div>
            {'<div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;"><div style="font-weight:800;color:#0F2847;font-size:13px;margin-bottom:4px;">💰 상속세 플랜 (4페이지)</div><div style="font-size:12px;color:#666;line-height:1.5;">사업용 자산 기반 시뮬·가업상속공제·종신보험 재원</div></div>' if is_personal else '<div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;"><div style="font-weight:800;color:#0F2847;font-size:13px;margin-bottom:4px;">📈 기업가치평가 (4페이지)</div><div style="font-size:12px;color:#666;line-height:1.5;">비상장주식 가치·상속세 시뮬·승계 전략</div></div>'}
            <div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #0F2847;border-radius:0 10px 10px 0;padding:12px 16px;">
                <div style="font-weight:800;color:#0F2847;font-size:13px;margin-bottom:4px;">💼 고용지원금 (5페이지)</div>
                <div style="font-size:12px;color:#666;line-height:1.5;">신청 가능한 지원금 + 신청 절차 상세</div>
            </div>
        </div>

        <!-- 풀버전 분량 강조 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border:2px solid #C9A961;border-radius:12px;padding:16px 22px;text-align:center;">
            <div style="font-size:11px;color:#8B6F3E;letter-spacing:2px;font-weight:700;">정식 컨설팅 풀버전</div>
            <div style="font-size:36px;font-weight:900;color:#8B6F3E;margin:6px 0;line-height:1;">
                {'42페이지+' if is_personal else '50페이지+'}
            </div>
            <div style="font-size:13px;color:#3A2F1E;">
                {biz_type} 맞춤 · 7개 핵심 챕터 풀 분석
            </div>
        </div>

        <!-- 연락처 -->
        {f'''<div style="margin-top:16px;background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;border-radius:12px;padding:16px 22px;text-align:center;">
            <div style="font-size:11px;color:#C9A961;letter-spacing:2px;font-weight:700;margin-bottom:6px;">📞 정식 컨설팅 문의</div>
            <div style="font-size:16px;font-weight:800;">{author_name}</div>
            {f'<div style="font-size:18px;color:#C9A961;font-weight:900;margin-top:4px;">{author_phone}</div>' if author_phone else ''}
        </div>''' if author_name else ''}
    </div>
</div>
"""
