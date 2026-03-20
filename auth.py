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
