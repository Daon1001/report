# 🔐 사용자 승인 시스템 설정 가이드

## 개요

이 앱은 **관리자 승인제**로 운영됩니다.
- 관리자 이메일: `incheon00@gmail.com`
- 사용자가 로그인 페이지에서 승인 요청 → 관리자가 승인 → 사용 가능
- 승인 DB는 **GitHub Gist**에 저장되어 Streamlit 재배포/GitHub 수정 시에도 유지됩니다.

## 설정 방법 (최초 1회)

### 1단계: GitHub Personal Access Token 발급

1. [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens) 접속
2. **Generate new token (classic)** 클릭
3. Note: `streamlit-report-auth`
4. Scopes: ✅ `gist` 만 체크
5. **Generate token** 클릭 → 토큰 복사 (한 번만 보임!)

### 2단계: GitHub Gist 생성 (사용자 DB)

1. [gist.github.com](https://gist.github.com) 접속
2. Filename: `users_db.json`
3. 내용:
```json
{
  "users": {
    "incheon00@gmail.com": {
      "name": "관리자",
      "org": "",
      "status": "approved",
      "requested_at": "2025-01-01T00:00:00",
      "approved_at": "2025-01-01T00:00:00",
      "role": "admin"
    }
  },
  "updated_at": "2025-01-01T00:00:00"
}
```
4. **Create secret gist** 클릭
5. URL에서 Gist ID 복사 (예: `https://gist.github.com/username/abc123def456` → `abc123def456`)

### 3단계: Streamlit Cloud에 Secrets 등록

1. [share.streamlit.io](https://share.streamlit.io)에서 앱의 **Settings** 클릭
2. **Secrets** 탭에서 아래 내용 입력:

```toml
[gist]
id = "여기에_Gist_ID_붙여넣기"
token = "여기에_Personal_Access_Token_붙여넣기"
```

3. **Save** 클릭

### 완료!

이제 앱을 실행하면:
1. `incheon00@gmail.com`으로 로그인 → 바로 관리자로 접속
2. 다른 사용자가 승인 요청 → 관리자 패널에서 승인/거부
3. 승인된 사용자는 이메일만 입력하면 바로 로그인

## 작동 방식

```
[사용자] 이메일 입력 → 승인 요청
    ↓
[GitHub Gist] users_db.json에 "pending" 상태로 저장
    ↓
[관리자] 관리자 패널에서 승인 클릭
    ↓
[GitHub Gist] 해당 사용자 "approved"로 변경
    ↓
[사용자] 다시 이메일 입력 → 메인 페이지 접속!
```

## 데이터 영속성

| 상황 | 데이터 유지 여부 |
|------|---------------|
| Streamlit 앱 재시작 | ✅ 유지 (Gist에 저장) |
| GitHub 코드 수정 후 재배포 | ✅ 유지 (Gist에 저장) |
| Streamlit Cloud 새로 배포 | ✅ 유지 (Gist에 저장) |
| Gist 직접 삭제 | ❌ 데이터 손실 |

## 관리자 기능

- 승인 대기 목록에서 원클릭 승인/거부
- 전체 사용자 목록 확인
- **사용자 목록 엑셀 다운로드** (백업용)
- 사용자 삭제 (관리자 계정은 삭제 불가)

## Gist 없이 로컬에서 테스트

Gist 설정 없이도 앱은 작동합니다 (session_state fallback).
단, 브라우저를 닫으면 데이터가 초기화됩니다.
```bash
streamlit run app.py
```
