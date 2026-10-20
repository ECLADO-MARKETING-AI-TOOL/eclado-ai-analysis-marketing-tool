"""Presentation helpers for the ECLADO admin preview."""

from base64 import b64encode
from html import escape
from pathlib import Path

import streamlit as st

CHART_COLORS = ["#2534a4", "#69b5f5", "#8a85cf", "#28a3b6"]


def apply_theme() -> None:
    st.markdown(
        """
<style>
:root { --eclado-blue:#2534a4; --eclado-ink:#172343; }
.stApp { background:#f5f7fc; color:var(--eclado-ink); }
[data-testid="stMainBlockContainer"] { padding-top:2.7rem; max-width:1700px; }
h1,h2,h3 { color:var(--eclado-ink); letter-spacing:-.035em; }
h1 { font-size:2rem!important; }
h2 { font-size:1.4rem!important; }
h3 { font-size:1.12rem!important; }
[data-testid="stCaptionContainer"] { color:#71809b; }
[data-testid="stSidebar"] {
 background:linear-gradient(165deg,#111a39 0%,#172447 65%,#223661 100%);
 color:#edf3ff; border-right:1px solid #23345a;
}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:#edf3ff; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#b0c1e1; }
[data-testid="stSidebar"] hr { border-color:#ffffff20; }
[data-testid="stSidebar"] [data-baseweb="select"]>div,
[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="base-input"] {
 background:#25365b; color:#f4f7ff; border-color:#4d638b;
}
[data-testid="stSidebar"] input { color:#f4f7ff; }
[data-testid="stSidebar"] button { background:#25365b; color:#edf3ff; border-color:#50658e; }
.st-key-primary_nav [role="radiogroup"],.st-key-sales_page [role="radiogroup"] { gap:7px; }
.st-key-primary_nav [role="radiogroup"] label,
.st-key-sales_page [role="radiogroup"] label {
 padding:12px 14px; margin:0; border-radius:13px; width:100%;
 transition:background .15s ease;
}
.st-key-primary_nav label:hover,.st-key-sales_page label:hover { background:#ffffff12; }
.st-key-primary_nav label:has(input:checked),.st-key-sales_page label:has(input:checked) {
 background:linear-gradient(110deg,#3148bb,#487fd5); box-shadow:0 5px 18px #080f292b;
}
.st-key-primary_nav label:focus-within,.st-key-sales_page label:focus-within {
 outline:2px solid #8dcfff; outline-offset:2px;
}
.st-key-sales_page [data-testid="stMarkdownContainer"] p::before { content:'└ '; color:#91b7ee; }
[data-testid="stMetric"] {
 background:white; border:1px solid #e0e6f1; border-radius:18px;
 padding:22px 20px; min-height:145px; box-shadow:0 3px 12px #17234306;
}
[data-testid="stMetricLabel"] { color:#71809b; }
[data-testid="stMetricValue"] { font-size:1.85rem; font-weight:750; letter-spacing:-.04em; }
.st-key-kpi_primary [data-testid="stColumn"]:first-child [data-testid="stMetric"] {
 background:linear-gradient(125deg,#2534a4,#477acb 70%,#6daeea); border-color:transparent;
}
.st-key-kpi_primary [data-testid="stColumn"]:first-child [data-testid="stMetric"] * { color:white; }
div[class*="st-key-panel_"] {
 background:white; padding:22px; border:1px solid #e0e6f1;
 border-radius:18px; box-shadow:0 3px 12px #17234306;
}
[data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button {
 border-radius:11px; min-height:43px;
}
button[kind="primaryFormSubmit"],button[kind="primary"] {
 background:linear-gradient(110deg,#2534a4,#487fd5); color:white;
}
[data-baseweb="tab-highlight"] { background:#2534a4; }
.eclado-brand { display:flex; flex-direction:column; gap:12px; padding:4px 0 18px; }
.eclado-brand-logo { background:white; border:1px solid #dce6fa;
 border-radius:14px; padding:18px 20px; }
.eclado-brand-logo img { display:block; width:100%; max-width:230px;
 height:auto; margin:0 auto; }
.eclado-brand small { color:#b0c1e1; display:block; font-size:11px; text-align:center; }
.eclado-login-header { text-align:center; padding:22px 12px 32px; margin:0 auto 10px; }
.eclado-login-header img { display:block; width:210px; max-width:55vw;
 height:auto; margin:0 auto 24px; }
.eclado-login-header h1 { font-family:"Malgun Gothic","Apple SD Gothic Neo",sans-serif;
 color:#2534a4; font-size:clamp(1.55rem,3vw,2.5rem)!important;
 font-weight:750; line-height:1.4; letter-spacing:-.045em; padding:0; text-wrap:balance; }
.eclado-login-header p { color:#64769a; font-size:15px; margin:14px 0 0; }
[data-testid="stAppViewContainer"]:has(.eclado-login-header) {
 background:radial-gradient(ellipse at 15% 12%,#dceeff 0%,transparent 55%),
 radial-gradient(ellipse at 90% 75%,#e6e3fa 0%,transparent 50%),#f5f7fc;
}
.st-key-panel_login { border-top:3px solid #69b5f5!important;
 box-shadow:0 12px 40px #2534a410!important; }
.eclado-bars { display:grid; gap:17px; margin:20px 0; }
.eclado-bar-row { display:grid; grid-template-columns:minmax(70px,1fr) 2fr minmax(90px,auto);
 gap:14px; align-items:center; font-size:14px; }
.eclado-bar-track { height:12px; background:#edf0f8; border-radius:20px; position:relative; }
.eclado-bar-fill { height:12px; position:absolute; border-radius:20px;
 background:linear-gradient(90deg,#8dcfff,#384bb8); }
.eclado-bar-fill.negative { background:linear-gradient(90deg,#8a85cf,#bbb6ed); }
.eclado-bar-value { text-align:right; font-weight:700; }
.eclado-bar-zero { position:absolute; left:50%; top:-3px; height:18px;
 border-left:1px solid #8c99b5; }
@media(max-width:700px) {
 [data-testid="stMainBlockContainer"] { padding:1.5rem 1rem; }
 div[class*="st-key-panel_"] { padding:16px; }
 .eclado-bar-row { gap:8px; grid-template-columns:65px 1fr 100px; font-size:12px; }
}
</style>
""",
        unsafe_allow_html=True,
    )


def brand() -> None:
    logo = Path(__file__).with_name("assets") / "eclado-logo.png"
    encoded_logo = b64encode(logo.read_bytes()).decode("ascii")
    st.markdown(
        '<div class="eclado-brand"><div class="eclado-brand-logo">'
        f'<img src="data:image/png;base64,{encoded_logo}" alt="ECLADO LABORATORY 공식 로고">'
        '</div><small>관리자 콘솔</small></div>',
        unsafe_allow_html=True,
    )


def horizontal_bars(rows: list[tuple[str, int | None]], unit: str) -> None:
    """Display exact values while preserving missing values and negative refunds."""
    maximum = max((abs(value) for _, value in rows if value is not None), default=0)
    signed = any(value is not None and value < 0 for _, value in rows)
    rendered = []
    for label, value in rows:
        width = abs(value or 0) / maximum * (50 if signed else 100) if maximum else 0
        left = 50 - width if value is not None and value < 0 else (50 if signed else 0)
        negative = " negative" if value is not None and value < 0 else ""
        shown = "데이터 없음" if value is None else f"{value:,}{unit}"
        zero = '<span class="eclado-bar-zero"></span>' if signed else ""
        rendered.append(
            f'<div class="eclado-bar-row"><span>{escape(label)}</span>'
            f'<div class="eclado-bar-track" aria-hidden="true">{zero}'
            f'<span class="eclado-bar-fill{negative}" '
            f'style="left:{left:.3f}%;width:{width:.3f}%"></span></div>'
            f'<span class="eclado-bar-value">{escape(shown)}</span></div>'
        )
    if rows:
        st.markdown(
            '<div class="eclado-bars">' + "".join(rendered) + "</div>", unsafe_allow_html=True
        )
    else:
        st.caption("표시할 데이터가 없습니다.")
