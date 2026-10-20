from datetime import date, timedelta

import httpx
import streamlit as st
from pydantic import ValidationError

from eclado_admin.repositories.dashboard_repository import DashboardRepository
from eclado_shared.schemas.sales import MonthlyChange, SalesAnalysis


def _change_table(rows: list[MonthlyChange]) -> None:
    if not rows:
        st.info("조건을 충족하는 비교 데이터가 없습니다.")
        return
    st.dataframe(
        [
            {
                "상품·연령층": row.label,
                "직전 30일 매출": row.previous,
                "최근 30일 매출": row.current,
                "직전 30일 일평균": row.previous_average,
                "최근 30일 일평균": row.current_average,
                "매출 증감액": row.delta,
                "매출 증감률(%)": round(row.percent, 2),
                "직전 주문수량": row.previous_units,
                "최근 주문수량": row.current_units,
                "주문수량 증감": row.units_delta,
                "주문수량 증감률(%)": round(row.units_percent, 2)
                if row.units_percent is not None
                else None,
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )


def render_product_insights(result: SalesAnalysis) -> None:
    st.caption("동일한 분석 데이터의 구매·환불·평점 기반 분석 · 생성형 AI 호출 없음")
    positive, negative = st.columns(2)
    for column, title, field in [
        (positive, "긍정적 리뷰 상품 Top 10", "positive"),
        (negative, "부정적 리뷰 상품 Top 10", "negative"),
    ]:
        with column, st.container(key=f"panel_review_{field}"):
            st.subheader(title)
            st.caption("선택 기간 작성 리뷰 · 긍정 4~5점 / 부정 1~2점 · 해당 리뷰 건수순")
            rows = sorted(
                [row for row in result.product_reviews if getattr(row, field) > 0],
                key=lambda row: (-getattr(row, field), row.product_id),
            )[:10]
            if rows:
                st.dataframe(
                    [
                        {
                            "순위": index + 1,
                            "상품": row.name,
                            "해당 리뷰": getattr(row, field),
                            "전체 리뷰": row.count,
                            "평균 평점": row.average_rating,
                        }
                        for index, row in enumerate(rows)
                    ],
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("선택 기간에 해당 리뷰가 없습니다.")
    with st.container(key="panel_review_rise"):
        st.subheader("리뷰가 갑자기 늘어난 상품 Top 10")
        st.caption("조회 종료일 기준 최근 7일 vs 직전 7일 · 증가 건수순 (초안 기준)")
        if result.review_rises:
            st.dataframe(
                [
                    {
                        "상품": row.name,
                        "직전 7일": row.previous,
                        "최근 7일": row.current,
                        "증가 건수": row.delta,
                        "증가율(%)": round(row.percent, 2) if row.percent is not None else None,
                        "비교 상태": "기준 0건·증가율 산출 불가"
                        if row.previous == 0
                        else "비교 가능",
                    }
                    for row in result.review_rises
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("증가한 상품이 없거나 14일 비교 이력이 부족합니다.")
    with st.container(key="panel_monthly_product_change"):
        st.subheader("월 이동평균 대비 매출 급변 상품 · 10% 이상")
        st.caption(
            "종료일 기준 최근 30일 일평균 vs 직전 30일 일평균 · 상승/하락 모두 포함. "
            "출시 후 30일 이내 상품 제외. "
            "주문수량은 환불 차감 전 결제 수량이며 매출은 환불 차감 후."
        )
        if not result.change_history_complete:
            st.info("60일 전체 비교 이력이 필요합니다. 누락 기간을 0원으로 채우지 않습니다.")
        else:
            _change_table(
                [
                    row
                    for row in result.monthly_product_changes
                    if row.launch_status == "established"
                ]
            )
            unknown = [
                row for row in result.monthly_product_changes if row.launch_status == "unknown"
            ]
            if unknown:
                st.warning("현재 데이터에 출시일이 없는 상품은 신제품 제외 여부를 확인해야 합니다.")
                with st.expander("출시일 확인 필요 · 매출 급변 후보", expanded=True):
                    _change_table(unknown)
        st.caption("직전 매출 0원·음수는 증감률을 산출하지 않아 급변 목록에서 제외합니다.")
    with st.container(key="panel_monthly_age_change"):
        st.subheader("매출이 급변한 연령층 · 10% 이상")
        st.caption("동일한 30일 비교 · 각 구간 기여 고객 5명 이상 · 구매 시점 연령 기준")
        _change_table(result.monthly_age_changes)
    with st.expander("공식 상품 카탈로그 · 용량/EAN/가격"):
        _catalog(result.start, result.end)


def _catalog(start: date, end: date) -> None:
    try:
        result = DashboardRepository().get_dashboard(
            "pending", start, min(end, start + timedelta(days=365))
        )
    except (httpx.HTTPError, ValidationError):
        st.error("공식 상품 카탈로그 API 연결을 확인해 주세요.")
        return
    st.caption("공식몰 표시 가격 · 거래 매출과 별개 · 기존 가격 유지")
    st.dataframe(
        [
            {
                "상품 ID": row.product_id,
                "상품명": row.name,
                "용량": " / ".join(spec.capacity for spec in row.specifications) or "확인 필요",
                "EAN": " / ".join(
                    f"{spec.capacity}: {spec.ean or '미기재'}" for spec in row.specifications
                )
                or "확인 필요",
                "판매가(원)": row.sale_price,
                "할인판매가(원)": row.discounted_price,
                "소비자가(원)": row.list_price,
            }
            for row in result.catalog
        ],
        hide_index=True,
        use_container_width=True,
    )
