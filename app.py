"""
재무경영진단 리포트 생성기 - Streamlit App
- 관리자 승인제 로그인 시스템
- 관리자: incheon00@gmail.com
"""
import streamlit as st
import tempfile
import os
import sys
import io
import datetime

# ── 경로 설정 (Streamlit Cloud 호환) ──
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
# 상위 디렉토리도 추가 (혹시 서브폴더에 있을 경우)
PARENT_DIR = os.path.dirname(APP_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from auth import (
    ADMIN_EMAIL, request_approval, approve_user, reject_user, delete_user,
    check_user_status, is_admin, get_all_users, users_to_dataframe,
    get_user_profile, update_user_profile, _get_gist_config,
    log_report_generation, get_user_usage_stats, get_all_usage_summary,
    usage_to_dataframe, usage_logs_to_dataframe,
)

st.set_page_config(page_title="재무경영진단 리포트 생성기", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 800; color: #4A5FC1; margin-bottom: 0.5rem; }
    .sub-header { color: #666; margin-bottom: 2rem; }
    .metric-card { background: #F8F9FC; border-radius: 12px; padding: 20px; border: 1px solid #E5E7EB; text-align: center; }
    .metric-label { font-size: 0.85rem; color: #666; }
    .metric-value { font-size: 1.5rem; font-weight: 800; color: #4A5FC1; }
    .section-divider { border-top: 2px solid #4A5FC1; margin: 2rem 0 1rem 0; padding-top: 1rem; }
    .login-title { font-size: 2rem; font-weight: 800; color: #4A5FC1; text-align: center; margin-bottom: 8px; }
    .login-subtitle { color: #888; text-align: center; margin-bottom: 30px; font-size: 0.95rem; }
    .status-pending { background: #FFF3E0; color: #E65100; padding: 12px 20px; border-radius: 8px; text-align: center; }
    .status-rejected { background: #FFEBEE; color: #C62828; padding: 12px 20px; border-radius: 8px; text-align: center; }
    .admin-badge { background: #4A5FC1; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .pending-user { background: #FFF8E7; border: 1px solid #F0B429; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

for key, val in [("logged_in", False), ("user_email", ""), ("user_name", ""), ("user_org", ""), ("user_title", ""), ("user_phone", ""), ("show_signup", False)]:
    if key not in st.session_state:
        st.session_state[key] = val

def logout():
    for key in ["logged_in", "user_email", "user_name", "user_org", "user_title", "user_phone"]:
        st.session_state[key] = "" if key != "logged_in" else False
    st.session_state.show_signup = False

# ══════════════════════════════════════
# 로그인 페이지 (이메일만 입력)
# ══════════════════════════════════════
def show_login_page():
    # RSV 스타일 로고/타이틀 영역
    st.markdown("""
    <div style="text-align:center; padding: 40px 20px 20px;">
        <div style="display:inline-block; background:linear-gradient(180deg,#F4D98A,#C9A961,#8B6F3E); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:#C9A961; font-size:48px; font-weight:900; letter-spacing:12px;">RSV</div>
        <div style="color:#999; letter-spacing:5px; font-size:12px; margin-bottom:8px;">RICH SECRET VAULT</div>
        <div style="color:#0F2847; font-size:22px; font-weight:700; letter-spacing:2px;">📊 재무경영진단 리포트 생성기</div>
    </div>
    """, unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if not st.session_state.show_signup:
            # ── 로그인 화면 (이메일만) ──
            st.markdown("### 🔐 로그인")
            email = st.text_input("이메일", placeholder="example@company.com", key="login_email").strip().lower()
            
            lc1, lc2 = st.columns(2)
            with lc1:
                if st.button("로그인", type="primary", use_container_width=True):
                    if not email or "@" not in email:
                        st.error("올바른 이메일을 입력해주세요.")
                    else:
                        status = check_user_status(email)
                        if status == "approved":
                            # Gist에서 저장된 프로필 불러오기
                            profile = get_user_profile(email)
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.user_name = profile.get("name", email)
                            st.session_state.user_org = profile.get("org", "")
                            st.session_state.user_title = profile.get("title", "")
                            st.session_state.user_phone = profile.get("phone", "")
                            st.rerun()
                        elif status == "pending":
                            st.markdown('<div class="status-pending">⏳ 승인 대기 중입니다. 관리자가 승인하면 이용 가능합니다.</div>', unsafe_allow_html=True)
                        elif status == "rejected":
                            st.markdown('<div class="status-rejected">❌ 승인이 거부되었습니다. 관리자에게 문의하세요.</div>', unsafe_allow_html=True)
                        else:
                            st.error("❌ 등록되지 않은 이메일입니다. '승인 신청' 버튼을 눌러주세요.")
            with lc2:
                if st.button("✋ 승인 신청 (신규)", use_container_width=True):
                    st.session_state.show_signup = True
                    st.rerun()
            
            st.markdown(f"<p style='text-align:center;color:#999;font-size:12px;margin-top:20px;'>관리자: {ADMIN_EMAIL}</p>", unsafe_allow_html=True)
        
        else:
            # ── 승인 신청 화면 ──
            st.markdown("### ✋ 신규 사용자 승인 신청")
            st.info("아래 정보를 입력하시면 관리자에게 승인 신청이 전달됩니다.")
            
            req_email = st.text_input("이메일", placeholder="example@company.com").strip().lower()
            req_name = st.text_input("이름", placeholder="홍길동")
            req_company = st.text_input("회사명 / 소속", placeholder="(주)회사명 또는 중소기업경영지원단")
            req_purpose = st.text_area("사용 목적 (선택)", placeholder="예: 재무경영진단 컨설팅 업무에 활용", height=80)
            
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("📨 승인 요청", type="primary", use_container_width=True):
                    if not req_email or "@" not in req_email:
                        st.error("올바른 이메일을 입력해주세요.")
                    elif not req_name:
                        st.error("이름을 입력해주세요.")
                    else:
                        existing = check_user_status(req_email)
                        if existing == "approved":
                            st.warning("이미 승인된 이메일입니다. 로그인 화면으로 돌아가서 로그인해주세요.")
                        elif existing == "pending":
                            st.info("이미 신청하셨습니다. 승인을 기다려주세요.")
                        elif existing == "rejected":
                            st.error("이전 신청이 거부되었습니다. 관리자에게 문의하세요.")
                        else:
                            approved = request_approval(req_email, req_name, req_company)
                            if approved:
                                # 관리자(자동 승인)인 경우 바로 로그인
                                st.session_state.logged_in = True
                                st.session_state.user_email = req_email
                                st.session_state.user_name = req_name
                                st.session_state.user_org = req_company
                                st.session_state.show_signup = False
                                st.rerun()
                            else:
                                st.success(f"✅ {req_email} 승인 신청이 완료되었습니다!\n관리자 승인 후 로그인 가능합니다.")
            with sc2:
                if st.button("← 로그인 화면으로", use_container_width=True):
                    st.session_state.show_signup = False
                    st.rerun()

# ══════════════════════════════════════
# 관리자 패널
# ══════════════════════════════════════
def show_admin_panel():
    st.markdown("## 🔧 관리자 패널")
    
    # Gist 연결 상태 확인
    gist_id, token = _get_gist_config()
    if gist_id and token:
        st.success(f"✅ Gist 연결됨 (ID: {gist_id[:8]}...)")
    else:
        st.error("❌ Gist 설정 안 됨! Streamlit Cloud → Settings → Secrets에 gist.id와 gist.token을 설정하세요.")
        st.code("""
[gist]
id = "여기에_Gist_ID"
token = "여기에_GitHub_Token"
        """, language="toml")
    
    users = get_all_users()
    user_list = users.get("users", {})
    total = len(user_list)
    approved = sum(1 for u in user_list.values() if u.get("status") == "approved")
    pending = sum(1 for u in user_list.values() if u.get("status") == "pending")
    cols = st.columns(4)
    cols[0].metric("전체", total)
    cols[1].metric("승인", approved)
    cols[2].metric("대기", pending)
    cols[3].metric("거부", total - approved - pending)

    pending_users = {e: u for e, u in user_list.items() if u.get("status") == "pending"}
    if pending_users:
        st.markdown("### ⏳ 승인 대기")
        for email, info in pending_users.items():
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            c1.write(f"**{info.get('name', '')}** ({email})")
            c2.write(info.get("org", "-"))
            if c3.button("✅ 승인", key=f"a_{email}"):
                approve_user(email)
                st.rerun()
            if c4.button("❌ 거부", key=f"r_{email}"):
                reject_user(email)
                st.rerun()

    st.markdown("### 👥 전체 사용자")
    df = users_to_dataframe()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine='openpyxl')
        buf.seek(0)
        st.download_button("📥 사용자 목록 엑셀 다운로드", data=buf, file_name="사용자_승인목록.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    # ════════════════════════════════════════
    # 📊 사용량 통계 (Usage Analytics)
    # ════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📊 사용량 통계")
    
    usage_summary = get_all_usage_summary()
    
    if not usage_summary:
        st.info("아직 리포트 생성 기록이 없습니다. 사용자가 리포트를 생성하면 여기에 통계가 표시됩니다.")
    else:
        # ─── 전체 핵심 지표 ───
        total_reports = sum(int(u.get("total", 0)) for u in usage_summary.values())
        total_this_month = sum(int(u.get("this_month", 0)) for u in usage_summary.values())
        active_users = sum(1 for u in usage_summary.values() if int(u.get("total", 0)) > 0)
        
        # 가장 많이 쓴 사용자
        top_user_email = max(usage_summary.keys(), key=lambda e: int(usage_summary[e].get("total", 0))) if usage_summary else "-"
        top_user_count = int(usage_summary.get(top_user_email, {}).get("total", 0))
        
        mc = st.columns(4)
        mc[0].metric("총 리포트 생성", f"{total_reports:,}건")
        mc[1].metric("이번 달", f"{total_this_month:,}건")
        mc[2].metric("활성 사용자", f"{active_users}명")
        mc[3].metric("최다 사용자", f"{top_user_count}건", help=f"{top_user_email}")
        
        # ─── 사용자별 사용 횟수 테이블 ───
        st.markdown("#### 🏆 사용자별 사용 횟수")
        usage_df = usage_to_dataframe()
        if not usage_df.empty:
            # 0건인 사용자는 별도 옵션으로 숨김
            show_zero = st.checkbox("0건 사용자도 표시", value=False, key="show_zero_users")
            display_df = usage_df if show_zero else usage_df[usage_df["총 사용횟수"] > 0]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 엑셀 다운로드
            buf2 = io.BytesIO()
            usage_df.to_excel(buf2, index=False, engine='openpyxl')
            buf2.seek(0)
            st.download_button("📥 사용량 통계 엑셀 다운로드", data=buf2,
                file_name=f"사용량통계_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="usage_download")
        
        # ─── 최근 사용 로그 ───
        st.markdown("#### 📋 최근 사용 내역")
        with st.expander("최근 200건 보기", expanded=False):
            logs_df = usage_logs_to_dataframe()
            if not logs_df.empty:
                st.dataframe(logs_df, use_container_width=True, hide_index=True, height=400)
                # 로그 엑셀 다운로드
                buf3 = io.BytesIO()
                logs_df.to_excel(buf3, index=False, engine='openpyxl')
                buf3.seek(0)
                st.download_button("📥 전체 사용 로그 엑셀", data=buf3,
                    file_name=f"사용로그_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="logs_download")
            else:
                st.info("사용 로그 없음")
        
        # ─── 파일 유형별 분포 ───
        st.markdown("#### 📁 파일 유형별 사용 분포")
        type_counts = {"법인 PDF": 0, "개인사업자 PDF": 0, "크레탑 엑셀": 0, "크레탑 PDF": 0}
        for u in usage_summary.values():
            by_type = u.get("by_type", {}) or {}
            type_counts["법인 PDF"] += int(by_type.get("corporate_tax_pdf", 0))
            type_counts["개인사업자 PDF"] += int(by_type.get("personal_tax_pdf", 0))
            type_counts["크레탑 엑셀"] += int(by_type.get("crehard_xlsx", 0))
            type_counts["크레탑 PDF"] += int(by_type.get("crehard_pdf", 0))
        
        tc = st.columns(4)
        tc[0].metric("🏢 법인 PDF", f"{type_counts['법인 PDF']}건")
        tc[1].metric("👤 개인사업자 PDF", f"{type_counts['개인사업자 PDF']}건")
        tc[2].metric("📊 크레탑 엑셀", f"{type_counts['크레탑 엑셀']}건")
        tc[3].metric("📑 크레탑 PDF", f"{type_counts['크레탑 PDF']}건")

    st.markdown("---")
    st.markdown("### 🗑️ 사용자 삭제")
    del_email = st.text_input("삭제할 이메일")
    if st.button("삭제") and del_email:
        if del_email == ADMIN_EMAIL:
            st.error("관리자 계정은 삭제 불가")
        elif delete_user(del_email.strip().lower()):
            st.success(f"{del_email} 삭제 완료")
            st.rerun()

# ══════════════════════════════════════
# 메인 페이지
# ══════════════════════════════════════
def show_main_page():
    from parsers.excel_parser import parse_balance_sheet, parse_income_statement, parse_manufacturing_cost
    from parsers.pdf_parser import parse_company_overview, parse_credit_report
    from parsers.financial_ratios import calculate_ratios, calculate_valuation
    from report.html_template import generate_report_html, format_number, fn
    from report.pdf_generator import generate_pdf
    import pandas as pd

    top1, top2, top3 = st.columns([6, 3, 1])
    with top1:
        st.markdown('<div class="main-header">📊 재무경영진단 리포트 생성기</div>', unsafe_allow_html=True)
    with top2:
        label = f"👤 {st.session_state.user_name}"
        if is_admin(st.session_state.user_email):
            label += ' <span class="admin-badge">관리자</span>'
        st.markdown(f"<div style='text-align:right;padding-top:16px;'>{label}</div>", unsafe_allow_html=True)
    with top3:
        if st.button("로그아웃"):
            logout()
            st.rerun()

    if is_admin(st.session_state.user_email):
        # 대기 중인 사용자 수 표시
        all_users = get_all_users()
        pending_count = sum(1 for u in all_users.get("users", {}).values() if u.get("status") == "pending")
        admin_label = f"🔧 관리자 패널 ({pending_count}건 대기)" if pending_count > 0 else "🔧 관리자 패널"
        tab_report, tab_admin = st.tabs(["📊 리포트 생성", admin_label])
        with tab_admin:
            show_admin_panel()
        with tab_report:
            _report_ui()
    else:
        _report_ui()

def _report_ui():
    from parsers.excel_parser import parse_balance_sheet, parse_income_statement, parse_manufacturing_cost
    from parsers.pdf_parser import parse_company_overview, parse_credit_report
    from parsers.financial_ratios import calculate_ratios, calculate_valuation
    from report.html_template import generate_report_html, format_number, fn
    from report.pdf_generator import generate_pdf
    import pandas as pd

    with st.sidebar:
        # ── 내 정보 (Gist에 저장됨) ──
        st.header("👤 내 정보")
        profile = get_user_profile(st.session_state.user_email)
        
        author_name = st.text_input("작성자명", value=profile.get("name") or st.session_state.get("user_name", ""))
        author_org = st.text_input("소속", value=profile.get("org") or st.session_state.get("user_org", ""))
        author_title = st.text_input("직급", value=profile.get("title") or st.session_state.get("user_title", ""), placeholder="예: 지사장, 팀장, 대표")
        author_phone = st.text_input("연락처", value=profile.get("phone") or st.session_state.get("user_phone", ""), placeholder="010-0000-0000")
        
        if st.button("💾 내 정보 저장", use_container_width=True):
            update_user_profile(st.session_state.user_email, author_name, author_org, author_title, author_phone)
            st.session_state.user_name = author_name
            st.success("저장 완료!")
        
        # 리포트에 표시될 작성자 정보 조합
        author_display = f"{author_name} {author_title}".strip() if author_title else author_name
        author_org_display = author_org
        
        # ── 내 사용량 표시 (관리자에게만 노출) ──
        if is_admin(st.session_state.user_email):
            try:
                my_stats = get_user_usage_stats(st.session_state.user_email)
                my_total = int(my_stats.get("total", 0))
                my_month = int(my_stats.get("this_month", 0))
                last_used = (my_stats.get("last_used") or "")[:10]  # 날짜만
                if my_total > 0:
                    st.markdown(f"""
                    <div style='background:linear-gradient(135deg,#0F2847,#1B3A6B);color:white;padding:10px 14px;border-radius:8px;margin-top:8px;font-size:12px;line-height:1.5;'>
                        <div style='font-weight:700;color:#C9A961;font-size:11px;letter-spacing:0.5px;margin-bottom:4px;'>📊 내 사용 현황 <span style='background:#C9A961;color:#0F2847;padding:1px 6px;border-radius:8px;font-size:9px;margin-left:4px;'>관리자</span></div>
                        <div>📑 총 <strong>{my_total}</strong>건 생성 &nbsp;|&nbsp; 이번 달 <strong>{my_month}</strong>건</div>
                        {f"<div style='font-size:11px;opacity:0.85;margin-top:2px;'>최근: {last_used}</div>" if last_used else ""}
                    </div>
                    """, unsafe_allow_html=True)
            except Exception:
                pass
        
        st.markdown("---")
        st.header("📁 파일 업로드")
        st.caption("크레탑 엑셀 또는 세무조정계산서 PDF — 어떤 자료든 자동 분류됩니다.")
        
        uploaded_files = st.file_uploader(
            "엑셀/PDF 파일을 모두 선택하세요",
            type=["xlsx", "xls", "pdf"],
            accept_multiple_files=True,
            key="all_files",
            help="크레탑 엑셀(ETFI112E1.xlsx 등) 또는 세무조정계산서 PDF를 업로드하세요. 둘 다 가능!"
        )
        
        # 파일 자동 분류 (내용 기반 — 파일명 무관)
        file_map = {"bs": None, "is": None, "mfg": None, "re": None, "cf": None, "ce": None, "overview": None, "credit": None, "tax_adjustment": None}
        # 세무조정계산서 PDF의 자동 인식 결과 저장용
        tax_pdf_detected_type = None   # 'corporate' | 'personal' | 'unknown'
        tax_pdf_diagnostic = []        # 인식 실패 시 디버그 정보
        
        def detect_file_type(f):
            """파일 내용을 읽어 유형 자동 판별"""
            import pandas as pd
            nonlocal tax_pdf_detected_type, tax_pdf_diagnostic
            name = f.name.lower()
            if name.endswith('.pdf'):
                # PDF는 세무조정계산서인지 먼저 체크
                f.seek(0)
                try:
                    import tempfile
                    from parsers.pdf_parser import is_tax_adjustment_pdf, is_personal_tax_adjustment_pdf
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        tmp.write(f.getvalue())
                        tmp_path = tmp.name
                    
                    # 법인/개인 둘 다 체크
                    is_corp_doc = is_tax_adjustment_pdf(tmp_path)
                    is_pers_doc = is_personal_tax_adjustment_pdf(tmp_path)
                    
                    # 자동 인식 진단을 위한 키워드 검색 결과 수집
                    try:
                        import pdfplumber
                        with pdfplumber.open(tmp_path) as pdf:
                            sample = ""
                            for i in range(min(15, len(pdf.pages))):
                                sample += (pdf.pages[i].extract_text() or "") + "\n"
                            tax_pdf_diagnostic = [
                                ("법인세과세표준", "법인세과세표준" in sample),
                                ("종합소득세", "종합소득세" in sample),
                                ("과세표준확정신고", "과세표준확정신고" in sample),
                                ("표준재무상태표", "표준재무상태표" in sample),
                                ("표준손익계산서", "표준손익계산서" in sample),
                                ("사업소득명세서", "사업소득명세서" in sample),
                                ("세무조정계산서", "세무조정계산서" in sample),
                            ]
                    except Exception:
                        pass
                    
                    os.unlink(tmp_path)
                    
                    if is_corp_doc:
                        tax_pdf_detected_type = 'corporate'
                        return "tax_adjustment"
                    elif is_pers_doc:
                        tax_pdf_detected_type = 'personal'
                        return "tax_adjustment"
                    # 둘 다 아닌데 세무조정 관련 키워드가 있으면 알 수 없는 양식으로 표시
                    has_any_tax_keyword = any(matched for _, matched in tax_pdf_diagnostic) if tax_pdf_diagnostic else False
                    if has_any_tax_keyword:
                        tax_pdf_detected_type = 'unknown'
                        # 알 수 없는 양식이라도 일단 tax_adjustment 슬롯에 넣음 — 사용자가 수동 강제로 처리 가능하도록
                        return "tax_adjustment"
                except Exception as e:
                    print(f"세무조정계산서 판별 오류: {e}")
                finally:
                    f.seek(0)
                # 세무조정계산서가 아니면 크레탑 PDF (개요/신용)
                return "overview_pdf" if file_map["overview"] is None else "credit_pdf"
            try:
                f.seek(0)
                try:
                    df = pd.read_excel(f, sheet_name=0, header=None, nrows=35)
                except Exception:
                    f.seek(0)
                    return "unknown"
                finally:
                    f.seek(0)
                texts = set()
                for r in range(min(35, df.shape[0])):
                    for c in range(df.shape[1]):
                        v = df.iloc[r, c]
                        if pd.notna(v):
                            texts.add(str(v).strip())
                all_text = ' '.join(texts)
                if '기업프로필' in all_text or '기업 브리핑 보고서' in all_text or '기업 브리핑' in all_text:
                    return "overview_xls"
                if '기업 신용등급 보고서' in all_text or '연도별 등급 이력' in all_text or ('기업신용등급' in all_text and '등급설명' in all_text):
                    return "credit_xls"
                if '자산(*)' in texts or '유동자산(*)' in texts or '당좌자산(*)' in texts:
                    return "bs"
                if '매출액(*)' in texts and ('매출원가(*)' in texts or '매출총이익' in all_text):
                    return "is"
                if '미처분이익잉여금' in all_text and '전기이월' in all_text:
                    return "re"
                if '원재료비(*)' in texts or '노동관계비용(*)' in texts or '당기총제조비용' in all_text:
                    return "mfg"
                if '영업활동' in all_text and '현금흐름' in all_text:
                    return "cf"
                if '자본변동' in all_text:
                    return "ce"
                return "unknown"
            except:
                return "unknown"
        
        if uploaded_files:
            for f in uploaded_files:
                ftype = detect_file_type(f)
                if ftype == "tax_adjustment":
                    file_map["tax_adjustment"] = f
                elif ftype in ("overview_pdf", "overview_xls"):
                    file_map["overview"] = f
                elif ftype in ("credit_pdf", "credit_xls"):
                    file_map["credit"] = f
                elif ftype in file_map:
                    file_map[ftype] = f
            
            # 분류 결과 표시
            st.markdown("**📋 파일 자동 분류 결과:**")
            
            # 세무조정계산서 우선 표시
            if file_map["tax_adjustment"]:
                fname = file_map["tax_adjustment"].name
                if tax_pdf_detected_type == 'corporate':
                    st.success(f"🏢 **법인 세무조정계산서로 인식됨**: `{fname}`")
                    st.caption("✨ 이 PDF 1개로 재무상태표·손익계산서·기업정보·법인세 심층진단까지 모두 자동 추출됩니다!")
                elif tax_pdf_detected_type == 'personal':
                    st.success(f"👤 **개인사업자 세무조정계산서로 인식됨**: `{fname}`")
                    st.caption("✨ 종합소득세 신고서 기반으로 분석합니다. 개인사업자에게 부적합한 챕터는 자동 비활성화됩니다.")
            elif tax_pdf_detected_type == 'unknown':
                # 세무조정 관련 키워드는 있는데 법인/개인 어느 쪽도 명확히 인식 못한 케이스
                st.warning("⚠️ **알 수 없는 양식의 세무조정계산서입니다.** 자동 인식에 실패했어요.")
                with st.expander("🔍 인식 진단 정보 (어떤 키워드를 찾았는지)", expanded=True):
                    st.caption("아래는 업로드한 PDF에서 검색한 결과입니다. 세무사 사무실마다 양식이 약간씩 달라서 일부 키워드가 다를 수 있어요.")
                    for kw, found in tax_pdf_diagnostic:
                        icon = "✅" if found else "❌"
                        st.markdown(f"{icon} `{kw}`")
                    st.markdown("---")
                    st.markdown("""
                    **💡 다음 중 하나로 진행해보세요:**
                    1. 🔧 아래 **'사업자 유형'** 영역에서 **수동 강제 처리** 옵션 사용
                    2. 📊 또는 **크레탑 엑셀 자료**(ETFI112E1.xlsx 등)로 대체 업로드  
                    3. 📞 양식이 너무 다르면 RSV 운영팀에 PDF 샘플 전달해주세요 → 패턴 추가 업데이트
                    """)
            
            # 일반 크레탑 자료 분류 결과 (세무조정계산서가 아닌 경우)
            if not file_map["tax_adjustment"]:
                labels = {
                    "bs": "📊 재무상태표", "is": "📈 손익계산서", "mfg": "🏭 제조원가명세서",
                    "re": "💰 이익잉여금처분", "cf": "💵 현금흐름표", "ce": "📑 자본변동표",
                    "overview": "📄 기업개요", "credit": "🏦 신용등급"
                }
                for key, label in labels.items():
                    f = file_map[key]
                    if f:
                        st.markdown(f"✅ {label}: `{f.name}`")
                
                # 필수 파일 체크
                missing = []
                if not file_map["bs"]: missing.append("재무상태표")
                if not file_map["is"]: missing.append("손익계산서")
                if missing:
                    st.warning(f"⚠️ 필수 파일 누락: {', '.join(missing)}")
                    st.info("💡 **팁:** 세무조정계산서 PDF 1개만 올려도 자동 분석됩니다!")
        
        st.markdown("---")
        st.header("🏢 기업 정보")
        st.caption("⚠️ 신용등급·EW등급·재무진단은 이미지라 자동추출 불가 — 직접 입력해주세요")
        company_name_input = st.text_input("기업명", placeholder="(주)원파워", key="ci_name")
        company_ceo_input = st.text_input("대표자", placeholder="이병진", key="ci_ceo")
        company_bizno_input = st.text_input("사업자번호", placeholder="215-88-00406", key="ci_biz")
        company_emp_input = st.text_input("종업원수", placeholder="25명", key="ci_emp")
        company_addr_input = st.text_input("주소", placeholder="경기 고양시 일산서구...", key="ci_addr")
        company_industry_input = st.text_input("업종", placeholder="(C18119) 기타 인쇄업", key="ci_ind")
        company_product_input = st.text_input("주요제품", placeholder="인쇄스티커, 라벨 등", key="ci_prod")
        st.markdown("**아래 항목은 수동 입력 필요:**")
        company_grade_input = st.text_input("신용등급 ⭐", placeholder="bb-", key="ci_grade")
        company_ew_input = st.selectbox("EW등급 ⭐", ["", "정상", "유보", "주의", "경고", "위험"], key="ci_ew")
        company_diag_growth = st.selectbox("재무진단-성장성", ["", "우수", "양호", "보통", "미흡", "열위"], key="ci_d1")
        company_diag_profit = st.selectbox("재무진단-수익성", ["", "우수", "양호", "보통", "미흡", "열위"], key="ci_d2")
        company_diag_structure = st.selectbox("재무진단-재무구조", ["", "우수", "양호", "보통", "미흡", "열위"], key="ci_d3")
        company_diag_debt = st.selectbox("재무진단-부채상환능력", ["", "우수", "양호", "보통", "미흡", "열위", "등급없음"], key="ci_d4")
        company_diag_activity = st.selectbox("재무진단-활동성", ["", "우수", "양호", "보통", "미흡", "열위"], key="ci_d5")
        
        st.markdown("---")
        st.header("💰 세금 시뮬레이션")
        st.caption("급여·퇴직금 세금 시뮬레이션 입력값")
        sim_monthly = st.number_input("월급여 (만원)", min_value=100, max_value=50000, value=1000, step=100, key="sim_m")
        sim_profit = st.number_input("법인 영업이익 (만원)", min_value=0, max_value=500000, value=50000, step=5000, key="sim_p")
        sim_corprate = st.selectbox("법인세율 (%)", [9, 10, 19, 21], index=0, key="sim_cr")
        sim_hope = st.number_input("희망 수령액 (세전, 만원)", min_value=1000, max_value=500000, value=50000, step=5000, key="sim_h")
        sim_tenure = st.number_input("근속연수 (년)", min_value=1, max_value=50, value=15, step=1, key="sim_t")
        sim_retire_year = st.number_input("퇴직 예정연도", min_value=2024, max_value=2060, value=2035, step=1, key="sim_ry")
        
        # 정관배수 자동 결정
        auto_mult = 3 if sim_retire_year <= 2019 else 2
        st.info(f"정관배수: **{auto_mult}배** ({'2019년 이전 → 3배' if auto_mult == 3 else '2020년 이후 → 2배'})")
        
        st.markdown("---")
        st.caption("💡 발행주식수와 액면가는 자본금에서 자동 계산됩니다.")

    shares = 0
    par_value = 5000
    
    # 수동 입력값을 company dict에 반영하는 함수
    def merge_manual_input(company_data):
        manual_fields = {
            "기업명": company_name_input,
            "대표자명": company_ceo_input,
            "사업자번호": company_bizno_input,
            "종업원수": company_emp_input,
            "주소": company_addr_input,
            "표준산업분류": company_industry_input,
            "주요제품": company_product_input,
            "기업신용등급": company_grade_input,
            "EW등급": company_ew_input,
        }
        for key, val in manual_fields.items():
            if val and val.strip():
                company_data[key] = val.strip()
        # 재무진단
        diag = company_data.get("재무진단", {})
        diag_inputs = {
            "성장성": company_diag_growth,
            "수익성": company_diag_profit,
            "재무구조": company_diag_structure,
            "부채상환능력": company_diag_debt,
            "활동성": company_diag_activity,
        }
        for key, val in diag_inputs.items():
            if val and val.strip():
                diag[key] = val.strip()
        company_data["재무진단"] = diag
        return company_data

    def _count_extracted_data(tax_data):
        """파서 결과에서 추출된 의미있는 데이터 항목 수를 셈 (어느 파서가 더 잘 작동했는지 비교용)"""
        if not tax_data or not isinstance(tax_data, dict):
            return 0
        score = 0
        # 기업명/대표자
        company = tax_data.get("company", {})
        if company.get("기업명"): score += 2
        if company.get("대표자명"): score += 1
        if company.get("사업자번호"): score += 1
        # BS 데이터
        bs = tax_data.get("bs", {})
        years = bs.get("years", [])
        for y in years:
            if y in bs and isinstance(bs[y], dict):
                # 0이 아닌 값 개수
                score += sum(1 for v in bs[y].values() if isinstance(v, (int, float)) and v != 0)
        # IS 데이터
        isc = tax_data.get("isc", {})
        for y in isc.get("years", []):
            if y in isc and isinstance(isc[y], dict):
                score += sum(1 for v in isc[y].values() if isinstance(v, (int, float)) and v != 0)
        return score

    def save_file(f):
        ext = os.path.splitext(f.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(f.getbuffer())
            saved_path = tmp.name
        
        # .xls 파일은 미리 .xlsx로 변환 (xlrd 없이도 작동, openpyxl 이미지 추출 가능)
        if ext == '.xls':
            try:
                import subprocess, glob
                tmp_dir = tempfile.mkdtemp()
                subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'xlsx', '--outdir', tmp_dir, saved_path],
                    capture_output=True, timeout=60
                )
                converted = glob.glob(os.path.join(tmp_dir, '*.xlsx'))
                if converted:
                    return converted[0]  # 변환된 xlsx 반환
            except Exception:
                pass  # 변환 실패하면 원본 .xls 반환
        
        return saved_path

    # 필수: 세무조정계산서 PDF 1개 OR (재무상태표 + 손익계산서) 엑셀
    has_tax_doc = file_map.get("tax_adjustment") is not None
    has_required = has_tax_doc or (file_map["bs"] and file_map["is"])
    
    # 사용자가 이전에 라디오에서 강제 선택한 값 (세션에 저장되어 있음)
    # 'auto' | 'force_corporate' | 'force_personal'
    forced_mode = st.session_state.get("biz_type_forced_mode", "auto")
    
    if has_required:
        saved_paths = []
        
        try:
            with st.spinner("📊 분석 중..."):
                if has_tax_doc:
                    # ─── 세무조정계산서 PDF 1개로 모든 데이터 추출 ───
                    from parsers.pdf_parser import (
                        parse_tax_adjustment_pdf, extract_tax_deep_analysis,
                        is_personal_tax_adjustment_pdf, is_corporate_tax_adjustment_pdf,
                        parse_personal_tax_adjustment_pdf, extract_personal_tax_deep_analysis,
                    )
                    tax_path = save_file(file_map["tax_adjustment"])
                    saved_paths.append(tax_path)
                    
                    # 개인사업자 vs 법인 자동 판별 (1차) — 둘 다 엄격하게 체크
                    is_corp_doc = is_corporate_tax_adjustment_pdf(tax_path)
                    is_personal_doc = is_personal_tax_adjustment_pdf(tax_path)
                    
                    # 사용자가 수동 강제 선택했으면 그게 최우선
                    if forced_mode == "force_personal":
                        st.info("📌 **사용자 강제 선택: 개인사업자 모드**")
                        tax_data = parse_personal_tax_adjustment_pdf(tax_path)
                        tax_deep = extract_personal_tax_deep_analysis(tax_path)
                        is_personal_doc = True
                    elif forced_mode == "force_corporate":
                        st.info("📌 **사용자 강제 선택: 법인 모드**")
                        tax_data = parse_tax_adjustment_pdf(tax_path)
                        tax_deep = extract_tax_deep_analysis(tax_path)
                        is_personal_doc = False
                    # 자동 모드: 1순위 명확하게 개인사업자
                    elif is_personal_doc:
                        st.info("👤 **개인사업자 세무조정계산서**로 인식되었습니다. (종합소득세 신고)")
                        tax_data = parse_personal_tax_adjustment_pdf(tax_path)
                        tax_deep = extract_personal_tax_deep_analysis(tax_path)
                    # 2순위: 명확하게 법인
                    elif is_corp_doc:
                        tax_data = parse_tax_adjustment_pdf(tax_path)
                        tax_deep = extract_tax_deep_analysis(tax_path)
                    # 3순위: 둘 다 명확하지 않음(unknown) - 양쪽 시도 후 데이터 많은 쪽 채택
                    else:
                        st.warning("⚠️ 알 수 없는 양식의 세무조정계산서입니다. 양쪽 파서로 시도해봅니다...")
                        
                        # 법인 파서 시도
                        try:
                            corp_data = parse_tax_adjustment_pdf(tax_path)
                            corp_score = _count_extracted_data(corp_data)
                        except Exception:
                            corp_data, corp_score = None, 0
                        
                        # 개인 파서 시도
                        try:
                            pers_data = parse_personal_tax_adjustment_pdf(tax_path)
                            pers_score = _count_extracted_data(pers_data)
                        except Exception:
                            pers_data, pers_score = None, 0
                        
                        if pers_score > corp_score and pers_score > 0:
                            st.info(f"👤 **개인사업자 모드로 진행** (개인 파서 추출 항목: {pers_score}개)")
                            tax_data = pers_data
                            tax_deep = extract_personal_tax_deep_analysis(tax_path)
                            is_personal_doc = True
                        elif corp_score > 0:
                            st.info(f"🏢 **법인 모드로 진행** (법인 파서 추출 항목: {corp_score}개)")
                            tax_data = corp_data
                            tax_deep = extract_tax_deep_analysis(tax_path)
                        else:
                            st.error("❌ **데이터 추출에 실패했습니다.** 이 PDF 양식은 현재 지원되지 않습니다.")
                            st.markdown("""
                            **다음 방법을 시도해보세요:**
                            1. 📊 **크레탑 엑셀 자료**(ETFI112E1.xlsx 시리즈)로 대체 업로드
                            2. 📞 RSV 운영팀에 이 PDF 샘플 전달 → 양식 패턴 추가 업데이트
                            3. 🔧 아래 사업자 유형에서 **수동 강제 처리** 선택 후 재시도
                            """)
                            # 일단 빈 데이터로라도 진행 (사용자가 수동 입력 가능)
                            tax_data = pers_data or corp_data or {
                                "company": {"기업명": "", "기업유형": ""},
                                "bs": {"years": []}, "isc": {"years": []}, 
                                "mfg": {"years": []}, "credit": {},
                            }
                            tax_deep = None
                    
                    bs = tax_data["bs"]
                    isc = tax_data["isc"]
                    mfg = tax_data["mfg"]
                    company = tax_data["company"]
                    credit = tax_data["credit"]
                    # 신용등급/제조원가가 없으면 신용 PDF 추가 처리 가능
                    if file_map.get("credit"):
                        cr_path = save_file(file_map["credit"]); saved_paths.append(cr_path)
                        if cr_path.endswith(('.xls', '.xlsx')):
                            from parsers.pdf_parser import parse_credit_report_excel
                            credit = parse_credit_report_excel(cr_path)
                        else:
                            credit = parse_credit_report(cr_path)
                else:
                    tax_deep = None  # 크레탑 경로엔 세무진단 없음
                    is_personal_doc = False  # 일단 False, 아래에서 기업개요 보고 재판정
                    # ─── 크레탑 엑셀/PDF로 분석 (기존 로직) ───
                    bs_path = save_file(file_map["bs"]); saved_paths.append(bs_path)
                    is_path = save_file(file_map["is"]); saved_paths.append(is_path)
                    mfg_path = save_file(file_map["mfg"]) if file_map["mfg"] else None
                    if mfg_path: saved_paths.append(mfg_path)
                    ov_path = save_file(file_map["overview"]) if file_map["overview"] else None
                    if ov_path: saved_paths.append(ov_path)
                    cr_path = save_file(file_map["credit"]) if file_map["credit"] else None
                    if cr_path: saved_paths.append(cr_path)
                    
                    bs = parse_balance_sheet(bs_path)
                    isc = parse_income_statement(is_path)
                    mfg = parse_manufacturing_cost(mfg_path) if mfg_path else {"years": bs.get("years", []), "raw": {}}
                    # 기업개요: PDF 또는 Excel 지원
                    if ov_path:
                        if ov_path.endswith(('.xls', '.xlsx')):
                            from parsers.pdf_parser import parse_company_overview_excel
                            company = parse_company_overview_excel(ov_path)
                        else:
                            company = parse_company_overview(ov_path)
                    else:
                        company = parse_company_overview(None)
                    # 신용등급
                    if cr_path:
                        if cr_path.endswith(('.xls', '.xlsx')):
                            from parsers.pdf_parser import parse_credit_report_excel
                            credit = parse_credit_report_excel(cr_path)
                        else:
                            credit = parse_credit_report(cr_path)
                    else:
                        credit = {}
                    
                    # ─── 크레탑 자료에서 개인/법인 자동 판별 ───
                    # 크레탑 기업개요 파일에 '기업유형/형태' 필드가 있고,
                    # 거기에 '개인사업자' 또는 '개인기업' 키워드가 있으면 개인사업자로 처리
                    biz_type_str = str(company.get("기업유형", "")).strip()
                    if biz_type_str and any(kw in biz_type_str for kw in ["개인사업자", "개인기업", "개인 사업자"]):
                        is_personal_doc = True
                        company["기업유형"] = "개인사업자"  # 표준화
                
                company = merge_manual_input(company)
                ratios = calculate_ratios(bs, isc)
                valuation = calculate_valuation(bs, isc, shares=shares or None, par_value=par_value)
            years = bs.get("years", [])
            yl = [y.replace("-12-31","년") for y in years]
            if years:
                latest = years[-1] if not has_tax_doc else years[0]  # 세무조정계산서는 최신연도가 첫번째
                # BS 키 호환: 자산총계 또는 자산
                total_asset = bs.get("자산",{}).get(latest) or bs.get("자산총계",{}).get(latest)
                st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                cols = st.columns(6)
                for col, (lb, vl) in zip(cols, [
                    ("총자산", format_number(total_asset,"억원")),
                    ("매출액", format_number(isc.get("매출액",{}).get(latest),"억원")),
                    ("영업이익", format_number(isc.get("영업이익",{}).get(latest),"억원")),
                    ("당기순이익", format_number(isc.get("당기순이익",{}).get(latest),"억원")),
                    ("부채비율", f"{ratios.get('부채비율',{}).get(latest,0) or 0:.1f}%"),
                    ("ROE", f"{ratios.get('ROE',{}).get(latest,0) or 0:.1f}%"),
                ]):
                    with col:
                        st.markdown(f'<div class="metric-card"><div class="metric-label">{lb}</div><div class="metric-value">{vl}</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # ════════════════════════════════════════
            # 🆕 보고서 모드 선택 (상단 큰 탭)
            # ════════════════════════════════════════
            st.markdown("### 📊 어떤 보고서를 만들까요?")
            
            mode_cols = st.columns(3)
            current_mode = st.session_state.get("report_mode", "full")
            
            with mode_cols[0]:
                if st.button(
                    "📄 **샘플링**\n\n영업·미계약자용\n*약 10~15페이지*",
                    use_container_width=True,
                    type="primary" if current_mode == "sampling" else "secondary",
                    key="btn_mode_sampling",
                ):
                    st.session_state["report_mode"] = "sampling"
                    st.rerun()
            with mode_cols[1]:
                if st.button(
                    "⚡ **심플**\n\n빠른 진단·핵심만\n*약 2페이지*",
                    use_container_width=True,
                    type="primary" if current_mode == "simple" else "secondary",
                    key="btn_mode_simple",
                ):
                    st.session_state["report_mode"] = "simple"
                    st.rerun()
            with mode_cols[2]:
                if st.button(
                    "📚 **풀버전**\n\n정식 컨설팅 자료\n*약 40~50페이지*",
                    use_container_width=True,
                    type="primary" if current_mode == "full" else "secondary",
                    key="btn_mode_full",
                ):
                    st.session_state["report_mode"] = "full"
                    st.rerun()
            
            report_mode = st.session_state.get("report_mode", "full")
            
            # 모드별 안내 박스
            mode_info = {
                "sampling": ("📄 **샘플링 모드** — 미계약 대표님께 보여드릴 영업용 티저 보고서. 각 챕터 첫 페이지만 보여주고 나머지는 'SAMPLE' 워터마크로 잠긴 상태. 마지막에 정식 계약 CTA 페이지 포함.", "#C9A961"),
                "simple": ("⚡ **심플 모드** — 첫 미팅 또는 시간 부족할 때 빠른 진단용. 종합 대시보드 1페이지 + 추천 액션. 챕터 선택 불필요.", "#0F2847"),
                "full": ("📚 **풀버전** — 정식 컨설팅 자료. 아래에서 원하는 챕터·페이지를 자유롭게 선택 가능.", "#2E7D32"),
            }
            _info_text, _info_color = mode_info[report_mode]
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{_info_color}10,{_info_color}20);"
                f"border-left:4px solid {_info_color};padding:10px 14px;border-radius:0 8px 8px 0;"
                f"margin:8px 0 16px;font-size:13px;'>{_info_text}</div>",
                unsafe_allow_html=True
            )
            
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # ─── 챕터 선택 UI (풀버전 모드에서만 노출) ───
            if report_mode == "full":
                st.markdown("### 📑 출력할 챕터를 선택해주세요")
            else:
                st.markdown(f"### 📑 {('샘플링' if report_mode == 'sampling' else '심플')} 모드 — 챕터 자동 선택됨")
                st.caption(f"이 모드에서는 챕터 구성이 자동으로 정해집니다. 풀버전 선택 시에만 챕터 커스터마이징 가능합니다.")
            
            # 개인사업자 여부 (위 분석 단계에서 결정됨)
            auto_is_personal = locals().get('is_personal_doc', False) or company.get('기업유형') == '개인사업자'
            auto_detected_label = "👤 개인사업자" if auto_is_personal else "🏢 법인"
            
            # 자동 판별 결과 + 수동 강제 옵션 (항상 노출)
            st.markdown("#### 🔧 사업자 유형")
            mode_cols = st.columns([1, 2])
            with mode_cols[0]:
                st.markdown(f"**자동 판별 결과:**\n\n{auto_detected_label}")
            with mode_cols[1]:
                # 현재 세션의 강제 모드 가져오기
                _current_mode = st.session_state.get("biz_type_forced_mode", "auto")
                _mode_label_map = {
                    "auto": "🤖 자동 (자동 판별 결과대로)",
                    "force_corporate": "🏢 법인으로 강제 처리",
                    "force_personal": "👤 개인사업자로 강제 처리",
                }
                _options = list(_mode_label_map.values())
                # 자동 인식 실패(unknown)인 경우 안내
                if tax_pdf_detected_type == 'unknown':
                    st.warning("⚠️ 자동 인식이 명확하지 않아요. 아래에서 직접 선택해주세요")
                    if _current_mode == "auto":
                        _current_mode = "force_corporate"  # 추천 기본값
                
                _current_idx = list(_mode_label_map.keys()).index(_current_mode)
                business_type_mode = st.radio(
                    "처리 방식",
                    options=_options,
                    index=_current_idx,
                    help="자동 판별이 잘못되었거나 양식이 특이하면 수동으로 강제 지정 가능. 변경 시 자동 재분석됩니다.",
                    key="biz_type_radio",
                    horizontal=False,
                )
                # 라디오 선택값을 세션상태에 저장 (다음 재실행 때 분석에 적용)
                _selected_key = [k for k, v in _mode_label_map.items() if v == business_type_mode][0]
                if st.session_state.get("biz_type_forced_mode") != _selected_key:
                    st.session_state["biz_type_forced_mode"] = _selected_key
                    st.rerun()  # 강제 모드 변경 시 재분석
            
            # 최종 is_personal 결정
            if business_type_mode.startswith("🤖"):
                is_personal = auto_is_personal
            elif business_type_mode.startswith("🏢"):
                is_personal = False
            else:  # 👤
                is_personal = True
            
            # 강제 적용 시 알림
            if not business_type_mode.startswith("🤖"):
                forced = "개인사업자" if is_personal else "법인"
                st.info(f"📌 **수동 강제: {forced}로 처리합니다.** (자동 판별 결과 무시)")
            
            if is_personal:
                chapter_count_caption = "약 30페이지 (개인사업자 맞춤 + 상속세 플랜)"
            elif has_tax_doc:
                chapter_count_caption = "약 51페이지"
            else:
                chapter_count_caption = "약 49페이지"
            st.caption(f"필요한 챕터만 선택해서 맞춤형 리포트를 생성할 수 있습니다 · 모두 선택 시 전체 리포트({chapter_count_caption}) 생성")
            
            if is_personal:
                st.success("👤 **개인사업자 모드** — 종합소득세 기반 분석 (비상장주식·임원퇴직금·배당·정관 챕터는 개인사업자에게 해당없어 자동 비활성화됩니다)")
            elif has_tax_doc:
                st.success("✨ **세무조정계산서 인식됨** — '세무 심층진단' 챕터(2페이지)가 추가로 활성화되었습니다!")
            
            # 모드 안내: sampling/simple은 챕터 선택이 자동
            if report_mode != "full":
                st.info("ℹ️ 현재 모드는 챕터 구성이 자동으로 결정됩니다. 아래 체크박스를 만져도 무시됩니다. 자유롭게 챕터를 고르려면 위에서 **📚 풀버전**을 선택하세요.")
            
            ch_cols1 = st.columns(3)
            ch_cols2 = st.columns(3)
            ch_cols3 = st.columns(3)
            
            with ch_cols1[0]:
                ch_finance = st.checkbox("📊 **기업재무분석**", value=True, 
                    help="재무상태표·손익계산서·재무비율·경비분석 (약 7페이지)")
            with ch_cols1[1]:
                # 세무 심층진단: 세무조정계산서가 있을 때만 활성화
                tax_deep_label = "💼 **종합소득세 심층진단** ⭐NEW" if is_personal else "💼 **세무 심층진단** ⭐NEW"
                tax_deep_help = "종합소득세 조정 결과·절세 효율 분석 (약 2페이지)" if is_personal else "법인세 조정 결과·절세 효율·손금불산입 리스크 분석 (약 2페이지) · 세무조정계산서 업로드 시 활성화"
                ch_tax_deep = st.checkbox(tax_deep_label, 
                    value=has_tax_doc, 
                    disabled=not has_tax_doc,
                    help=tax_deep_help)
            with ch_cols1[2]:
                ch_credit = st.checkbox("🏦 **신용등급 관리**", value=True,
                    help="신용등급 진단·등급 가이드·ROE/현금흐름 (약 3페이지)")
            
            with ch_cols2[0]:
                # 개인사업자는 비상장주식 개념 없음 → 자동 OFF + 비활성
                ch_valuation = st.checkbox("📈 **기업가치평가**", 
                    value=(not is_personal),
                    disabled=is_personal,
                    help="비상장주식 가치·상속세 시뮬레이션 (약 4페이지) · 개인사업자는 해당없음")
            with ch_cols2[1]:
                # 개인사업자는 본인=대표 → 임원보상 개념 없음
                ch_executive = st.checkbox("👔 **임원소득보상플랜**",
                    value=(not is_personal),
                    disabled=is_personal,
                    help="급여·배당·퇴직금 시뮬레이션 (약 3페이지) · 개인사업자는 해당없음")
            with ch_cols2[2]:
                # 개인사업자는 배당 개념 없음
                ch_dividend = st.checkbox("💰 **배당플랜**",
                    value=(not is_personal),
                    disabled=is_personal,
                    help="배당전략·미처분이익잉여금·종신보험 (약 4페이지) · 개인사업자는 해당없음")
            
            with ch_cols3[0]:
                # 개인사업자도 인증/벤처/특허는 활용 가능 → 챕터 자체는 활성화
                # (정관/법인관리 페이지는 페이지별 토글에서 기본 OFF)
                governance_label = "📋 **기업제도정비**" + (" 🔄" if is_personal else "")
                governance_help = ("정관/법인관리 자동 제외, 인증·벤처·특허 페이지만 표시 (약 3페이지)" 
                                  if is_personal 
                                  else "정관·법인관리·인증·특허전략 (약 6페이지)")
                ch_governance = st.checkbox(governance_label,
                    value=True,  # 개인/법인 둘 다 기본 ON
                    help=governance_help)
            with ch_cols3[1]:
                ch_labor = st.checkbox("⚖️ **노무 컨설팅**", value=True,
                    help="노동법체크·5인비교·비과세수당 + 판례 기반 심층 11페이지 (약 16페이지)")
            with ch_cols3[2]:
                ch_subsidy = st.checkbox("💼 **고용지원금**", value=True,
                    help="신청 가능한 고용지원금 + 상세 정보 (약 5페이지)")
            
            # 4번째 줄: RSV 핵심 가치 + (개인사업자만) 상속세 플랜
            if is_personal:
                ch_final_cols = st.columns(2)
                with ch_final_cols[0]:
                    ch_personal_inheritance = st.checkbox(
                        "💰 **상속세 플랜** ⭐NEW", value=True,
                        help="개인사업자 맞춤 상속세 시뮬·가업상속공제·종신보험 재원 마련 (약 4페이지)"
                    )
                with ch_final_cols[1]:
                    ch_insurance = st.checkbox("🛡️ **RSV 핵심 가치**", value=True,
                        help="보험 가입의 진짜 의미 (마지막 페이지)")
            else:
                ch_personal_inheritance = False
                ch_insurance = st.checkbox("🛡️ **RSV 핵심 가치**", value=True,
                    help="보험 가입의 진짜 의미 (마지막 페이지)")
            
            selected_pages = {
                "finance": ch_finance, "tax_deep": ch_tax_deep and has_tax_doc,
                "credit": ch_credit, "valuation": ch_valuation and (not is_personal),
                "executive": ch_executive and (not is_personal),
                "dividend": ch_dividend and (not is_personal),
                "governance": ch_governance,  # 개인사업자도 가능 (페이지별 처리)
                "labor": ch_labor, "subsidy": ch_subsidy, "insurance_final": ch_insurance,
                "personal_inheritance": ch_personal_inheritance and is_personal,  # 🆕 개인사업자 상속세 플랜
                "is_personal": is_personal,
            }
            
            # ─── 페이지별 세부 토글 (펼침 메뉴) ───
            with st.expander("🔧 **페이지 단위 세부 조정** (펼쳐서 원하지 않는 페이지 끄기)", expanded=False):
                st.caption("기본은 모두 켜져 있습니다. 특정 페이지만 끄고 싶으면 체크 해제하세요. 큰 챕터가 꺼져있으면 해당 페이지들은 무관합니다.")
                
                # 1) 기업재무분석 (7페이지)
                if ch_finance:
                    st.markdown("**📊 기업재무분석** (7페이지)")
                    fc = st.columns(4)
                    with fc[0]: p1 = st.checkbox("기업개요", value=True, key="p_fin_overview")
                    with fc[1]: p2 = st.checkbox("재무상태표", value=True, key="p_fin_bs")
                    with fc[2]: p3 = st.checkbox("손익계산서", value=True, key="p_fin_is")
                    with fc[3]: p4 = st.checkbox("재무 요약", value=True, key="p_fin_summary")
                    fc2 = st.columns(4)
                    with fc2[0]: p5 = st.checkbox("재무비율(1)", value=True, key="p_fin_ratio1")
                    with fc2[1]: p6 = st.checkbox("재무비율(2)", value=True, key="p_fin_ratio2")
                    with fc2[2]: p7 = st.checkbox("경비 분석", value=True, key="p_fin_expense")
                    selected_pages.update({
                        "finance.overview": p1, "finance.bs": p2, "finance.is": p3,
                        "finance.summary": p4, "finance.ratio1": p5, "finance.ratio2": p6,
                        "finance.expense": p7,
                    })
                
                # 2) 세무 심층진단 (최대 7페이지: 기본 2 + 컨설팅 5)
                if ch_tax_deep and has_tax_doc:
                    label_prefix = "💼 종합소득세 심층진단" if is_personal else "💼 세무 심층진단"
                    st.markdown(f"**{label_prefix}** (최대 7페이지)")
                    tc = st.columns(4)
                    with tc[0]: t1 = st.checkbox("계산 흐름", value=True, key="p_tax_eff")
                    with tc[1]: t2 = st.checkbox("리스크 진단", value=True, key="p_tax_exp")
                    with tc[2]: t3 = st.checkbox("접대비 점검", value=True, key="p_tax_ent")
                    with tc[3]: t4 = st.checkbox("차량 분석", value=True, key="p_tax_veh")
                    tc2 = st.columns(4)
                    with tc2[0]: t5 = st.checkbox("감가상각", value=True, key="p_tax_dep")
                    with tc2[1]: t6 = st.checkbox("고용 진단", value=True, key="p_tax_emp")
                    with tc2[2]: t7 = st.checkbox("절세 마스터리", value=True, key="p_tax_mast")
                    selected_pages.update({
                        "tax_deep.efficiency": t1, "tax_deep.expense": t2,
                        "tax_deep.entertainment": t3, "tax_deep.vehicle": t4,
                        "tax_deep.depreciation": t5, "tax_deep.employment": t6,
                        "tax_deep.mastery": t7,
                    })
                
                # 3) 신용등급 관리 (3페이지)
                if ch_credit:
                    st.markdown("**🏦 신용등급 관리** (3페이지)")
                    cc = st.columns(3)
                    with cc[0]: c1 = st.checkbox("신용등급 현황", value=True, key="p_cre_main")
                    with cc[1]: c2 = st.checkbox("등급 가이드", value=True, key="p_cre_guide")
                    with cc[2]: c3 = st.checkbox("ROE·현금흐름", value=True, key="p_cre_prof")
                    selected_pages.update({
                        "credit.main": c1, "credit.guide": c2, "credit.profitability": c3,
                    })
                
                # 4) 기업가치평가 (법인만, 4페이지)
                if ch_valuation and not is_personal:
                    st.markdown("**📈 기업가치평가** (4페이지)")
                    vc = st.columns(4)
                    with vc[0]: v1 = st.checkbox("주식 가치평가", value=True, key="p_val_main")
                    with vc[1]: v2 = st.checkbox("세금 안내", value=True, key="p_val_tax")
                    with vc[2]: v3 = st.checkbox("상속세 시뮬", value=True, key="p_val_inh")
                    with vc[3]: v4 = st.checkbox("상속세 공제", value=True, key="p_val_ded")
                    selected_pages.update({
                        "valuation.main": v1, "valuation.tax_ref": v2,
                        "valuation.inheritance": v3, "valuation.deduction": v4,
                    })
                
                # 5) 임원소득보상플랜 (법인만, 3페이지)
                if ch_executive and not is_personal:
                    st.markdown("**👔 임원소득보상플랜** (3페이지)")
                    ec = st.columns(3)
                    with ec[0]: e1 = st.checkbox("보상플랜 개요", value=True, key="p_exe_over")
                    with ec[1]: e2 = st.checkbox("급여 세금", value=True, key="p_exe_sal")
                    with ec[2]: e3 = st.checkbox("퇴직금 플랜", value=True, key="p_exe_ret")
                    selected_pages.update({
                        "executive.overview": e1, "executive.salary": e2, "executive.retirement": e3,
                    })
                
                # 6) 배당플랜 (법인만, 4페이지)
                if ch_dividend and not is_personal:
                    st.markdown("**💰 배당플랜** (4페이지)")
                    dc = st.columns(4)
                    with dc[0]: d1 = st.checkbox("배당 전략", value=True, key="p_div_str")
                    with dc[1]: d2 = st.checkbox("미처분이익", value=True, key="p_div_ret")
                    with dc[2]: d3 = st.checkbox("법인보험", value=True, key="p_div_ins")
                    with dc[3]: d4 = st.checkbox("상속 재원", value=True, key="p_div_inh")
                    selected_pages.update({
                        "dividend.strategy": d1, "dividend.retained": d2,
                        "dividend.insurance": d3, "dividend.inheritance": d4,
                    })
                
                # 7) 기업제도정비 (개인사업자는 정관/법인관리 자동 OFF)
                if ch_governance:
                    if is_personal:
                        st.markdown("**📋 기업제도정비** (3페이지 · 개인사업자 모드)")
                        st.caption("👤 개인사업자에게 정관·법인관리는 부적용 → 자동 제외")
                        gc = st.columns(3)
                        with gc[0]: g3 = st.checkbox("업종별 인증전략", value=True, key="p_gov_cert")
                        with gc[1]: g4 = st.checkbox("벤처/연구소", value=True, key="p_gov_cdet")
                        with gc[2]: g5 = st.checkbox("특허 전략", value=True, key="p_gov_pat")
                        selected_pages.update({
                            "governance.articles": False,    # 정관 OFF
                            "governance.management": False,  # 법인관리 OFF
                            "governance.certification": g3,
                            "governance.cert_detail": g4,
                            "governance.patent": g5,
                        })
                    else:
                        st.markdown("**📋 기업제도정비** (5페이지)")
                        gc = st.columns(5)
                        with gc[0]: g1 = st.checkbox("정관 개정", value=True, key="p_gov_art")
                        with gc[1]: g2 = st.checkbox("법인 관리", value=True, key="p_gov_mng")
                        with gc[2]: g3 = st.checkbox("업종별 인증", value=True, key="p_gov_cert")
                        with gc[3]: g4 = st.checkbox("벤처/연구소", value=True, key="p_gov_cdet")
                        with gc[4]: g5 = st.checkbox("특허 전략", value=True, key="p_gov_pat")
                        selected_pages.update({
                            "governance.articles": g1,
                            "governance.management": g2,
                            "governance.certification": g3,
                            "governance.cert_detail": g4,
                            "governance.patent": g5,
                        })
                
                # 7.5) 🆕 개인사업자 상속세 플랜 (4페이지)
                if ch_personal_inheritance and is_personal:
                    st.markdown("**💰 상속세 플랜** (4페이지 · 개인사업자 전용)")
                    pic = st.columns(4)
                    with pic[0]: pi1 = st.checkbox("상속세 시뮬", value=True, key="p_pi_sim")
                    with pic[1]: pi2 = st.checkbox("가업상속공제", value=True, key="p_pi_succ")
                    with pic[2]: pi3 = st.checkbox("종신보험 재원", value=True, key="p_pi_ins")
                    with pic[3]: pi4 = st.checkbox("상속세 공제", value=True, key="p_pi_ded")
                    selected_pages.update({
                        "personal_inheritance.tax_sim": pi1,
                        "personal_inheritance.succession": pi2,
                        "personal_inheritance.insurance": pi3,
                        "personal_inheritance.deduction": pi4,
                    })
                
                # 8) 노무 컨설팅 (기본 5 + 심층 11 = 16페이지)
                if ch_labor:
                    st.markdown("**⚖️ 노무 컨설팅 — 기본** (5페이지)")
                    lc1 = st.columns(5)
                    with lc1[0]: l1 = st.checkbox("컨설턴트 역할", value=True, key="p_lab_role")
                    with lc1[1]: l2 = st.checkbox("규모별 이슈", value=True, key="p_lab_chk")
                    with lc1[2]: l3 = st.checkbox("13대 체크", value=True, key="p_lab_comp")
                    with lc1[3]: l4 = st.checkbox("5인 비교", value=True, key="p_lab_5p")
                    with lc1[4]: l5 = st.checkbox("비과세 수당", value=True, key="p_lab_nontax")
                    
                    st.markdown("**⚖️ 노무 컨설팅 — 심층 (판례·법규 기반)** (11페이지)")
                    lc2 = st.columns(4)
                    with lc2[0]: l6 = st.checkbox("퇴직금 함정", value=True, key="p_lab_sev")
                    with lc2[1]: l7 = st.checkbox("포괄임금·통상임금", value=True, key="p_lab_inc")
                    with lc2[2]: l8 = st.checkbox("부당해고 예방", value=True, key="p_lab_dis")
                    with lc2[3]: l9 = st.checkbox("괴롭힘·성희롱", value=True, key="p_lab_har")
                    lc3 = st.columns(4)
                    with lc3[0]: l10 = st.checkbox("연차 산정", value=True, key="p_lab_ann")
                    with lc3[1]: l11 = st.checkbox("임금체불 리스크", value=True, key="p_lab_wage")
                    with lc3[2]: l12 = st.checkbox("취업규칙", value=True, key="p_lab_rul")
                    with lc3[3]: l13 = st.checkbox("육아휴직", value=True, key="p_lab_par")
                    lc4 = st.columns(3)
                    with lc4[0]: l14 = st.checkbox("외국인·고령자", value=True, key="p_lab_for")
                    with lc4[1]: l15 = st.checkbox("노동 분쟁 대응", value=True, key="p_lab_disp")
                    with lc4[2]: l16 = st.checkbox("⭐ 자가진단표", value=True, key="p_lab_diag")
                    
                    selected_pages.update({
                        "labor.consultant_role": l1, "labor.checklist": l2,
                        "labor.compliance": l3, "labor.5person": l4, "labor.nontax": l5,
                        "labor.severance": l6, "labor.inclusive_wage": l7,
                        "labor.dismissal": l8, "labor.harassment": l9,
                        "labor.annual_leave": l10, "labor.wage_arrears": l11,
                        "labor.rules": l12, "labor.parental_leave": l13,
                        "labor.foreign_senior": l14, "labor.dispute": l15,
                        "labor.risk_diagnosis": l16,
                    })
            
            n_selected = sum(1 for k, v in selected_pages.items() 
                            if v and not k.startswith(("finance.", "tax_deep.", "credit.", "valuation.", 
                                                       "executive.", "dividend.", "governance.", "labor."))
                            and k != "is_personal")
            
            if n_selected == 0:
                st.warning("⚠️ 최소 1개 챕터는 선택해주세요.")
            else:
                st.info(f"✅ **{n_selected}개 챕터** 선택됨")
            
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            if st.button("🚀 리포트 생성", type="primary", use_container_width=True, disabled=(n_selected == 0)):
                with st.spinner("PDF 생성 중..."):
                    sim_params = {
                        "monthly_salary": sim_monthly,
                        "biz_profit": sim_profit,
                        "corp_tax_rate": sim_corprate,
                        "hope_amount": sim_hope,
                        "tenure": sim_tenure,
                        "retire_year": sim_retire_year,
                    }
                    html = generate_report_html(company=company, bs=bs, isc=isc, mfg=mfg,
                        ratios=ratios, valuation=valuation, credit=credit,
                        author_name=author_display, author_org=author_org_display, author_phone=author_phone,
                        sim_params=sim_params, selected_pages=selected_pages, tax_deep=tax_deep,
                        report_mode=st.session_state.get("report_mode", "full"))
                    
                    # ─── 사용량 로그 기록 ───
                    try:
                        # 파일 종류 식별
                        if has_tax_doc:
                            file_type_log = "personal_tax_pdf" if is_personal else "corporate_tax_pdf"
                        elif file_map.get("overview") and file_map["overview"].name.lower().endswith(('.xls', '.xlsx')):
                            file_type_log = "crehard_xlsx"
                        else:
                            file_type_log = "crehard_pdf"
                        
                        # 선택된 큰 챕터 수만 카운트 (페이지별 토글은 제외)
                        n_chap = sum(1 for k, v in selected_pages.items() 
                                    if v and "." not in k and k != "is_personal")
                        # 페이지 수 추정 (HTML class="page" 개수)
                        n_pg = html.count('class="page ')
                        
                        log_report_generation(
                            email=st.session_state.get("user_email", ""),
                            company_name=company.get("기업명", ""),
                            file_type=file_type_log,
                            is_personal=is_personal,
                            n_chapters=n_chap,
                            n_pages=n_pg,
                        )
                    except Exception as _e:
                        print(f"사용량 로그 기록 실패 (무시): {_e}")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
                        out = f.name
                    result = generate_pdf(html, out)
                    if os.path.exists(result):
                        with open(result,'rb') as f:
                            data = f.read()
                        cname = company.get("기업명","기업")
                        ext = "pdf" if result.endswith('.pdf') else "html"
                        st.success(f"✅ {'PDF' if ext=='pdf' else 'HTML'} 생성 완료!")
                        st.download_button(f"📥 다운로드", data=data,
                            file_name=f"{cname}_재무경영진단리포트.{ext}",
                            mime="application/pdf" if ext=="pdf" else "text/html",
                            use_container_width=True)
                        os.unlink(result)
        except Exception as e:
            st.error(str(e))
            import traceback; st.code(traceback.format_exc())
        finally:
            for p in saved_paths:
                if os.path.exists(p): os.unlink(p)
    else:
        st.info("👈 사이드바에서 엑셀/PDF 파일을 업로드해주세요. 파일명으로 자동 분류됩니다.")
        c1, c2 = st.columns(2)
        c1.markdown("""
        **엑셀 파일 (ETFI112E1 시리즈)**
        - `ETFI112E1.xlsx` — 재무상태표 **(필수)**
        - `ETFI112E1__1_.xlsx` — 손익계산서 **(필수)**
        - `ETFI112E1__2_.xlsx` — 이익잉여금처분계산서
        - `ETFI112E1__3_.xlsx` 또는 `__5_` — 제조원가명세서
        - `ETFI112E1__4_.xlsx` — 현금흐름표
        - `ETFI112E1__6_.xlsx` — 자본변동표
        """)
        c2.markdown("""
        **PDF 파일**
        - `개요.pdf` — CRETOP 기업 브리핑 보고서
        - `신용.pdf` — CRETOP 기업 신용등급 보고서
        
        **한 번에 모두 선택하여 업로드 가능!**
        3개~8개 파일을 한꺼번에 드래그하세요.
        """)

# ══════════════════════════════════════
# 라우팅
# ══════════════════════════════════════
if not st.session_state.logged_in:
    show_login_page()
else:
    show_main_page()
