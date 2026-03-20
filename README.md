# 📊 재무경영진단 리포트 생성기

CRETOP 기업 데이터와 재무제표 엑셀 파일을 업로드하면, **전문 재무경영진단 리포트 PDF**를 자동으로 생성하는 Streamlit 웹 애플리케이션입니다.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 주요 기능

- **엑셀/PDF 파일 업로드** → 자동 데이터 파싱
- **재무비율 자동 계산** (안정성, 수익성, 성장성, 활동성)
- **비상장주식 기업가치 평가** (상증세법상 보충적 평가방법)
- **신용등급 관리** 현황 요약
- **PDF 리포트 자동 생성 및 다운로드**

## 📋 입력 파일

### 필수 (엑셀)
| 파일명 | 내용 |
|--------|------|
| `ETFI112E1.xlsx` | 재무상태표 (3개년) |
| `ETFI112E1__1_.xlsx` | 손익계산서 (3개년) |
| `ETFI112E1__5_.xlsx` | 제조원가명세서 (3개년) |

### 선택 (PDF)
| 파일명 | 내용 |
|--------|------|
| `개요.pdf` | CRETOP 기업 브리핑 보고서 |
| `신용.pdf` | CRETOP 기업 신용등급 보고서 |

## 📊 생성되는 리포트 구성

1. **기업재무분석**
   - 기업개요 (기업정보, 재무진단 결과)
   - 요약 재무상태표
   - 요약 손익계산서
   - 재무현황 개요
   - 재무비율 분석 (안정성/수익성/성장성/활동성)
   - 주요 경비율 분석

2. **기업가치평가**
   - 비상장주식 가치평가
   - 연도별 기업가치 예상 추이

3. **신용등급 관리**
   - 기업신용등급 현황
   - 현금흐름등급 이력

## 🚀 설치 및 실행

### 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/financial-report-generator.git
cd financial-report-generator

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# WeasyPrint 시스템 의존성 (Ubuntu/Debian)
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Streamlit 앱 실행
streamlit run app.py
```

### Streamlit Cloud 배포

1. 이 저장소를 GitHub에 Push합니다.
2. [share.streamlit.io](https://share.streamlit.io)에 접속합니다.
3. **New app** → GitHub 저장소 선택 → `app.py` 지정
4. **Deploy** 클릭

> ⚠️ Streamlit Cloud에서 WeasyPrint를 사용하려면 `packages.txt`에 시스템 패키지가 필요합니다.

## 📁 프로젝트 구조

```
financial-report-generator/
├── app.py                      # Streamlit 메인 앱
├── requirements.txt            # Python 의존성
├── packages.txt                # 시스템 패키지 (Streamlit Cloud)
├── .streamlit/
│   └── config.toml             # Streamlit 설정
├── parsers/
│   ├── __init__.py
│   ├── excel_parser.py         # 엑셀 파일 파싱
│   ├── pdf_parser.py           # PDF 파일 파싱
│   └── financial_ratios.py     # 재무비율 계산 & 기업가치 평가
├── report/
│   ├── __init__.py
│   ├── html_template.py        # HTML 리포트 템플릿
│   └── pdf_generator.py        # PDF 생성 (WeasyPrint)
└── README.md
```

## ⚙️ 기술 스택

| 분류 | 기술 |
|------|------|
| **프론트엔드** | Streamlit |
| **데이터 파싱** | pandas, openpyxl, pdfplumber |
| **PDF 생성** | WeasyPrint (HTML → PDF) |
| **재무 분석** | 자체 계산 모듈 (Python) |

## 📐 재무비율 계산 기준

### 안정성 지표
- **부채비율** = 부채총계 / 자본총계 × 100
- **유동비율** = 유동자산 / 유동부채 × 100

### 수익성 지표
- **영업이익률** = 영업이익 / 매출액 × 100
- **ROE** = 당기순이익 / 자기자본 × 100
- **ROA** = 당기순이익 / 총자산 × 100

### 성장성 지표
- **매출액증가율** = (당기매출액 - 전기매출액) / 전기매출액 × 100

### 활동성 지표
- **총자산회전율** = 매출액 / 총자산
- **재고자산회전율** = 매출액 / 재고자산

## 📈 기업가치 평가 방법

비상장주식 **상증세법상 보충적 평가방법** 적용:

```
1주당 평가액 = (순자산가치 × 2 + 순손익가치 × 3) ÷ 5
```

- **순자산가치** = 자본총계 / 발행주식수
- **순손익가치** = 가중평균순손익 / 환원율(10%) / 발행주식수
- 가중평균순손익: 3개년 가중평균 (최근 3, 중간 2, 과거 1)

## 📄 라이선스

MIT License
