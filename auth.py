"""
사용자 인증/승인 모듈
- GitHub Gist를 영구 DB로 사용 (Streamlit 재배포해도 데이터 유지)
- 관리자: incheon00@gmail.com
- Gist API Token은 st.secrets에 저장
"""
import streamlit as st
import json
import requests
import datetime
from typing import Dict, List, Optional

ADMIN_EMAIL = "incheon00@gmail.com"

# 🚀 추가: 무조건 승인 처리할 일반 사용자 이메일 목록을 여기에 작성하세요.
ALLOWED_USERS = [
    "ykim116@naver.com",
    "suphong@naver.com",
    "poiemaesthesia@naver.com",
    "ygkim576459@naver.com",
    "tchope0501@naver.com",
    "tomaspjy@gmail.com",
    "john.lee4004@gmail.com",
    "chotan486@naver.com",
]


def _get_gist_config():
    """Gist ID와 Token을 secrets에서 가져오기"""
    try:
        gist_id = st.secrets["gist"]["id"]
        gist_token = st.secrets["gist"]["token"]
        return gist_id, gist_token
    except Exception:
        return None, None


def _load_users_from_gist() -> Dict:
    """Gist에서 사용자 DB 로드"""
    gist_id, token = _get_gist_config()
    if not gist_id or not token:
        return _load_users_local()
    
    try:
        headers = {"Authorization": f"token {token}"}
        resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            content = data["files"]["users_db.json"]["content"]
            return json.loads(content)
    except Exception as e:
        st.warning(f"Gist 연결 실패, 로컬 모드로 전환: {e}")
    
    return _load_users_local()


def _save_users_to_gist(users: Dict) -> bool:
    """Gist에 사용자 DB 저장"""
    gist_id, token = _get_gist_config()
    if not gist_id or not token:
        return _save_users_local(users)
    
    try:
        headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "files": {
                "users_db.json": {
                    "content": json.dumps(users, ensure_ascii=False, indent=2)
                }
            }
        }
        resp = requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=headers, json=payload, timeout=10
        )
        return resp.status_code == 200
    except Exception:
        return _save_users_local(users)


def _load_users_local() -> Dict:
    """로컬 파일 fallback (개발용)"""
    try:
        if "users_db" in st.session_state:
            return st.session_state["users_db"]
    except:
        pass
    return {"users": {}, "updated_at": ""}


def _save_users_local(users: Dict) -> bool:
    """로컬 session_state fallback"""
    st.session_state["users_db"] = users
    return True


def get_all_users() -> Dict:
    """전체 사용자 목록"""
    return _load_users_from_gist()


def request_approval(email: str, name: str, org: str) -> bool:
    """승인 요청 등록"""
    # 🚀 강제 승인 명단 및 관리자 예외 처리
    if email == ADMIN_EMAIL or email in ALLOWED_USERS:
        return True
        
    users = _load_users_from_gist()
    
    if email == ADMIN_EMAIL:
        users["users"][email] = {
            "name": name,
            "org": org,
            "status": "approved",
            "requested_at": datetime.datetime.now().isoformat(),
            "approved_at": datetime.datetime.now().isoformat(),
            "role": "admin"
        }
    elif email not in users["users"]:
        users["users"][email] = {
            "name": name,
            "org": org,
            "status": "pending",
            "requested_at": datetime.datetime.now().isoformat(),
            "approved_at": None,
            "role": "user"
        }
    else:
        # 이미 등록된 사용자
        return users["users"][email]["status"] == "approved"
    
    users["updated_at"] = datetime.datetime.now().isoformat()
    _save_users_to_gist(users)
    return users["users"][email]["status"] == "approved"


def approve_user(email: str) -> bool:
    """사용자 승인 (관리자 전용)"""
    users = _load_users_from_gist()
    if email in users["users"]:
        users["users"][email]["status"] = "approved"
        users["users"][email]["approved_at"] = datetime.datetime.now().isoformat()
        users["updated_at"] = datetime.datetime.now().isoformat()
        return _save_users_to_gist(users)
    return False


def reject_user(email: str) -> bool:
    """사용자 거부 (관리자 전용)"""
    users = _load_users_from_gist()
    if email in users["users"]:
        users["users"][email]["status"] = "rejected"
        users["updated_at"] = datetime.datetime.now().isoformat()
        return _save_users_to_gist(users)
    return False


def delete_user(email: str) -> bool:
    """사용자 삭제 (관리자 전용)"""
    users = _load_users_from_gist()
    if email in users["users"] and email != ADMIN_EMAIL:
        del users["users"][email]
        users["updated_at"] = datetime.datetime.now().isoformat()
        return _save_users_to_gist(users)
    return False


def check_user_status(email: str) -> Optional[str]:
    """사용자 상태 확인 (approved/pending/rejected/None)"""
    # 🚀 강제 승인 명단 및 관리자 예외 처리 (여기서 걸리면 바로 approved 반환)
    if email == ADMIN_EMAIL or email in ALLOWED_USERS:
        return "approved"
        
    users = _load_users_from_gist()
    if email in users["users"]:
        return users["users"][email]["status"]
    return None


def is_admin(email: str) -> bool:
    return email == ADMIN_EMAIL


def users_to_dataframe():
    """사용자 DB를 DataFrame으로 변환 (엑셀 다운로드용)"""
    import pandas as pd
    users = _load_users_from_gist()
    rows = []
    for email, info in users.get("users", {}).items():
        rows.append({
            "이메일": email,
            "이름": info.get("name", ""),
            "소속": info.get("org", ""),
            "직급": info.get("title", ""),
            "연락처": info.get("phone", ""),
            "상태": info.get("status", ""),
            "역할": info.get("role", "user"),
            "요청일시": info.get("requested_at", ""),
            "승인일시": info.get("approved_at", ""),
        })
    return pd.DataFrame(rows)


def get_user_profile(email: str) -> Dict:
    """사용자 프로필 조회"""
    users = _load_users_from_gist()
    return users.get("users", {}).get(email, {})


def update_user_profile(email: str, name: str, org: str, title: str, phone: str) -> bool:
    """사용자 프로필 업데이트 (이름, 소속, 직급, 연락처)"""
    users = _load_users_from_gist()
    if email in users["users"]:
        users["users"][email]["name"] = name
        users["users"][email]["org"] = org
        users["users"][email]["title"] = title
        users["users"][email]["phone"] = phone
        users["updated_at"] = datetime.datetime.now().isoformat()
        return _save_users_to_gist(users)
    return False


# ════════════════════════════════════════════════════════════════
# 사용량 추적 (Usage Tracking)
# ════════════════════════════════════════════════════════════════
def log_report_generation(
    email: str,
    company_name: str = "",
    file_type: str = "unknown",   # 'corporate_tax_pdf' | 'personal_tax_pdf' | 'crehard_xlsx' | 'crehard_pdf'
    is_personal: bool = False,
    n_chapters: int = 0,
    n_pages: int = 0,
) -> bool:
    """리포트 생성 시 사용 로그 기록.
    Gist users_db.json 안에 usage_logs 배열 + usage_summary 객체로 저장.
    최근 1000건만 유지 (오래된 로그는 자동 삭제).
    """
    if not email:
        return False
    
    try:
        users = _load_users_from_gist()
        if "usage_logs" not in users:
            users["usage_logs"] = []
        if "usage_summary" not in users:
            users["usage_summary"] = {"by_user": {}}
        
        now = datetime.datetime.now()
        log_entry = {
            "email": email,
            "timestamp": now.isoformat(),
            "company_name": company_name[:50] if company_name else "",  # 50자 제한
            "file_type": file_type,
            "is_personal": bool(is_personal),
            "n_chapters": int(n_chapters),
            "n_pages": int(n_pages),
        }
        users["usage_logs"].append(log_entry)
        
        # 최근 1000건만 유지
        if len(users["usage_logs"]) > 1000:
            users["usage_logs"] = users["usage_logs"][-1000:]
        
        # 사용자별 요약 업데이트
        summary = users["usage_summary"]["by_user"]
        if email not in summary:
            summary[email] = {
                "total": 0,
                "this_month": 0,
                "last_used": None,
                "first_used": now.isoformat(),
                "by_type": {},   # 파일 유형별 카운트
                "month_key": now.strftime("%Y-%m"),
            }
        
        u_sum = summary[email]
        u_sum["total"] = int(u_sum.get("total", 0)) + 1
        u_sum["last_used"] = now.isoformat()
        
        # 월별 카운트: 월이 바뀌면 this_month 리셋
        current_month = now.strftime("%Y-%m")
        if u_sum.get("month_key") != current_month:
            u_sum["month_key"] = current_month
            u_sum["this_month"] = 1
        else:
            u_sum["this_month"] = int(u_sum.get("this_month", 0)) + 1
        
        # 파일 유형별 카운트
        u_sum["by_type"] = u_sum.get("by_type", {})
        u_sum["by_type"][file_type] = int(u_sum["by_type"].get(file_type, 0)) + 1
        
        users["updated_at"] = now.isoformat()
        return _save_users_to_gist(users)
    except Exception as e:
        print(f"사용 로그 저장 실패: {e}")
        return False


def get_user_usage_stats(email: str) -> Dict:
    """특정 사용자의 사용량 통계"""
    users = _load_users_from_gist()
    summary = users.get("usage_summary", {}).get("by_user", {}).get(email, {})
    if not summary:
        return {"total": 0, "this_month": 0, "last_used": None, "by_type": {}}
    
    # 월 키 확인 — 사용 안 한 새 달이면 this_month 0으로 표시
    import datetime as _dt
    current_month = _dt.datetime.now().strftime("%Y-%m")
    if summary.get("month_key") != current_month:
        # 표시할 때만 0으로 변경 (저장은 그대로)
        summary = dict(summary)
        summary["this_month"] = 0
    
    return summary


def get_all_usage_logs(limit: int = 200) -> List[Dict]:
    """전체 사용 로그 (최신순, 기본 200건)"""
    users = _load_users_from_gist()
    logs = users.get("usage_logs", [])
    return list(reversed(logs[-limit:]))


def get_all_usage_summary() -> Dict[str, Dict]:
    """전체 사용자별 사용량 요약 (관리자용).
    Returns: {email: {total, this_month, last_used, by_type, ...}}
    """
    users = _load_users_from_gist()
    summary = users.get("usage_summary", {}).get("by_user", {})
    
    # this_month 보정
    import datetime as _dt
    current_month = _dt.datetime.now().strftime("%Y-%m")
    result = {}
    for email, info in summary.items():
        info = dict(info)
        if info.get("month_key") != current_month:
            info["this_month"] = 0
        result[email] = info
    return result


def usage_to_dataframe():
    """사용량 통계를 DataFrame으로 변환 (엑셀 다운로드용)"""
    import pandas as pd
    users = _load_users_from_gist()
    user_list = users.get("users", {})
    summary = get_all_usage_summary()
    
    rows = []
    # 전체 등록된 사용자 + 화이트리스트 + 관리자 모두 포함
    all_emails = set(user_list.keys()) | set(summary.keys()) | {ADMIN_EMAIL} | set(ALLOWED_USERS)
    for email in sorted(all_emails):
        user_info = user_list.get(email, {})
        usage = summary.get(email, {})
        by_type = usage.get("by_type", {}) or {}
        rows.append({
            "이메일": email,
            "이름": user_info.get("name", ""),
            "소속": user_info.get("org", ""),
            "총 사용횟수": usage.get("total", 0),
            "이번달 사용": usage.get("this_month", 0),
            "최근 사용일": (usage.get("last_used", "") or "")[:19].replace("T", " "),
            "첫 사용일": (usage.get("first_used", "") or "")[:19].replace("T", " "),
            "법인 PDF": by_type.get("corporate_tax_pdf", 0),
            "개인사업자 PDF": by_type.get("personal_tax_pdf", 0),
            "크레탑 자료": by_type.get("crehard_xlsx", 0) + by_type.get("crehard_pdf", 0),
        })
    # 총 사용횟수 많은 순으로 정렬
    rows.sort(key=lambda r: -int(r["총 사용횟수"]))
    return pd.DataFrame(rows)


def usage_logs_to_dataframe():
    """전체 사용 로그를 DataFrame으로 변환"""
    import pandas as pd
    logs = get_all_usage_logs(limit=1000)
    rows = []
    for log in logs:
        rows.append({
            "일시": (log.get("timestamp", "") or "")[:19].replace("T", " "),
            "이메일": log.get("email", ""),
            "기업명": log.get("company_name", ""),
            "유형": "👤 개인사업자" if log.get("is_personal") else "🏢 법인",
            "파일 종류": {
                "corporate_tax_pdf": "법인 세무조정계산서",
                "personal_tax_pdf": "개인사업자 세무조정계산서",
                "crehard_xlsx": "크레탑 엑셀",
                "crehard_pdf": "크레탑 PDF",
            }.get(log.get("file_type", ""), log.get("file_type", "")),
            "챕터수": log.get("n_chapters", 0),
            "페이지수": log.get("n_pages", 0),
        })
    return pd.DataFrame(rows)
