# -*- coding: utf-8 -*-
"""
multi_business_parser.py
개인사업자 종합소득세 신고서에서 사업장별로 재무제표를 분리 추출.

설계 핵심:
  - 한 신고서에 사업장이 여러 개일 수 있다 (대표자 합산 신고).
  - 사업장 식별/재무 숫자는 '결산 재무상태표/손익계산서'의
    "회사명 : 상호 (사업자번호)" 헤더로 끊는 게 가장 정확하다.
    (사업소득명세서 합산표는 세금용이라 사업장↔숫자가 어긋날 수 있음)
  - 매출 0·무실적 사업장도 포함하되 is_inactive=True 로 표시.

pdf_parser.py 안에 이 함수들을 그대로 붙여넣고,
parse_personal_tax_adjustment_pdf 가 끝난 뒤
result["businesses"] = parse_businesses(pdf)  형태로 채우면 된다.
"""
import re

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def _parse_amount(s):
    if not s:
        return None
    s = str(s).strip()
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()').replace(',', '').replace(' ', '')
    if not s or s == '-':
        return None
    try:
        v = int(s) if s.lstrip('-').isdigit() else float(s)
        return -v if neg else v
    except Exception:
        return None


def _clean(line):
    """한글 사이 공백 제거: '매 출 액' → '매출액'"""
    return re.sub(r'(?<=[가-힣])\s+(?=[가-힣])', '', line)


def _amt_after_label(line, label):
    """라벨 뒤 첫 번째 큰 금액(당기) 반환. 결산서 양식(콤마 숫자)용."""
    c = _clean(line)
    idx = c.find(label)
    if idx < 0:
        return None
    nums = re.findall(r'-?\(?[\d,]{4,}\)?', c[idx:])
    return _parse_amount(nums[0]) if nums else None


# ─────────────────────────────────────────────────────────
# 1) 사업장 목록 + 페이지 범위 찾기
# ─────────────────────────────────────────────────────────
_HEADER_RE = re.compile(r'회사명\s*[:：]\s*(.+?)\s*\((\d{3}-\d{2}-\d{5})\)')


def find_business_pages(pdf):
    """
    결산 재무상태표/손익계산서/제조원가명세서 페이지를 사업장별로 묶는다.
    반환: [{상호, 사업자번호, bs_page, is_page, cost_page}, ...]
    """
    businesses = {}  # 사업자번호 -> dict

    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        head = text[:600]
        m = _HEADER_RE.search(head)
        if not m:
            continue
        name, bizno = m.group(1).strip(), m.group(2)
        # 표준양식(콜론)·합계표·목차는 제외하고 결산서 양식만
        if "표준" in head[:120] or "목차" in head[:60]:
            continue

        b = businesses.setdefault(bizno, {
            "상호": name, "사업자번호": bizno,
            "bs_page": None, "is_page": None, "cost_page": None,
        })
        # 페이지 종류 판별 (제목 키워드)
        h2 = _clean(head)
        if "재무상태표" in h2 and b["bs_page"] is None:
            b["bs_page"] = i
        elif "손익계산서" in h2 and b["is_page"] is None:
            b["is_page"] = i
        elif ("제조원가명세서" in h2 or "원가명세서" in h2) and b["cost_page"] is None:
            b["cost_page"] = i

    # 등장 순서 유지
    return list(businesses.values())


# ─────────────────────────────────────────────────────────
# 2) 사업장 1곳 재무 추출
# ─────────────────────────────────────────────────────────
_BS_ITEMS = [
    ("유동자산", "유동자산"), ("비유동자산", "비유동자산"),
    ("자산총계", "자산총계"),
    ("유동부채", "유동부채"), ("비유동부채", "비유동부채"),
    ("부채총계", "부채총계"),
    ("자본금", "자본금"), ("자본총계", "자본총계"),
]
_IS_ITEMS = [
    ("매출액", "매출액"), ("매출원가", "매출원가"),
    ("매출총이익", "매출총이익"),
    ("판매관리비", "판매비와관리비"),
    ("영업이익", "영업이익"),        # 손실이면 '영업손실'로 따로 처리
    ("영업외수익", "영업외수익"), ("영업외비용", "영업외비용"),
    ("당기순이익", "당기순이익"),    # 손실이면 '당기순손실'로 따로 처리
]


def _extract_statement(text, items, loss_pairs):
    """결산서 텍스트에서 항목 추출. loss_pairs: [(이익라벨, 손실라벨, 결과키)]"""
    out = {}
    lines = text.split("\n")
    for key, label in items:
        for ln in lines:
            if label in _clean(ln):
                v = _amt_after_label(ln, label)
                if v is not None:
                    out[key] = v
                    break
    # 손실 라벨 처리 (이익으로 안 잡혔을 때 음수로)
    for profit_key, loss_label, _ in loss_pairs:
        if out.get(profit_key) is None:
            for ln in lines:
                if loss_label in _clean(ln):
                    v = _amt_after_label(ln, loss_label)
                    if v is not None:
                        out[profit_key] = -abs(v)  # 손실 → 음수
                        break
    return out


def parse_one_business(pdf, biz, cy):
    """사업장 1곳의 BS/IS를 결산서 페이지에서 추출."""
    result = {
        "상호": biz["상호"], "사업자번호": biz["사업자번호"],
        "bs": {"years": [cy] if cy else []},
        "isc": {"years": [cy] if cy else []},
        "업종": "", "is_inactive": False,
    }

    # 재무상태표
    if biz.get("bs_page") is not None:
        t = pdf.pages[biz["bs_page"]].extract_text() or ""
        bs = _extract_statement(t, _BS_ITEMS,
                                loss_pairs=[])  # BS엔 손실라벨 없음
        if bs and cy:
            bs.setdefault("자산총계", 0)
            bs["자산"] = bs.get("자산총계", 0)
            bs["부채"] = bs.get("부채총계", 0)
            bs["자본"] = bs.get("자본총계", 0)
            result["bs"][cy] = bs

    # 손익계산서
    if biz.get("is_page") is not None:
        t = pdf.pages[biz["is_page"]].extract_text() or ""
        isc = _extract_statement(
            t, _IS_ITEMS,
            loss_pairs=[("영업이익", "영업손실", "영업이익"),
                        ("당기순이익", "당기순손실", "당기순이익")],
        )
        if isc and cy:
            isc["매출"] = isc.get("매출액", 0)
            isc["판매비와관리비"] = isc.get("판매관리비", 0)
            isc["당기순손익"] = isc.get("당기순이익", 0)
            result["isc"][cy] = isc

    # 무실적 판정: 매출 0 그리고 당기순이익 0
    매출 = (result["isc"].get(cy, {}) or {}).get("매출액", 0) or 0
    순익 = (result["isc"].get(cy, {}) or {}).get("당기순이익", 0) or 0
    if 매출 == 0 and 순익 == 0:
        result["is_inactive"] = True

    return result


# ─────────────────────────────────────────────────────────
# 3) 전체 사업장 파싱 진입점
# ─────────────────────────────────────────────────────────
def parse_businesses(pdf, cy):
    """모든 사업장의 재무를 리스트로 반환."""
    bizs = find_business_pages(pdf)
    return [parse_one_business(pdf, b, cy) for b in bizs]
