"""
컨설팅 심층분석 모듈 - 세무조정계산서에서 컨설팅 가치 높은 데이터 추출

지원 분석:
1. 접대비(기업업무추진비) 분석
2. 업무용 승용차 분석
3. 감가상각 포트폴리오
4. 고용현황 + 통합고용세액공제
5. 제세공과금
6. 세액감면명세서
7. 세액공제액조정명세서
8. 소득금액조정합계표
9. 최저한세
10. 성실신고확인 결과 (개인사업자)
"""
import re
from typing import Dict, Any, List


def _parse_amount(s):
    """'1,234,567' 또는 '(1,234)' 같은 문자열을 정수로 변환"""
    if s is None: return None
    s = str(s).strip().replace(",", "").replace(" ", "").replace("원", "")
    if not s or s == "-": return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
        neg = True
    try:
        v = int(float(s))
        return -v if neg else v
    except:
        return None


def _find_page_idx(pdf, header_keyword, body_keyword=None, exclude_toc=True):
    """헤더 키워드 + (선택)본문 키워드로 페이지 찾기. 목차/총괄표 페이지 제외."""
    # 글자 사이 공백 허용 패턴
    pat = r'\s*'.join(list(header_keyword.replace(' ', '')))
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        head = text[:300]
        if exclude_toc:
            if "목차" in head[:50] or "세무조정계산서총괄표" in head[:50]:
                continue
        if re.search(pat, head):
            if body_keyword is None or body_keyword in text:
                return i
    return None


def extract_consulting_deep_analysis(filepath: str, is_personal: bool = False) -> Dict[str, Any]:
    """세무조정계산서 PDF에서 컨설팅 심층 분석용 데이터 추출.
    개인사업자/법인 양쪽 호환.
    """
    result = {
        # ─── 1. 접대비(기업업무추진비) ───
        "접대비": {
            "계정금액": None,
            "신용카드사용액": None,
            "신용카드비율": None,      # %
            "현금사용액_3만원초과": None,
            "현금사용액_3만원이하": None,
            "한도액": None,            # 기본한도 + 매출연동
            "한도초과": None,           # 손금불산입
            "한도사용률": None,         # %
        },
        # ─── 2. 업무용 승용차 ───
        "업무용차량": {
            "차량목록": [],            # [{차량번호, 종류, 임차/자가, 보험가입, 운행기록, 업무비율, 비용, ...}, ...]
            "총비용": None,
            "필요경비불산입": None,    # 한도초과액
            "필요경비산입": None,
            "임직원전용보험": None,    # 전체 차량 가입 여부
            "운행기록": None,
        },
        # ─── 3. 감가상각 ───
        "감가상각": {
            "유형자산_기말": None,     # 재무상태표상 가액
            "감가상각누계": None,
            "미상각잔액": None,        # 향후 감가상각 가능액
            "상각범위액": None,
            "회사손금계상액": None,
            "건축물": None,
            "기계장치": None,
            "기타자산": None,
            "무형자산": None,
            "당기상각비": None,        # 손익에 영향
        },
        # ─── 4. 고용 & 통합고용세액공제 ───
        "고용": {
            "당기_상시근로자수": None,
            "전기_상시근로자수": None,
            "증가인원": None,
            "청년근로자_당기": None,
            "청년근로자_전기": None,
            "청년증가": None,
            "당기_총급여": None,
            "전기_총급여": None,
            "통합고용공제_신청": None,
            "통합고용공제_금액": None,
            "사원수": None,            # 근로자 고용현황 사원 수
            "임원수": None,
            "신규입사": None,
            "퇴사자수": None,
        },
        # ─── 5. 제세공과금 ───
        "제세공과금": {
            "총액": None,
            "손금산입": None,
            "손금불산입": None,         # 벌과금 등
            "내역": [],                 # [{과목, 금액, 손금여부}, ...]
        },
        # ─── 6. 세액감면 ───
        "세액감면": {
            "감면항목": [],            # [{항목명, 감면액}, ...]
            "총감면액": None,
        },
        # ─── 7. 세액공제 ───
        "세액공제": {
            "공제항목": [],            # [{항목명, 공제액}, ...]
            "총공제액": None,
            "이월공제잔액": None,      # 향후 활용 가능
        },
        # ─── 8. 소득금액조정 ───
        "소득금액조정": {
            "익금산입_총액": None,     # 가산 총액 (개인은 '필요경비 부인')
            "손금산입_총액": None,     # 차감 총액 (개인은 '필요경비 추가')
            "익금산입_내역": [],       # [{과목, 금액, 처분, 사유}, ...]
            "손금산입_내역": [],
            "순조정": None,            # 익금산입 - 손금산입
        },
        # ─── 9. 최저한세 ───
        "최저한세": {
            "감면전세액": None,
            "감면후세액": None,
            "최저한세": None,
            "최저한세적용": None,       # 적용 여부
        },
        # ─── 10. 성실신고확인 ───
        "성실신고": {
            "대상여부": False,
            "확인자명": None,
            "사업자명": None,
            "주요지적사항": None,
        },
        # ─── 인사이트 자동 진단 (절세마스터리) ───
        "절세진단": {
            "활용중인_공제감면": [],
            "추천_공제감면": [],
            "주의사항": [],
            "절세여력_점수": None,     # 0-100
        },
        "is_personal": is_personal,
    }
    
    try:
        import pdfplumber
    except ImportError:
        return result
    import os
    if not os.path.exists(filepath):
        return result
    
    try:
        with pdfplumber.open(filepath) as pdf:
            # ─── 페이지 위치 매핑 ───
            sections = {
                "접대비": _find_page_idx(pdf, "기업업무추진비조정명세서", "계 정 과 목"),
                "차량": _find_page_idx(pdf, "업무용승용차관련비용", "업무용 사용비율"),
                "감가상각합계": _find_page_idx(pdf, "감가상각비조정명세서합계표", "기말현재액"),
                "고용세액공제": _find_page_idx(pdf, "통합고용세액공제공제세액계산서", "상시근로자"),
                "근로자고용현황": _find_page_idx(pdf, "근로자고용현황", "공제구분"),
                "제세공과금": _find_page_idx(pdf, "제세공과금조정명세서"),
                "감면세액": _find_page_idx(pdf, "감면세액조정명세서"),
                "세액공제액": _find_page_idx(pdf, "세액공제액조정명세서"),
                "소득금액조정": _find_page_idx(pdf, "소득금액조정합계표"),
                "최저한세": _find_page_idx(pdf, "최저한세조정명세서"),
                "성실신고": _find_page_idx(pdf, "성실신고확인서", "성실신고확인대상사업자"),
            }
            
            # ════════════════════════════════════════
            # 1. 접대비(기업업무추진비) 분석
            # ════════════════════════════════════════
            if sections["접대비"] is not None:
                t = pdf.pages[sections["접대비"]].extract_text() or ""
                # 같은 양식이 4쪽이라 다음 페이지까지 합치기
                for p in range(sections["접대비"] + 1, min(sections["접대비"] + 4, len(pdf.pages))):
                    pt = pdf.pages[p].extract_text() or ""
                    if "기업업무추진비" in pt[:200] or "한 도" in pt[:300] or "조정명세서" in pt[:200]:
                        t += "\n" + pt
                    else:
                        break
                
                # ⑤ 계 정 금 액 (가장 명확)
                m = re.search(r'⑤\s*계\s*정\s*금\s*액\s+([\d,]+)', t)
                if m: result["접대비"]["계정금액"] = _parse_amount(m.group(1))
                
                # ⑪ 계(⑥+⑩) = 신용카드 + 현금 총합 = 계정금액과 같음
                # 신용카드 사용액: ⑥ 신용카드 등 사용금액 → 다음 줄 또는 ⑥ ＋ ⑩ 합계에서 역산
                # "⑪ 계( ⑥ ＋ ⑩ ) 31,619,090" - 이게 총액
                # "⑩ 계(⑦ ＋ ⑧ ＋ ⑨) 26,700" - 이게 신용카드 미사용분(현금)
                m_total = re.search(r'⑪\s*계[^\d]*?([\d,]+)', t)
                m_cash_total = re.search(r'⑩\s*계[^\d]*?([\d,]+)', t)
                total_v = _parse_amount(m_total.group(1)) if m_total else None
                cash_v = _parse_amount(m_cash_total.group(1)) if m_cash_total else None
                if total_v and cash_v is not None:
                    result["접대비"]["신용카드사용액"] = total_v - cash_v
                
                # 3만원 이하 ⑧ (신용카드 미사용분에 포함되는 작은 금액)
                m = re.search(r'⑧\s*3\s*만\s*원\s*이\s*하\s+([\d,]+)', t)
                if m: result["접대비"]["현금사용액_3만원이하"] = _parse_amount(m.group(1))
                
                # ⑬ 기업업무추진비 한도액 합계 (⑧+⑩+⑫) — 진짜 최종 한도
                m = re.search(r'⑬\s*기\s*업\s*업\s*무\s*추\s*진\s*비\s*한\s*도\s*액\s*합\s*계[^\d]*?([\d,]+)', t)
                if not m:
                    # fallback: ⑧ 일반기업업무추진비 한도액
                    m = re.search(r'⑧\s*일\s*반\s*기\s*업\s*업\s*무\s*추\s*진\s*비\s*한\s*도\s*액[^\d]*?([\d,]+)', t)
                if m: result["접대비"]["한도액"] = _parse_amount(m.group(1))
                
                # 한도초과 (손금불산입)
                m = re.search(r'한\s*도\s*초\s*과(?:액)?[^\d]{1,20}?(\d{1,3}(?:,\d{3})+)', t)
                if m: 
                    v = _parse_amount(m.group(1))
                    if v and v < 100000000:  # 1억 미만이면 사용 (오매치 방지)
                        result["접대비"]["한도초과"] = v
                
                # 계산값
                if result["접대비"]["계정금액"]:
                    if result["접대비"]["신용카드사용액"] is not None:
                        result["접대비"]["신용카드비율"] = round(
                            result["접대비"]["신용카드사용액"] / result["접대비"]["계정금액"] * 100, 1
                        )
                    if result["접대비"]["한도액"]:
                        result["접대비"]["한도사용률"] = round(
                            result["접대비"]["계정금액"] / result["접대비"]["한도액"] * 100, 1
                        )
            
            # ════════════════════════════════════════
            # 2. 업무용 승용차
            # ════════════════════════════════════════
            if sections["차량"] is not None:
                t = pdf.pages[sections["차량"]].extract_text() or ""
                
                # 차량 라인 패턴: "Y 32거1745 산타페 자가 여 100.0000 366 366 ..."
                # 더 간단하게: 차량번호 패턴(2~3자리숫자+한글1자+4자리숫자) 찾기
                for line in t.split("\n"):
                    m = re.search(r'(\d{2,3}[가-힣]\d{4})\s+(\S+)\s+(\S+)\s+(여|부)\s+([\d.]+)', line)
                    if m:
                        car = {
                            "차량번호": m.group(1),
                            "종류": m.group(2),
                            "임차여부": m.group(3),  # 자가/임차
                            "보험가입": m.group(4) == "여",
                            "업무비율": float(m.group(5)),
                        }
                        # 같은 라인의 끝에서 비용 합계 추출
                        amounts = re.findall(r'\b\d{1,3}(?:,\d{3})+\b', line)
                        if amounts:
                            try:
                                car["관련비용합계"] = _parse_amount(amounts[-1])
                            except:
                                pass
                        result["업무용차량"]["차량목록"].append(car)
                
                # 필요경비 불산입/산입 합계
                m = re.search(r'필\s*요\s*경\s*비\s*불\s*산\s*입\s*합\s*계[^\d]*?([\d,]+)', t)
                if m: result["업무용차량"]["필요경비불산입"] = _parse_amount(m.group(1))
                m = re.search(r'필\s*요\s*경\s*비\s*산\s*입\s*합\s*계[^\d]*?([\d,]+)', t)
                if m: result["업무용차량"]["필요경비산입"] = _parse_amount(m.group(1))
                
                # 총비용 계산
                if result["업무용차량"]["차량목록"]:
                    total = sum(c.get("관련비용합계", 0) or 0 for c in result["업무용차량"]["차량목록"])
                    result["업무용차량"]["총비용"] = total or None
                    result["업무용차량"]["임직원전용보험"] = all(
                        c.get("보험가입", False) for c in result["업무용차량"]["차량목록"]
                    )
                
                # 운행기록 작성 여부
                if "운행기록" in t and ("작성" in t or "있음" in t):
                    result["업무용차량"]["운행기록"] = True
            
            # ════════════════════════════════════════
            # 3. 감가상각 합계표
            # ════════════════════════════════════════
            if sections["감가상각합계"] is not None:
                t = pdf.pages[sections["감가상각합계"]].extract_text() or ""
                
                # "101 기말현재액 01 1,193,374,161 756,685,909 303,837,127 132,851,125"
                # 합계 / 건축물 / 기계장치 / 기타자산 / 무형
                def _find_4cols(label):
                    """라벨 + 코드 + 4개 컬럼 값"""
                    pat = re.escape(label) + r'.*?\d{2}\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)'
                    m = re.search(pat, t)
                    if m:
                        return [_parse_amount(m.group(i+1)) for i in range(4)]
                    return None
                
                # 기말현재액
                vals = _find_4cols("기말현재액")
                if vals:
                    result["감가상각"]["유형자산_기말"] = vals[0]
                    result["감가상각"]["건축물"] = vals[1]
                    result["감가상각"]["기계장치"] = vals[2]
                    result["감가상각"]["기타자산"] = vals[3]
                
                vals = _find_4cols("감가상각누계액")
                if vals:
                    result["감가상각"]["감가상각누계"] = vals[0]
                
                vals = _find_4cols("미상각잔액")
                if vals:
                    result["감가상각"]["미상각잔액"] = vals[0]
                
                vals = _find_4cols("상각범위액")
                if vals:
                    result["감가상각"]["상각범위액"] = vals[0]
                
                vals = _find_4cols("회사손금계상액")
                if vals:
                    result["감가상각"]["회사손금계상액"] = vals[0]
                    result["감가상각"]["당기상각비"] = vals[0]
                
                # 무형고정자산 (마지막 5번째 열)
                pat = r'기말현재액[^\n]*?\d+\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+([\d,]+)'
                m = re.search(pat, t)
                if m:
                    result["감가상각"]["무형자산"] = _parse_amount(m.group(1))
            
            # ════════════════════════════════════════
            # 4. 고용 + 통합고용세액공제
            # ════════════════════════════════════════
            if sections["고용세액공제"] is not None:
                t = pdf.pages[sections["고용세액공제"]].extract_text() or ""
                
                # PDF 표 형식이라 "⑥ 상시근로자 수" 라벨 다음 줄에 숫자가 있음
                # 패턴: "⑥ 상시근로자 수\n(⑦+⑧)\n6.75 9.75"
                # 또는 표 row 추출
                
                # 1) 표 추출 시도
                try:
                    page = pdf.pages[sections["고용세액공제"]]
                    tables = page.extract_tables() or []
                    for tbl in tables:
                        for row in tbl:
                            if not row: continue
                            row_text = " ".join(str(c or "") for c in row)
                            if "상시근로자 수" in row_text and "⑥" in row_text:
                                # 마지막 2~3개 숫자가 직전전/직전/당기
                                nums = re.findall(r'\d+\.?\d*', row_text)
                                # 'X.XX' 형식 (소수점 있는 인원수) 우선
                                float_nums = [n for n in nums if '.' in n]
                                if len(float_nums) >= 2:
                                    result["고용"]["전기_상시근로자수"] = float(float_nums[-2])
                                    result["고용"]["당기_상시근로자수"] = float(float_nums[-1])
                                break
                except Exception:
                    pass
                
                # 2) 표 추출 안되면 텍스트에서 직접
                if result["고용"]["당기_상시근로자수"] is None:
                    # 라인별 검사: '⑥ 상시근로자 수' 또는 '(⑦+⑧)' 라인 근처의 숫자
                    lines = t.split('\n')
                    for i, line in enumerate(lines):
                        if "⑥" in line and "상시근로자" in line:
                            # 다음 3줄에서 숫자 찾기
                            search_zone = " ".join(lines[i:i+4])
                            nums = re.findall(r'\d+\.\d+', search_zone)
                            if len(nums) >= 2:
                                result["고용"]["전기_상시근로자수"] = float(nums[-2])
                                result["고용"]["당기_상시근로자수"] = float(nums[-1])
                            break
                
                # 청년근로자
                m = re.search(r'⑦\s*청년등상시근로자\s*수[^\d]*?([\d.]+)\s+([\d.]+)', t)
                if m:
                    result["고용"]["청년근로자_전기"] = float(m.group(1))
                    result["고용"]["청년근로자_당기"] = float(m.group(2))
                
                # 증가인원
                if result["고용"]["당기_상시근로자수"] and result["고용"]["전기_상시근로자수"]:
                    result["고용"]["증가인원"] = round(
                        result["고용"]["당기_상시근로자수"] - result["고용"]["전기_상시근로자수"], 2
                    )
                if result["고용"]["청년근로자_당기"] is not None and result["고용"]["청년근로자_전기"] is not None:
                    result["고용"]["청년증가"] = round(
                        result["고용"]["청년근로자_당기"] - result["고용"]["청년근로자_전기"], 2
                    )
                
                result["고용"]["통합고용공제_신청"] = True
                
                # 공제세액 (이 양식 또는 세액공제명세서에서)
                # "통합고용세액공제 2024 25,500,000" 같은 패턴 (2024는 연도)
                for p in range(sections["고용세액공제"], min(sections["고용세액공제"] + 5, len(pdf.pages))):
                    pt = pdf.pages[p].extract_text() or ""
                    m = re.search(r'통\s*합\s*고\s*용\s*세\s*액\s*공\s*제\s+20\d{2}\s+([\d,]+)', pt)
                    if m:
                        v = _parse_amount(m.group(1))
                        if v and v > 100000:  # 10만원 이상이면 의미있는 공제금액
                            result["고용"]["통합고용공제_금액"] = v
                            break
            
            # 근로자 고용현황 - 사원수, 신규, 퇴사
            if sections["근로자고용현황"] is not None:
                t = pdf.pages[sections["근로자고용현황"]].extract_text() or ""
                # "2024년 총급여"
                m = re.search(r'2024\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+([\d.]+)\s+([\d,]+)', t)
                if m:
                    result["고용"]["당기_총급여"] = _parse_amount(m.group(2))
                # 사원수 (라인별 카운트)
                emp_lines = re.findall(r'\d{4}\s+5\s+[가-힣]{2,5}\s+\d{6,7}', t)
                result["고용"]["사원수"] = len(emp_lines) or None
                # 임원/대표 카운트
                exec_count = len(re.findall(r'대표/임원', t))
                result["고용"]["임원수"] = exec_count or None
                # 퇴사자: 라인에 두 날짜가 있는 경우
                resign_count = sum(1 for line in t.split('\n') 
                                   if re.search(r'20\d{2}/\d{2}/\d{2}\s+20\d{2}/\d{2}/\d{2}', line))
                result["고용"]["퇴사자수"] = resign_count or None
            
            # ════════════════════════════════════════
            # 5. 제세공과금
            # ════════════════════════════════════════
            if sections["제세공과금"] is not None:
                t = pdf.pages[sections["제세공과금"]].extract_text() or ""
                # 합계 라인
                m = re.search(r'합\s*계[^\d]*?([\d,]+)', t)
                if m: result["제세공과금"]["총액"] = _parse_amount(m.group(1))
                
                # 세부 내역: "재산세 1,234,567" 같은 형태
                items = []
                tax_keywords = ["재산세", "자동차세", "주민세", "사업소세", "면허세", "취득세", 
                               "등록세", "인지세", "벌금", "과태료", "가산금", "교통유발"]
                for line in t.split("\n"):
                    for kw in tax_keywords:
                        if kw in line:
                            m = re.search(rf'{kw}[^\d]*?([\d,]+)', line)
                            if m:
                                amt = _parse_amount(m.group(1))
                                if amt:
                                    items.append({"항목": kw, "금액": amt, 
                                                  "손금여부": kw not in ["벌금", "과태료", "가산금"]})
                                break
                result["제세공과금"]["내역"] = items
                
                # 손금불산입 (벌금/과태료/가산금)
                m = re.search(r'손\s*금\s*불\s*산\s*입[^\d]*?([\d,]+)', t)
                if m: result["제세공과금"]["손금불산입"] = _parse_amount(m.group(1))
            
            # ════════════════════════════════════════
            # 6. 세액감면명세서
            # ════════════════════════════════════════
            if sections["감면세액"] is not None:
                t = pdf.pages[sections["감면세액"]].extract_text() or ""
                
                # 다음 페이지까지 (양식이 한 페이지 넘을 수 있음)
                for p in range(sections["감면세액"] + 1, min(sections["감면세액"] + 3, len(pdf.pages))):
                    pt = pdf.pages[p].extract_text() or ""
                    if "세액공제액조정명세서" in pt[:200]:
                        break
                    t += "\n" + pt
                
                # 감면 항목: 라인별로 한글 라벨 뒤에 큰 금액 (10만원 이상)
                gam_keywords = [
                    "중소기업에 대한 특별세액감면", "중소기업특별세액감면",
                    "창업중소기업 등에 대한 세액감면", "창업중소기업",
                    "고용유지중소기업", "수도권 외 이전",
                    "성실신고확인비용", "근로소득", "전자신고",
                ]
                items = []
                for kw in gam_keywords:
                    # 라인 검색 (한글 사이 공백 무시)
                    pat = r'\s*'.join(list(kw.replace(' ', '')))
                    for line in t.split('\n'):
                        if re.search(pat, line):
                            # 같은 라인 마지막 큰 숫자 (10만원+)
                            nums = re.findall(r'\d{1,3}(?:,\d{3})+', line)
                            for n in reversed(nums):
                                v = _parse_amount(n)
                                if v and v >= 100000:  # 의미있는 금액
                                    items.append({"항목": kw, "금액": v})
                                    break
                            break
                
                # 중복 제거
                seen = set()
                unique_items = []
                for it in items:
                    key = it["항목"]
                    if key not in seen:
                        seen.add(key)
                        unique_items.append(it)
                result["세액감면"]["감면항목"] = unique_items
                
                # 총감면액: "합 계" 라인의 큰 숫자
                for line in t.split('\n'):
                    if re.match(r'^\s*합\s*계', line):
                        nums = re.findall(r'\d{1,3}(?:,\d{3})+', line)
                        if nums:
                            v = _parse_amount(nums[-1])
                            if v and v >= 100000:
                                result["세액감면"]["총감면액"] = v
                                break
                # 합계 못 찾으면 항목 합산
                if not result["세액감면"]["총감면액"] and unique_items:
                    result["세액감면"]["총감면액"] = sum(it["금액"] for it in unique_items)
            
            # ════════════════════════════════════════
            # 7. 세액공제액조정명세서
            # ════════════════════════════════════════
            if sections["세액공제액"] is not None:
                t = pdf.pages[sections["세액공제액"]].extract_text() or ""
                
                gong_keywords = [
                    "통합고용세액공제", "통합투자세액공제", "연구·인력개발", 
                    "연구인력개발", "R&D",
                    "전자신고", "기장세액공제", "성실신고확인비용",
                    "근로소득증대",
                ]
                items = []
                for kw in gong_keywords:
                    clean_kw = kw.replace(' ', '').replace('·', '')
                    pat = r'\s*'.join(list(clean_kw))
                    for line in t.split('\n'):
                        if re.search(pat, line):
                            # 라인의 모든 숫자 추출, 연도(20XX) 제외 + 10만원 이상
                            nums = re.findall(r'\d{1,3}(?:,\d{3})+', line)
                            for n in nums:
                                v = _parse_amount(n)
                                # 연도 패턴(2020-2030, 4자리 정수) 제외
                                if v and v >= 100000:
                                    items.append({"항목": kw, "금액": v})
                                    break
                            break
                
                # 중복 제거
                seen = set()
                unique_items = []
                for it in items:
                    if it["항목"] not in seen:
                        seen.add(it["항목"])
                        unique_items.append(it)
                result["세액공제"]["공제항목"] = unique_items
                
                # 총공제액: "합 계" 라인
                for line in t.split('\n'):
                    if re.match(r'^\s*합\s*계', line):
                        nums = re.findall(r'\d{1,3}(?:,\d{3})+', line)
                        if nums:
                            v = _parse_amount(nums[0])  # 합계 라인의 첫 큰 금액
                            if v and v >= 100000:
                                result["세액공제"]["총공제액"] = v
                                break
                if not result["세액공제"]["총공제액"] and unique_items:
                    result["세액공제"]["총공제액"] = sum(it["금액"] for it in unique_items)
            
            # ════════════════════════════════════════
            # 8. 소득금액조정합계표
            # ════════════════════════════════════════
            if sections["소득금액조정"] is not None:
                t = pdf.pages[sections["소득금액조정"]].extract_text() or ""
                # 같은 양식이 여러 쪽에 걸칠 수 있음
                for p in range(sections["소득금액조정"] + 1, min(sections["소득금액조정"] + 2, len(pdf.pages))):
                    pt = pdf.pages[p].extract_text() or ""
                    if "소득금액조정" in pt[:100] or "익금산입" in pt[:200]:
                        t += "\n" + pt
                    else:
                        break
                
                # 합계 금액
                m = re.search(r'익금산입[^\n]{0,30}?합\s*계[^\d]*?([\d,]+)', t)
                if m: result["소득금액조정"]["익금산입_총액"] = _parse_amount(m.group(1))
                m = re.search(r'손금산입[^\n]{0,30}?합\s*계[^\d]*?([\d,]+)', t)
                if m: result["소득금액조정"]["손금산입_총액"] = _parse_amount(m.group(1))
                
                # 순조정
                a = result["소득금액조정"]["익금산입_총액"] or 0
                b = result["소득금액조정"]["손금산입_총액"] or 0
                if a or b:
                    result["소득금액조정"]["순조정"] = a - b
                
                # 항목별 내역 (간단 추출 - 한글 라벨 + 금액)
                lines = t.split("\n")
                in_add_section = False
                in_sub_section = False
                for line in lines:
                    if "익금산입" in line and "손금불산입" in line:
                        in_add_section = True; in_sub_section = False
                        continue
                    if "손금산입" in line and "익금불산입" in line:
                        in_sub_section = True; in_add_section = False
                        continue
                    # 항목 라인: "과목명 금액 처분"
                    m = re.match(r'^\s*([가-힣]{2,15})\s+([\d,]{5,})\s+(\S+)?', line.strip())
                    if m:
                        item = {"과목": m.group(1), "금액": _parse_amount(m.group(2))}
                        if m.group(3): item["처분"] = m.group(3)[:10]
                        if in_add_section and item["금액"]:
                            result["소득금액조정"]["익금산입_내역"].append(item)
                        elif in_sub_section and item["금액"]:
                            result["소득금액조정"]["손금산입_내역"].append(item)
            
            # ════════════════════════════════════════
            # 9. 최저한세
            # ════════════════════════════════════════
            if sections["최저한세"] is not None:
                t = pdf.pages[sections["최저한세"]].extract_text() or ""
                m = re.search(r'감\s*면\s*전\s*세\s*액[^\d]*?([\d,]+)', t)
                if m: result["최저한세"]["감면전세액"] = _parse_amount(m.group(1))
                m = re.search(r'감\s*면\s*후\s*세\s*액[^\d]*?([\d,]+)', t)
                if m: result["최저한세"]["감면후세액"] = _parse_amount(m.group(1))
                m = re.search(r'최\s*저\s*한\s*세\s*액[^\d]*?([\d,]+)', t)
                if m: result["최저한세"]["최저한세"] = _parse_amount(m.group(1))
                
                # 최저한세 적용 여부 (감면후세액 < 최저한세면 적용)
                a = result["최저한세"]["감면후세액"]
                m_val = result["최저한세"]["최저한세"]
                if a is not None and m_val is not None:
                    result["최저한세"]["최저한세적용"] = a < m_val
            
            # ════════════════════════════════════════
            # 10. 성실신고확인 (개인사업자만)
            # ════════════════════════════════════════
            if is_personal and sections["성실신고"] is not None:
                t = pdf.pages[sections["성실신고"]].extract_text() or ""
                result["성실신고"]["대상여부"] = True
                
                m = re.search(r'①\s*성\s*명\s+([가-힣]{2,5})', t)
                if m: result["성실신고"]["사업자명"] = m.group(1)
                
                # 확인자 (세무대리인)
                m = re.search(r'확인자[^\n]*?([가-힣]{2,5}\s*세무회계|[가-힣]{2,5}회계법인|[가-힣]{2,5}세무사사무소)', t)
                if m: result["성실신고"]["확인자명"] = m.group(1).strip()
            
            # ════════════════════════════════════════
            # 절세 진단 자동 분석
            # ════════════════════════════════════════
            diagnosis = result["절세진단"]
            score = 50  # 시작 점수
            
            # 활용 중인 공제/감면
            if result["고용"]["통합고용공제_신청"]:
                diagnosis["활용중인_공제감면"].append("통합고용세액공제")
                score += 10
            if result["세액감면"]["총감면액"] and result["세액감면"]["총감면액"] > 0:
                diagnosis["활용중인_공제감면"].append("세액감면")
                score += 5
            if result["세액공제"]["총공제액"] and result["세액공제"]["총공제액"] > 0:
                diagnosis["활용중인_공제감면"].append("세액공제")
                score += 5
            
            # 추천 공제/감면
            applied = set(result["고용"]["증가인원"] is not None and result["고용"]["증가인원"] > 0 
                         and "통합고용세액공제" in diagnosis["활용중인_공제감면"]
                         for _ in [None])
            if result["고용"]["증가인원"] and result["고용"]["증가인원"] > 0:
                if "통합고용세액공제" not in diagnosis["활용중인_공제감면"]:
                    diagnosis["추천_공제감면"].append("통합고용세액공제 (고용 증가 있는데 미신청!)")
                    score -= 10
            if not result["고용"]["통합고용공제_신청"] and result["고용"]["당기_상시근로자수"]:
                diagnosis["추천_공제감면"].append("통합고용세액공제 검토 필요")
            
            # 주의사항
            if result["접대비"]["한도사용률"] and result["접대비"]["한도사용률"] > 90:
                diagnosis["주의사항"].append(f"접대비 한도 거의 소진 ({result['접대비']['한도사용률']:.1f}%) — 내년 한도 초과 위험")
                score -= 5
            if result["접대비"]["한도초과"] and result["접대비"]["한도초과"] > 0:
                diagnosis["주의사항"].append(f"접대비 한도 초과 {result['접대비']['한도초과']:,}원 손금불산입")
                score -= 10
            if result["업무용차량"]["필요경비불산입"] and result["업무용차량"]["필요경비불산입"] > 0:
                diagnosis["주의사항"].append(f"업무용차량 한도초과 {result['업무용차량']['필요경비불산입']:,}원 손금불산입")
                score -= 5
            if result["업무용차량"]["임직원전용보험"] is False:
                diagnosis["주의사항"].append("업무용차량 임직원전용보험 미가입 차량 있음 — 손금산입 제한")
                score -= 15
            if result["제세공과금"]["손금불산입"] and result["제세공과금"]["손금불산입"] > 0:
                diagnosis["주의사항"].append(f"벌과금/가산금 {result['제세공과금']['손금불산입']:,}원 손금불산입 발생")
                score -= 5
            if result["최저한세"]["최저한세적용"]:
                diagnosis["주의사항"].append("최저한세 적용 — 일부 감면이 무력화됨")
                score -= 10
            
            # 점수 보정
            diagnosis["절세여력_점수"] = max(0, min(100, score))
    
    except Exception as e:
        import traceback
        print(f"컨설팅 심층분석 오류: {e}")
        print(traceback.format_exc())
    
    return result
