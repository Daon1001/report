"""
재무비율 계산 모듈
- 안정성 지표: 부채비율, 유동비율, 차입금의존도
- 수익성 지표: 영업이익률, 매출순이익률, ROE, ROA
- 성장성 지표: 총자산증가율, 매출액증가율, 자기자본증가율
- 활동성 지표: 총자산회전율, 재고자산회전율, 매출채권회전율
"""
from typing import Dict, Any, Optional, List


def safe_div(a, b) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def safe_pct(a, b) -> Optional[float]:
    r = safe_div(a, b)
    return round(r * 100, 2) if r is not None else None


def safe_growth(curr, prev) -> Optional[float]:
    if curr is None or prev is None or prev == 0:
        return None
    return round((curr - prev) / abs(prev) * 100, 2)


def _gv(data, key, year):
    """BS/IS 데이터 양방향 접근 + 키 별칭 (html_template._get_fin_value와 동일 로직)"""
    if not isinstance(data, dict):
        return None
    aliases = {
        "판관비": ["판매비와관리비", "판매관리비"],
        "판매비와관리비": ["판매관리비", "판관비"],
        "판매관리비": ["판매비와관리비", "판관비"],
        "매출": ["매출액"],
        "매출액": ["매출"],
        "당기순이익": ["당기순손익"],
        "자산": ["자산총계"],
        "자산총계": ["자산"],
        "부채": ["부채총계"],
        "부채총계": ["부채"],
        "자본": ["자본총계"],
        "자본총계": ["자본"],
    }
    keys_to_try = [key] + aliases.get(key, [])
    for k in keys_to_try:
        # 형태 1: data[k][year]
        val1 = data.get(k)
        if isinstance(val1, dict):
            v = val1.get(year)
            if v is not None and not isinstance(v, dict):
                return v
        # 형태 2: data[year][k]
        val2 = data.get(year)
        if isinstance(val2, dict):
            v = val2.get(k)
            if v is not None:
                return v
    return None


def calculate_ratios(bs: Dict, isc: Dict) -> Dict[str, Any]:
    """재무비율 계산 - 양방향 데이터 접근 지원"""
    years = bs.get("years", [])
    ratios = {"years": years}
    
    for year in years:
        yr = year
        # BS 항목
        asset = _gv(bs, "자산", yr)
        curr_asset = _gv(bs, "유동자산", yr)
        non_curr_asset = _gv(bs, "비유동자산", yr)
        liability = _gv(bs, "부채", yr)
        curr_liability = _gv(bs, "유동부채", yr)
        equity = _gv(bs, "자본", yr)
        capital = _gv(bs, "자본금", yr)
        inventory = _gv(bs, "재고자산", yr)
        receivable = _gv(bs, "매출채권", yr)
        payable = _gv(bs, "매입채무", yr)
        
        # IS 항목
        revenue = _gv(isc, "매출액", yr)
        cogs = _gv(isc, "매출원가", yr)
        gross_profit = _gv(isc, "매출총이익", yr)
        sga = _gv(isc, "판관비", yr)
        op_income = _gv(isc, "영업이익", yr)
        net_income = _gv(isc, "당기순이익", yr)
        
        # ── 안정성 지표 ──
        ratios.setdefault("부채비율", {})[yr] = safe_pct(liability, equity)
        ratios.setdefault("유동비율", {})[yr] = safe_pct(curr_asset, curr_liability)
        ratios.setdefault("자기자본비율", {})[yr] = safe_pct(equity, asset)
        ratios.setdefault("차입금의존도", {})[yr] = 0  # 차입금 별도 없으면 0
        
        # ── 수익성 지표 ──
        ratios.setdefault("매출총이익률", {})[yr] = safe_pct(gross_profit, revenue)
        ratios.setdefault("영업이익률", {})[yr] = safe_pct(op_income, revenue)
        ratios.setdefault("매출순이익률", {})[yr] = safe_pct(net_income, revenue)
        ratios.setdefault("ROE", {})[yr] = safe_pct(net_income, equity) if equity and equity > 0 else None
        ratios.setdefault("ROA", {})[yr] = safe_pct(net_income, asset)
        
        # ── 활동성 지표 ──
        ratios.setdefault("총자산회전율", {})[yr] = round(safe_div(revenue, asset), 2) if safe_div(revenue, asset) else None
        ratios.setdefault("재고자산회전율", {})[yr] = round(safe_div(revenue, inventory), 2) if safe_div(revenue, inventory) else None
        ratios.setdefault("매출채권회전율", {})[yr] = round(safe_div(revenue, receivable), 2) if safe_div(revenue, receivable) else None
        ratios.setdefault("매입채무회전율", {})[yr] = round(safe_div(cogs, payable), 2) if safe_div(cogs, payable) else None
    
    # ── 성장성 지표 (전년대비) ──
    for i in range(1, len(years)):
        yr = years[i]
        prev_yr = years[i - 1]
        
        ratios.setdefault("총자산증가율", {})[yr] = safe_growth(
            _gv(bs, "자산", yr), _gv(bs, "자산", prev_yr))
        ratios.setdefault("매출액증가율", {})[yr] = safe_growth(
            _gv(isc, "매출액", yr), _gv(isc, "매출액", prev_yr))
        ratios.setdefault("자기자본증가율", {})[yr] = safe_growth(
            _gv(bs, "자본", yr), _gv(bs, "자본", prev_yr))
        ratios.setdefault("영업이익증가율", {})[yr] = safe_growth(
            _gv(isc, "영업이익", yr), _gv(isc, "영업이익", prev_yr))
        ratios.setdefault("순이익증가율", {})[yr] = safe_growth(
            _gv(isc, "당기순이익", yr), _gv(isc, "당기순이익", prev_yr))
    
    # 첫 해 성장성은 None
    if years:
        first = years[0]
        for key in ["총자산증가율", "매출액증가율", "자기자본증가율", "영업이익증가율", "순이익증가율"]:
            ratios.setdefault(key, {})[first] = None
    
    return ratios


def evaluate_ratio(name: str, value: Optional[float]) -> str:
    """재무비율 평가 (우수/양호/위험)"""
    if value is None:
        return "-"
    
    criteria = {
        "부채비율": {"우수": (None, 100), "양호": (100, 200), "위험": (200, None)},
        "유동비율": {"우수": (150, None), "양호": (100, 150), "위험": (None, 100)},
        "영업이익률": {"우수": (10, None), "양호": (5, 10), "위험": (None, 5)},
        "매출순이익률": {"우수": (7, None), "양호": (2, 7), "위험": (None, 2)},
        "ROE": {"우수": (15, None), "양호": (5, 15), "위험": (None, 5)},
        "ROA": {"우수": (5, None), "양호": (2, 5), "위험": (None, 2)},
        "총자산증가율": {"우수": (10, None), "양호": (0, 10), "위험": (None, 0)},
        "매출액증가율": {"우수": (10, None), "양호": (0, 10), "위험": (None, 0)},
    }
    
    if name not in criteria:
        return "양호"
    
    for grade, (low, high) in criteria[name].items():
        if low is None and high is not None and value < high:
            return grade
        if low is not None and high is None and value >= low:
            return grade
        if low is not None and high is not None and low <= value < high:
            return grade
    
    return "양호"


def calculate_valuation(bs: Dict, isc: Dict, shares: int = None, par_value: int = None) -> Dict[str, Any]:
    """
    비상장주식 보충적 평가방법에 의한 기업가치 계산
    (상증세법상 비상장주식 평가)
    1주당 가치 = (순자산가치 × 2 + 순손익가치 × 3) / 5
    """
    years = bs.get("years", [])
    if not years:
        return {}
    
    latest_year = years[-1]
    
    # 자본 = 순자산가치
    equity = _gv(bs, "자본", latest_year) or 0
    capital_stock = _gv(bs, "자본금", latest_year) or 0
    
    # 주식수 추정 (자본금 / 액면가)
    if shares is None:
        if par_value and par_value > 0:
            shares = int(capital_stock * 1000 / par_value)  # 천원 단위이므로 ×1000
        else:
            shares = int(capital_stock * 1000 / 5000)  # 기본 액면가 5000원
    
    if shares == 0:
        shares = 1
    
    # 순자산가치 (1주당) = 순자산(자본) / 주식수 (천원→원 변환)
    net_asset_per_share = (equity * 1000) / shares
    
    # 가중평균 순손익 (3개년)
    net_incomes = []
    weights = [1, 2, 3]  # 과거 → 최근 가중치
    for i, year in enumerate(years):
        ni = _gv(isc, "당기순이익", year)
        if ni is not None:
            w = weights[i] if i < len(weights) else 3
            net_incomes.append((ni, w))
    
    if net_incomes:
        weighted_sum = sum(ni * w for ni, w in net_incomes)
        weight_total = sum(w for _, w in net_incomes)
        avg_net_income = weighted_sum / weight_total  # 천원 단위
    else:
        avg_net_income = 0
    
    # 순손익가치 (1주당) = 가중평균순손익 / 순손익환원율(10%) / 주식수
    capitalization_rate = 0.10
    earnings_value_total = avg_net_income / capitalization_rate  # 천원
    earnings_per_share = (earnings_value_total * 1000) / shares  # 원
    
    # 1주당 평가액 = (순자산가치 × 2 + 순손익가치 × 3) / 5
    value_per_share = (net_asset_per_share * 2 + earnings_per_share * 3) / 5
    
    # 기업가치 = 1주당 가치 × 주식수
    total_value = value_per_share * shares
    
    return {
        "순자산가치_1주당": round(net_asset_per_share),
        "가중평균순손익": round(avg_net_income),
        "순손익가치_1주당": round(earnings_per_share),
        "1주당평가액": round(value_per_share),
        "기업가치": round(total_value),
        "주식수": shares,
        "자본금": equity,
        "기준일": latest_year,
    }
