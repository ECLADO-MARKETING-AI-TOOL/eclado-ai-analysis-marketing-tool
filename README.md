# ECLADO Marketing AI

> **Project mission:** Build an AI-powered sales intelligence, customer relationship management (CRM), and personalized marketing platform for the ECLADO cosmetics brand. The prototype must be designed so that, after business approval and authorized data access, the same application can transition to production by replacing or enabling data-provider integrations—not by rebuilding dashboards and business logic.
>
> **Current status:** Prototype / demonstration only. No verified live sales or customer data is connected. No production authentication, AI provider, coupon issuance, or message sending is enabled.

## 1. Product vision and scope (프로젝트 목적)

이 프로젝트는 **브랜드사가 실제 매출과 고객 행동을 이해하고, 고객 이탈을 줄이며, 재구매를 늘릴 수 있도록 지원하는 AI 마케팅 및 매출 분석 웹서비스**다. 단순히 그래프를 보여주는 매출 대시보드를 만드는 것이 최종 목적이 아니다.

- **대상 브랜드:** ECLADO(에끌라두)
- **주요 예정 데이터 소스:** `laonmall.co.kr` 사업자몰의 **승인된** 관리자 API 또는 공식 데이터 내보내기. 현재 API 제공 여부, 운영 플랫폼, 인증·접근 범위는 확인 전이며 단정하지 않는다.
- **현재 활용 가능한 별도 소스:** 기존 `ecladomall.co.kr`의 공개 상품명·표시 가격 스냅샷. 이는 카탈로그 참고용이며 `laonmall.co.kr`의 주문·회원·실제 매출을 대신하지 않는다.
- **주요 사용자:** 브랜드사 대표/책임자, 승인된 영업·마케팅 담당자, 필요 시 집계 데이터만 보는 분석 담당자.
- **궁극적인 결과:** 데이터 기반 이상 탐지 → AI의 근거 있는 해석과 해결책 제안 → 담당자 승인하에 개인화 마케팅 실행 → 성과 측정.

**사업자몰 특성:** 구매 회원은 개인 소비자가 아니라 피부관리실, 에스테틱 업체 등 사업자 고객일 수 있다. 따라서 회원/거래처 정보와 실제 최종 소비자 정보를 혼동하지 말 것. 피부 타입, 개인 사용 경험 등은 **본인이 적법하게 직접 제공하고 목적상 이용 가능한 정보**가 아닌 한 구매자의 특성으로 추정하지 않는다.

## 2. Core features (확정된 핵심 기능)

### 2.1 Sales intelligence (매출 분석)

- 일별·월별·연별 매출 추이와 지정 기간 비교.
- 상품/카테고리별 판매액, 수량, 주문 수, 취소·환불·할인 및 객단가 분석.
- 특정일 또는 특정 상품의 매출 급등·급락, 평소와 다른 주문·환불 패턴 감지.
- AI가 변화와 관련된 근거를 정리하고 **가능한 원인 가설**, 확인할 사항, 대응 방안을 제시.
- 가능하고 허가된 경우 시장 가격·프로모션·공개 리뷰·트렌드 등 외부 정보를 참고하되 출처, 관측 시점, 데이터 한계를 명시. 상관관계를 인과관계로 단정하지 않음.

### 2.2 Customer intelligence (고객 및 구매 행동 분석)

- 승인된 회원/거래처 정보(예: 이름, 연락처, 성별, 생일, 가입일 등)를 **실제 제공 및 이용이 허용된 범위에서만** 가져오기.
- 고객별 구매 이력, 구매 주기, 재구매 여부, 누적 구매액, 선호 제품 및 카테고리 분석.
- 신규·기존·반복 구매·장기 미구매 고객 분류와 고객 집단별 매출 비교.
- 회원 정보와 주문 데이터를 신뢰 가능한 고객 ID로 연결하고, 출처가 다른 기록을 무단으로 추정 병합하지 않기.
- 인구통계, 피부 유형, 취향 등의 속성을 이름이나 리뷰 문장만으로 사실처럼 추론하지 않기. 민감하거나 부정확한 프로필의 자동 생성을 피하기.

### 2.3 Personalized product recommendations and timely campaigns (개인화 추천·캠페인)

- 고객의 검증된 구매 기록, 직접 제공한 선호 정보, 제품 속성을 바탕으로 **추천 이유가 설명 가능한** 제품을 제안.
- 생일·재구매 예상 시점·장기 미구매 등 알맞은 시점에 쿠폰, 이벤트, 제품 추천 등 마케팅 시나리오를 제안.
- 현재 단계에서는 대상 고객 선정, 추천 문구, 예상 발송 시점, 쿠폰 시안을 **미리보기/가상 실행(dry-run)** 으로 구현.
- 실제 발송·쿠폰 지급은 별도 승인 후에만 활성화하며, 최신 마케팅 수신 동의, 수신 거부, 발송 시간 제한, 발송 빈도 제한, 중복 발송 방지, 예산·재고 조건, 사람의 승인 및 감사 로그를 적용.

### 2.4 Negative review response and churn prevention (부정 리뷰 대응·이탈 방지)

- 상품별 평점 하락, 부정 리뷰 증가, 반복되는 불만 키워드 감지.
- 예: 특정 앰플을 사용한 뒤 건조하다는 리뷰가 접수되면, AI가 **그 리뷰의 구체적 불만을 요약**하고 제품 설명과 검증된 속성을 비교해 고객 응대 초안을 만듦.
- 필요 시 검증된 특성을 가진 대체 상품 제안, 정중한 사과, 담당자 상담, 쿠폰 또는 사과 선물 시나리오를 제시.
- 실제 고객에게 메시지를 보내거나 선물을 지급하기 전에는 고객·리뷰·주문 연결 정확성, 적법한 연락 목적 및 동의, 재고/예산, 제품 추천의 적절성, 담당자 승인 여부를 확인.
- **주의:** 리뷰 내용으로 고객의 피부 타입, 건강 상태, 이탈 원인을 확정하지 않는다. 화장품 효능이나 적합성을 의학적으로 단정하지 않으며, 부정 리뷰 삭제·수정 대가로 혜택을 제공하지 않는다.

### 2.5 Brand management dashboard (브랜드사용 운영 화면)

- 매출 추이, 고객 동향, 상품별 성과, 리뷰 이슈, 추천 대응책을 한눈에 제공.
- 급격한 변화의 탐지 시점, 근거 데이터, 영향 범위, AI 해석 및 담당자 검토 상태를 구분.
- 데이터 최신 갱신 시점, 연동 오류, 데이터 누락/불일치를 표시.
- AI의 제안과 실제로 실행된 캠페인을 분리하고, 실행 결과를 추적할 수 있도록 설계.

## 3. Prototype-first, production-ready architecture (프로토타입 개발 원칙)

**사업자 승인 이전에는 실제 회원 명단이나 비공개 주문 데이터를 연결하지 않는다.** 실제 API 자격 증명이나 운영 DB 접근이 없어도 시연 가능한 프로토타입을 먼저 완성한다.

1. **현실적인 합성 데이터:** 고객·사업자·주문·주문항목·환불·리뷰·마케팅 동의·상품을 서로 연결한 가상 데이터로 핵심 흐름 검증. 가상 데이터는 화면과 API에서 반드시 명확히 표시.
2. **교체 가능한 데이터 입력 계층:** 더미 데이터 공급자와 향후 승인된 쇼핑몰 API/공식 내보내기 공급자가 동일한 정규화 모델로 데이터를 제공하도록 설계. 공급자별 API 구조를 UI나 AI 분석 코드에 직접 결합하지 않음.
3. **동일한 분석 엔진 재사용:** 매출 집계·고객 분류·리뷰 분석·캠페인 제안은 입력 데이터가 더미인지 실데이터인지와 무관하게 동작.
4. **연동 즉시 자동 운영되는 것처럼 가정하지 않음:** 운영 전 인증·권한, 데이터 매핑, 주문/환불 정합성, 개인정보·마케팅 동의, 전송 안전장치, 동기화·복구, 보안·성능 테스트, 사업자 승인 등 전환 조건을 통과해야 함.
5. **실시간 지향:** 승인 후 API가 제공하는 웹훅·증분 동기화·주기적 폴링 등을 활용하되, 실제 가능한 업데이트 주기는 제공업체의 API 제한과 계약에 따라 결정. 연동 전에는 실시간 수집이 가능하다고 홍보하지 않음.

## 4. Planned data integration (향후 laonmall 연동)

예정 데이터 영역:

| Domain | Example fields / required relationship |
| --- | --- |
| Products | source product ID, variant/SKU, name, category, price, status |
| Orders | source order ID, customer/member ID, order/payment timestamp, status, discounts, shipping |
| Order items | order ID, product/variant ID, quantity, **purchase-time** unit price and discounts |
| Refunds/cancellations | original order/item reference, amount, quantity, completion timestamp |
| Customers/business accounts | source member ID, approved profile/organization fields, enrollment date; contact data separated and access-controlled |
| Reviews | review ID, product and optionally verified order/member link, rating, comment, timestamp |
| Consent & outreach | channel/purpose-specific consent status and evidence, opt-out, eligibility, send/audit history |

모든 수입 작업은 소스, 수집 시점, ID 매핑, 중복 방지 키, 결과 건수, 오류 및 마지막 동기화 지점을 기록한다. 수집한 개인정보·실제 주문 원본·API 키는 공개 저장소에 절대 커밋하지 않는다. **원천 데이터가 제공되지 않은 항목은 임의 생성해서 실제 고객 정보인 것처럼 표시하지 않는다.**

실서비스 연동 시점에는 API 문서/이용조건과 사업자 권한, 과거 데이터 제공 범위, 고객 식별 방식, 동의 및 수신거부 데이터의 적합성을 확인한다.

## 5. AI responsibilities and restrictions (AI 개발 제한 규칙)

다음은 Codex, Copilot 및 모든 AI 개발 도구에 적용되는 프로젝트 수준의 요구사항이다.

### MUST

- 항상 본 README의 목표인 **매출 분석 → 고객 행동 이해 → 근거 기반 추천 → 승인된 맞춤 마케팅 → 결과 측정**에 연결되는 기능만 개발한다.
- 새로운 기능 제안과 이미 승인된 개발 요구사항을 구분한다. **제안만으로 기능을 범위에 추가하지 않는다.**
- 핵심 기능을 시연할 수 있는 더미 데이터를 활용하되, 실제/가상 여부를 모든 화면·리포트에 분명히 표시한다.
- 분석 결과에 데이터 기간·표본·출처·확실성/불확실성을 표시하고, AI 가설은 사실이나 인과 증명으로 표현하지 않는다.
- 기존 FastAPI / Streamlit / Supabase 계획과 저장소의 계층 경계를 우선 존중한다.
- 개발 변경 전 관련 기존 코드와 테스트를 읽고, 작은 단위로 수정한 뒤 테스트를 실행한다.
- 실고객 데이터 및 발송 기능 도입 전 인증, 권한, 동의, 수신거부, 전송·비용 제한, 감사 기록, 데이터 보존·삭제 요구사항을 충족한다.

### MUST NOT

- 사용자 승인 없이 주제를 벗어난 제품(범용 챗봇, 쇼핑몰 새로 구축, 완전히 별개의 앱 등)을 개발하지 않는다.
- 사용자 승인 없이 기술 스택을 전면 교체하거나 기존 기능·명세·폴더 구조를 대규모 변경하지 않는다.
- 사업자 승인 이전에 라온몰의 비공개 API, 고객 목록, 주문 원장에 무단 접근하거나 로그인/접근 통제를 우회하지 않는다.
- 공개몰 상품 가격을 실제 거래 단가, 실제 매출, 고객 구매 이력으로 둔갑시키지 않는다.
- 개인의 피부 타입·건강 상태·민감한 성향·구매하지 않은 이유·이탈 이유를 추측만으로 확정하지 않는다.
- AI가 단독으로 고객에게 메시지나 쿠폰/선물을 자동 발송하도록 기본 활성화하지 않는다.
- 실고객 식별자, 주문 원문, 리뷰 원문 등 필요 이상의 데이터를 외부 AI 모델에 전송하지 않는다.
- 프로젝트 문서나 코드에 기획되지 않은 기능을 임의로 추가하거나 GitHub에 커밋하지 않는다.

**Docs precedence:** This README sets business goals and scope. `AGENTS.md` and `docs/architecture.md` specify implementation and safety rules; `docs/product-plan.md` contains planning detail. If old documents refer only to `ecladomall.co.kr`, interpret that as the current **public catalog reference**, not the future source of confidential B2B orders and member records. Any material conflict must be surfaced for user review before implementation.

## 6. Delivery roadmap (개발 순서)

- **Phase 1 — Demo foundation:** existing synthetic sales, catalog and UI; add coherent synthetic customer/review/event scenarios, source labels, unified analytic contracts and reliable tests.
- **Phase 2 — Core analytics:** sales/product/customer dashboards, buying-pattern analysis, negative-review signals, anomaly detection, evidence-based AI insight previews (safe fake/model abstraction).
- **Phase 3 — Marketing workflow previews:** customer/product recommendation drafts, birthdays and other timing scenarios, negative-review recovery drafts, campaign preview, human approval states, dry-run and measurement placeholders. **No real sending.**
- **Phase 4 — Authorized integration:** after ECLADO approval, obtain permitted `laonmall.co.kr` API/export access; connect customer/order/refund/review/consent providers, run reconciliation, implement Supabase persistence/auth/permissions.
- **Phase 5 — Controlled production:** verified message/coupon providers, compliance and approval gates, monitoring, rate limits, rollback, audit and measured campaign outcomes; enable only after acceptance checks.

**Out of scope unless separately approved:** the assistant's optional feature proposals (predictive inventory/reorder alerts, advanced churn scoring, cross-sell models, controlled incrementality experiments, and broad marketplace competitive intelligence beyond the explicitly requested anomaly context). They remain proposals, not approved implementation requirements.

---

## 7. Current implementation status (현재 구현 상태)

FastAPI와 Streamlit으로 구성한 ECLADO 사장님 대시보드 초안입니다. 기존 `ecladomall.co.kr` 공식몰에서 수집한 공개 상품명·표시 가격을 보여주며, 실제 매출·환불·고객·리뷰는 연결 대기입니다. 별도 모드에서 가상 실적 화면을 검토할 수 있습니다. Supabase 자동 저장·직원 인증·Gemini·문자 발송은 아직 연결하지 않았습니다.

첫 화면은 **데모 로그인**입니다. 이메일 `user@example.com`, 비밀번호는 아무 값이나 한 글자 이상 입력하면 기존 분석 화면으로 이동합니다. **실제 계정 인증 및 API 접근 제어가 아니므로 운영용으로 사용하면 안 됩니다.** 데모 세션은 현재 브라우저 탭에서 유지되며, 입력된 비밀번호는 인증 서버로 전송하거나 기록하지 않습니다.

로그인 후 기본 화면은 **매출 분석 → 매출 요약**입니다. 사이드바에서 **매출 추이**, **고객별 매출 추이**를 선택하세요. 2020년부터 조회할 수 있으며, 이력이 없는 기간은 실제 0원으로 채우지 않습니다. 기존 가상 실적 또는 업로드할 더미 데이터로 화면을 확인할 수 있습니다. 각 화면의 **더미 데이터 연결**에서 JSON 예제 다운로드·업로드를 제공합니다. [1,000건 생성 전 입력 계약](docs/ver1-sales-analysis.md)을 먼저 확인하세요. 기존 카탈로그는 **상품·리뷰·AI** 메뉴에 있습니다.

상품은 **매출·상품** 탭에서 검색·분류·가격을 확인하세요. **공식몰 상품 · 실적 연동 대기**가 기본이며, 예시 매출을 확인하려면 **가상 실적 화면 미리보기**를 선택하세요. 가상 시나리오 기간은 2026-09-06 ~ 2026-10-20입니다. 실제 실적과 공개 가격을 혼합해서 해석하면 안 됩니다.

공유 DTO 변경 후 `DashboardResponse` 속성 오류가 나면 Streamlit 터미널에서 `Ctrl+C`로 종료하고 다시 실행하세요. 브라우저 새로고침만으로는 실행 중 Python의 이전 모델이 교체되지 않을 수 있습니다.

백엔드 주소 변경 시 `ECLADO_API_BASE_URL` 환경변수를 설정하세요. 공개 카탈로그 재수집과 실제 데이터 → Supabase → 요약 → AI 연동 방향은 [Ver.1 초안 안내](docs/ver1-preview.md)를 참고하세요. API와 Streamlit은 현재 로컬 주소로 실행합니다.

## 8. Requirements

- Windows 10/11 with PowerShell
- Python 3.12 or newer
- `uv` package manager
- Supabase project and provider credentials are not needed for local checks

Install `uv` using the official Windows installer, then from this repository root run:

```powershell
uv sync
```

## 9. Run locally

Start the API in one terminal:

```powershell
uv run uvicorn eclado_backend.main:app --app-dir backend --host 127.0.0.1 --reload
```

Start the admin screen in another terminal:

```powershell
uv run streamlit run admin/eclado_admin/main.py --server.headless=true
```

The API is available at `http://127.0.0.1:8000`; its OpenAPI page is at `/docs`. Streamlit is normally available at `http://localhost:8501`.

## 10. Checks

```powershell
uv run pytest
uv run ruff check .
uv run mypy
```

## 11. Project layout

- `backend/eclado_backend/api/routers/`: HTTP endpoints and request/response handling
- `backend/eclado_backend/services/`: business rules and orchestration
- `backend/eclado_backend/stores/`: persistence boundary; runtime SQL belongs here
- `admin/eclado_admin/`: Streamlit pages and UI components
- `admin/eclado_admin/repositories/`: the only admin layer that calls backend APIs
- `shared/eclado_shared/`: shared API transport and schemas; no database access
- `supabase/migrations/`: reviewed, ordered database schema changes
- `docs/`: architecture, decisions, and client change tracking

See [docs/architecture.md](docs/architecture.md) and [docs/product-plan.md](docs/product-plan.md) before adding integrations or handling production customer data.
