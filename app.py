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
    get_user_profile, update_user_profile
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
</style>
""", unsafe_allow_html=True)

for key, val in [("logged_in", False), ("user_email", ""), ("user_name", "")]:
    if key not in st.session_state:
        st.session_state[key] = val

def logout():
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_name = ""

# ══════════════════════════════════════
# 로그인 페이지
# ══════════════════════════════════════
def show_login_page():
    st.markdown("")
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="login-title">📊 재무경영진단 리포트</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">사용하려면 관리자 승인이 필요합니다</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("이메일", placeholder="example@company.com")
            name = st.text_input("이름", placeholder="홍길동")
            org = st.text_input("소속", placeholder="중소기업경영지원단")
            submitted = st.form_submit_button("로그인 / 승인 요청", use_container_width=True, type="primary")
        if submitted and email:
            email = email.strip().lower()
            status = check_user_status(email)
            if status == "approved":
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = name or email
                st.rerun()
            elif status == "pending":
                st.markdown('<div class="status-pending">⏳ 승인 대기 중입니다. 관리자가 승인하면 이용 가능합니다.</div>', unsafe_allow_html=True)
            elif status == "rejected":
                st.markdown('<div class="status-rejected">❌ 승인이 거부되었습니다. 관리자에게 문의하세요.</div>', unsafe_allow_html=True)
            else:
                if not name:
                    st.warning("이름을 입력해주세요.")
                else:
                    approved = request_approval(email, name, org)
                    if approved:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.user_name = name
                        st.rerun()
                    else:
                        st.success("✅ 승인 요청이 완료되었습니다! 관리자 승인 후 이용 가능합니다.")
        st.markdown(f"<p style='text-align:center;color:#999;font-size:12px;margin-top:20px;'>관리자: {ADMIN_EMAIL}</p>", unsafe_allow_html=True)

# ══════════════════════════════════════
# 관리자 패널
# ══════════════════════════════════════
def show_admin_panel():
    st.markdown("## 🔧 관리자 패널")
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
        tab_report, tab_admin = st.tabs(["📊 리포트 생성", "🔧 관리자 패널"])
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
        
        author_name = st.text_input("작성자명", value=profile.get("name", st.session_state.user_name))
        author_org = st.text_input("소속", value=profile.get("org", ""))
        author_title = st.text_input("직급", value=profile.get("title", ""), placeholder="예: 지사장, 팀장, 대표")
        author_phone = st.text_input("연락처", value=profile.get("phone", ""), placeholder="010-0000-0000")
        
        if st.button("💾 내 정보 저장", use_container_width=True):
            update_user_profile(st.session_state.user_email, author_name, author_org, author_title, author_phone)
            st.session_state.user_name = author_name
            st.success("저장 완료!")
        
        # 리포트에 표시될 작성자 정보 조합
        author_display = f"{author_name} {author_title}".strip() if author_title else author_name
        author_org_display = author_org
        
        st.markdown("---")
        st.header("📁 파일 업로드")
        st.caption("엑셀(ETFI112E1 시리즈)과 PDF를 한번에 업로드하세요. 파일명으로 자동 분류됩니다.")
        
        uploaded_files = st.file_uploader(
            "엑셀/PDF 파일을 모두 선택하세요",
            type=["xlsx", "xls", "pdf"],
            accept_multiple_files=True,
            key="all_files",
            help="ETFI112E1.xlsx, ETFI112E1__1_.xlsx 등 엑셀 파일과 개요.pdf, 신용.pdf를 한꺼번에 업로드"
        )
        
        # 파일 자동 분류
        file_map = {"bs": None, "is": None, "mfg": None, "re": None, "cf": None, "ce": None, "overview": None, "credit": None}
        if uploaded_files:
            for f in uploaded_files:
                name = f.name.lower()
                if name.endswith(('.xlsx', '.xls')):
                    if '__1_' in name or '__1__' in name or '(1)' in name:
                        file_map["is"] = f        # 손익계산서
                    elif '__2_' in name or '__2__' in name or '(2)' in name:
                        file_map["re"] = f        # 이익잉여금처분계산서
                    elif '__3_' in name or '__3__' in name or '(3)' in name:
                        file_map["mfg"] = f       # 제조원가명세서 (번호 다를 수 있음)
                    elif '__4_' in name or '__4__' in name or '(4)' in name:
                        file_map["cf"] = f        # 현금흐름표
                    elif '__5_' in name or '__5__' in name or '(5)' in name:
                        file_map["mfg"] = f       # 제조원가명세서
                    elif '__6_' in name or '__6__' in name or '(6)' in name:
                        file_map["ce"] = f        # 자본변동표
                    elif 'etfi' in name and '__' not in name and '(' not in name:
                        file_map["bs"] = f        # 재무상태표 (번호 없는 기본 파일)
                    else:
                        # 번호 없는 엑셀은 재무상태표로 추정
                        if file_map["bs"] is None:
                            file_map["bs"] = f
                elif name.endswith('.pdf'):
                    if '개요' in name or 'overview' in name or '브리핑' in name:
                        file_map["overview"] = f
                    elif '신용' in name or 'credit' in name or '등급' in name:
                        file_map["credit"] = f
                    elif file_map["overview"] is None:
                        file_map["overview"] = f
                    elif file_map["credit"] is None:
                        file_map["credit"] = f
            
            # 분류 결과 표시
            st.markdown("**📋 파일 분류 결과:**")
            labels = {
                "bs": "📊 재무상태표", "is": "📈 손익계산서", "mfg": "🏭 제조원가명세서",
                "re": "💰 이익잉여금처분", "cf": "💵 현금흐름표", "ce": "📑 자본변동표",
                "overview": "📄 기업 브리핑 PDF", "credit": "🏦 신용등급 PDF"
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
        
        st.markdown("---")
        st.subheader("📈 기업가치 평가 설정")
        shares = st.number_input("발행주식수", min_value=0, value=0, step=1000)
        par_value = st.number_input("액면가", min_value=0, value=5000, step=500)

    def save_file(f):
        ext = os.path.splitext(f.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(f.getbuffer())
            return tmp.name

    # 필수: 재무상태표 + 손익계산서 (제조원가는 선택)
    has_required = file_map["bs"] and file_map["is"]
    
    if has_required:
        saved_paths = []
        bs_path = save_file(file_map["bs"]); saved_paths.append(bs_path)
        is_path = save_file(file_map["is"]); saved_paths.append(is_path)
        mfg_path = save_file(file_map["mfg"]) if file_map["mfg"] else None
        if mfg_path: saved_paths.append(mfg_path)
        ov_path = save_file(file_map["overview"]) if file_map["overview"] else None
        if ov_path: saved_paths.append(ov_path)
        cr_path = save_file(file_map["credit"]) if file_map["credit"] else None
        if cr_path: saved_paths.append(cr_path)
        try:
            with st.spinner("📊 분석 중..."):
                bs = parse_balance_sheet(bs_path)
                isc = parse_income_statement(is_path)
                mfg = parse_manufacturing_cost(mfg_path) if mfg_path else {"years": bs.get("years", []), "raw": {}}
                company = parse_company_overview(ov_path)
                credit = parse_credit_report(cr_path) if cr_path else {}
                ratios = calculate_ratios(bs, isc)
                valuation = calculate_valuation(bs, isc, shares=shares or None, par_value=par_value)
            years = bs.get("years", [])
            yl = [y.replace("-12-31","년") for y in years]
            if years:
                latest = years[-1]
                st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                cols = st.columns(6)
                for col, (lb, vl) in zip(cols, [
                    ("총자산", format_number(bs.get("자산",{}).get(latest),"억원")),
                    ("매출액", format_number(isc.get("매출액",{}).get(latest),"억원")),
                    ("영업이익", format_number(isc.get("영업이익",{}).get(latest),"억원")),
                    ("당기순이익", format_number(isc.get("당기순이익",{}).get(latest),"억원")),
                    ("부채비율", f"{ratios.get('부채비율',{}).get(latest,0) or 0:.1f}%"),
                    ("ROE", f"{ratios.get('ROE',{}).get(latest,0) or 0:.1f}%"),
                ]):
                    with col:
                        st.markdown(f'<div class="metric-card"><div class="metric-label">{lb}</div><div class="metric-value">{vl}</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            if st.button("🚀 리포트 생성", type="primary", use_container_width=True):
                with st.spinner("PDF 생성 중..."):
                    html = generate_report_html(company=company, bs=bs, isc=isc, mfg=mfg,
                        ratios=ratios, valuation=valuation, credit=credit,
                        author_name=author_display, author_org=author_org_display, author_phone=author_phone)
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
