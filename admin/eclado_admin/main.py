import streamlit as st

from eclado_admin.demo_auth import DEMO_EMAIL, logout_demo, require_demo_login
from eclado_admin.sales_pages import render_sales_page
from eclado_admin.ui_theme import apply_theme, brand

st.set_page_config(page_title="ECLADO | 사장님 대시보드", page_icon="🌿", layout="wide")
apply_theme()
require_demo_login()

with st.sidebar:
    brand()
    st.caption("MARKETING INTELLIGENCE · Ver.1 초안")
    st.caption(f"{DEMO_EMAIL} · 데모 로그인")
    st.button("로그아웃", on_click=logout_demo, key="demo_logout", use_container_width=True)
    st.divider()
    st.markdown("### 매출 분석")
    sales_page = st.radio(
        "분석 메뉴",
        ["매출 요약", "매출 추이", "고객별 매출 추이", "매출·상품·리뷰 AI"],
        key="sales_page",
        label_visibility="collapsed",
    )

render_sales_page(sales_page)
