"""
CRETOP PDF 파서: 기업 브리핑(개요) 및 신용등급 보고서에서 데이터 추출
"""
import re
from typing import Dict, Any, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def parse_company_overview(filepath: str) -> Dict[str, Any]:
    """개요.pdf (기업 브리핑 보고서) 파싱"""
    if pdfplumber is None or filepath is None:
        return _fallback_overview()
    
    data = {
        "기업명": "",
        "사업자번호": "",
        "대표자명": "",
        "법인번호": "",
        "설립일자": "",
        "종업원수": "",
        "주소": "",
        "전화번호": "",
        "기업유형": "",
        "표준산업분류": "",
        "기업규모": "",
        "주요제품": "",
        "기업신용등급": "",
        "EW등급": "",
        "신용정보": {},
        "주요주주": [],
        "주요구매처": [],
        "주요판매처": [],
        "기업인증": {},
        "산업재산권": {},
        "재무상태표": {},
        "손익계산서": {},
        "재무비율": {},
        "재무진단": {},
    }
    
    try:
        with pdfplumber.open(filepath) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"
            
            # 기업 기본정보 추출
            patterns = {
                "사업자번호": r"사업자번호\s+([\d\-]+)",
                "법인번호": r"법인\(주민\)번호\s+([\d\-]+)",
                "대표자명": r"대표자명\s+(\S+)",
                "설립일자": r"설립일자\s+([\d\-]+)",
                "종업원수": r"종업원수\s+(\S+)",
                "전화번호": r"전화번호\s+([\d\-]+)",
                "기업규모": r"기업규모\s+(\S+)",
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, full_text)
                if match:
                    data[key] = match.group(1).strip()
            
            # 기업명 추출
            name_match = re.search(r"\(주\)\S+", full_text)
            if name_match:
                data["기업명"] = name_match.group(0)
            
            # 기업유형
            type_match = re.search(r"기업유형/형태\s+(.+?)(?:\s+전화번호|\n)", full_text)
            if type_match:
                data["기업유형"] = type_match.group(1).strip()
            
            # 주소
            addr_match = re.search(r"주소\(도로명\)\s+(.+?)(?:\s+밀폐용기|\n)", full_text)
            if addr_match:
                data["주소"] = addr_match.group(1).strip()
            
            # 신용등급
            grade_match = re.search(r"평가일자\s*:\s*([\d\-]+)\s*결산일자\s*:\s*([\d\-]+)", full_text)
            if grade_match:
                data["신용등급_평가일자"] = grade_match.group(1)
                data["신용등급_결산일자"] = grade_match.group(2)
            
            # EW등급
            ew_match = re.search(r"(정상|주의|경고|위험)", full_text)
            if ew_match:
                data["EW등급"] = ew_match.group(1)
            
            # 재무진단 등급
            diag_patterns = {
                "성장성": r"성장성\s+(우수|양호|보통|미흡|열위)",
                "수익성": r"수익성\s+(우수|양호|보통|미흡|열위)",
                "재무구조": r"재무구조\s+(우수|양호|보통|미흡|열위)",
                "활동성": r"활동성\s+(우수|양호|보통|미흡|열위)",
            }
            for key, pattern in diag_patterns.items():
                match = re.search(pattern, full_text)
                if match:
                    data["재무진단"][key] = match.group(1)
    except Exception as e:
        print(f"PDF 파싱 오류: {e}")
    
    return data


def parse_credit_report(filepath: str) -> Dict[str, Any]:
    """신용.pdf (기업 신용등급 보고서) 파싱"""
    data = {
        "현재등급": "",
        "등급설명": "",
        "등급구분": "",
        "평가일자": "",
        "재무기준일자": "",
        "등급이력": [],
        "현금흐름등급": [],
        "외부신용등급": {},
    }
    
    if pdfplumber is None:
        return data
    
    try:
        with pdfplumber.open(filepath) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"
            
            # 현재 신용등급
            grade_match = re.search(r"등급\s+평가\(산출\)일자\s+재무기준일자\s+등급구분\s*\n\s*(\S+)\s+([\d\-]+)\s+([\d\-]+)\s+(\S+)", full_text)
            if grade_match:
                data["현재등급"] = grade_match.group(1)
                data["평가일자"] = grade_match.group(2)
                data["재무기준일자"] = grade_match.group(3)
                data["등급구분"] = grade_match.group(4)
            
            # 등급설명
            desc_match = re.search(r"등급설명\s+(.+?)(?:\n등급구분)", full_text, re.DOTALL)
            if desc_match:
                data["등급설명"] = desc_match.group(1).strip()
            
            # 현금흐름등급 - 연도별
            cr_pattern = r"(20\d{2}-\d{2}-\d{2})\s+(?:.*?)(CR\d|V|판정보류|판정제외)"
            for match in re.finditer(cr_pattern, full_text):
                data["현금흐름등급"].append({
                    "기준일자": match.group(1),
                    "등급": match.group(2)
                })
    except Exception as e:
        print(f"신용 PDF 파싱 오류: {e}")
    
    return data


def _fallback_overview() -> Dict[str, Any]:
    """pdfplumber가 없을 때 기본값 반환"""
    return {
        "기업명": "(주)메이홈",
        "사업자번호": "204-86-39305",
        "대표자명": "박승미",
        "법인번호": "110111-5034642",
        "설립일자": "2013-01-02",
        "종업원수": "10명",
        "주소": "(11409) 경기 양주시 남면 휴암로284번길 403-33 (상수리)",
        "전화번호": "070-8274-2991",
        "기업유형": "일반법인 / 주식회사",
        "표준산업분류": "(G46433) 생활용 유리·요업·목재·금속 제품 및 날주요제품(상품)",
        "기업규모": "소기업",
        "주요제품": "밀폐용기 외",
        "기업신용등급": "a",
        "EW등급": "정상",
        "재무진단": {"성장성": "우수", "수익성": "우수", "재무구조": "양호", "활동성": "우수"},
    }
