"""Aggregate-only recommendation boundary; replace after Gemini approval."""

from typing import Protocol

from eclado_shared.schemas.dashboard import ProductPerformance, Recommendation


class MarketingAdvisor(Protocol):
    def recommend(self, products: list[ProductPerformance]) -> list[Recommendation]: ...


class RulePreviewAdvisor:
    def recommend(self, products: list[ProductPerformance]) -> list[Recommendation]:
        if not products:
            return []
        best = max(products, key=lambda product: product.units)
        least_reviewed = min(products, key=lambda product: product.review_count)
        result = [
            Recommendation(
                title="판매 상위 상품의 콘텐츠 실험",
                evidence=f"{best.name}: 선택 기간 순판매 {best.units}개.",
                action="상품 사용법 콘텐츠와 연관 상품 구성을 소규모로 비교하세요.",
                measurement="비교 그룹별 상품 전환율·순상품매출·환불률을 확인하세요.",
            ),
            Recommendation(
                title="리뷰가 적은 상품의 정보 보강",
                evidence=f"{least_reviewed.name}: 선택 기간 리뷰 {least_reviewed.review_count}건.",
                action="상품 설명·사용법과 리뷰 작성 경로를 먼저 점검하세요.",
                measurement="상품 조회 대비 구매율과 구매 후 리뷰 작성률을 비교하세요.",
            ),
        ]
        rated = [product for product in products if product.average_rating is not None]
        if rated:
            worst = min(rated, key=lambda product: product.average_rating or 0)
            result.append(
                Recommendation(
                    title="낮은 평점 상품의 경험 점검",
                    evidence=(
                        f"{worst.name}: 평균 {worst.average_rating}점, "
                        f"리뷰 {worst.review_count}건. 표본이 작으면 해석을 보류하세요."
                    ),
                    action="할인 확대 전에 승인된 리뷰와 CS 사유를 담당자가 검토하세요.",
                    measurement="개선 전후 평점·반품률을 관찰하고 인과관계는 실험으로 확인하세요.",
                )
            )
        return result
