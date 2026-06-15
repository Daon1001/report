"""
숨은 가지급금 / 가수금 탐지 모듈 (forensic)
─────────────────────────────────────────────────────────────
parse_tax_adjustment_pdf / parse_personal_tax_adjustment_pdf 의 결과 dict를
입력으로 받아, 위장 계정에 묻힌 가지급금·가수금 의심 신호를 룰 기반으로 탐지한다.

핵심: 세무조정계산서가 없어도 BS/IS만으로 대부분 작동한다.
      (세무조정 교차검증 룰 I만 deep 데이터가 있을 때 동작)

전제: 파서가 아래 계정들을 추출하도록 확장되어 있어야 효과가 난다.
      (현재 pdf_parser.py는 롤업 위주라, parser 확장과 함께 써야 함)
      자산: 단기대여금·장기대여금·미수금·미수수익·선급금·선급비용·
            가지급금·주임종단기채권·임차보증금·매출채권·재고자산·현금및현금성자산
      부채: 가수금·미지급금·선수금·예수금·단기차입금
      손익: 매출액·매출원가·이자수익·이자비용·이익잉여금
"""
from typing import Dict, Any, List, Optional
import re

# ── 튜닝 임계치 (업종별로 조정하세요) ────────────────────────────
TH = {
    "susp_asset_sales_warn": 0.15,   # 의심자산/매출 > 15% → 주의
    "susp_asset_sales_high": 0.30,   # > 30% → 경고
    "ar_sales_warn":         0.25,   # 매출채권/매출 > 25% → 회수지연/가공 의심
    "inv_cogs_warn":         0.40,   # 재고/매출원가 > 40% → 재고 과다/부풀리기
    "susp_jump":             0.50,   # 의심자산 전년比 +50% → 급증
    "susp_liab_sales_warn":  0.10,   # 가수금성 부채/매출 > 10%
    "loan_min":              5_000_000,   # 대여금 의심 최소 금액(원)
    "cash_re_ratio_low":     0.10,   # 현금/이익잉여금 < 10% → 자금 묶임 의심
}

ASSET_HIDE = ["단기대여금", "장기대여금", "대여금", "미수금", "미수수익",
              "선급금", "선급비용", "가지급금", "주임종단기채권", "임차보증금"]
LOAN_LIKE  = ["단기대여금", "장기대여금", "대여금"]          # 무이자 판정 대상
LIAB_HIDE  = ["가수금", "미지급금", "선수금", "예수금"]

SEV_WEIGHT = {"경고": 3, "주의": 2, "정보": 1}


# ── 양식 정규화: corporate / personal → {account: {year: val}} ──
def _normalize(section: Dict[str, Any]) -> Dict[str, Dict[Any, float]]:
    if not isinstance(section, dict):
        return {}
    years = section.get("years", []) or []
    out: Dict[str, Dict[Any, float]] = {}
    for k, v in section.items():
        if k in ("years", "year_labels"):
            continue
        if not isinstance(v, dict):
            continue
        if (k in years) or isinstance(k, int):
            # personal 양식: k=연도, v={계정:금액}
            for acct, val in v.items():
                if isinstance(val, (int, float)):
                    out.setdefault(acct, {})[k] = float(val)
        else:
            # corporate 양식: k=계정, v={연도:금액}
            for yr, val in v.items():
                if isinstance(val, (int, float)):
                    out.setdefault(k, {})[yr] = float(val)
    return out


def _years_desc(norm: Dict[str, Dict[Any, float]]) -> List[Any]:
    ys = set()
    for yv in norm.values():
        ys.update(yv.keys())

    def _k(y):
        m = re.search(r"(20\d{2})", str(y))
        return int(m.group(1)) if m else 0
    return sorted(ys, key=_k, reverse=True)


def _val(norm, account, year) -> float:
    return float(norm.get(account, {}).get(year, 0) or 0)


def _sum(norm, accounts, year) -> float:
    return sum(_val(norm, a, year) for a in accounts)


def _won(v: Optional[float]) -> str:
    if v is None:
        return "-"
    v = abs(float(v))
    if v >= 1e8:
        return f"{v/1e8:.1f}억"
    if v >= 1e4:
        return f"{v/1e4:,.0f}만"
    return f"{v:,.0f}원"


# ── 메인 ────────────────────────────────────────────────────────
def detect(result: Dict[str, Any],
           deep: Optional[Dict[str, Any]] = None,
           industry: str = "") -> Dict[str, Any]:
    """
    result: parse_(personal_)tax_adjustment_pdf 반환 dict
    deep:   extract_(personal_)tax_deep_analysis 반환 dict (선택, 세무조정 교차검증용)
    industry: '제조'·'도소매'·'부동산임대' 등 힌트 (선택)
    반환: {"score", "level", "findings": [...], "summary"}
    """
    bs = _normalize(result.get("bs", {}))
    isc = _normalize(result.get("isc", {}))
    years = _years_desc(bs) or _years_desc(isc)
    findings: List[Dict[str, Any]] = []

    if not years:
        return {"score": 0, "level": "데이터부족", "findings": [],
                "summary": "재무상태표 연도를 인식하지 못했습니다. 파서 추출 결과를 확인하세요."}

    cy = years[0]                      # 당기
    py = years[1] if len(years) > 1 else None   # 전기
    sales = _val(isc, "매출액", cy)
    cogs = _val(isc, "매출원가", cy)

    def add(code, title, sev, basis, talk):
        findings.append({"code": code, "title": title, "severity": sev,
                         "근거": basis, "멘트": talk})

    # ── 룰 A: 의심자산 합계 비율 ──
    susp = _sum(bs, ASSET_HIDE, cy)
    if susp > 0:
        contrib = {a: _val(bs, a, cy) for a in ASSET_HIDE if _val(bs, a, cy) > 0}
        detail = ", ".join(f"{a} {_won(v)}" for a, v in
                           sorted(contrib.items(), key=lambda x: -x[1]))
        if sales > 0:
            r = susp / sales
            if r >= TH["susp_asset_sales_high"]:
                add("SUSP_ASSET", "의심자산 과다(가지급금 위장 강한 의심)", "경고",
                    f"의심자산 {_won(susp)} / 매출 {_won(sales)} = {r*100:.0f}% (구성: {detail})",
                    f"대여금·미수금·선급금 등에 {_won(susp)}이 묶여 있습니다. "
                    f"이게 실제 영업자산이 아니라 대표님 개인 유출이면 사실상 가지급금입니다.")
            elif r >= TH["susp_asset_sales_warn"]:
                add("SUSP_ASSET", "의심자산 주의", "주의",
                    f"의심자산 {_won(susp)} / 매출 {_won(sales)} = {r*100:.0f}% (구성: {detail})",
                    f"{detail} 항목을 점검하세요. 회수·정산 예정이 불분명하면 가지급금성입니다.")
        else:
            add("SUSP_ASSET", "의심자산 존재(매출 미인식)", "정보",
                f"의심자산 {_won(susp)} (구성: {detail})",
                "매출 데이터가 없어 비율 판정은 보류. 구성 계정만 확인 바랍니다.")

    # ── 룰 B: 무이자 대여 (사실상 가지급금) ──
    loans = _sum(bs, LOAN_LIKE, cy)
    if loans >= TH["loan_min"]:
        interest_income = _val(isc, "이자수익", cy)
        proxy = interest_income if interest_income > 0 else _val(isc, "영업외수익", cy)
        if interest_income == 0 and _val(isc, "이자수익", cy) == 0:
            note = "(이자수익 미추출 → 영업외수익으로 추정)" if proxy else ""
            if proxy < loans * 0.005:   # 대여금의 0.5%에도 못 미치는 이자
                add("NO_INTEREST_LOAN", "무이자성 대여 의심", "경고",
                    f"대여금 {_won(loans)} 대비 이자수익 {_won(proxy)} 거의 없음 {note}",
                    f"대여금 {_won(loans)}에 이자수익이 사실상 없습니다. "
                    f"특수관계자 무상대여면 인정이자 익금산입 + 사실상 가지급금입니다.")

    # ── 룰 C: 매출채권 회수 이상 ──
    ar = _val(bs, "매출채권", cy)
    if ar > 0 and sales > 0:
        r = ar / sales
        if r >= TH["ar_sales_warn"]:
            add("AR_HIGH", "매출채권 과다(가공·미회수 의심)", "주의",
                f"매출채권 {_won(ar)} / 매출 {_won(sales)} = {r*100:.0f}%",
                "매출 대비 채권이 비정상적으로 큽니다. 장기 미회수·가공매출이면 "
                "그 안에 빠져나간 현금(가지급금)이 숨어 있을 수 있습니다.")

    # ── 룰 D: 재고 과다 (현금유출 은폐) ──
    inv = _val(bs, "재고자산", cy)
    if inv > 0 and cogs > 0 and "임대" not in industry:
        r = inv / cogs
        if r >= TH["inv_cogs_warn"]:
            add("INV_HIGH", "재고 과다(재고 부풀리기 의심)", "주의",
                f"재고자산 {_won(inv)} / 매출원가 {_won(cogs)} = {r*100:.0f}%",
                "재고가 매출원가 대비 과다합니다. 실재고와 차이가 크면 "
                "유출 현금을 재고로 위장했을 가능성이 있습니다. 실사 권유.")

    # ── 룰 E: 가수금성 부채 ──
    susp_liab = _sum(bs, LIAB_HIDE, cy)
    gasugum = _val(bs, "가수금", cy)
    if susp_liab > 0 and sales > 0:
        r = susp_liab / sales
        liab_detail = ", ".join(f"{a} {_won(_val(bs,a,cy))}" for a in LIAB_HIDE if _val(bs, a, cy) > 0)
        if gasugum > 0 or r >= TH["susp_liab_sales_warn"]:
            sev = "주의" if gasugum > 0 else "정보"
            add("SUSP_LIAB", "가수금성 부채 존재", sev,
                f"의심부채 {_won(susp_liab)} / 매출 {_won(sales)} = {r*100:.0f}% ({liab_detail})",
                "대표가 회사에 넣은 자금(가수금)이 있을 가능성. 출처 소명·정리(자본전입 등) "
                "필요. 현금매출 누락분이 가수금으로 들어온 경우라면 세무조사 리스크.")

    # ── 룰 F: 가지급금 + 가수금 동시 존재 (상계 미실행) ──
    if susp > 0 and (gasugum > 0 or susp_liab > 0):
        add("OFFSET_MISS", "가지급금·가수금 동시 존재(상계 미실행)", "주의",
            f"의심자산 {_won(susp)} ↔ 의심부채 {_won(susp_liab)}",
            "자산 측 가지급금성과 부채 측 가수금성이 동시에 있습니다. "
            "상계 처리하면 양쪽을 한 번에 줄일 수 있는데 미실행 상태로 보입니다.")

    # ── 룰 G: 의심자산 추세 급증 ──
    if py is not None:
        susp_prev = _sum(bs, ASSET_HIDE, py)
        if susp_prev > 0 and susp > susp_prev * (1 + TH["susp_jump"]):
            add("SUSP_TREND", "의심자산 급증", "주의",
                f"의심자산 {_won(susp_prev)} → {_won(susp)} (전년比 +{(susp/susp_prev-1)*100:.0f}%)",
                "의심자산이 전년 대비 급증했습니다. 회전 없이 누적되는 패턴이면 "
                "지속적 현금 유출(가지급금 누적) 신호입니다.")

    # ── 룰 H: 현금흐름 괴리 (proxy) ──
    re_ = _val(bs, "이익잉여금", cy)
    cash = _val(bs, "현금및현금성자산", cy)
    if re_ > 0 and susp > 0 and (cash / re_) < TH["cash_re_ratio_low"]:
        add("CASH_GAP", "이익 누적 대비 현금 빈약(자금 묶임)", "정보",
            f"이익잉여금 {_won(re_)} 누적 / 현금 {_won(cash)} ({cash/re_*100:.0f}%)",
            "이익은 쌓였는데 현금이 없습니다. 번 돈이 어딘가 자산에 묶여 있다는 뜻 — "
            "그 묶인 자산이 위 의심자산이라면 유출 정황이 더 뚜렷해집니다.")

    # ── 룰 I: 세무조정 교차검증 (deep 데이터 있을 때) ──
    if deep:
        incs = deep.get("세무조정_익금산입", []) or []
        has_imputed = any(("인정이자" in (x.get("과목", "")) or "가지급금" in (x.get("과목", "")))
                          for x in incs)
        if loans > 0 or _val(bs, "가지급금", cy) > 0:
            if has_imputed:
                add("TAX_CROSS", "인정이자 신고 확인됨", "정보",
                    "세무조정 익금산입에 인정이자/가지급금 항목 존재",
                    "인정이자는 처리되어 있습니다. 다만 BS 의심자산 전액이 반영됐는지 금액 대사 필요.")
            else:
                add("TAX_CROSS", "인정이자 누락 의심", "경고",
                    f"대여금/가지급금 {_won(max(loans,_val(bs,'가지급금',cy)))} 존재하나 익금산입 인정이자 없음",
                    "가지급금성 자산이 있는데 세무조정에 인정이자가 안 잡혔습니다. "
                    "누락이면 익금산입 + 대표 상여 처분 리스크입니다.")

    # ── 점수/등급 ──
    score = sum(SEV_WEIGHT.get(f["severity"], 0) for f in findings)
    level = "위험" if score >= 8 else "주의" if score >= 4 else "정상" if score == 0 else "관찰"
    n_warn = sum(1 for f in findings if f["severity"] == "경고")
    summary = (f"{cy} 기준 의심신호 {len(findings)}건(경고 {n_warn}건), 위험점수 {score} → '{level}'. "
               + ("우선 점검: " + "; ".join(f["title"] for f in findings if f["severity"] == "경고")
                  if n_warn else "치명적 경고는 없으나 관찰 항목을 확인하세요." if findings else
                  "BS/IS 기준 두드러진 은닉 신호는 발견되지 않았습니다."))

    return {"score": score, "level": level, "findings": findings, "summary": summary}
