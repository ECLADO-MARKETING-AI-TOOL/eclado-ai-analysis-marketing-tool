"""Local preview login only; provides no Supabase/API authentication or roles."""

from base64 import b64encode
from pathlib import Path

import httpx
import streamlit as st
from pydantic import ValidationError

from eclado_admin.browser_session import browser_session
from eclado_admin.demo_sessions import demo_sessions

DEMO_EMAIL = "user@example.com"
DEMO_USER_KEY = "eclado_demo_user"


def _submit_demo_login() -> None:
    email = str(st.session_state.get("demo_login_email", "")).strip().casefold()
    # Remove the submitted value before the following page renders.
    password = str(st.session_state.pop("demo_login_password", ""))
    if email != DEMO_EMAIL:
        st.session_state["demo_login_error"] = "데모 이메일 user@example.com을 입력해 주세요."
    elif not password:
        st.session_state["demo_login_error"] = "비밀번호는 아무 값이나 한 글자 이상 입력해 주세요."
    else:
        try:
            demo_sessions().revoke(st.session_state.get("demo_session_token"))
            token, _ = demo_sessions().issue()
        except (httpx.HTTPError, ValidationError):
            st.session_state["demo_login_error"] = (
                "로그인 서버 연결을 확인한 뒤 다시 시도해 주세요."
            )
            return
        st.session_state["demo_session_token"] = token
        st.session_state.pop("demo_session_clear", None)
        st.session_state[DEMO_USER_KEY] = DEMO_EMAIL
        st.session_state["demo_dashboard_mode"] = "공식몰 상품 · 실적 연동 대기"
        st.session_state.pop("demo_login_error", None)


def _restore_demo_login() -> bool:
    token = st.session_state.get("demo_session_token")
    expires = demo_sessions().expires_at(token)
    if token and expires is None:
        st.session_state.pop(DEMO_USER_KEY, None)
        st.session_state.pop("demo_session_token", None)
        st.session_state["demo_session_clear"] = True
        st.session_state["demo_login_error"] = "로그인 후 60분이 지나 다시 로그인해야 합니다."
    mode = "clear" if st.session_state.get("demo_session_clear") else "write" if expires else "read"
    stored = browser_session(mode, token if isinstance(token, str) else None, expires)
    if mode == "read":
        expires = demo_sessions().expires_at(stored)
        if expires is not None:
            st.session_state["demo_session_token"] = stored
    if expires is not None:
        st.session_state[DEMO_USER_KEY] = DEMO_EMAIL
        return True
    st.session_state.pop(DEMO_USER_KEY, None)
    return False


def require_demo_login() -> None:
    try:
        if _restore_demo_login():
            return
    except (httpx.HTTPError, ValidationError):
        st.error("로그인 유지 확인 서버에 연결할 수 없습니다. 잠시 후 새로고침해 주세요.")
        st.stop()
    logo = Path(__file__).with_name("assets") / "eclado-logo.png"
    encoded_logo = b64encode(logo.read_bytes()).decode("ascii")
    st.markdown(
        '<header class="eclado-login-header">'
        f'<img src="data:image/png;base64,{encoded_logo}" alt="ECLADO LABORATORY 로고">'
        '<h1>ECLADO 매출 분석 및 AI마케팅 도우미</h1>'
        '<p>매출과 고객의 흐름을 이해하고, 다음 마케팅을 준비하세요.</p></header>',
        unsafe_allow_html=True,
    )
    _, content, _ = st.columns([1, 1.5, 1])
    with content, st.container(key="panel_login"):
        st.subheader("관리자 데모 로그인")
        st.caption("로그인 후 매출·상품·고객 분석 화면으로 이동합니다.")
        st.caption("로그인 시점부터 60분간 유지됩니다. 같은 탭에서 새로고침해도 복원됩니다.")
        st.info("데모 계정: user@example.com · 비밀번호는 아무 값이나 입력하세요.")
        with st.form("demo_login", clear_on_submit=True):
            st.text_input("이메일", key="demo_login_email", placeholder=DEMO_EMAIL)
            st.text_input("비밀번호", key="demo_login_password", type="password")
            st.form_submit_button(
                "로그인", on_click=_submit_demo_login, use_container_width=True, type="primary"
            )
        error = st.session_state.pop("demo_login_error", None)
        if error:
            st.error(error)
        st.caption(
            "화면 검토용 데모 로그인입니다. 실제 Supabase 직원 인증은 아직 연결되지 않았습니다."
        )
    st.stop()


def logout_demo() -> None:
    failed = False
    try:
        demo_sessions().revoke(st.session_state.get("demo_session_token"))
    except (httpx.HTTPError, ValidationError):
        failed = True
    # Reset this browser session, including filters and any widget values.
    for key in list(st.session_state):
        del st.session_state[key]
    st.session_state["demo_session_clear"] = True
    if failed:
        st.session_state["demo_login_error"] = (
            "브라우저 로그인은 해제됐지만 서버 연결 확인이 필요합니다."
        )
