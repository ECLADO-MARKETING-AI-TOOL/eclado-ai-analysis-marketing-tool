import json
from datetime import UTC, date, datetime, timedelta

import httpx
import streamlit as st
from pydantic import ValidationError

from eclado_admin.product_insights_page import render_product_insights
from eclado_admin.repositories.sales_repository import SalesRepository
from eclado_admin.ui_theme import CHART_COLORS, horizontal_bars
from eclado_shared.schemas.sales import (
    DummySalesDataset,
    Persona,
    SalesAnalysis,
    SalesPoint,
    Source,
)

PERSONAS: dict[str, Persona] = {
    "전체 고객": "all",
    "첫 구매 고객": "new",
    "이전 구매 고객": "returning",
    "2회 이상 구매 고객": "repeat",
    "평균 상품 주문금액 10만원 이상": "high_value",
    "할인 이용 고객": "discount",
    "한 주문에 3개 이상 구매": "multi_item",
}
SOURCES: dict[str, Source] = {
    "실제 실적 · 연동 대기": "pending",
    "기존 가상 실적": "demo",
    "업로드 더미 데이터": "dummy",
}


def _won(value: int | float | None) -> str:
    return "데이터 없음" if value is None else f"{value:,.0f}원"


def _line(points: list[SalesPoint], averages: bool = False) -> None:
    rows = [
        {
            "날짜": str(row.day),
            "순상품매출": row.net,
            **(
                {
                    "20일 이동평균": row.ma20,
                    "30일(월) 이동평균": row.ma30,
                    "365일(연) 이동평균": row.ma365,
                }
                if averages
                else {}
            ),
        }
        for row in points
    ]
    if rows:
        if averages:
            st.line_chart(rows, x="날짜", color=[*CHART_COLORS])
        else:
            st.line_chart(rows, x="날짜", color=CHART_COLORS[0])


def _upload(repository: SalesRepository) -> None:
    with st.expander("더미 데이터 연결 · JSON 형식과 업로드"):
        st.caption("가상 고객·주문 전용입니다. 이름·전화번호 등 실제 개인정보는 넣지 마세요.")
        template = {
            "schema_version": "1",
            "synthetic": True,
            "coverage_start": "2020-01-01",
            "coverage_end": "2020-12-31",
            "customers": [
                {"customer_id": "dummy-customer-1", "gender": "female", "birth_year": 1990}
            ],
            "orders": [
                {
                    "order_id": "dummy-order-1",
                    "customer_id": "dummy-customer-1",
                    "paid_on": "2020-01-15",
                    "shipping": 3000,
                    "items": [
                        {
                            "item_id": "dummy-item-1",
                            "product_id": "11",
                            "quantity": 1,
                            "unit_price": 50000,
                            "discount": 5000,
                        }
                    ],
                }
            ],
            "refunds": [],
        }
        st.download_button(
            "입력 예제 다운로드",
            json.dumps(template, ensure_ascii=False, indent=2),
            file_name="eclado-dummy-contract-v1.json",
            mime="application/json",
        )
        st.caption(
            "전체 고객·주문·환불 스냅샷을 교체합니다. 동일 파일 재입력은 중복 합산되지 않습니다."
        )
        uploaded = st.file_uploader("더미 데이터 JSON", type=["json"], key="sales_dummy_upload")
        if st.button("더미 데이터 검증 후 연결", disabled=uploaded is None):
            assert uploaded is not None
            if uploaded.size > 8 * 1024 * 1024:
                st.error("파일은 8MB 이하여야 합니다.")
            else:
                try:
                    dataset = DummySalesDataset.model_validate_json(uploaded.getvalue())
                    imported = repository.import_dummy(dataset)
                except ValidationError:
                    st.error(
                        "JSON 계약을 확인하세요. "
                        "필수값·형식·금액 또는 허용되지 않은 필드가 있습니다."
                    )
                except httpx.HTTPStatusError as error:
                    try:
                        body = error.response.json()
                        detail = body.get("detail") if isinstance(body, dict) else None
                    except ValueError:
                        detail = None
                    st.error(
                        detail
                        if isinstance(detail, str)
                        else "상품·고객·주문 연결과 규격을 확인하세요."
                    )
                except httpx.HTTPError:
                    st.error("업로드 API에 연결할 수 없습니다. 기존 데이터는 유지됩니다.")
                else:
                    st.session_state["sales_next_source"] = "업로드 더미 데이터"
                    st.session_state["sales_next_range"] = (
                        dataset.coverage_start,
                        dataset.coverage_end,
                    )
                    st.session_state["sales_import_notice"] = (
                        f"더미 고객 {imported.customers:,}명 · 주문 {imported.orders:,}건 · "
                        f"항목 {imported.items:,}건 연결 ({imported.status})"
                    )
                    st.rerun()


def render_sales_page(page: str) -> None:
    repository = SalesRepository()
    today = (datetime.now(UTC) + timedelta(hours=9)).date()
    if "sales_next_source" in st.session_state:
        st.session_state["sales_source"] = st.session_state.pop("sales_next_source")
    if "sales_next_range" in st.session_state:
        loaded_start, loaded_end = st.session_state.pop("sales_next_range")
        for name in ["매출 요약", "매출 추이", "고객별 매출 추이", "매출·상품·리뷰 AI"]:
            st.session_state[f"sales_start_{name}"] = loaded_start
            st.session_state[f"sales_end_{name}"] = loaded_end
    with st.sidebar:
        st.divider()
        source_label = st.selectbox(
            "분석 데이터", list(SOURCES), index=2, key="sales_source"
        )
        st.caption("현재 초안은 저장된 더미 데이터로 시작합니다. 실제 실적과 구분해서 확인하세요.")
        default_start = date(2020, 1, 1) if page == "매출 추이" else today.replace(day=1)
        start = st.date_input(
            "분석 시작일",
            default_start,
            min_value=date(2020, 1, 1),
            max_value=today,
            key=f"sales_start_{page}",
        )
        end = st.date_input(
            "분석 종료일",
            today,
            min_value=date(2020, 1, 1),
            max_value=today,
            key=f"sales_end_{page}",
        )
        gender, age = "all", "전체"
        persona: Persona = "all"
        if page == "고객별 매출 추이":
            gender_label = st.selectbox("성별", ["전체", "남성", "여성", "미상"])
            gender = {"전체": "all", "남성": "male", "여성": "female", "미상": "unknown"}[
                gender_label
            ]
            age = st.selectbox(
                "연령대",
                [
                    "전체",
                    *[f"{value}대" for value in range(10, 90, 10)],
                    "10대 미만",
                    "90대 이상",
                    "미상",
                ],
            )
            persona = PERSONAS[st.selectbox("구매 성향", list(PERSONAS))]
        percent, minimum = 50.0, 100000
        if page == "매출 추이":
            with st.expander("급변 알림 설정"):
                percent = st.number_input(
                    "최소 증감률(%)", min_value=1.0, max_value=1000.0, value=50.0
                )
                minimum = st.number_input(
                    "최소 증감액(원)", min_value=0, max_value=1000000000, value=100000, step=10000
                )
    st.title(f"매출 분석 · {page}")
    st.caption(f"{start} – {end} · Asia/Seoul · KRW")
    if start > end:
        st.error("분석 시작일은 종료일보다 늦을 수 없습니다.")
        return
    notice = st.session_state.pop("sales_import_notice", None)
    if notice:
        st.success(notice)
    try:
        result = repository.analyze(
            SOURCES[source_label], start, end, gender, age, persona, percent, minimum
        )
    except (httpx.HTTPError, ValidationError):
        st.error("매출 API 연결·입력 형식을 확인하세요. 임의 실적을 대신 표시하지 않습니다.")
        return
    if result.source == "pending":
        st.info("실제 실적 연동 대기 · 매출·고객 원장이 연결되면 이 화면에서 분석합니다.")
        if st.button("저장된 더미 데이터로 분석", key="open_saved_dummy"):
            st.session_state["sales_next_source"] = "업로드 더미 데이터"
            st.rerun()
    else:
        st.warning(f"{result.status} · 실제 ECLADO 실적이 아닙니다.")
    if result.coverage_start:
        st.caption(f"제공된 이력: {result.coverage_start} – {result.coverage_end}")
        if result.source == "dummy" and st.sidebar.button(
            "더미 전체 기간 보기", key="dummy_full_range", use_container_width=True
        ):
            st.session_state["sales_next_range"] = (
                result.coverage_start, result.coverage_end
            )
            st.rerun()
        if not result.complete:
            st.info(
                "조회 기간 중 이력이 없는 부분은 빈 값으로 표시합니다. "
                "합계는 제공된 이력만 포함합니다."
            )
    if result.totals is None:
        st.info(result.status)
        if result.source == "dummy" and result.coverage_start is None:
            st.info("저장된 더미 데이터가 없습니다. 아래 JSON 업로드로 데이터를 연결하세요.")
    if page == "매출 요약":
        _summary(result)
    elif page == "매출 추이":
        _trends(result)
    elif page == "고객별 매출 추이":
        _customers(result)
    else:
        render_product_insights(result)
    _upload(repository)
    with st.expander("지표·고객 성향 정의"):
        for note in result.notes:
            st.write(note)
        st.write(
            "신규/이전 구매는 제공 이력의 첫 결제일, 반복 구매는 2회 이상 주문, "
            "할인 이용·3개 이상 구매·평균 10만원 이상은 종료일까지의 관측 이력 기준입니다."
        )


def _summary(result: SalesAnalysis) -> None:
    totals = result.totals
    st.subheader("사장님 매출 현황")
    with st.container(key="kpi_primary"):
        for column, label, value in zip(
            st.columns(4),
            ["선택기간 순상품매출", "기준월 매출(종료일까지)", "기준일 일매출", "결제 주문 수"],
            [
                _won(totals.net if totals else None),
                _won(result.month_net),
                _won(result.day_net),
                f"{totals.orders:,}건" if totals else "데이터 없음",
            ],
            strict=True,
        ):
            column.metric(label, value)
    if totals:
        for column, label, value in zip(
            st.columns(4),
            ["결제 시점 평균 상품 주문금액", "구매 고객", "상품 환불", "기간 내 반복 구매 고객"],
            [
                _won(result.paid_order_average),
                f"{totals.buyers:,}명",
                _won(totals.refunds),
                f"{result.repeat_buyers:,}명",
            ],
            strict=True,
        ):
            column.metric(label, value)
        if result.previous_net is not None:
            st.write(
                f"직전 동일 길이 기간 순상품매출 {_won(result.previous_net)} · "
                f"차이 {_won(totals.net - result.previous_net)}"
            )
        st.caption(
            f"할인 전 상품매출 {_won(totals.gross)} · 할인 {_won(totals.discounts)} · "
            f"배송비(별도) {_won(totals.shipping)} · 기타 매출: 정의·원천 확인 대기"
        )
    with st.container(key="panel_summary_monthly"):
        st.subheader("월별 매출")
        st.dataframe(
            [
                {
                    "월": row.period,
                    "순상품매출(원)": row.net,
                    "결제 주문": row.orders,
                    "조회구간 이력 완전": row.complete,
                }
                for row in result.monthly
            ],
            hide_index=True,
        )
    with st.container(key="panel_summary_daily"):
        st.subheader("일별 매출")
        _line(result.daily)
    with st.container(key="panel_summary_products"):
        st.subheader(f"상품별 매출 Top 120 · 현재 {len(result.products)}개")
        st.caption(
            "관측된 거래가 있는 상품만 순위에 포함합니다. "
            "120개 미만이면 없는 상품을 만들지 않습니다."
        )
        _product_table(result)
    _reviews(result)


def _reviews(result: SalesAnalysis) -> None:
    with st.container(key="panel_reviews"):
        st.subheader("구매 연결 리뷰 분석")
        st.caption(
            f"기간 내 리뷰 {result.review_count:,}건 · 작성 고객 {result.reviewer_count:,}명 · "
            "긍정=4~5점 / 부정=1~2점 / 3점=중립 · 평점 기준이며 AI 감성 추론 아님"
        )
        if result.product_reviews:
            st.dataframe(
                [{
                    "상품": row.name, "리뷰 수": row.count, "평균 평점": row.average_rating,
                    "긍정": row.positive, "부정": row.negative,
                } for row in sorted(
                    result.product_reviews, key=lambda row: (-row.count, row.product_id)
                )],
                hide_index=True, use_container_width=True,
            )
            st.caption(
                "표의 리뷰 수·평균 평점 제목을 클릭해 "
                "적은 리뷰 및 좋은/나쁜 평점 순으로 정렬하세요."
            )
        else:
            st.caption("선택 기간·고객군의 구매 연결 리뷰가 없습니다.")


def _product_table(result: SalesAnalysis) -> None:
    st.dataframe(
        [
            {
                "순위": index + 1,
                "상품": row.name,
                "상품 ID": row.product_id,
                "순상품매출(원)": row.net,
                "결제 상품금액": row.paid_amount,
                "환불": row.refunds,
                "순판매 수량": row.units,
                "결제 주문": row.orders,
            }
            for index, row in enumerate(result.products)
        ],
        hide_index=True,
        use_container_width=True,
    )


def _trends(result: SalesAnalysis) -> None:
    with st.container(key="kpi_primary"):
        for column, label, value in zip(
            st.columns(3),
            ["선택기간 순상품매출", "기준일 일매출", "기준월 매출(종료일까지)"],
            [result.totals.net if result.totals else None, result.day_net, result.month_net],
            strict=True,
        ):
            column.metric(label, _won(value))
    recent, distribution = st.columns(2)
    with recent, st.container(key="panel_recent"):
        st.subheader("일별 매출 · 최근 14일")
        st.caption("조회 종료일까지의 순상품매출 · 환불 차감 포함")
        horizontal_bars([(row.day.strftime("%m/%d"), row.net) for row in result.daily[-14:]], "원")
    with distribution, st.container(key="panel_orders"):
        st.subheader("주문금액대 분포")
        st.caption("결제 시점 할인 후 상품금액 기준 · 배송비·환불 별도")
        horizontal_bars([(row.label, row.count) for row in result.order_amounts], "건")
    with st.container(key="panel_moving_averages"):
        st.subheader("2020년부터 보는 매출 흐름")
        st.caption("월=30일, 연=365일, 단기=20일 후행 단순이동평균 · 원 단위/일평균")
        _line(result.daily, averages=True)
    left, right = st.columns(2)
    with left, st.container(key="panel_monthly"):
        st.subheader("월별 합계")
        if result.monthly:
            st.bar_chart(
                [{"월": row.period, "순상품매출": row.net} for row in result.monthly], x="월"
            )
    with right, st.container(key="panel_yearly"):
        st.subheader("연도별 합계")
        if result.yearly:
            st.bar_chart(
                [{"연도": row.period, "순상품매출": row.net} for row in result.yearly], x="연도"
            )
    st.subheader("상품 매출 급변 Alert")
    st.caption("조회 종료일 기준 직전 동일 길이 구간 비교 · 증감액 큰 순 · 상승/하락 각각 최대 5개")
    for tab, window in zip(st.tabs(["하루", "1주", "한달(30일)"]), [1, 7, 30], strict=True):
        with tab:
            for column, direction, label in zip(
                st.columns(2), ["up", "down"], ["급상승", "급하락"], strict=True
            ):
                with column:
                    st.markdown(f"#### {label}")
                    alerts = [
                        row
                        for row in result.alerts
                        if row.window == window and row.direction == direction
                    ]
                    if not alerts:
                        st.write("조건을 충족하는 상품이 없거나 비교 이력이 부족합니다.")
                    for alert in alerts:
                        with st.expander(f"{alert.name} · 차이 {_won(alert.delta)}", expanded=True):
                            st.write(f"직전 {_won(alert.previous)} → 최근 {_won(alert.current)}")
                            st.caption(
                                f"{alert.percent:+.1f}%"
                                if alert.percent is not None
                                else alert.reason
                            )
                            _line(alert.series)
                            st.dataframe(
                                [
                                    {"일자": str(row.day), "순상품매출(원)": row.net}
                                    for row in alert.series
                                ],
                                hide_index=True,
                            )
    st.subheader("고객별 평균 주문금액대 분포")
    if result.customer_averages:
        st.bar_chart(
            [{"금액대": row.label, "고객 수": row.count} for row in result.customer_averages],
            x="금액대",
        )


def _customers(result: SalesAnalysis) -> None:
    with st.container(key="panel_customer_0"):
        st.subheader("선택 고객군의 매출 흐름")
        if result.totals:
            st.metric("선택 고객군 순상품매출", _won(result.totals.net))
        _line(result.daily)
        for title, rows in [
            ("10대~80대 연령별 매출", result.age_cohorts),
            ("성별 매출", result.gender_cohorts),
        ]:
            st.subheader(title)
            if rows:
                st.bar_chart(
                    [{"고객군": row.label, "순상품매출": row.net} for row in rows],
                    x="고객군", color=CHART_COLORS[0],
                )
                st.dataframe(
                    [
                        {
                            "고객군": row.label,
                            "기여 고객": "5명 미만" if row.suppressed else str(row.buyers),
                            "순상품매출(원)": row.net,
                        }
                        for row in rows
                    ],
                    hide_index=True,
                )
    with st.container(key="panel_customer_1"):
        st.subheader("연령별 월 매출 추이")
        if result.cohort_trends:
            data: dict[str, dict[str, str | int | None]] = {}
            for row in result.cohort_trends:
                data.setdefault(row.period, {"월": row.period})[row.label] = row.net
            st.line_chart(list(data.values()), x="월")
    with st.container(key="panel_customer_2"):
        st.subheader("성별 월 매출 추이")
        if result.gender_trends:
            gender_data: dict[str, dict[str, str | int | None]] = {}
            for row in result.gender_trends:
                gender_data.setdefault(row.period, {"월": row.period})[row.label] = row.net
            st.line_chart(list(gender_data.values()), x="월")
    with st.container(key="panel_customer_3"):
        st.subheader("선택 고객군이 구매한 상품")
        _product_table(result)
        st.info(
            "피부 상태·성격·구매 동기는 추측하지 않습니다. "
            "구매 행동 기반 고객군을 왼쪽에서 선택하세요."
        )
    with st.container(key="panel_regions"):
        st.subheader("지역별 고객 매출 · 시·군·구")
        st.caption("제공된 지역만 집계 · 기여 고객 5명 미만 금액 숨김 · 상세 주소 미수집")
        st.dataframe([
            {"지역": row.label, "기여 고객": "5명 미만" if row.suppressed else str(row.buyers),
             "순상품매출(원)": row.net}
            for row in result.region_cohorts
        ], hide_index=True, use_container_width=True)
    _reviews(result)
