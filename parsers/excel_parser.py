"""
Excel 파일 파서: ETFI112E1 시리즈 엑셀에서 재무데이터 추출
- ETFI112E1.xlsx: 재무상태표 (Balance Sheet)
- ETFI112E1__1_.xlsx: 손익계산서 (Income Statement)
- ETFI112E1__5_.xlsx: 제조원가명세서 (Manufacturing Cost Statement)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def _clean_value(val) -> Optional[float]:
    """NaN/None을 None으로, 숫자는 float으로 변환"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _parse_sheet(filepath: str) -> Dict[str, Dict[str, Optional[float]]]:
    """엑셀 시트를 파싱하여 {계정명: {연도: 값}} 딕셔너리로 변환"""
    df = pd.read_excel(filepath, sheet_name='Sheet1', header=None)
    
    # 연도 헤더 추출 (row 1)
    years = []
    for col_idx in range(2, df.shape[1]):
        val = df.iloc[1, col_idx]
        if pd.notna(val):
            years.append(str(val).strip())
        else:
            years.append(f"col_{col_idx}")
    
    result = {}
    for row_idx in range(2, df.shape[0]):
        account_name = df.iloc[row_idx, 1]
        if pd.isna(account_name):
            continue
        account_name = str(account_name).strip()
        
        values = {}
        for i, year in enumerate(years):
            col_idx = i + 2
            if col_idx < df.shape[1]:
                values[year] = _clean_value(df.iloc[row_idx, col_idx])
        
        result[account_name] = values
    
    return result


def parse_balance_sheet(filepath: str) -> Dict[str, Any]:
    """재무상태표 파싱"""
    raw = _parse_sheet(filepath)
    years = sorted(set(y for v in raw.values() for y in v.keys() if y.startswith('20')))
    
    def get(name: str, year: str) -> Optional[float]:
        return raw.get(name, {}).get(year)
    
    data = {"years": years, "raw": raw}
    
    # 주요 항목 구조화
    for year in years:
        yr_key = year
        data.setdefault("자산", {})[yr_key] = get("자산(*)", year)
        data.setdefault("유동자산", {})[yr_key] = get("유동자산(*)", year)
        data.setdefault("당좌자산", {})[yr_key] = get("당좌자산(*)", year)
        data.setdefault("현금및현금성자산", {})[yr_key] = get("현금 및 현금성자산(*)", year)
        data.setdefault("매출채권", {})[yr_key] = get("매출채권(*)", year)
        data.setdefault("재고자산", {})[yr_key] = get("재고자산(*)", year)
        data.setdefault("비유동자산", {})[yr_key] = get("비유동자산(*)", year)
        data.setdefault("유형자산", {})[yr_key] = get("유형자산(*)", year)
        data.setdefault("부채", {})[yr_key] = get("부채(*)", year)
        data.setdefault("유동부채", {})[yr_key] = get("유동부채(*)", year)
        data.setdefault("매입채무", {})[yr_key] = get("매입채무(*)", year)
        data.setdefault("비유동부채", {})[yr_key] = get("비유동부채(*)", year) 
        data.setdefault("자본", {})[yr_key] = get("자본(*)", year)
        data.setdefault("자본금", {})[yr_key] = get("자본금(*)", year)
        data.setdefault("이익잉여금", {})[yr_key] = get("이익잉여금(*)", year)
        data.setdefault("미처분이익잉여금", {})[yr_key] = get("미처분이익잉여금(결손금)", year)
        data.setdefault("당기순이익_bs", {})[yr_key] = get("*당기순이익", year)
    
    return data


def parse_income_statement(filepath: str) -> Dict[str, Any]:
    """손익계산서 파싱"""
    raw = _parse_sheet(filepath)
    years = sorted(set(y for v in raw.values() for y in v.keys() if y.startswith('20')))
    
    def get(name: str, year: str) -> Optional[float]:
        return raw.get(name, {}).get(year)
    
    data = {"years": years, "raw": raw}
    
    for year in years:
        yr_key = year
        data.setdefault("매출액", {})[yr_key] = get("매출액(*)", year)
        data.setdefault("매출원가", {})[yr_key] = get("매출원가(*)", year)
        data.setdefault("매출총이익", {})[yr_key] = get("매출총이익(손실)", year)
        data.setdefault("판관비", {})[yr_key] = get("판매비와관리비(*)", year)
        data.setdefault("영업이익", {})[yr_key] = get("영업이익(손실)", year)
        data.setdefault("영업외수익", {})[yr_key] = get("영업외수익(*)", year)
        data.setdefault("영업외비용", {})[yr_key] = get("영업외비용(*)", year)
        data.setdefault("법인세차감전순이익", {})[yr_key] = get("법인세비용차감전순손익", year)
        data.setdefault("법인세비용", {})[yr_key] = get("법인세비용", year)
        data.setdefault("당기순이익", {})[yr_key] = get("당기순이익(순손실)", year)
        
        # 판관비 세부
        data.setdefault("급여", {})[yr_key] = get("급여(*)", year)
        data.setdefault("퇴직급여", {})[yr_key] = get("퇴직급여", year)
        data.setdefault("복리후생비", {})[yr_key] = get("복리후생비", year)
        data.setdefault("지급수수료", {})[yr_key] = get("지급수수료", year)
        data.setdefault("감가상각비", {})[yr_key] = get("감가상각비", year)
        data.setdefault("운반비", {})[yr_key] = get("운반비", year)
        data.setdefault("임차료", {})[yr_key] = get("임차료", year)
        data.setdefault("보험료", {})[yr_key] = get("보험료", year)
    
    return data


def parse_manufacturing_cost(filepath: str) -> Dict[str, Any]:
    """제조원가명세서 파싱"""
    raw = _parse_sheet(filepath)
    years = sorted(set(y for v in raw.values() for y in v.keys() if y.startswith('20')))
    
    def get(name: str, year: str) -> Optional[float]:
        return raw.get(name, {}).get(year)
    
    data = {"years": years, "raw": raw}
    
    for year in years:
        yr_key = year
        data.setdefault("원재료비", {})[yr_key] = get("원재료비(*)", year)
        data.setdefault("노동관계비용", {})[yr_key] = get("노동관계비용(*)", year)
        data.setdefault("경비", {})[yr_key] = get("경비(*)", year)
        data.setdefault("당기총제조비용", {})[yr_key] = get("당기총제조비용", year)
        data.setdefault("당기제품제조원가", {})[yr_key] = get("당기제품제조원가", year)
    
    return data
