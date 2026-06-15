"""
크레탑(CRETOP) 표준재무제표 엑셀 로더 + 통합 진단 어댑터
─────────────────────────────────────────────────────────────
어떤 입력이든(엑셀 BS/IS/제조원가, 또는 세무조정계산서 PDF) 받아
hidden_loan_detector.detect()가 먹을 수 있는 표준 result dict로 정규화한다.

크레탑 엑셀 4종(파일명 ETFI112E1*.xlsx 형태):
  - 재무상태표      : 최상위 계정 '자산'
  - 손익계산서      : 최상위 계정 '매출액'
  - 이익잉여금처분  : 최상위 계정 '미처분이익잉여금'
  - 제조원가명세서  : 최상위 계정 '원재료비'

사용 예:
    from report.cretop_fs_loader import load_any, diagnose
    result = load_any(["bs.xlsx","is.xlsx","mfg.xlsx"])     # 엑셀 여러 개
    result = load_any("세무조정.pdf")                        # PDF 한 개
    report = diagnose(result)                                # 진단까지 한 번에
"""
from typing import Dict, Any, List, Union, Optional
import os
import re

try:
    import openpyxl
except ImportError:
    openpyxl = None


# ── 계정명 정규화 사전: 크레탑 표기 → 탐지 모듈 표준키 ──────────────
# 탐지 모듈(hidden_loan_detector)이 찾는 키로 통일한다.
ACCOUNT_ALIAS = {
    # 자산
    "현금및현금성자산": "현금및현금성자산",
    "현금및현금등가물": "현금및현금성자산",
    "현금및예금": "현금및현금성자산",
    "매출채권": "매출채권",
    "단기대여금": "단기대여금",
    "기타단기대여금": "단기대여금",
    "장기대여금": "장기대여금",
    "미수금": "미수금",
    "기타미수금": "미수금",
    "미수수익": "미수수익",
    "선급금": "선급금",
    "선급비용": "선급비용",
    "가지급금": "가지급금",
    "재고자산": "재고자산",
    "임차보증금": "임차보증금",
    "보증금등": "임차보증금",
    "주임종단기채권": "주임종단기채권",
    "자산총계": "자산총계", "자산": "자산총계",
    "이익잉여금": "이익잉여금",
    "미처분이익잉여금결손금": "이익잉여금",
    # 부채 (가수금성)
    "가수금": "가수금",
    "주주임원종업원단기차입금": "가수금",   # 대표→회사 차입 = 가수금성
    "주임종단기차입금": "가수금",
    "미지급금": "미지급금",
    "기타미지급금": "미지급금",
    "선수금": "선수금",
    "기타선수금": "선수금",
    "예수금": "예수금",
    "기타예수금": "예수금",
    "단기차입금": "단기차입금",
    "장기차입금": "장기차입금",
    "특수관계자장기차입금": "특수관계자장기차입금",
    "부채총계": "부채총계", "부채": "부채총계",
    "자본총계": "자본총계", "자본": "자본총계",
    "유동자산": "유동자산", "비유동자산": "비유동자산",
    "유동부채": "유동부채", "비유동부채": "비유동부채",
    "자본금": "자본금",
    # 손익
    "매출액": "매출액",
    "매출원가": "매출원가",
    "매출총이익손실": "매출총이익", "매출총이익": "매출총이익",
    "판매비와관리비": "판매관리비",
    "영업이익손실": "영업이익", "영업이익": "영업이익",
    "영업외수익": "영업외수익",
    "영업외비용": "영업외비용",
    "이자수익": "이자수익",
    "이자비용": "이자비용",
    "법인세비용차감전순손익": "세전이익",
    "당기순이익순손실": "당기순이익", "당기순이익": "당기순이익",
}


def _clean_name(name: str) -> str:
    """'(대손충당금)(*)', '   유동자산(*)', '*당기순이익' → 정규화 키"""
    if not name:
        return ""
    s = str(name).strip()
    s = s.replace("(*)", "").replace("*", "")
    s = s.strip()
    # 괄호로 시작하는 차감항목(대손충당금/감가상각누계액 등)은 별도 보존용 표시
    paren = s.startswith("(") and s.endswith(")")
    core = re.sub(r"[()\s,·ㆍ\.]", "", s)   # 공백·괄호·중점·점 제거
    return ("(차감)" + core) if paren else core


def _won(v):
    if v is None:
        return "-"
    v = abs(float(v))
    if v >= 1e8:
        return f"{v/1e8:.1f}억"
    if v >= 1e4:
        return f"{v/1e4:,.0f}만"
    return f"{v:,.0f}원"


# ── 엑셀 1개 파싱 → {정규화계정: {연도: 원}} + 종류 ───────────────
def _parse_cretop_xlsx(path: str):
    if openpyxl is None or not os.path.exists(path):
        return {}, [], "unknown"
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    # 1) 연도 헤더 행 찾기 ('계정명' 셀이 있는 행)
    years: List[str] = []
    name_col = 1
    for r in rows:
        cells = [str(c) if c is not None else "" for c in r]
        if any("계정명" in c for c in cells):
            name_col = next((i for i, c in enumerate(cells) if "계정명" in c), 1)
            for c in cells:
                if re.match(r"\d{4}-\d{2}-\d{2}", c):
                    years.append(c)
            break
    if not years:
        # 폴백: 헤더에 yyyy-mm-dd 없는 경우, 4자리연도 추출
        for r in rows:
            for c in r:
                if c and re.match(r"\d{4}-\d{2}-\d{2}", str(c)):
                    years.append(str(c))
            if years:
                break

    # 2) 단위 배수 (기본 천원)
    mult = 1000
    head_blob = " ".join(str(c) for r in rows[:3] for c in r if c)
    if "단위" in head_blob:
        if "백만" in head_blob:
            mult = 1_000_000
        elif "천원" in head_blob:
            mult = 1000
        elif "원" in head_blob and "천" not in head_blob and "백만" not in head_blob:
            mult = 1

    # 3) 계정 추출
    acc: Dict[str, Dict[str, float]] = {}
    first_real = None
    for r in rows:
        raw = r[name_col] if len(r) > name_col else None
        if not raw:
            continue
        key = _clean_name(raw)
        if not key or key == "감사의견" or key == "계정명":
            continue
        if first_real is None and not key.startswith("(차감)"):
            first_real = key
        vals = {}
        for i, y in enumerate(years):
            cell = r[name_col + 1 + i] if len(r) > name_col + 1 + i else None
            if isinstance(cell, (int, float)):
                vals[y] = float(cell) * mult
        if vals:
            std = ACCOUNT_ALIAS.get(key)
            # 같은 표준키가 여러 줄에 나오면(소계/세부) 첫 매칭(상위 소계)만 사용
            if std and std not in acc:
                acc[std] = vals
            # 표준키 없어도 특수관계자장기차입금 등은 원키로 보존
            elif key in ("특수관계자장기차입금",) and key not in acc:
                acc[key] = vals

    # 4) 종류 판별
    kind = "unknown"
    fr = first_real or ""
    if fr.startswith("자산"):
        kind = "bs"
    elif fr.startswith("매출액"):
        kind = "is"
    elif "미처분이익잉여금" in fr:
        kind = "equity"
    elif fr.startswith("원재료비") or "제조" in fr:
        kind = "mfg"
    return acc, years, kind


# ── 여러 입력을 받아 표준 result dict 생성 ─────────────────────────
def load_any(paths: Union[str, List[str]]) -> Dict[str, Any]:
    """
    paths: 엑셀 경로 리스트(BS/IS/제조원가/이익잉여금 섞여도 됨) 또는 PDF 경로(str/리스트).
    반환: hidden_loan_detector.detect()가 먹는 {"bs","isc","mfg","is_personal","_meta"} dict.
    """
    if isinstance(paths, str):
        paths = [paths]

    # ── PDF가 섞여 있으면 기존 PDF 파서로 위임 ──
    pdfs = [p for p in paths if p.lower().endswith(".pdf")]
    if pdfs:
        return _load_from_pdf(pdfs[0])

    # ── 엑셀 경로들 ──
    bs_acc: Dict[str, Dict[str, float]] = {}
    is_acc: Dict[str, Dict[str, float]] = {}
    mfg_acc: Dict[str, Dict[str, float]] = {}
    all_years: List[str] = []
    kinds_found = []

    for p in paths:
        if not p.lower().endswith((".xlsx", ".xls")):
            continue
        acc, years, kind = _parse_cretop_xlsx(p)
        if years and not all_years:
            all_years = years
        kinds_found.append(kind)
        if kind == "bs":
            bs_acc.update(acc)
        elif kind == "is":
            is_acc.update(acc)
        elif kind == "mfg":
            mfg_acc.update(acc)
        elif kind == "equity":
            # 이익잉여금처분: 이익잉여금만 BS 보강용으로 흡수
            if "이익잉여금" in acc and "이익잉여금" not in bs_acc:
                bs_acc["이익잉여금"] = acc["이익잉여금"]

    # detect()는 corporate 양식 {계정:{연도:값}} + section["years"] 를 먹는다
    bs = {"years": all_years, **bs_acc}
    isc = {"years": all_years, **is_acc}
    mfg = {"years": all_years, **mfg_acc}

    return {
        "bs": bs, "isc": isc, "mfg": mfg,
        "is_personal": False,
        "company": {"기업명": "", "기업유형": ""},
        "_meta": {"source": "cretop_xlsx", "kinds": kinds_found, "years": all_years},
    }


def _load_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """세무조정계산서 PDF → 기존 pdf_parser로 위임 (법인/개인 자동판별)."""
    meta = {"source": "tax_pdf", "path": pdf_path}
    try:
        from parsers.pdf_parser import (
            is_personal_tax_adjustment_pdf,
            parse_tax_adjustment_pdf,
            parse_personal_tax_adjustment_pdf,
        )
    except Exception as e:
        return {"bs": {"years": []}, "isc": {"years": []}, "mfg": {"years": []},
                "is_personal": False, "_meta": {**meta, "error": f"parser import 실패: {e}"}}

    try:
        if is_personal_tax_adjustment_pdf(pdf_path):
            r = parse_personal_tax_adjustment_pdf(pdf_path)
            r["is_personal"] = True
        else:
            r = parse_tax_adjustment_pdf(pdf_path)
            r["is_personal"] = False
        r["_meta"] = meta
        return r
    except Exception as e:
        return {"bs": {"years": []}, "isc": {"years": []}, "mfg": {"years": []},
                "is_personal": False, "_meta": {**meta, "error": str(e)}}


# ── 한 방에 진단까지 ───────────────────────────────────────────────
def diagnose(result_or_paths: Union[Dict[str, Any], str, List[str]],
             industry: str = "") -> Dict[str, Any]:
    """
    입력이 경로(들)이면 load_any로 적재 후 진단, 이미 result dict면 바로 진단.
    반환: detect() 결과 + "_input_meta".
    """
    if isinstance(result_or_paths, (str, list)):
        result = load_any(result_or_paths)
    else:
        result = result_or_paths

    try:
        from report.hidden_loan_detector import detect
    except Exception:
        from hidden_loan_detector import detect  # 같은 폴더 폴백

    deep = result.get("_tax_deep")  # PDF 경로면 별도 추출 필요(아래 안내)
    out = detect(result, deep=deep, industry=industry or
                 result.get("company", {}).get("기업유형", ""))
    out["_input_meta"] = result.get("_meta", {})
    return out


if __name__ == "__main__":
    import sys, json
    args = sys.argv[1:]
    if not args:
        print("사용법: python cretop_fs_loader.py <엑셀…|PDF>")
        sys.exit(0)
    rep = diagnose(args)
    print(f"\n등급: {rep['level']} | 위험점수: {rep['score']}")
    print(rep["summary"])
    print("입력:", rep["_input_meta"])
    for f in rep["findings"]:
        print(f"\n[{f['severity']}] {f['title']}\n  {f['근거']}\n  {f['멘트']}")
