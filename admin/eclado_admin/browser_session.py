"""Bridge tab storage to Streamlit without URL tokens or third-party scripts."""

from pathlib import Path
from uuid import uuid4

import streamlit as st
from streamlit.components.v2 import component

_session_component = component(
    "eclado_preview_session",
    js=(Path(__file__).with_name("assets") / "demo_session.js").read_text(encoding="utf-8"),
)


def browser_session(mode: str, token: str | None, expires: float | None) -> str | None:
    request_id = st.session_state.setdefault("demo_browser_request_id", uuid4().hex)
    result = _session_component(
        key="demo_browser_session",
        data={
            "mode": mode,
            "token": token,
            "expires": expires * 1000 if expires else None,
            "request_id": request_id,
        },
        default={"stored": None},
        on_stored_change=lambda: None,
        on_expired_change=lambda: None,
        height=0,
    )
    return result.stored if isinstance(result.stored, str) else None
