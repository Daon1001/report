"""
CRETOP PDF 파서: 기업 브리핑(개요) 및 신용등급 보고서에서 데이터 추출
"""
import re
import os
from typing import Dict, Any, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def parse_company_overview(filepath: str) -> Dict[str, Any]:
    """개요.pdf (기업 브리핑 보고서) 파싱 - 다양한 기업에 대응"""
    if pdfplumber is None or filepath is None:
        return _fallback_overview()
    
    data = {
        "기업명": "", "사업자번호": "", "대표자명": "", "법인번호": "",
        "설립일자": "", "종업원수": "", "주소": "", "전화번호": "",
        "기업유형": "", "표준산업분류": "", "기업규모": "", "주요제품": "",
        "기업신용등급": "", "EW등급": "",
        "신용정보": {}, "주요주주": [], "주요구매처": [], "주요판매처": [],
        "기업인증": {}, "산업재산권": {}, "재무상태표": {}, "손익계산서": {},
        "재무비율": {}, "재무진단": {},
    }
    
    try:
        with pdfplumber.open(filepath) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"
            
            if not full_text.strip():
                return data
            
            # ── 기업 기본정보 ──
            patterns = {
                "사업자번호": r"사업자번호\s+([\d\-]+)",
                "법인번호": r"법인\(주민\)번호\s+([\d\-]+)",
                "대표자명": r"대표자명\s+(\S+)",
                "설립일자": r"설립일자\s+([\d\-]+)",
                "종업원수": r"종업원수\s+(\d+\s*명)",
                "전화번호": r"전화번호\s+([\d\-]+)",
                "기업규모": r"기업규모\s+(\S+)",
            }
            for key, pattern in patterns.items():
                match = re.search(pattern, full_text)
                if match:
                    data[key] = match.group(1).strip()
            
            # 기업명 - (주)XXX 또는 주식회사XXX 패턴
            name_match = re.search(r"\(주\)\S+", full_text)
            if name_match:
                data["기업명"] = name_match.group(0)
            else:
                name_match2 = re.search(r"기업명\s*[:：]?\s*(\S+)", full_text)
                if name_match2:
                    data["기업명"] = name_match2.group(1)
            
            # 기업유형
            type_match = re.search(r"기업유형/형태\s+(.+?)(?:\s+전화번호|\n)", full_text)
            if type_match:
                data["기업유형"] = type_match.group(1).strip()
            
            # 주소 - 더 범용적 패턴
            addr_match = re.search(r"주소\(도로명\)\s+(.+?)(?:\s+주요제품|\s+전화번호|\n)", full_text)
            if not addr_match:
                addr_match = re.search(r"주소\(도로명\)\s+(\(.+?\).*?)(?:\n)", full_text)
            if addr_match:
                data["주소"] = addr_match.group(1).strip()
            
            # 표준산업분류
            ind_match = re.search(r"표준산업분류\(11차\)\s+(\(.+?\).+?)(?:\s+주요제품|\n)", full_text)
            if ind_match:
                data["표준산업분류"] = ind_match.group(1).strip()
            
            # 주요제품
            prod_match = re.search(r"주요제품\(상품\)\s+(.+?)(?:\n)", full_text)
            if prod_match:
                data["주요제품"] = prod_match.group(1).strip()
            
            # 기업신용등급 - 소문자/대문자 모두 (a, bb-, BBB+ 등)
            grade_match = re.search(r"평가일자\s*:\s*([\d\-]+)\s*\n?\s*결산일자\s*:\s*([\d\-]+)", full_text)
            if grade_match:
                data["신용등급_평가일자"] = grade_match.group(1)
                data["신용등급_결산일자"] = grade_match.group(2)
            
            # 신용등급 값 추출 (게이지 옆의 등급 텍스트)
            credit_grade = re.search(r"\n\s*([a-dA-D]{1,3}[+-]?)\s*\n.*?평가일자", full_text, re.DOTALL)
            if credit_grade:
                data["기업신용등급"] = credit_grade.group(1).strip()
            else:
                # bb-, a, bbb+ 등 패턴
                credit_grade2 = re.search(r"기업신용등급.*?\n\s*([a-dA-D]{1,3}[+-]?)\s*\n", full_text, re.DOTALL)
                if credit_grade2:
                    data["기업신용등급"] = credit_grade2.group(1).strip()
            
            # EW등급 - 정상/주의/경고/위험/유보 모두 인식
            ew_match = re.search(r"(정상|주의|경고|위험|유보)\s*[▼▲►▶]?\s*\n.*?기준일자", full_text, re.DOTALL)
            if ew_match:
                data["EW등급"] = ew_match.group(1)
            else:
                ew_match2 = re.search(r"EW\s*등급.*?(정상|주의|경고|위험|유보)", full_text, re.DOTALL)
                if ew_match2:
                    data["EW등급"] = ew_match2.group(1)
                else:
                    # 단순 검색
                    for ew_val in ["정상", "유보", "주의", "경고", "위험"]:
                        if ew_val in full_text:
                            data["EW등급"] = ew_val
                            break
            
            # 재무진단 등급 - "보통 이하" 등도 인식
            diag_patterns = {
                "성장성": r"성장성\s+(우수|양호|보통[^\n]*|미흡|열위)",
                "수익성": r"수익성\s+(우수|양호|보통[^\n]*|미흡|열위)",
                "재무구조": r"재무구조\s+(우수|양호|보통[^\n]*|미흡|열위)",
                "부채상환능력": r"부채상환능력\s+(우수|양호|보통[^\n]*|미흡|열위|등급없음)",
                "활동성": r"활동성\s+(우수|양호|보통[^\n]*|미흡|열위)",
            }
            for key, pattern in diag_patterns.items():
                match = re.search(pattern, full_text)
                if match:
                    val = match.group(1).strip()
                    # "보통 이하" → "보통"으로 정규화
                    if "보통" in val:
                        val = "보통"
                    data["재무진단"][key] = val
    
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
    """기본 빈 값 반환"""
    return {
        "기업명": "", "사업자번호": "", "대표자명": "", "법인번호": "",
        "설립일자": "", "종업원수": "", "주소": "", "전화번호": "",
        "기업유형": "", "표준산업분류": "", "기업규모": "", "주요제품": "",
        "기업신용등급": "", "EW등급": "", "재무진단": {},
    }


def parse_company_overview_excel(filepath: str) -> Dict[str, Any]:
    """기업개요 엑셀(report.xls) 파싱 — CRETOP 엑셀 다운로드 형식"""
    import pandas as pd
    import numpy as np
    
    data = _fallback_overview()
    
    try:
        # xls → libreoffice 변환이 필요할 수 있음. 일단 pandas로 시도
        try:
            xls = pd.ExcelFile(filepath)
        except (ImportError, Exception):
            # xlrd가 없거나 xls 읽기 실패 → libreoffice로 변환
            import subprocess, tempfile, glob
            tmp_dir = tempfile.mkdtemp()
            subprocess.run(['libreoffice', '--headless', '--convert-to', 'xlsx', 
                          '--outdir', tmp_dir, filepath], 
                         capture_output=True, timeout=30)
            candidates = glob.glob(tmp_dir + '/*.xlsx')
            if candidates:
                xls = pd.ExcelFile(candidates[0])
            else:
                xls = pd.ExcelFile(filepath)
        
        sheets = xls.sheet_names
        
        # 모든 시트의 텍스트를 합쳐서 검색
        all_cells = []
        for sheet in sheets:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            for r in range(df.shape[0]):
                for c in range(df.shape[1]):
                    val = df.iloc[r, c]
                    if pd.notna(val):
                        all_cells.append((str(val).strip(), r, c, sheet, df))
        
        # 키-값 쌍 추출 (키 셀 옆이나 같은 행에서 값 찾기)
        def find_value_after(keyword):
            for val, r, c, sheet, df in all_cells:
                # 키워드가 셀에 포함되어 있으면
                if keyword in val:
                    # 같은 셀에 값도 있는 경우 ("사업자번호 215-88-00406")
                    cleaned = val.replace(keyword, '').strip(' :：-·・').strip()
                    if cleaned and cleaned != val and len(cleaned) > 1:
                        return cleaned
                    # 같은 행의 오른쪽 셀들 탐색 (최대 15칸)
                    for cc in range(c+1, min(c+15, df.shape[1])):
                        rv = df.iloc[r, cc]
                        if pd.notna(rv):
                            sv = str(rv).strip()
                            if sv and sv != keyword and len(sv) > 0:
                                return sv
            return ""
        
        # (주)XXX 패턴으로 기업명 직접 찾기
        company_name = ""
        for val, r, c, s, d in all_cells:
            if val.startswith("(주)") and len(val) > 3:
                company_name = val
                break
        
        data["기업명"] = company_name or find_value_after("기업명")
        
        # 사업자번호 - "215-88-00406" 패턴 직접 찾기
        import re as _re
        bizno = find_value_after("사업자번호")
        if not bizno or len(bizno) < 10:
            for val, r, c, s, d in all_cells:
                if _re.match(r'^\d{3}-\d{2}-\d{5}$', val):
                    bizno = val
                    break
        data["사업자번호"] = bizno
        data["대표자명"] = find_value_after("대표자명")
        data["법인번호"] = find_value_after("법인(주민)번호")
        data["설립일자"] = find_value_after("설립일자")
        data["종업원수"] = find_value_after("종업원수")
        data["주소"] = find_value_after("주소(도로명)")
        data["전화번호"] = find_value_after("전화번호")
        data["기업유형"] = find_value_after("기업유형/형태")
        data["표준산업분류"] = find_value_after("표준산업분류")
        data["기업규모"] = find_value_after("기업규모")
        data["주요제품"] = find_value_after("주요제품(상품)")
        
        # 재무진단
        for diag in ["성장성", "수익성", "재무구조", "부채상환능력", "활동성"]:
            val = find_value_after(diag)
            if val and val in ["우수", "양호", "보통", "미흡", "열위", "보통 이하", "등급없음"]:
                if "보통" in val:
                    val = "보통"
                data["재무진단"][diag] = val
        
        # 신용등급 (bb-, a, BBB+ 등) - 텍스트 먼저 시도
        for val, r, c, s, d in all_cells:
            if re.match(r'^[a-dA-D]{1,3}[+-]?$', val) and len(val) <= 4:
                data["기업신용등급"] = val
                break
        
        # EW등급 - '법인등기정보 정상'과 구분
        for val, r, c, s, d in all_cells:
            if val in ("정상", "유보", "주의", "경고", "위험"):
                row_texts = set()
                for cc in range(d.shape[1]):
                    rv = d.iloc[r, cc]
                    if pd.notna(rv):
                        row_texts.add(str(rv).strip())
                if '법인등기정보' in ' '.join(row_texts):
                    continue
                data["EW등급"] = val
                break
        
        # ── 이미지 추출 (신용등급 게이지, EW등급, 재무진단) ──
        import base64, zipfile
        import xml.etree.ElementTree as _ET
        
        try:
            # xlsx 파일 경로 결정
            xlsx_path = None
            if hasattr(xls, 'io') and isinstance(xls.io, str):
                xlsx_path = xls.io
            else:
                xlsx_path = filepath
            
            # xlsx가 아닌 경우 (xls) → libreoffice 변환 시도
            if not xlsx_path.lower().endswith('.xlsx'):
                import subprocess, tempfile, glob
                tmp_dir = tempfile.mkdtemp()
                try:
                    subprocess.run(
                        ['libreoffice', '--headless', '--convert-to', 'xlsx', '--outdir', tmp_dir, xlsx_path],
                        capture_output=True, timeout=60
                    )
                    converted = glob.glob(tmp_dir + '/*.xlsx')
                    if converted:
                        xlsx_path = converted[0]
                except Exception:
                    pass
            
            # xlsx는 ZIP 파일 → zipfile로 직접 이미지 추출 (openpyxl 불필요!)
            if xlsx_path and zipfile.is_zipfile(xlsx_path):
                with zipfile.ZipFile(xlsx_path, 'r') as zf:
                    # 시트별 이미지 매핑 구축
                    sheet_images_map = {}  # {sheet_num: [(rId, image_path, size), ...]}
                    
                    for sheet_num in range(1, 20):
                        sheet_rels = f'xl/worksheets/_rels/sheet{sheet_num}.xml.rels'
                        if sheet_rels not in zf.namelist():
                            continue
                        
                        # 시트의 drawing 파일 찾기
                        rels_xml = zf.read(sheet_rels).decode('utf-8')
                        rels_root = _ET.fromstring(rels_xml)
                        drawing_file = None
                        for rel in rels_root:
                            target = rel.attrib.get('Target', '')
                            if 'drawing' in target.lower():
                                drawing_file = 'xl/' + target.lstrip('../')
                                break
                        
                        if not drawing_file:
                            continue
                        
                        # drawing의 이미지 관계 파싱
                        dr_rels = drawing_file.rsplit('/', 1)[0] + '/_rels/' + drawing_file.rsplit('/', 1)[1] + '.rels'
                        if dr_rels not in zf.namelist():
                            continue
                        
                        dr_xml = zf.read(dr_rels).decode('utf-8')
                        dr_root = _ET.fromstring(dr_xml)
                        
                        imgs = []
                        for rel in dr_root:
                            target = rel.attrib.get('Target', '')
                            if 'image' in target.lower():
                                img_path = 'xl/' + target.lstrip('../')
                                if img_path in zf.namelist():
                                    img_data = zf.read(img_path)
                                    imgs.append((rel.attrib.get('Id', ''), img_data, len(img_data)))
                        
                        if imgs:
                            sheet_images_map[sheet_num] = imgs
                    
                    # Sheet2 (index 2): 기업프로필 → 신용등급 게이지 + EW등급
                    if 2 in sheet_images_map:
                        imgs = sheet_images_map[2]
                        # 로고(45KB)와 배경(600KB+) 제외, 3~20KB만
                        small = [(rid, d, s) for rid, d, s in imgs if 3000 < s < 20000]
                        if len(small) >= 2:
                            data["신용등급_이미지"] = base64.b64encode(small[0][1]).decode('utf-8')
                            data["EW등급_이미지"] = base64.b64encode(small[1][1]).decode('utf-8')
                        elif len(small) == 1:
                            data["신용등급_이미지"] = base64.b64encode(small[0][1]).decode('utf-8')
                    
                    # 마지막 시트: 재무진단 (도넛 차트 5개, 3~15KB)
                    last_sheet = max(sheet_images_map.keys()) if sheet_images_map else 0
                    if last_sheet > 2 and last_sheet in sheet_images_map:
                        imgs = sheet_images_map[last_sheet]
                        donuts = [(rid, d, s) for rid, d, s in imgs if 3000 < s < 15000]
                        diag_keys = ["성장성", "수익성", "재무구조", "부채상환능력", "활동성"]
                        for idx, dk in enumerate(diag_keys):
                            if idx < len(donuts):
                                data.setdefault("재무진단_이미지", {})[dk] = base64.b64encode(donuts[idx][1]).decode('utf-8')
        
        except Exception as e:
            import traceback
            print(f"이미지 추출 오류: {e}")
            traceback.print_exc()
    
    except Exception as e:
        print(f"기업개요 엑셀 파싱 오류: {e}")
    
    return data


def parse_credit_report_excel(filepath: str) -> Dict[str, Any]:
    """신용등급 엑셀(report__1_.xls) 파싱"""
    import pandas as pd
    import numpy as np
    
    data = {
        "현재등급": "", "등급설명": "", "등급구분": "",
        "평가일자": "", "재무기준일자": "",
        "등급이력": [], "현금흐름등급": [], "외부신용등급": {},
    }
    
    try:
        try:
            xls = pd.ExcelFile(filepath)
        except ImportError:
            import subprocess, tempfile, os
            tmp_dir = tempfile.mkdtemp()
            subprocess.run(['libreoffice', '--headless', '--convert-to', 'xlsx',
                          '--outdir', tmp_dir, filepath],
                         capture_output=True, timeout=30)
            import glob
            candidates = glob.glob(tmp_dir + '/*.xlsx')
            xls = pd.ExcelFile(candidates[0]) if candidates else None
            if not xls:
                return data
        
        all_cells = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            for r in range(df.shape[0]):
                for c in range(df.shape[1]):
                    val = df.iloc[r, c]
                    if pd.notna(val):
                        all_cells.append((str(val).strip(), r, c, sheet, df))
        
        # 등급 이력 (bb-, a 등 + 날짜 패턴)
        for val, r, c, sheet, df in all_cells:
            if re.match(r'^[a-dA-D]{1,3}[+-]?$', val) and len(val) <= 4:
                if not data["현재등급"]:
                    data["현재등급"] = val
                # 같은 행에서 날짜 찾기
                dates = []
                for cc in range(df.shape[1]):
                    cv = df.iloc[r, cc]
                    if pd.notna(cv) and re.match(r'20\d{2}-\d{2}-\d{2}', str(cv).strip()):
                        dates.append(str(cv).strip())
                if dates:
                    data["등급이력"].append({
                        "등급": val,
                        "평가일자": dates[0] if dates else "",
                        "재무기준일자": dates[1] if len(dates) > 1 else "",
                    })
        
        # 등급설명
        for val, r, c, s, d in all_cells:
            if "채무상환능력" in val:
                data["등급설명"] = val
                break
        
        # 평가일자
        for val, r, c, s, d in all_cells:
            if "평가일자" in val and ":" in val:
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', val)
                if date_match:
                    data["평가일자"] = date_match.group(1)
            elif "결산일자" in val and ":" in val:
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', val)
                if date_match:
                    data["재무기준일자"] = date_match.group(1)
        
        # 현금흐름등급
        for val, r, c, sheet, df in all_cells:
            if re.match(r'^CR\d$', val):
                # 같은 행에서 날짜 찾기
                for cc in range(df.shape[1]):
                    cv = df.iloc[r, cc]
                    if pd.notna(cv) and re.match(r'20\d{2}-\d{2}-\d{2}', str(cv).strip()):
                        data["현금흐름등급"].append({
                            "기준일자": str(cv).strip(),
                            "등급": val
                        })
                        break
    
    except Exception as e:
        print(f"신용등급 엑셀 파싱 오류: {e}")
    
    return data


# ════════════════════════════════════════════════════════════════
# 세무조정계산서 파서 (크레탑 대안)
# ════════════════════════════════════════════════════════════════
def is_tax_adjustment_pdf(filepath: str) -> bool:
    """업로드된 PDF가 세무조정계산서인지 자동 판별 (법인/개인 구분 없이 세무조정계산서 형태인지만 확인)"""
    if pdfplumber is None or not os.path.exists(filepath):
        return False
    try:
        with pdfplumber.open(filepath) as pdf:
            # 처음 5페이지 안에 키워드 확인
            sample_text = ""
            for i in range(min(5, len(pdf.pages))):
                sample_text += (pdf.pages[i].extract_text() or "") + "\n"
            keywords = ["법인세과세표준", "세무조정", "표준재무상태표", "법인세과세표준및세액조정"]
            return any(kw in sample_text for kw in keywords)
    except:
        return False


def is_corporate_tax_adjustment_pdf(filepath: str) -> bool:
    """업로드된 PDF가 '법인용' 세무조정계산서인지 자동 판별.
    개인사업자 키워드(종합소득세 등)가 없고 법인 키워드(법인세과세표준)는 있어야 함.
    """
    if pdfplumber is None or not os.path.exists(filepath):
        return False
    try:
        with pdfplumber.open(filepath) as pdf:
            sample = ""
            for i in range(min(15, len(pdf.pages))):
                sample += (pdf.pages[i].extract_text() or "") + "\n"
            has_corporate = "법인세과세표준" in sample
            has_personal = "종합소득세" in sample and "과세표준확정신고" in sample
            return has_corporate and not has_personal
    except:
        return False


def _parse_amount(s):
    """'1,677,377,118' 또는 '(1,234)' 같은 문자열을 숫자(원 단위)로 변환"""
    if not s: return None
    s = str(s).strip()
    if not s or s == '-': return None
    is_negative = s.startswith('(') and s.endswith(')')
    s = s.strip('()').replace(',', '').replace(' ', '')
    try:
        v = int(s) if s.isdigit() else float(s)
        return -v if is_negative else v
    except:
        return None


def _find_section_pages(pdf):
    """세무조정계산서에서 재무상태표·손익계산서·제조원가·기업개요 페이지 위치 찾기.
    결산서 양식(2개년 비교)을 우선 사용. 표준양식·합계양식·목차는 제외."""
    sections = {"bs": [], "is": [], "mfg": [], "overview": []}
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        first_300 = text[:300]
        
        # 법인세과세표준및세액신고서 (기업정보) - 가장 먼저 체크 (제외 키워드와 무관)
        # 실제 양식은 "사업자등록번호" + "법인등록번호" + "법 인 명" 모두 포함
        if (not sections["overview"] and 
            "법인세과세표준및세액신고서" in text and 
            "사업자등록번호" in text and 
            "법인등록번호" in text and
            "목차" not in first_300[:50]):
            sections["overview"].append(i)
            continue
        
        # 제외 키워드: 목차, 표준재무상태표, 합계표준재무상태표
        is_excluded = (
            "목차" in first_300[:50] or
            "표준재무상태표" in first_300 or
            "합계표준재무상태표" in first_300 or
            "법인세법시행규칙" in first_300[:200]
        )
        if is_excluded:
            continue
        
        # 결산서 양식 재무상태표
        if ("재 무 상 태 표" in first_300 or "재무상태표" in first_300):
            if "회사명" in text[:500] or "회 사 명" in text[:500]:
                sections["bs"].append(i)
        
        # 결산서 양식 손익계산서
        if ("손 익 계 산 서" in first_300 or "손익계산서" in first_300):
            if "회사명" in text[:500] or "회 사 명" in text[:500]:
                sections["is"].append(i)
        
        # 제조원가명세서
        if "제 조 원 가 명 세 서" in first_300 or "제조원가명세서" in first_300:
            if "회사명" in text[:500] or "회 사 명" in text[:500]:
                sections["mfg"].append(i)
    
    return sections


def parse_tax_adjustment_pdf(filepath: str) -> Dict[str, Any]:
    """
    세무조정계산서 PDF에서 BS/IS/제조원가/기업정보 통합 추출
    반환: {"company": {...}, "bs": {...}, "isc": {...}, "mfg": {...}, "credit": {...}}
    """
    result = {
        "company": {"기업명": "", "사업자번호": "", "법인번호": "", "대표자명": "", 
                    "설립일자": "", "주소": "", "전화번호": "", "종업원수": "",
                    "기업신용등급": "-", "현금흐름등급": "-"},
        "bs": {"years": []},
        "isc": {"years": []},
        "mfg": {"years": []},
        "credit": {"현재등급": "-", "현금흐름등급": []},
    }
    
    if pdfplumber is None or not os.path.exists(filepath):
        return result
    
    try:
        with pdfplumber.open(filepath) as pdf:
            sections = _find_section_pages(pdf)
            
            # ── 1) 기업 기본정보 ── (법인세과세표준및세액신고서)
            if sections["overview"]:
                t = pdf.pages[sections["overview"][0]].extract_text() or ""
                # 사업자등록번호: "① 사업자등록번호 795-86-02089"
                m = re.search(r"사업자등록번호\s+(\d{3}-\d{2}-\d{5})", t)
                if m: result["company"]["사업자번호"] = m.group(1)
                # 법인번호: "② 법인등록번호 164811-0144159"
                m = re.search(r"법인등록번호\s+(\d{6}-\d{7})", t)
                if m: result["company"]["법인번호"] = m.group(1)
                # 기업명: "③ 법 인 명 (주)라인글로벌"
                m = re.search(r"법\s*인\s*명\s+([^\s\④\d]+)", t)
                if m: result["company"]["기업명"] = m.group(1).strip()
                # 전화번호
                m = re.search(r"전\s*화\s*번\s*호\s+([\d\-]+)", t)
                if m: result["company"]["전화번호"] = m.group(1)
                # 대표자: "⑤ 대 표 자 성 명 이믿음"
                m = re.search(r"대\s*표\s*자\s*성\s*명\s+([가-힣]{2,5})", t)
                if m: result["company"]["대표자명"] = m.group(1)
                # 소재지: "⑦ 소 재 지 충청남도..."
                m = re.search(r"소\s*재\s*지\s+([가-힣\d\s,()]+?)(?=⑧|업\s*태|\n)", t)
                if m: result["company"]["주소"] = m.group(1).strip()
                # 업태: "⑧ 업 태 정보통신업/도소매업"
                m = re.search(r"업\s*태\s+([^\s⑨\n]+)", t)
                if m: result["company"]["기업유형"] = m.group(1)
                # 사업연도: "⑪ 사 업 연 도 2025.01.01~2025.12.31"
                m = re.search(r"사\s*업\s*연\s*도\s+(\d{4})\.\d{2}\.\d{2}", t)
                if m: result["company"]["설립일자"] = "-"  # 세무조정계산서엔 설립일자 없음, 사업연도만
            
            # ── 2) 재무상태표 ──
            bs_text = ""
            for pidx in sections["bs"][:3]:  # 최대 3페이지
                bs_text += (pdf.pages[pidx].extract_text() or "") + "\n"
            
            if bs_text:
                # 연도 추출: "제 5(당)기 2025년" "제 4(전)기 2024년"
                year_matches = re.findall(r"제\s*\d+\s*\(?(?:당|전|전전)?\)?기\s*(\d{4})년", bs_text)
                years_list = list(dict.fromkeys(year_matches))[:3]  # 중복 제거, 최대 3개
                if not years_list:
                    # fallback: 그냥 4자리 연도
                    yrs = re.findall(r"(\d{4})년", bs_text)
                    years_list = list(dict.fromkeys(yrs))[:3]
                
                years_normalized = [f"{y}-12-31" for y in years_list]
                result["bs"]["years"] = years_normalized
                if result["company"]["기업명"] == "":
                    # BS에서 회사명 다시 시도
                    m = re.search(r"회\s*사\s*명\s*[:：]\s*((?:\(주\))?\S+)", bs_text)
                    if m: result["company"]["기업명"] = m.group(1)
                
                # 항목별 추출 - "항목명 ... 숫자1 숫자2" 패턴
                # 한글 사이 공백 제거 후 매칭
                def _clean_line(line):
                    """한글 사이 공백 정규화: '자 산 총 계' → '자산총계'"""
                    return re.sub(r'(?<=[가-힣])\s+(?=[가-힣])', '', line)
                
                bs_items_map = {
                    "유동자산": ["유동자산"],
                    "당좌자산": ["당좌자산"],
                    "재고자산": ["재고자산"],
                    "비유동자산": ["비유동자산"],
                    "투자자산": ["투자자산"],
                    "유형자산": ["유형자산"],
                    "무형자산": ["무형자산"],
                    "자산총계": ["자산총계"],
                    "유동부채": ["유동부채"],
                    "비유동부채": ["비유동부채"],
                    "부채총계": ["부채총계"],
                    "자본금": ["자본금"],
                    "자본잉여금": ["자본잉여금"],
                    "이익잉여금": ["이익잉여금"],
                    "자본총계": ["자본총계"],
                    "매출채권": ["매출채권"],
                    "현금및현금성자산": ["현금및현금성자산", "현금성자산"],
                    "매입채무": ["매입채무"],
                    "단기차입금": ["단기차입금"],
                    "장기차입금": ["장기차입금"],
                }
                
                lines = bs_text.split("\n")
                for line in lines:
                    cleaned = _clean_line(line)
                    for canonical, variants in bs_items_map.items():
                        for v in variants:
                            if v in cleaned:
                                # 숫자 추출 (괄호 안 음수 포함)
                                nums = re.findall(r"\(?[\d,]+\)?", line)
                                amounts = []
                                for n in nums:
                                    parsed = _parse_amount(n)
                                    if parsed is not None and abs(parsed) >= 100:  # 너무 작은 숫자는 코드일 가능성
                                        amounts.append(parsed)
                                if amounts and canonical not in result["bs"]:
                                    result["bs"][canonical] = {}
                                    for i, yr in enumerate(years_normalized):
                                        if i < len(amounts):
                                            result["bs"][canonical][yr] = amounts[i]
                                break
            
            # ── 3) 손익계산서 ──
            is_text = ""
            for pidx in sections["is"][:3]:
                is_text += (pdf.pages[pidx].extract_text() or "") + "\n"
            
            if is_text:
                # IS의 연도가 BS와 다를 수 있으니 같은 연도 사용
                if not result["bs"]["years"]:
                    year_matches = re.findall(r"제\s*\d+\s*\(?(?:당|전|전전)?\)?기\s*(\d{4})년", is_text)
                    years_list = list(dict.fromkeys(year_matches))[:3]
                    years_normalized = [f"{y}-12-31" for y in years_list]
                else:
                    years_normalized = result["bs"]["years"]
                
                result["isc"]["years"] = years_normalized
                
                is_items_map = {
                    "매출액": ["매출액"],
                    "매출원가": ["매출원가"],
                    "매출총이익": ["매출총이익"],
                    "판매비와관리비": ["판매비와관리비", "판매비와관리비"],
                    "판관비": ["판매비와관리비"],
                    "영업이익": ["영업이익"],
                    "영업외수익": ["영업외수익"],
                    "영업외비용": ["영업외비용"],
                    "세전이익": ["법인세차감전이익", "법인세차감전순이익"],
                    "법인세": ["법인세등"],
                    "당기순이익": ["당기순이익"],
                    "급여": ["임원급여"],
                    "감가상각비": ["감가상각비"],
                    "지급임차료": ["지급임차료"],
                    "보험료": ["보험료"],
                    "복리후생비": ["복리후생비"],
                    "접대비": ["접대비", "기업업무추진비"],
                    "운반비": ["운반비"],
                    "세금과공과": ["세금과공과"],
                    "통신비": ["통신비"],
                    "수도광열비": ["수도광열비"],
                    "외주비": ["외주비"],
                }
                
                def _clean_line(line):
                    return re.sub(r'(?<=[가-힣])\s+(?=[가-힣])', '', line)
                
                lines = is_text.split("\n")
                for line in lines:
                    cleaned = _clean_line(line)
                    for canonical, variants in is_items_map.items():
                        for v in variants:
                            if v in cleaned:
                                nums = re.findall(r"\(?[\d,]+\)?", line)
                                amounts = []
                                for n in nums:
                                    parsed = _parse_amount(n)
                                    if parsed is not None and abs(parsed) >= 100:
                                        amounts.append(parsed)
                                if amounts and canonical not in result["isc"]:
                                    result["isc"][canonical] = {}
                                    for i, yr in enumerate(years_normalized):
                                        if i < len(amounts):
                                            result["isc"][canonical][yr] = amounts[i]
                                break
            
            # ── 4) 제조원가명세서 (있으면) ──
            if sections["mfg"]:
                mfg_text = pdf.pages[sections["mfg"][0]].extract_text() or ""
                result["mfg"]["years"] = result["bs"]["years"]
                # 추후 확장: 원재료비, 노무비, 경비 등
            else:
                result["mfg"]["years"] = result["bs"]["years"]
    
    except Exception as e:
        import traceback
        print(f"세무조정계산서 파싱 오류: {e}")
        print(traceback.format_exc())
    
    # ── alias 키 추가: calculate_ratios 호환성 ──
    # calculate_ratios는 "자산", "부채", "자본" 키로 찾음
    if "자산총계" in result["bs"]: result["bs"]["자산"] = result["bs"]["자산총계"]
    if "부채총계" in result["bs"]: result["bs"]["부채"] = result["bs"]["부채총계"]
    if "자본총계" in result["bs"]: result["bs"]["자본"] = result["bs"]["자본총계"]
    
    return result


# ════════════════════════════════════════════════════════════════
# 세무조정계산서 - 심층 분석 데이터 추출
# ════════════════════════════════════════════════════════════════
def extract_tax_deep_analysis(filepath: str) -> Dict[str, Any]:
    """
    세무조정계산서에서 심층 분석용 데이터 추출:
    - 법인세 조정 결과 (산출세액·공제감면·차감세액)
    - 소득금액조정 (익금산입·손금불산입 총액)
    - 업무용 차량 비용·손금불산입
    - 접대비 한도·초과액
    - 중소기업 자격
    - 통합고용세액공제 현황
    """
    result = {
        "법인세": {
            "당기순이익": None,
            "익금산입_손금불산입": None,
            "손금산입_익금불산입": None,
            "각사업연도소득금액": None,
            "이월결손금": None,
            "과세표준": None,
            "세율": None,
            "산출세액": None,
            "공제감면세액": None,
            "차감세액": None,
            "가산세": None,
            "원천납부세액": None,
            "차감납부세액": None,
        },
        "세무조정_익금산입": [],   # [{과목, 금액}]
        "세무조정_손금산입": [],
        "업무용차량": {
            "보유대수": 0,
            "총비용": None,
            "감가상각비": None,
            "유류비": None,
            "보험료": None,
            "수선비": None,
            "기타": None,
            "손금불산입": None,
            "업무사용비율": None,
        },
        "접대비": {
            "한도액": None,
            "지출액": None,
            "손금불산입": None,
        },
        "중소기업": {
            "해당여부": None,
            "업종": "",
        },
        "통합고용세액공제": {
            "신청여부": False,
            "공제금액": None,
        },
    }
    
    if pdfplumber is None or not os.path.exists(filepath):
        return result
    
    try:
        with pdfplumber.open(filepath) as pdf:
            # ── 1) 법인세과세표준및세액조정계산서 (p.7 부근) ──
            for i, page in enumerate(pdf.pages[:15]):
                text = page.extract_text() or ""
                if "법인세과세표준및세액조정계산서" in text and "결산서상당기순손익" in text:
                    # 주요 금액 추출 - 번호+숫자 패턴
                    patterns = {
                        "당기순이익": r"결산서상당기순손익\s*0?1\s+([\d,]+)",
                        "익금산입_손금불산입": r"익금산입\s*0?2\s+([\d,]+)",
                        "각사업연도소득금액": r"각사업연도소득금액\s*\([\=\+\-\s]+\)\s*0?6\s+([\d,]+)",
                        "이월결손금": r"이\s*월\s*결\s*손\s*금\s*0?7\s+([\d,]+)",
                        "과세표준": r"과\s*세\s*표\s*준\s*\([\+\-\s]+\)\s*10\s+([\d,]+)",
                        "산출세액": r"산\s*출\s*세\s*액\s*12\s+([\d,]+)",
                        "공제감면세액": r"공\s*제\s*감\s*면\s*세\s*액\s*1[7-9]\s+([\d,]+)",
                        "차감세액": r"차\s*감\s*세\s*액\s*18\s+([\d,]+)",
                        "가산세": r"가\s*산\s*세\s*액\s*20\s+([\d,]+)",
                        "원천납부세액": r"원천납부세액\s*24\s+([\d,]+)",
                    }
                    for key, pat in patterns.items():
                        m = re.search(pat, text)
                        if m:
                            result["법인세"][key] = _parse_amount(m.group(1))
                    
                    # 세율: "세 율 11 9" 형태
                    m = re.search(r"세\s*율\s*11\s+(\d+)", text)
                    if m:
                        result["법인세"]["세율"] = int(m.group(1))
                    
                    # 차감납부세액 (음수 가능 - 환급)
                    m = re.search(r"차감납부세액\s*[\(\)\+\-\s]*49\s+(-?[\d,]+)", text)
                    if m:
                        result["법인세"]["차감납부세액"] = _parse_amount(m.group(1))
                    break
            
            # ── 2) 소득금액조정합계표 (p.26 부근) ──
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if "소득금액조정합계표" in text[:200]:
                    # "잡손실 331,873 ... 기타사외유출 500" 형태로 익금산입 항목 추출
                    lines = text.split("\n")
                    in_income = False  # 익금산입 구간인지
                    for line in lines:
                        if "익금산입" in line and "손금불산입" in line:
                            in_income = True
                            continue
                        if "손금산입" in line and "익금불산입" in line:
                            in_income = False
                            continue
                        # "항목명 금액 ... 처분 코드" 패턴
                        m = re.match(r"^([가-힣\s]+)\s+([\d,]+)\s+", line.strip())
                        if m and "합계" not in m.group(1):
                            amount = _parse_amount(m.group(2))
                            if amount and amount > 0:
                                entry = {"과목": m.group(1).strip(), "금액": amount}
                                if in_income:
                                    result["세무조정_익금산입"].append(entry)
                                else:
                                    result["세무조정_손금산입"].append(entry)
                    break
            
            # ── 3) 업무용승용차 (p.37 부근) ──
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if "업무용승용차관련비용명세서" in text[:200]:
                    # 차량 대수 (차종 등장 횟수로 추정)
                    car_lines = re.findall(r"\d+호\s+\d+\s+\S+", text)
                    result["업무용차량"]["보유대수"] = len(car_lines) if car_lines else 1
                    
                    # 합계 금액 (가장 큰 금액들)
                    amounts = re.findall(r"([\d,]+)\s*$", text, re.MULTILINE)
                    big_amounts = [_parse_amount(a) for a in amounts if _parse_amount(a) and _parse_amount(a) > 1000000]
                    if big_amounts:
                        # 가장 큰 값을 합계로 가정
                        result["업무용차량"]["총비용"] = max(big_amounts) if big_amounts else None
                    
                    # 업무사용비율
                    m = re.search(r"100\.0000", text)
                    if m:
                        result["업무용차량"]["업무사용비율"] = 100.0
                    break
            
            # ── 4) 중소기업기준검토표 (p.48 부근) ──
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if "중소기업기준검토표" in text[:200]:
                    if "중소기업" in text:
                        result["중소기업"]["해당여부"] = True
                    # 업종 추출
                    m = re.search(r"업\s*종\s*([가-힣\s\,\/]+)", text)
                    if m:
                        result["중소기업"]["업종"] = m.group(1).strip()[:30]
                    break
            
            # ── 5) 통합고용세액공제 (p.66 부근) ──
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if "통합고용세액공제공제세액계산서" in text[:200]:
                    result["통합고용세액공제"]["신청여부"] = True
                    # 공제금액 추출 시도
                    m = re.search(r"공\s*제\s*세\s*액\s+([\d,]+)", text)
                    if m:
                        result["통합고용세액공제"]["공제금액"] = _parse_amount(m.group(1))
                    break
    
    except Exception as e:
        import traceback
        print(f"세무 심층분석 오류: {e}")
        print(traceback.format_exc())
    
    # 컨설팅 심층 분석 데이터 추가
    try:
        from parsers.consulting_deep import extract_consulting_deep_analysis
        result["consulting"] = extract_consulting_deep_analysis(filepath, is_personal=False)
    except Exception as e:
        print(f"컨설팅 분석 추가 오류: {e}")
        result["consulting"] = {}
    
    return result


# ════════════════════════════════════════════════════════════════
# 개인사업자 세무조정계산서 (종합소득세 신고서) 파서
# ════════════════════════════════════════════════════════════════
def is_personal_tax_adjustment_pdf(filepath: str) -> bool:
    """업로드된 PDF가 '개인사업자' 세무조정계산서인지 자동 판별.
    - 법인용: '법인세과세표준' 키워드
    - 개인용: '종합소득세' + '표준손익계산서' 키워드 (법인 키워드 없음)
    """
    if pdfplumber is None or not os.path.exists(filepath):
        return False
    try:
        with pdfplumber.open(filepath) as pdf:
            sample = ""
            for i in range(min(15, len(pdf.pages))):
                sample += (pdf.pages[i].extract_text() or "") + "\n"
            has_personal = (
                ("종합소득세" in sample)
                and (("표준손익계산서" in sample) or ("사업소득명세서" in sample))
            )
            has_corporate = "법인세과세표준" in sample
            return has_personal and not has_corporate
    except Exception:
        return False


def _colon_amount(s):
    """'  :960:297:664' 같은 콜론 구분 금액에서 숫자만 모아 정수로 반환"""
    if not s:
        return None
    nums = re.findall(r'\d+', s)
    if not nums:
        return None
    try:
        return int(''.join(nums))
    except Exception:
        return None


def _label_amount_in_line(line, label):
    """한 라인 안에서 라벨이 처음 나온 위치부터 첫 코드(2자리)+금액 패턴을 찾아 반환.
    표준재무상태표/표준손익계산서의 좌우 2단 레이아웃을 위해 라인 단위로 정확히 매치.
    
    예) 'Ⅰ. 유동자산 01 : :960:297:664 (2) 장기투자증권 32 : : : : 0'
        라벨 'Ⅰ. 유동자산' 다음 코드 '01' + 콜론 구분 '960:297:664' 만 추출
    예) '(1) 장기금융상품 31 : : : : 0자산 총계 (Ⅰ+Ⅱ) 62 : 2:959:470:276'
        라벨 '자산 총계' 뒤에 '(Ⅰ+Ⅱ) 62 : 2:959:470:276' 가 와도 잡음
    """
    idx = line.find(label)
    if idx < 0:
        return None
    sub = line[idx + len(label):]
    # 라벨 뒤에는 괄호 안 부가설명(Ⅰ+Ⅱ 등)이 올 수 있음 → 첫 코드(2자리)+금액 찾기
    m = re.search(r'(\d{2})\s+([:\s\d]+?)(?=\s+[\(\[]?\d?[\)\]]?\s*[가-힣Ⅰ-Ⅹⅰ-ⅹ]|\d{1,2}\s*\.|$)', sub)
    if m:
        return _colon_amount(m.group(2))
    return None


def parse_personal_tax_adjustment_pdf(filepath: str) -> Dict[str, Any]:
    """
    개인사업자 세무조정계산서 PDF에서 사업자정보/BS/IS/제조원가 통합 추출.
    반환 구조는 법인용 parse_tax_adjustment_pdf와 호환 (company/bs/isc/mfg/credit 키 동일).
    """
    result = {
        "company": {
            "기업명": "",
            "사업자번호": "",
            "법인번호": "",        # 개인은 없음
            "대표자명": "",
            "설립일자": "",
            "주소": "",
            "전화번호": "",
            "휴대전화": "",
            "종업원수": "",
            "기업유형": "개인사업자",
            "업태": "",
            "주업종코드": "",
            "기장의무": "",
            "신고유형": "",
            "기업신용등급": "-",
            "현금흐름등급": "-",
        },
        "bs": {"years": []},
        "isc": {"years": []},
        "mfg": {"years": []},
        "credit": {"현재등급": "-", "현금흐름등급": []},
        "is_personal": True,
    }
    if pdfplumber is None or not os.path.exists(filepath):
        return result

    try:
        with pdfplumber.open(filepath) as pdf:
            # 0) 표지에서 과세연도(당기) 추출 — 한글/한자 양식 모두 대응
            cy = None
            cover = pdf.pages[0].extract_text() or ""
            # (1) 한글 양식: "...부터 2025년..." 종료 연도
            m = re.search(r'(\d{4})\s*년\s*\d{1,2}\s*[월月]\s*\d{1,2}\s*[일日]\s*부터\s*(\d{4})\s*년', cover)
            if m:
                cy = int(m.group(2))
            # (2) 한자 양식: "至 2025年 12月 31日" (종료=당기)
            if cy is None:
                m = re.search(r'[至~]\s*(\d{4})\s*[年년]', cover)
                if m:
                    cy = int(m.group(1))
            # (3) 폴백: "自 2025年" 시작연도
            if cy is None:
                m = re.search(r'[自]\s*(\d{4})\s*[年년]', cover)
                if m:
                    cy = int(m.group(1))
            # (4) 최후 폴백: 표지에 있는 가장 큰 4자리 연도
            if cy is None:
                yrs = [int(y) for y in re.findall(r'(20\d{2})\s*[年년]?', cover)]
                cy = max(yrs) if yrs else None
            if cy:
                result["bs"]["years"] = [cy]
                result["isc"]["years"] = [cy]
                result["mfg"]["years"] = [cy]
                year_labels = [f"{cy}년"]
                result["bs"]["year_labels"] = year_labels
                result["isc"]["year_labels"] = year_labels
                result["mfg"]["year_labels"] = year_labels

            # 1) 핵심 페이지 인덱스 찾기
            # 목차/총괄표 페이지에는 페이지 번호와 함께 라벨이 나열되므로 제외해야 함
            idx_filing = None      # 종합소득세신고서
            idx_biz = None         # 사업소득명세서
            idx_bs = None          # 표준재무상태표
            idx_is = None          # 표준손익계산서
            idx_cost = None        # 표준원가명세서
            idx_smb = None         # 중소기업기준검토표
            idx_ent = None         # 기업업무추진비
            idx_car = None         # 업무용승용차
            for i, page in enumerate(pdf.pages):
                full = page.extract_text() or ""
                head = full[:200]
                # 목차/총괄표 페이지는 스킵 (여러 서식명이 페이지 번호와 함께 나열)
                if "목차" in head or "세무조정계산서총괄표" in head:
                    continue
                # 종합소득세신고서: 본문이어야 함
                if idx_filing is None and "종합소득세" in head and "과세표준확정신고" in head:
                    idx_filing = i
                # 사업소득명세서: 헤더에 명시되고 ⑤ 등 항목 코드가 본문에 있어야 함
                if idx_biz is None and "사업소득명세서" in head and ("⑤" in full or "사업자등록번호" in full):
                    idx_biz = i
                # 표준재무상태표: 헤더에 명시되고 본문에 코드 01,02 등이 있어야 함
                if idx_bs is None and "표준재무상태표" in head and "유동자산" in full:
                    idx_bs = i
                if idx_is is None and "표준손익계산서" in head and "매출액" in full:
                    idx_is = i
                if idx_cost is None and "표준원가명세서" in head and ("재료비" in full or "제조원가" in full):
                    idx_cost = i
                if idx_smb is None and "중소기업기준검토표" in head and "중소기업" in full:
                    idx_smb = i
                if idx_ent is None and ("기업업무추진비" in head and "조정명세서" in head):
                    idx_ent = i
                if idx_car is None and "업무용승용차" in head and "관련비용" in full:
                    idx_car = i

            # 2) 종합소득세 신고서 - 대표자 기본정보 + 세금 데이터
            tax_summary = {}
            if idx_filing is not None:
                t = pdf.pages[idx_filing].extract_text() or ""
                # 성명
                m = re.search(r'①\s*성\s*명\s+([가-힣]{2,5})', t) or re.search(r'성\s*명\s+([가-힣]{2,5})', t)
                if m:
                    result["company"]["대표자명"] = m.group(1)
                # 사업자번호 - 신고서 페이지에는 세무대리인 번호가 먼저 나오므로
                # 사업소득명세서(⑤ 사 업 자 등 록 번 호)에서 추출 (아래 4번에서 처리)
                pass
                # 휴대전화 - 글자 사이 공백/하이픈 모두 처리
                m = re.search(r'⑥\s*휴\s*대\s*전\s*화\s+([\d\-\s]+?)(?=⑦|전자|\n)', t)
                if m:
                    result["company"]["휴대전화"] = re.sub(r'\s+', '', m.group(1)).strip('-')
                # 주소
                m = re.search(r'③\s*주\s+소\s+([^\n]+?)(?=④|\n)', t)
                if m:
                    result["company"]["주소"] = m.group(1).strip()
                # 기장의무
                if "복식부기의무자" in t:
                    result["company"]["기장의무"] = "복식부기"
                elif "간편장부" in t:
                    result["company"]["기장의무"] = "간편장부"
                # 신고유형
                if "외부조정" in t:
                    result["company"]["신고유형"] = "외부조정"
                elif "성실신고확인" in t:
                    result["company"]["신고유형"] = "성실신고확인"
                elif "자기조정" in t:
                    result["company"]["신고유형"] = "자기조정"

                # 세금 항목들 (라벨 + 코드 번호) — 라인 단위로 매치
                def _find_by_code(label_chars, code):
                    """'종 합 소 득 금 액 19 241,240,704' 같은 라인에서 금액 추출.
                    라벨 글자 사이 공백, 괄호 안 숫자(과세표준(19-20) 같은 형태) 모두 허용."""
                    label_pat = r'\s*'.join(list(label_chars))
                    line_pat = label_pat + r'.*?(?<!\d)' + str(code) + r'(?!\d)\s+([\d,]+)'
                    mm = re.search(line_pat, t)
                    return _parse_amount(mm.group(1)) if mm else None

                tax_summary["종합소득금액"] = _find_by_code("종합소득금액", 19)
                tax_summary["소득공제"] = _find_by_code("소득공제", 20)
                tax_summary["과세표준"] = _find_by_code("과세표준", 21)
                tax_summary["산출세액"] = _find_by_code("산출세액", 23)
                tax_summary["세액감면"] = _find_by_code("세액감면", 24)
                tax_summary["세액공제"] = _find_by_code("세액공제", 25)

            # 3) 사업소득명세서 - 상호/사업장/매출/필요경비
            if idx_biz is not None:
                t = pdf.pages[idx_biz].extract_text() or ""
                # 상호
                m = re.search(r'④\s*상\s*\n?\s*호\s+([^\s\n]+)', t)
                if m:
                    result["company"]["기업명"] = m.group(1).strip()
                # 사업자번호 (⑤ 사 업 자 등 록 번 호 134-25-43756)
                m = re.search(r'⑤[^\d]{0,40}(\d{3}\s*-\s*\d{2}\s*-\s*\d{5})', t)
                if m:
                    result["company"]["사업자번호"] = re.sub(r'\s+', '', m.group(1))
                # 주업종코드
                m = re.search(r'⑧\s*주\s*업\s*종\s*코\s*드\s+(\d{6})', t)
                if m:
                    result["company"]["주업종코드"] = m.group(1)
                # 사업장 소재지 (없으면 대표자 주소 사용)
                m = re.search(r'소재지\s+([^\n]+?)(?=국내|국외|\n)', t)
                if m and not result["company"]["주소"]:
                    result["company"]["주소"] = m.group(1).strip()
                # 총수입금액 / 필요경비 / 소득금액
                m = re.search(r'⑨[^\d]*?([\d,]+)', t)
                if m: tax_summary["총수입금액"] = _parse_amount(m.group(1))
                m = re.search(r'⑩\s*필\s*요\s*경\s*비[^\d]*([\d,]+)', t)
                if m: tax_summary["필요경비"] = _parse_amount(m.group(1))
                m = re.search(r'⑪\s*소\s*득\s*금\s*액[^\d]*([\d,]+)', t)
                if m: tax_summary["사업소득금액"] = _parse_amount(m.group(1))

            # 4) 표준재무상태표 (좌우 2단 레이아웃 → 라인별 처리)
            bs_raw = {}
            if idx_bs is not None:
                bs_text = ""
                for p in range(idx_bs, min(idx_bs + 3, len(pdf.pages))):
                    page_t = pdf.pages[p].extract_text() or ""
                    if p > idx_bs and "표준손익계산서" in page_t[:200]:
                        break
                    bs_text += page_t + "\n"
                
                # 라인 단위로 라벨 매치 (왼쪽 단의 첫 매치를 사용)
                # 핵심 항목 키: 표시명 매핑 (라벨 변형 패턴 포함)
                bs_items = [
                    ("유동자산", ["Ⅰ. 유동자산", "Ⅰ.유동자산"]),
                    ("비유동자산", ["Ⅱ.비유동자산", "Ⅱ. 비유동자산"]),
                    ("자산총계", ["자산 총계", "자산총계"]),
                    ("유동부채", ["Ⅰ. 유동부채", "Ⅰ.유동부채"]),
                    ("비유동부채", ["Ⅱ. 비유동부채", "Ⅱ.비유동부채"]),
                    ("부채총계", ["부채총계", "부채 총계"]),
                    ("자본금", ["Ⅲ. 자본금", "Ⅲ.자본금"]),
                    ("이익잉여금", ["Ⅴ.이익잉여금", "Ⅴ. 이익잉여금", "Ⅳ.이익잉여금", "Ⅳ. 이익잉여금"]),
                    ("자본총계", ["자본 총계", "자본총계"]),
                ]
                for key, label_variants in bs_items:
                    found = False
                    for label in label_variants:
                        if found:
                            break
                        for line in bs_text.split("\n"):
                            if label in line:
                                v = _label_amount_in_line(line, label)
                                if v is not None:
                                    bs_raw[key] = v
                                    found = True
                                    break

            # BS dict 구성 (당기만 1개년)
            if bs_raw and cy:
                result["bs"][cy] = {
                    "유동자산": bs_raw.get("유동자산", 0),
                    "비유동자산": bs_raw.get("비유동자산", 0),
                    "자산총계": bs_raw.get("자산총계", 0),
                    "유동부채": bs_raw.get("유동부채", 0),
                    "비유동부채": bs_raw.get("비유동부채", 0),
                    "부채총계": bs_raw.get("부채총계", 0),
                    "자본금": bs_raw.get("자본금", 0),
                    "자본잉여금": 0,
                    "이익잉여금": bs_raw.get("이익잉여금", 0),
                    "자본총계": bs_raw.get("자본총계", 0),
                }
                # alias 키 (호환)
                result["bs"][cy]["자산"] = result["bs"][cy]["자산총계"]
                result["bs"][cy]["부채"] = result["bs"][cy]["부채총계"]
                result["bs"][cy]["자본"] = result["bs"][cy]["자본총계"]

            # 5) 표준손익계산서
            is_raw = {}
            if idx_is is not None:
                is_text = ""
                for p in range(idx_is, min(idx_is + 3, len(pdf.pages))):
                    page_t = pdf.pages[p].extract_text() or ""
                    if p > idx_is and "표준원가명세서" in page_t[:200]:
                        break
                    is_text += page_t + "\n"
                
                is_items = [
                    ("매출액", ["Ⅰ.매출액", "Ⅰ. 매출액"]),
                    ("매출원가", ["Ⅱ.매출원가", "Ⅱ. 매출원가"]),
                    ("매출총이익", ["Ⅲ.매출총이익", "Ⅲ. 매출총이익"]),
                    ("판매관리비", ["Ⅳ.판매비와관리비", "Ⅳ. 판매비와관리비",
                                  "Ⅳ.판매비와 관리비", "Ⅳ. 판매비와 관리비"]),
                    ("영업이익", ["Ⅴ.영업손익", "Ⅴ. 영업손익",
                                "V.영업손익", "V. 영업손익"]),
                    ("영업외수익", ["Ⅵ.영업외수익", "Ⅵ. 영업외수익",
                                  "VI.영업외수익", "VI. 영업외수익"]),
                    ("영업외비용", ["Ⅶ.영업외비용", "Ⅶ. 영업외비용",
                                  "VII.영업외비용", "VII. 영업외비용"]),
                    ("당기순이익", ["Ⅷ.당기순손익", "Ⅷ. 당기순손익",
                                  "VIII.당기순손익", "VIII. 당기순손익"]),
                ]
                for key, label_variants in is_items:
                    found = False
                    for label in label_variants:
                        if found:
                            break
                        for line in is_text.split("\n"):
                            if label in line:
                                v = _label_amount_in_line(line, label)
                                if v is not None:
                                    is_raw[key] = v
                                    found = True
                                    break

            if is_raw and cy:
                result["isc"][cy] = dict(is_raw)
                # alias 키
                result["isc"][cy]["매출"] = is_raw.get("매출액", 0)
                result["isc"][cy]["판매비와관리비"] = is_raw.get("판매관리비", 0)
                result["isc"][cy]["당기순손익"] = is_raw.get("당기순이익", 0)

            # 6) 표준원가명세서 (제조업만)
            if idx_cost is not None:
                cost_text = pdf.pages[idx_cost].extract_text() or ""
                # 당기제품제조원가 / 재료비 등 핵심 항목만
                mfg_raw = {}
                for key, label in [
                    ("당기제품제조원가", "당기제품제조원가"),
                    ("재료비", "Ⅰ.재료비"),
                    ("노무비", "Ⅱ.노무비"),
                    ("경비", "Ⅲ.경비"),
                ]:
                    for line in cost_text.split("\n"):
                        if label in line:
                            v = _label_amount_in_line(line, label)
                            if v is not None:
                                mfg_raw[key] = v
                                break
                if mfg_raw and cy:
                    result["mfg"][cy] = mfg_raw

            # 7) 추가 데이터를 _personal_tax 키에 보관 (심층진단/리포트용)
            result["_personal_tax"] = {
                "사업기간": f"{cy}.01.01 ~ {cy}.12.31" if cy else "",
                **tax_summary,
            }

            # 8) 다중 사업장 분리 추출 (사업장이 여러 개일 때 사업장별 섹션용)
            try:
                from parsers.multi_business_parser import parse_businesses
                result["businesses"] = parse_businesses(pdf, cy)
            except Exception as _e:
                print(f"다중 사업장 파싱 실패(무시): {_e}")
                result["businesses"] = []

    except Exception as e:
        import traceback
        print(f"개인사업자 PDF 파싱 오류: {e}")
        print(traceback.format_exc())

    return result


def extract_personal_tax_deep_analysis(filepath: str) -> Dict[str, Any]:
    """개인사업자 세무조정계산서 심층 분석.
    법인용 extract_tax_deep_analysis와 호환되는 구조로 반환하되,
    '법인세' 키 자리에 종합소득세 정보를 채워 같은 페이지 템플릿 재활용 가능하게 함.
    """
    result = {
        "법인세": {  # 같은 키 사용 (개인=종소세지만 템플릿 호환)
            "당기순이익": None,
            "익금산입_손금불산입": None,
            "손금산입_익금불산입": None,
            "각사업연도소득금액": None,
            "이월결손금": None,
            "과세표준": None,
            "세율": None,
            "산출세액": None,
            "공제감면세액": None,
            "차감세액": None,
            "가산세": None,
            "원천납부세액": None,
            "총부담세액": None,
        },
        "세무조정_익금산입": [],
        "세무조정_손금불산입": [],
        "업무용차량": {"보유대수": 0, "총비용": None, "업무사용비율": None,
                    "임직원전용보험가입": None, "운행기록작성": None,
                    "손금산입액": None, "손금불산입액": None},
        "접대비": {"한도액": None, "지출액": None, "손금불산입": None},
        "중소기업": {"해당여부": False, "업종": ""},
        "통합고용세액공제": {"신청여부": False, "공제금액": None},
        "is_personal": True,
        "_personal_extra": {
            "총수입금액": None,
            "필요경비": None,
            "사업소득금액": None,
            "종합소득금액": None,
            "소득공제": None,
            "세액감면": None,
            "세액공제": None,
            "신고유형": "",
            "기장의무": "",
        },
    }

    if pdfplumber is None or not os.path.exists(filepath):
        return result

    try:
        with pdfplumber.open(filepath) as pdf:
            # 종합소득세 신고서 페이지 찾기
            for i, page in enumerate(pdf.pages):
                head = (page.extract_text() or "")[:200]
                if "종합소득세" in head and "과세표준확정신고" in head:
                    t = page.extract_text() or ""
                    
                    def _find_by_code(label_chars, code):
                        """라벨 + 코드 + 금액 견고한 매치 (괄호숫자 무관)"""
                        label_pat = r'\s*'.join(list(label_chars))
                        line_pat = label_pat + r'.*?(?<!\d)' + str(code) + r'(?!\d)\s+([\d,]+)'
                        mm = re.search(line_pat, t)
                        return _parse_amount(mm.group(1)) if mm else None

                    result["법인세"]["과세표준"] = _find_by_code("과세표준", 21)
                    result["법인세"]["산출세액"] = _find_by_code("산출세액", 23)
                    감면 = _find_by_code("세액감면", 24) or 0
                    공제 = _find_by_code("세액공제", 25) or 0
                    result["법인세"]["공제감면세액"] = (감면 or 0) + (공제 or 0)
                    
                    종합소득 = _find_by_code("종합소득금액", 19)
                    소득공제 = _find_by_code("소득공제", 20)
                    result["_personal_extra"]["종합소득금액"] = 종합소득
                    result["_personal_extra"]["소득공제"] = 소득공제
                    result["_personal_extra"]["세액감면"] = 감면
                    result["_personal_extra"]["세액공제"] = 공제
                    
                    # 차감세액 = 산출 - 감면 - 공제
                    san = result["법인세"]["산출세액"] or 0
                    result["법인세"]["차감세액"] = max(san - (감면 or 0) - (공제 or 0), 0)
                    
                    # 신고유형/기장의무
                    if "외부조정" in t: result["_personal_extra"]["신고유형"] = "외부조정"
                    elif "성실신고확인" in t: result["_personal_extra"]["신고유형"] = "성실신고확인"
                    elif "자기조정" in t: result["_personal_extra"]["신고유형"] = "자기조정"
                    if "복식부기의무자" in t: result["_personal_extra"]["기장의무"] = "복식부기"
                    elif "간편장부" in t: result["_personal_extra"]["기장의무"] = "간편장부"
                    break

            # 사업소득명세서 페이지
            for i, page in enumerate(pdf.pages):
                head = (page.extract_text() or "")[:200]
                if "사업소득명세서" in head:
                    t = page.extract_text() or ""
                    m = re.search(r'⑨[^\d]*?([\d,]+)', t)
                    if m: result["_personal_extra"]["총수입금액"] = _parse_amount(m.group(1))
                    m = re.search(r'⑩\s*필\s*요\s*경\s*비[^\d]*([\d,]+)', t)
                    if m: result["_personal_extra"]["필요경비"] = _parse_amount(m.group(1))
                    m = re.search(r'⑪\s*소\s*득\s*금\s*액[^\d]*([\d,]+)', t)
                    if m: result["_personal_extra"]["사업소득금액"] = _parse_amount(m.group(1))
                    break

            # 표준손익계산서에서 당기순이익 가져오기
            for i, page in enumerate(pdf.pages):
                full = page.extract_text() or ""
                head = full[:200]
                if "목차" in head or "세무조정계산서총괄표" in head:
                    continue
                if "표준손익계산서" in head and "매출액" in full:
                    is_text = ""
                    for p in range(i, min(i + 3, len(pdf.pages))):
                        ptxt = pdf.pages[p].extract_text() or ""
                        if p > i and "표준원가명세서" in ptxt[:200]:
                            break
                        is_text += ptxt + "\n"
                    for line in is_text.split("\n"):
                        for label in ["Ⅷ.당기순손익", "Ⅷ. 당기순손익",
                                      "VIII.당기순손익", "VIII. 당기순손익"]:
                            if label in line:
                                v = _label_amount_in_line(line, label)
                                if v:
                                    result["법인세"]["당기순이익"] = v
                                    break
                        if result["법인세"]["당기순이익"]:
                            break
                    if result["법인세"]["당기순이익"]:
                        break

            # 중소기업기준검토표 → 중소기업 여부
            for i, page in enumerate(pdf.pages):
                head = (page.extract_text() or "")[:200]
                if "중소기업기준검토표" in head:
                    t = page.extract_text() or ""
                    if "중소기업" in t and ("해당" in t or "여" in t):
                        result["중소기업"]["해당여부"] = True
                    # 업종
                    m = re.search(r'주\s*업\s*종\s*[^\n]{0,30}?([가-힣\w]+업)', t)
                    if m:
                        result["중소기업"]["업종"] = m.group(1)[:20]
                    break

            # 업무용승용차 페이지
            for i, page in enumerate(pdf.pages):
                head = (page.extract_text() or "")[:200]
                if "업무용승용차" in head:
                    t = page.extract_text() or ""
                    if "업무전용자동차보험" in t or "임직원전용보험" in t:
                        result["업무용차량"]["임직원전용보험가입"] = True
                    if "운행기록" in t and ("작성" in t or "있음" in t):
                        result["업무용차량"]["운행기록작성"] = True

                    # 차량 대수: 차량번호 패턴(예: 64보6764, 12나3456) 등장 개수
                    plates = re.findall(r'\d{2,3}[가-힣]\d{4}', t)
                    plates = list(dict.fromkeys(plates))  # 중복 제거
                    if plates:
                        result["업무용차량"]["보유대수"] = len(plates)

                    # 업무사용비율 (100/365 형태가 보이면 100%)
                    if "100" in t and "365" in t:
                        result["업무용차량"]["업무사용비율"] = 100.0

                    # 연간 총비용(합계): 페이지 내 가장 큰 금액(6자리 이상)
                    nums = [_parse_amount(x) for x in re.findall(r'[\d,]{6,}', t)]
                    nums = [n for n in nums if n and n > 100000]
                    if nums:
                        result["업무용차량"]["총비용"] = max(nums)
                    break

            # 접대비(기업업무추진비) 한도/지출/손금불산입
            for i, page in enumerate(pdf.pages):
                head = (page.extract_text() or "")[:200]
                if "기업업무추진비" in head and "조정명세서" in head:
                    t = page.extract_text() or ""
                    tns = re.sub(r'\s+', '', t)  # 공백 제거본 (라벨 글자 사이 공백 대응)
                    m = re.search(r'조정대상기업업무추진비해당금액[^\d]*([\d,]+)', tns)
                    if m:
                        result["접대비"]["지출액"] = _parse_amount(m.group(1))
                    m = re.search(r'기업업무추진비한도액합계[^\d]*([\d,]+)', tns)
                    if m:
                        result["접대비"]["한도액"] = _parse_amount(m.group(1))
                    m = re.search(r'기업업무추진비한도초과액[^\d]*([\d,]+)', tns)
                    if m:
                        result["접대비"]["손금불산입"] = _parse_amount(m.group(1))
                    break

    except Exception as e:
        import traceback
        print(f"개인사업자 심층분석 오류: {e}")
        print(traceback.format_exc())

    # 컨설팅 심층 분석 데이터 추가
    try:
        from parsers.consulting_deep import extract_consulting_deep_analysis
        result["consulting"] = extract_consulting_deep_analysis(filepath, is_personal=True)
    except Exception as e:
        print(f"컨설팅 분석 추가 오류: {e}")
        result["consulting"] = {}

    return result
