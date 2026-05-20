"""
컨설팅 심층 분석 페이지 (HTML) - 세무조정계산서 기반
1. 접대비(기업업무추진비) 분석
2. 업무용 승용차 분석
3. 감가상각 포트폴리오
4. 고용현황 & 통합고용세액공제
5. 절세진단 마스터리
"""


def _fmt(v, suffix="원", placeholder="—"):
    """숫자 포맷팅"""
    if v is None or v == 0:
        return placeholder
    if isinstance(v, float):
        return f"{v:,.1f}{suffix}"
    return f"{v:,}{suffix}"


def _logo_header(LOGO_SMALL, section_badge, page_title):
    return f"""
    <div class="page-header">
        <img src="{LOGO_SMALL}" class="header-logo" alt="RSV"/>
        <span class="section-badge">{section_badge}</span>
        <span class="page-title-main">{page_title}</span>
    </div>"""


# ════════════════════════════════════════════════════════════════
# 1. 접대비(기업업무추진비) 분석 페이지
# ════════════════════════════════════════════════════════════════
def consulting_entertainment_page(consulting: dict, company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    ent = consulting.get("접대비", {}) or {}
    section = "💼 종합소득세 심층진단" if is_personal else "💼 세무 심층진단"
    
    used = ent.get("계정금액") or 0
    limit = ent.get("한도액") or 0
    over = ent.get("한도초과") or 0
    rate = ent.get("한도사용률") or 0
    card_ratio = ent.get("신용카드비율") or 0
    card_amt = ent.get("신용카드사용액") or 0
    
    # 사용률에 따른 색상
    if rate >= 90:
        rate_color, rate_bg, rate_label = "#C62828", "#FFEBEE", "⚠️ 한도 임박"
    elif rate >= 70:
        rate_color, rate_bg, rate_label = "#E65100", "#FFF3E0", "⚡ 주의 구간"
    else:
        rate_color, rate_bg, rate_label = "#2E7D32", "#E8F5E9", "✅ 여유"
    
    # 컨설팅 한 줄 메시지
    if rate >= 90:
        msg = f"한도까지 거의 다 쓰셨네요. 내년에는 매출이 늘지 않으면 <strong>한도 초과로 세금 추가</strong>될 수 있어요. 운영 방식 점검이 필요합니다."
    elif rate >= 70:
        msg = f"여유는 있지만 추세를 보면 내년에 한도에 닿을 수 있어요. <strong>접대비 분류 기준</strong>을 한번 정리해보면 좋겠습니다."
    elif used > 0:
        msg = f"한도 대비 여유가 충분하네요. 다만 <strong>신용카드/현금영수증 비율 99%</strong>는 매우 모범적이지만, 영수증 미비 발견 시 손금 인정 안 되는 점 유의하세요."
    else:
        msg = "접대비 사용액이 매우 적거나 없습니다. 영업 활동 비용을 누락하고 계실 가능성이 있어요."
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, section, "기업업무추진비(접대비) 한도 점검")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            "<strong>접대비는 가장 자주 한도 초과로 세금 더 내는 항목</strong>입니다."
            세무조정계산서 기준으로 사장님의 접대비가 한도 안에 있는지, 신용카드 비율은 충분한지 진단합니다.
        </div>

        <!-- 핵심 지표 카드 -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:8px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;letter-spacing:0.5px;">사용액 (당기)</div>
                <div style="font-size:18px;font-weight:800;color:#0F2847;margin-top:4px;">{_fmt(used)}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;letter-spacing:0.5px;">법정 한도</div>
                <div style="font-size:18px;font-weight:800;color:#0F2847;margin-top:4px;">{_fmt(limit)}</div>
            </div>
            <div style="background:{rate_bg};border:1px solid {rate_color};border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#666;font-weight:600;letter-spacing:0.5px;">한도 사용률</div>
                <div style="font-size:24px;font-weight:900;color:{rate_color};margin-top:2px;">{rate:.1f}%</div>
                <div style="font-size:10px;color:{rate_color};font-weight:700;">{rate_label}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;letter-spacing:0.5px;">신용카드 비율</div>
                <div style="font-size:18px;font-weight:800;color:{'#2E7D32' if card_ratio >= 95 else '#E65100'};margin-top:4px;">{card_ratio:.1f}%</div>
            </div>
        </div>

        <!-- 시각화 바 -->
        <div style="margin-top:20px;background:#F4F1EC;border-radius:12px;padding:18px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#666;margin-bottom:6px;">
                <span>사용액 vs 한도</span>
                <span>{_fmt(used)} / {_fmt(limit)}</span>
            </div>
            <div style="position:relative;height:32px;background:#E5E7EB;border-radius:8px;overflow:hidden;">
                <div style="position:absolute;left:0;top:0;height:100%;width:{min(rate, 100):.0f}%;background:linear-gradient(90deg,{rate_color},{rate_color}99);"></div>
                <div style="position:absolute;left:50%;top:0;height:100%;width:1px;background:rgba(0,0,0,0.3);"></div>
                <div style="position:absolute;left:50%;top:-18px;font-size:10px;color:#888;transform:translateX(-50%);">50%</div>
            </div>
        </div>

        <!-- 세부 내역 -->
        <h3 class="subsection-title" style="margin-top:12px;">◆ 사용 내역 상세</h3>
        <table class="data-table financial-table compact">
            <thead><tr><th>구분</th><th class="num">금액</th><th>비고</th></tr></thead>
            <tbody>
                <tr><td>① 신용카드·현금영수증 사용</td>
                    <td class="num">{_fmt(card_amt)}</td>
                    <td style="text-align:left;font-size:12px;">{card_ratio:.1f}% — {'우수한 적격증빙 비율' if card_ratio >= 95 else '적격증빙 비율 개선 필요'}</td></tr>
                <tr><td>② 3만원 이하 현금 사용</td>
                    <td class="num">{_fmt(ent.get('현금사용액_3만원이하'))}</td>
                    <td style="text-align:left;font-size:12px;">소액 영수증 (한도 내 손금 인정)</td></tr>
                <tr class="total-row"><td><strong>총 접대비 사용액</strong></td>
                    <td class="num"><strong>{_fmt(used)}</strong></td>
                    <td style="text-align:left;font-size:12px;"><strong>한도 {_fmt(limit)} 대비 {rate:.1f}%</strong></td></tr>
                {f'<tr style="background:rgba(198,40,40,0.08);"><td style="color:#C62828;"><strong>⚠️ 한도 초과 (손금불산입)</strong></td><td class="num" style="color:#C62828;"><strong>+{over:,}원</strong></td><td style="text-align:left;font-size:12px;color:#C62828;">한도 초과분은 세무상 비용 인정 안됨 → 세금 추가</td></tr>' if over > 0 else ''}
            </tbody>
        </table>

        <!-- 컨설팅 메시지 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-left:5px solid #C9A961;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:#8B6F3E;font-size:13px;margin-bottom:6px;">💡 컨설턴트의 시각</div>
            <div style="font-size:13px;line-height:1.6;color:#2B2416;">{msg}</div>
        </div>

        <!-- 한도 계산 공식 -->
        <div style="margin-top:14px;background:#fff;border:1px dashed #B5A78A;border-radius:8px;padding:11px 16px;font-size:12px;color:#3A2F1E;">
            <strong>📐 접대비 한도 계산 공식</strong> &nbsp;|&nbsp; 
            기본한도 (중소기업 3,600만원 / 일반 1,200만원) + 매출액 × 적용률 (100억 이하 0.3%, 그 이상 누진)
            {'· <strong>중소기업이면 한도가 3배</strong>이니 중소기업 인증 유지가 중요합니다.' if is_personal else ''}
        </div>
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 2. 업무용 승용차 분석 페이지
# ════════════════════════════════════════════════════════════════
def consulting_vehicle_page(consulting: dict, company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    car = consulting.get("업무용차량", {}) or {}
    cars = car.get("차량목록", []) or []
    section = "💼 종합소득세 심층진단" if is_personal else "💼 세무 심층진단"
    
    total = car.get("총비용") or sum(c.get("관련비용합계", 0) or 0 for c in cars)
    insurance_ok = car.get("임직원전용보험")
    over = car.get("필요경비불산입") or 0
    
    # 차량 라인 HTML
    car_rows = ""
    for i, c in enumerate(cars):
        ins_label = "✅ 가입" if c.get("보험가입") else "❌ 미가입"
        ins_color = "#2E7D32" if c.get("보험가입") else "#C62828"
        biz_ratio = c.get("업무비율", 0)
        car_rows += f"""
            <tr>
                <td><strong>{c.get('차량번호', '-')}</strong></td>
                <td>{c.get('종류', '-')}</td>
                <td>{c.get('임차여부', '-')}</td>
                <td style="color:{ins_color};font-weight:600;">{ins_label}</td>
                <td>{biz_ratio:.1f}%</td>
                <td class="num">{_fmt(c.get('관련비용합계'))}</td>
            </tr>
        """
    if not car_rows:
        car_rows = '<tr><td colspan="6" style="text-align:center;color:#999;padding:20px;">업무용 승용차 데이터 없음 (개인 차량 또는 미보유)</td></tr>'
    
    # 진단 메시지
    if not cars:
        msg = "업무용 승용차 사용 내역이 신고되지 않았습니다. 사장님 명의로 차량 보유 시 사업 비용 처리 가능한지 검토해보세요."
        msg_color = "#666"
    elif insurance_ok is False:
        msg = "<strong>일부 차량이 임직원전용 보험에 가입되어 있지 않습니다.</strong> 가입 안 된 차량은 비용의 50%만 인정됩니다. 즉시 보험 가입 검토 필요!"
        msg_color = "#C62828"
    elif over > 0:
        msg = f"한도(연 1,500만원)를 초과한 비용 <strong>{over:,}원</strong>이 손금불산입 처리되었습니다. 차량 1대당 한도이므로 고가 차량 1대보다 중저가 2대가 절세에 유리합니다."
        msg_color = "#E65100"
    else:
        msg = "임직원전용 보험 가입, 운행기록 작성, 한도 내 사용 — <strong>업무용 차량 세무 관리 우수</strong>합니다. 8년이 지나면 감가상각 비용이 사라지므로 신규 차량 도입 시점 검토하세요."
        msg_color = "#2E7D32"
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, section, "업무용 승용차 비용 진단")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            "<strong>업무용 차량은 세무조사 표적</strong>입니다. 임직원전용보험 미가입 시 비용의 50%만 인정,
            한도 초과 시 손금불산입. 사장님 차량 상태를 한눈에 점검합니다."
        </div>

        <!-- 핵심 지표 -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:8px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">보유 차량 수</div>
                <div style="font-size:22px;font-weight:800;color:#0F2847;margin-top:4px;">{len(cars)}대</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">총 차량 비용</div>
                <div style="font-size:16px;font-weight:800;color:#0F2847;margin-top:4px;">{_fmt(total)}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">전용보험 가입</div>
                <div style="font-size:16px;font-weight:800;color:{'#2E7D32' if insurance_ok else '#C62828' if insurance_ok is False else '#888'};margin-top:4px;">{'✅ 전체 가입' if insurance_ok else '⚠️ 미가입' if insurance_ok is False else '—'}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">한도 초과 손금불산입</div>
                <div style="font-size:16px;font-weight:800;color:{'#C62828' if over > 0 else '#2E7D32'};margin-top:4px;">{_fmt(over) if over else '✅ 없음'}</div>
            </div>
        </div>

        <!-- 차량별 상세 -->
        <h3 class="subsection-title" style="margin-top:16px;">◆ 차량별 사용 현황</h3>
        <table class="data-table financial-table compact">
            <thead><tr><th>차량번호</th><th>차종</th><th>구분</th><th>전용보험</th><th>업무비율</th><th class="num">관련비용</th></tr></thead>
            <tbody>{car_rows}</tbody>
        </table>

        <!-- 컨설팅 메시지 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-left:5px solid {msg_color};padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:{msg_color};font-size:13px;margin-bottom:6px;">💡 컨설턴트의 시각</div>
            <div style="font-size:13px;line-height:1.6;color:#2B2416;">{msg}</div>
        </div>

        <!-- 4대 핵심 체크 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 업무용 차량 4대 핵심 체크</h3>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;font-size:12.5px;">
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:10px 14px;border-radius:0 8px 8px 0;">
                <strong>1️⃣ 임직원전용 자동차보험</strong><br>
                <span style="color:#666;">미가입 시 차량비용 50%만 인정. 가족 등 등재 시 무효</span>
            </div>
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:10px 14px;border-radius:0 8px 8px 0;">
                <strong>2️⃣ 운행기록부 작성</strong><br>
                <span style="color:#666;">미작성 시 차량비용 한도 1,500만원으로 일괄 적용</span>
            </div>
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:10px 14px;border-radius:0 8px 8px 0;">
                <strong>3️⃣ 차량 1대당 한도</strong><br>
                <span style="color:#666;">연간 차량비 1,500만 / 감가상각 800만 (정액)</span>
            </div>
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:10px 14px;border-radius:0 8px 8px 0;">
                <strong>4️⃣ 5년 감가상각 (정액법)</strong><br>
                <span style="color:#666;">취득가 4,000만 차량이면 연 800만씩 5년간 비용</span>
            </div>
        </div>
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 3. 감가상각 포트폴리오 페이지
# ════════════════════════════════════════════════════════════════
def consulting_depreciation_page(consulting: dict, company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    dep = consulting.get("감가상각", {}) or {}
    section = "💼 종합소득세 심층진단" if is_personal else "💼 세무 심층진단"
    
    total = dep.get("유형자산_기말") or 0
    accum = dep.get("감가상각누계") or 0
    remain = dep.get("미상각잔액") or 0
    annual = dep.get("당기상각비") or 0
    
    bldg = dep.get("건축물") or 0
    machine = dep.get("기계장치") or 0
    other = dep.get("기타자산") or 0
    
    # 향후 절세 효과 (잔존가치 / 연간상각비)
    years_left = (remain / annual) if annual and remain else 0
    
    # 자산 구성 비율
    if total:
        bldg_pct = bldg / total * 100
        machine_pct = machine / total * 100
        other_pct = other / total * 100
    else:
        bldg_pct = machine_pct = other_pct = 0
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, section, "감가상각 포트폴리오 & 향후 절세 효과")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            "<strong>감가상각비는 현금 안 나가는 비용</strong>입니다. 매년 자동으로 비용이 잡혀 세금을 줄여주는,
            사장님이 가지고 있는 <strong>'세금 깎개'</strong>를 한번에 확인해드립니다."
        </div>

        <!-- 핵심 카드 -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:8px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">유형자산 취득가</div>
                <div style="font-size:16px;font-weight:800;color:#0F2847;margin-top:4px;">{_fmt(total)}</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">감가상각 누계</div>
                <div style="font-size:16px;font-weight:800;color:#888;margin-top:4px;">{_fmt(accum)}</div>
            </div>
            <div style="background:#E8F5E9;border:1px solid #2E7D32;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#1B5E20;font-weight:700;">미상각 잔액 (앞으로 비용)</div>
                <div style="font-size:18px;font-weight:900;color:#2E7D32;margin-top:4px;">{_fmt(remain)}</div>
            </div>
            <div style="background:#FFF8E1;border:1px solid #C9A961;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#8B6F3E;font-weight:700;">당기 감가상각비</div>
                <div style="font-size:18px;font-weight:900;color:#C9A961;margin-top:4px;">{_fmt(annual)}</div>
            </div>
        </div>

        <!-- 자산 구성 -->
        <h3 class="subsection-title" style="margin-top:16px;">◆ 자산 구성 (취득가 기준)</h3>
        <div style="margin-top:6px;">
            <div style="display:flex;height:36px;border-radius:8px;overflow:hidden;border:1px solid #E5E7EB;">
                <div style="width:{bldg_pct:.1f}%;background:linear-gradient(180deg,#1B3A6B,#0F2847);display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:700;" title="건축물">{f'건축물 {bldg_pct:.0f}%' if bldg_pct > 8 else ''}</div>
                <div style="width:{machine_pct:.1f}%;background:linear-gradient(180deg,#C9A961,#8B6F3E);display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:700;" title="기계장치">{f'기계장치 {machine_pct:.0f}%' if machine_pct > 8 else ''}</div>
                <div style="width:{other_pct:.1f}%;background:linear-gradient(180deg,#6D8FB8,#4A6B8F);display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:700;" title="기타">{f'기타 {other_pct:.0f}%' if other_pct > 8 else ''}</div>
            </div>
        </div>
        
        <table class="data-table financial-table compact" style="margin-top:10px;">
            <thead><tr><th>자산구분</th><th class="num">취득가액</th><th>비율</th><th>비고</th></tr></thead>
            <tbody>
                <tr><td><strong>🏢 건축물</strong></td>
                    <td class="num">{_fmt(bldg)}</td><td>{bldg_pct:.1f}%</td>
                    <td style="text-align:left;font-size:12px;">정액법, 보통 40년</td></tr>
                <tr><td><strong>⚙️ 기계장치</strong></td>
                    <td class="num">{_fmt(machine)}</td><td>{machine_pct:.1f}%</td>
                    <td style="text-align:left;font-size:12px;">정률법 가능, 5~8년</td></tr>
                <tr><td><strong>🛠️ 기타자산</strong></td>
                    <td class="num">{_fmt(other)}</td><td>{other_pct:.1f}%</td>
                    <td style="text-align:left;font-size:12px;">차량/비품/공구</td></tr>
            </tbody>
        </table>

        <!-- 향후 절세 시뮬레이션 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 향후 절세 효과 시뮬레이션</h3>
        <div style="background:linear-gradient(135deg,#E8F5E9,#C8E6C9);border-left:5px solid #2E7D32;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="display:flex;justify-content:space-around;text-align:center;flex-wrap:wrap;gap:14px;">
                <div>
                    <div style="font-size:11px;color:#1B5E20;font-weight:600;">미상각 잔액</div>
                    <div style="font-size:20px;font-weight:900;color:#2E7D32;margin-top:2px;">{_fmt(remain)}</div>
                </div>
                <div style="font-size:24px;color:#666;align-self:center;">÷</div>
                <div>
                    <div style="font-size:11px;color:#1B5E20;font-weight:600;">연간 상각비</div>
                    <div style="font-size:20px;font-weight:900;color:#2E7D32;margin-top:2px;">{_fmt(annual)}</div>
                </div>
                <div style="font-size:24px;color:#666;align-self:center;">=</div>
                <div>
                    <div style="font-size:11px;color:#1B5E20;font-weight:600;">예상 잔여 년수</div>
                    <div style="font-size:20px;font-weight:900;color:#0F2847;margin-top:2px;">약 {years_left:.1f}년</div>
                </div>
            </div>
            <div style="margin-top:14px;font-size:13px;color:#2B2416;line-height:1.6;">
                <strong>💡 의미:</strong> 앞으로 약 <strong>{years_left:.1f}년 동안 매년 {_fmt(annual)}</strong>의 감가상각비가 자동으로 비용 처리되어
                {('종합소득세' if is_personal else '법인세')}를 줄여줍니다. 
                {f'연간 절세 예상액: 약 <strong style="color:#2E7D32;">{int(annual * (0.24 if is_personal else 0.09)):,}원</strong> 이상' if annual else ''}
            </div>
        </div>

        <!-- 컨설팅 메시지 -->
        <div style="margin-top:14px;background:#FFF8E1;border-left:5px solid #C9A961;padding:12px 16px;border-radius:0 10px 10px 0;font-size:13px;line-height:1.6;color:#2B2416;">
            <strong style="color:#8B6F3E;">📌 컨설턴트의 조언:</strong> 
            기계장치 비중이 높을수록 단기 비용 처리 효과가 큽니다. 
            <strong>설비 노후화로 신규 투자 계획이 있다면 통합투자세액공제(중소기업 12%)</strong>와 함께 활용하세요.
            건축물은 보통 40년 상각이라 절세 효과가 천천히 나타나지만 안정적입니다.
        </div>
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 4. 고용현황 & 통합고용세액공제 페이지
# ════════════════════════════════════════════════════════════════
def consulting_employment_page(consulting: dict, company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    emp = consulting.get("고용", {}) or {}
    section = "💼 종합소득세 심층진단" if is_personal else "💼 세무 심층진단"
    
    cur = emp.get("당기_상시근로자수") or 0
    prev = emp.get("전기_상시근로자수") or 0
    inc = emp.get("증가인원") or 0
    
    youth_cur = emp.get("청년근로자_당기") or 0
    youth_prev = emp.get("청년근로자_전기") or 0
    youth_inc = emp.get("청년증가") or 0
    
    applied = emp.get("통합고용공제_신청")
    credit_amt = emp.get("통합고용공제_금액") or 0
    
    total_emp = emp.get("사원수") or 0
    exec_n = emp.get("임원수") or 0
    resign = emp.get("퇴사자수") or 0
    
    # 증가 방향
    if inc > 0:
        inc_color = "#2E7D32"
        inc_label = f"📈 {inc:+.1f}명 증가"
        inc_msg = "고용 증가! 통합고용세액공제 대상입니다."
    elif inc < 0:
        inc_color = "#C62828"
        inc_label = f"📉 {inc:+.1f}명 감소"
        inc_msg = "고용 감소 — 기존 통합고용공제 추징 가능성 점검 필요"
    else:
        inc_color = "#666"
        inc_label = "→ 변동 없음"
        inc_msg = "고용 인원 동일 유지"
    
    # 잠재 공제액 추정 (수도권 기준 청년 1,450만/장년 850만 × 3년)
    if inc > 0:
        potential = int(inc * 850 * 10000)  # 단순 추정
        potential_msg = f"단순 추정: 일반근로자 {inc:.1f}명 증가 → 연 약 <strong>{potential:,}원</strong> × 3년"
    else:
        potential_msg = ""
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, section, "고용 현황 & 통합고용세액공제 진단")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            "<strong>고용 1명 증가 = 연 700~1,450만원 세액공제 × 3년</strong>입니다.
            사장님 회사의 고용 현황과 통합고용세액공제 활용 상태를 점검합니다."
        </div>

        <!-- 핵심 카드 -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:8px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">전기 상시근로자</div>
                <div style="font-size:22px;font-weight:800;color:#0F2847;margin-top:4px;">{prev:.2f}<span style="font-size:13px;">명</span></div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">당기 상시근로자</div>
                <div style="font-size:22px;font-weight:800;color:#0F2847;margin-top:4px;">{cur:.2f}<span style="font-size:13px;">명</span></div>
            </div>
            <div style="background:rgba({'46,125,50' if inc > 0 else '198,40,40' if inc < 0 else '136,136,136'},0.1);border:1px solid {inc_color};border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:{inc_color};font-weight:700;">고용 변화</div>
                <div style="font-size:16px;font-weight:900;color:{inc_color};margin-top:4px;">{inc_label}</div>
            </div>
            <div style="background:{'#E8F5E9' if applied else '#FFEBEE'};border:1px solid {'#2E7D32' if applied else '#C62828'};border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:11px;color:#666;font-weight:600;">통합고용세액공제</div>
                <div style="font-size:14px;font-weight:800;color:{'#2E7D32' if applied else '#C62828'};margin-top:4px;">
                    {'✅ 신청 완료' if applied else '❌ 미신청'}<br>
                    <span style="font-size:13px;">{_fmt(credit_amt) if credit_amt else ''}</span>
                </div>
            </div>
        </div>

        <!-- 청년/장년 구성 -->
        <h3 class="subsection-title" style="margin-top:16px;">◆ 상시근로자 구성 (청년 vs 장년)</h3>
        <table class="data-table financial-table compact">
            <thead><tr><th>구분</th><th>전기</th><th>당기</th><th>증감</th><th>공제 단가 (수도권)</th></tr></thead>
            <tbody>
                <tr>
                    <td><strong>🌱 청년·장애인·60세이상</strong></td>
                    <td>{youth_prev:.2f}명</td>
                    <td>{youth_cur:.2f}명</td>
                    <td style="color:{'#2E7D32' if youth_inc > 0 else '#C62828' if youth_inc < 0 else '#666'};font-weight:700;">{youth_inc:+.2f}명</td>
                    <td>연 1,450만 × 3년 = 4,350만</td>
                </tr>
                <tr>
                    <td><strong>🏢 일반(장년)</strong></td>
                    <td>{prev - youth_prev:.2f}명</td>
                    <td>{cur - youth_cur:.2f}명</td>
                    <td style="color:{'#2E7D32' if (inc - youth_inc) > 0 else '#C62828' if (inc - youth_inc) < 0 else '#666'};font-weight:700;">{(inc - youth_inc):+.2f}명</td>
                    <td>연 850만 × 3년 = 2,550만</td>
                </tr>
                <tr class="total-row">
                    <td><strong>합계 (상시근로자)</strong></td>
                    <td><strong>{prev:.2f}명</strong></td>
                    <td><strong>{cur:.2f}명</strong></td>
                    <td style="color:{inc_color};font-weight:900;">{inc:+.2f}명</td>
                    <td><strong>{inc_msg}</strong></td>
                </tr>
            </tbody>
        </table>

        <!-- 사원수/임원/퇴사 -->
        {f'''<h3 class="subsection-title" style="margin-top:14px;">◆ 인사 관리 현황 (참고)</h3>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">총 등재 사원</div>
                <div style="font-size:20px;font-weight:800;color:#0F2847;">{total_emp}명</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">대표/임원</div>
                <div style="font-size:20px;font-weight:800;color:#0F2847;">{exec_n}명</div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:11px;color:#888;font-weight:600;">당기 퇴사자</div>
                <div style="font-size:20px;font-weight:800;color:{('#E65100' if resign > 3 else '#0F2847')};">{resign}명</div>
            </div>
        </div>''' if total_emp else ''}

        <!-- 컨설팅 메시지 + 잠재 공제 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#FFF8E1,#F9F1DC);border-left:5px solid #C9A961;padding:14px 18px;border-radius:0 12px 12px 0;">
            <div style="font-weight:800;color:#8B6F3E;font-size:13px;margin-bottom:6px;">💡 컨설턴트의 시각</div>
            <div style="font-size:13px;line-height:1.6;color:#2B2416;">
                {('이미 통합고용세액공제를 활용 중이시고 ' + ('고용도 증가하셔서 ' if inc > 0 else '') + '훌륭한 인사 운영을 하고 계십니다.' if applied else '<strong style="color:#C62828;">⚠️ 통합고용세액공제 미신청.</strong> 고용 1명 증가만으로도 연 850만 × 3년 = 2,550만원 세금 절약 가능합니다.')}
                {('<br><br>📊 ' + potential_msg) if potential_msg else ''}
            </div>
        </div>

        <!-- 통합고용세액공제 조건 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 통합고용세액공제 조건 (2024 기준)</h3>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;font-size:12.5px;">
            <div style="background:#fff;border-left:3px solid #2E7D32;padding:10px 14px;border-radius:0 8px 8px 0;">
                <strong>✅ 신청 조건</strong><br>
                <span style="color:#666;">전년 대비 상시근로자 증가 (소수점 포함) · 3년 동안 매년 별도 신청</span>
            </div>
            <div style="background:#fff;border-left:3px solid #C62828;padding:10px 14px;border-radius:0 8px 8px 0;">
                <strong>⚠️ 추징 조건</strong><br>
                <span style="color:#666;">감소 시 받은 공제 토해내야 함 — 고용 유지가 중요!</span>
            </div>
        </div>
    </div>
</div>
"""


# ════════════════════════════════════════════════════════════════
# 5. 절세진단 마스터리 페이지
# ════════════════════════════════════════════════════════════════
def consulting_tax_mastery_page(consulting: dict, tax_deep: dict, company: dict, is_personal: bool, LOGO_SMALL: str) -> str:
    diag = consulting.get("절세진단", {}) or {}
    section = "💼 종합소득세 심층진단" if is_personal else "💼 세무 심층진단"
    
    score = diag.get("절세여력_점수") or 50
    activated = diag.get("활용중인_공제감면", []) or []
    recommended = diag.get("추천_공제감면", []) or []
    warnings = diag.get("주의사항", []) or []
    
    # 점수 등급
    if score >= 80:
        grade, grade_color, grade_msg = "A", "#2E7D32", "탁월한 절세 관리"
    elif score >= 65:
        grade, grade_color, grade_msg = "B", "#7CB342", "양호한 절세 활용"
    elif score >= 50:
        grade, grade_color, grade_msg = "C", "#FB8C00", "보통 — 개선 여지 있음"
    elif score >= 35:
        grade, grade_color, grade_msg = "D", "#E65100", "절세 활용 미흡"
    else:
        grade, grade_color, grade_msg = "E", "#C62828", "세무 리스크 높음 — 즉시 점검"
    
    # 세액감면/공제 데이터
    gam = consulting.get("세액감면", {}) or {}
    gong = consulting.get("세액공제", {}) or {}
    total_gam = gam.get("총감면액") or 0
    total_gong = gong.get("총공제액") or 0
    total_saved = total_gam + total_gong
    
    # 항목 리스트
    gam_html = ""
    for it in (gam.get("감면항목") or []):
        gam_html += f'<li>{it["항목"]} · <strong>{_fmt(it["금액"])}</strong></li>'
    for it in (gong.get("공제항목") or []):
        gam_html += f'<li>{it["항목"]} · <strong>{_fmt(it["금액"])}</strong></li>'
    if not gam_html:
        gam_html = '<li style="color:#999;">활용 중인 감면·공제 항목 미확인</li>'
    
    # 추천 항목 (개인/법인별 차별)
    if is_personal:
        rec_items = [
            ("🌱 중소기업 특별세액감면", "사업소득세의 20% 감면 (이미 적용 중일 가능성)"),
            ("👥 통합고용세액공제", "고용 1명 증가 = 연 850만~1,450만 × 3년"),
            ("📊 성실신고확인비용 세액공제", "성실신고 대상자, 확인비용의 60% 세액공제"),
            ("🏛️ 기장세액공제", "복식부기 기장, 산출세액 20% 한도"),
            ("📡 전자신고 세액공제", "본인 전자신고 시 연 1~2만원"),
        ]
    else:
        rec_items = [
            ("👥 통합고용세액공제", "고용 1명 증가 = 연 850만~1,450만 × 3년"),
            ("🔬 연구·인력개발비 세액공제", "R&D 비용의 25%(중소) 세액공제"),
            ("⚙️ 통합투자세액공제", "사업용 자산 투자액의 12%(중소) 세액공제"),
            ("🌱 중소기업특별세액감면", "수도권 외 5~30%, 수도권 내 10~30% 감면"),
            ("📡 전자신고 세액공제", "법인세 전자신고 시 2~10만원"),
        ]
    rec_html = ""
    for icon_name, desc in rec_items:
        is_active = any(icon_name.split(" ", 1)[1] in a or a in icon_name for a in activated)
        check = "✅" if is_active else "○"
        color = "#2E7D32" if is_active else "#999"
        rec_html += f"""
            <tr>
                <td style="color:{color};font-weight:700;width:30px;text-align:center;">{check}</td>
                <td><strong>{icon_name}</strong></td>
                <td style="font-size:12px;color:#666;">{desc}</td>
            </tr>
        """
    
    # 주의사항
    warn_html = ""
    if warnings:
        for w in warnings:
            warn_html += f'<li style="margin-bottom:6px;color:#C62828;">⚠️ {w}</li>'
    else:
        warn_html = '<li style="color:#2E7D32;">✅ 발견된 세무 리스크 없음</li>'
    
    return f"""
<div class="page content-page">
    {_logo_header(LOGO_SMALL, section, "절세 마스터리 종합 진단")}
    <div class="page-body">
        <div class="info-box" style="margin-bottom:8px;padding:11px 16px;font-size:13px;">
            "사장님이 <strong>지금 어떤 절세 도구를 쓰고 있는지, 어떤 걸 놓치고 있는지</strong>를 한 페이지에 압축했습니다.
            이게 컨설팅의 핵심입니다."
        </div>

        <!-- 절세 점수 -->
        <div style="display:grid;grid-template-columns:200px 1fr;gap:20px;margin-top:8px;align-items:center;">
            <div style="background:linear-gradient(135deg,{grade_color},{grade_color}99);border-radius:14px;padding:18px;text-align:center;color:white;">
                <div style="font-size:11px;letter-spacing:2px;font-weight:600;">절세 활용도</div>
                <div style="font-size:60px;font-weight:900;line-height:1;margin:6px 0;">{grade}</div>
                <div style="font-size:24px;font-weight:800;">{score}<span style="font-size:14px;">/100</span></div>
                <div style="font-size:11px;margin-top:6px;opacity:0.9;">{grade_msg}</div>
            </div>
            <div>
                <div style="background:#E8F5E9;padding:12px 16px;border-radius:10px;border-left:4px solid #2E7D32;">
                    <div style="font-size:11px;color:#1B5E20;font-weight:700;margin-bottom:4px;">💰 당기 절감한 세금 (감면+공제)</div>
                    <div style="font-size:24px;font-weight:900;color:#2E7D32;">{_fmt(total_saved)}</div>
                </div>
                <div style="background:#FFF8E1;padding:12px 16px;border-radius:10px;border-left:4px solid #C9A961;margin-top:8px;">
                    <div style="font-size:11px;color:#8B6F3E;font-weight:700;margin-bottom:4px;">📋 활용 중인 절세 항목</div>
                    <ul style="margin:0;padding-left:20px;font-size:12.5px;color:#2B2416;line-height:1.6;">{gam_html}</ul>
                </div>
            </div>
        </div>

        <!-- 활용 가능한 공제·감면 체크리스트 -->
        <h3 class="subsection-title" style="margin-top:16px;">◆ {("개인사업자" if is_personal else "법인") } 핵심 절세 항목 체크리스트</h3>
        <table class="data-table financial-table compact" style="font-size:12.5px;">
            <thead><tr><th style="width:30px;">상태</th><th style="width:230px;">항목</th><th>혜택</th></tr></thead>
            <tbody>{rec_html}</tbody>
        </table>

        <!-- 주의사항 -->
        <h3 class="subsection-title" style="margin-top:14px;">◆ 발견된 세무 리스크</h3>
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:12px 18px;">
            <ul style="margin:0;padding-left:20px;font-size:13px;line-height:1.8;">{warn_html}</ul>
        </div>

        <!-- 컨설팅 결론 -->
        <div style="margin-top:14px;background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;border-radius:12px;padding:16px 20px;">
            <div style="font-weight:800;font-size:14px;margin-bottom:8px;color:#C9A961;">🎯 컨설팅 결론</div>
            <div style="font-size:13px;line-height:1.7;">
                사장님은 절세 활용도 <strong style="color:#C9A961;">{grade}등급 ({score}점)</strong>으로 
                <strong>{grade_msg}</strong> 상태입니다. 
                {("당기 절감한 세금 " + _fmt(total_saved) + "은 다음 사업연도에도 유지·확대할 수 있는 항목이며, 미활용 항목 중 1~2개만 추가로 챙겨도 추가 절세 가능합니다." if total_saved else "아직 활용 중인 절세 항목이 적습니다. 위 체크리스트를 기반으로 1순위 통합고용세액공제부터 검토하세요.")}
                {("발견된 리스크 " + str(len(warnings)) + "건은 다음 신고 전에 반드시 점검 필요합니다." if warnings else "")}
            </div>
        </div>
    </div>
</div>
"""
