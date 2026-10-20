# ECLADO AI Marketing and Sales Analytics Plan

**Status:** Product plan, not an implementation authorization for production data or messaging  
**Planning basis:** Public ECLADO mall pages reviewed on 2026-10-20; data access and metric definitions still require confirmation with the business owner.

## 1. Product goal

Provide authorized ECLADO staff with a single operational view of sales, products, customers, and marketing activity. Begin with accurate reporting and human-approved customer segments. Add AI summaries and assisted campaign recommendations only after source data, consent, and metric definitions are reliable. Automated SMS should be the last step, not the first.

Primary users:

- Owner: full dashboard, configuration, access, and campaign approval.
- Authorized sales/marketing manager: analytics, customer segments, and campaigns within assigned permissions.
- Optional analyst: aggregated reporting only, without direct identifiers or message-send permission.

## 2. What the public mall tells us

The official mall at [ecladomall.co.kr](https://ecladomall.co.kr/) publicly exposes product names, product detail links/IDs, category groupings, sale and displayed list prices, some stock/sold-out states, time-sale/promotional context, review counts/ratings, and membership/event navigation. Categories include product types such as toner, ampoule/serum, cream, cleanser and mask, as well as concern- and product-line groupings.

Examples observed on the public toner category page included Exo Clinica Toner 500ml at 57,000 KRW, NK-CX Protein Poten Booster 100ml displayed at 70,000 KRW against 96,000 KRW, and Royal Milk Protein Toner 500ml on promotion at 37,500 KRW against 75,000 KRW. These are time-sensitive page observations, not verified current prices or transaction prices. The public review page also shows product associations, rating/review totals, masked reviewer names, and review text; it does not provide a reliable customer-order ledger.

The public privacy page reviewed is marked with an effective date of 2025-01-21 and itself contains language identifying it as a sample form with template-like placeholders. It mentions account, order, marketing, and review-related processing. Do not treat this page as confirmation of the company's current consent records, legal basis, exact retention schedule, or integration permissions; obtain the current approved policy and consent data from the business owner.

**Use public product pages only for catalog enrichment and timestamped observed-price snapshots.** Prefer the mall platform's authorized admin/API/export path for product and variant data. If no authorized feed is available, agree on a permitted collection method before building a scheduled collector. Public prices, review text, and category pages cannot establish today's sales, lifetime customer spend, inventory truth, or who bought which item.

## 3. Data sources and ingestion

Build an ingestion boundary so the business logic does not depend on a particular source:

1. **Product catalog:** authorized Cafe24/admin API or export as primary source; public product pages as an explicitly labeled catalog/price fallback where allowed. Capture source, external product ID, variant/SKU where available, category/line, status, observed/list/sale price, stock state if authorized, URL, and `observed_at`.
2. **Orders and order lines:** authorized order API/export including created/paid/fulfilled/cancelled/refunded timestamps, customer/member reference, item/variant, quantity, purchase-time unit price, discounts/coupon allocations, shipping, and payment status.
3. **Customers and consent:** member/customer IDs, only approved profile fields, marketing consent by channel, consent source/time, opt-out time, and account lifecycle. Keep source-system identity separate from internal identity.
4. **Reviews:** authorized review feed/export with source review ID, product/order reference when available, rating, text, created time, and purchase-verification flag. Store raw content only if approved and necessary; otherwise minimize or pseudonymize before analysis.
5. **Campaigns and delivery:** campaign definition, target rule/version, eligibility decision, approved content, coupon, send attempt, provider result, suppression reason, and idempotency key.

Every import should record source, start/end time, watermark/cursor, row counts, validation errors, and a replay-safe batch identifier. Upserts must be idempotent. Preserve source IDs and provenance; quarantine records with ambiguous product/customer mapping rather than silently merging them.

## 4. Initial database domains

Use normalized operational tables and derive dashboards from views/aggregates. Exact names can follow repository conventions, but the relationships should support:

- `products`, `product_variants`, `categories`, and product-category/line mappings.
- `product_price_observations` for timestamped public or admin price observations. Never overwrite past observations.
- `customers` with internal ID and source-system mapping; minimal permitted demographic fields; no unnecessary raw identifiers in analytics tables.
- `customer_consents` as an auditable event history (channel, purpose, granted/withdrawn, timestamp, source, policy/version). A current-state view can be derived from events.
- `orders`, `order_items`, and `order_adjustments` for discounts, cancellations, refunds, and shipping. Store item purchase-time amounts so later catalog price changes do not rewrite history.
- `reviews` with source ID, product/order relationship, rating, text or minimized representation, verification status, and provenance.
- `customer_segments`/`segment_memberships` with rule version and evaluation timestamp; avoid persisting opaque AI-only eligibility decisions.
- `campaigns`, `campaign_recipients` or eligibility decisions, `marketing_message_outbox`, `message_events`, and `audit_logs`.
- `import_runs` and `ai_analysis_runs` to record source and model/prompt versions.

Keep SQL in backend stores. Enable Supabase RLS and define least-privilege policies before exposing tables; the service role key must never reach Streamlit/browser code. Do not place direct PII in analytics aggregates or AI prompts.

## 5. Metric definitions to agree before implementation

Use Asia/Seoul business dates for dashboard periods and record timestamps in UTC. Display KRW as integer won. Each metric must say whether it is based on order date, payment date, or fulfillment date. Recommended default is payment date for paid-sales views, with separate order and fulfillment counts.

- **Listed price / sale price:** current source observation, with source and observation time; not a transaction amount.
- **Units sold:** sum of paid quantities minus cancelled/refunded quantities under an agreed refund policy.
- **Product gross sales:** sum of line quantity × purchase-time unit price before allocated discounts.
- **Net merchandise sales:** paid item amounts after item/order coupon discounts and refunds; exclude shipping and separately report it. Finance must confirm treatment of tax, points, partial refunds, and payment fees.
- **Total sales / today / this month:** aggregate net merchandise sales for the selected payment-date window, net of cancellations/refunds according to the agreed policy. Show gross, discount, refund, shipping, and net separately so the headline is auditable.
- **Customer cumulative purchase amount:** net merchandise sales across eligible paid orders, with order count, first purchase date, and latest purchase date. Clarify whether guest and cross-channel orders are included.
- **Average order value:** net merchandise sales divided by eligible paid orders; exclude fully cancelled orders.
- **Top products:** rank by units, net sales, and unique purchasing customers separately; these answer different questions.
- **New / active / dormant / loyal:** define explicit, configurable thresholds based on purchase behavior. A starting proposal is dormant after 90 days without a paid purchase and loyal from a threshold such as 3 completed orders or business-approved lifetime spend. Validate against repurchase cycles and current membership rules before campaigns.
- **Customer demographic breakdown:** only from permitted, reliable profile fields. Show unknown/missing bucket, use age bands rather than exact birth dates, and suppress small cohorts. Never infer demographic attributes from name, review, or purchase pattern.

Without authorized historical order, cancellation, refund, and customer mapping data, sales KPIs must show “데이터 연동 대기” rather than zero or a fabricated estimate.

## 6. Backend plan (FastAPI)

Keep the existing strict dependency direction: `api/routers -> services -> stores`.

- **Routers:** authenticated API contracts for dashboard metrics, product catalog, order/customer aggregates, segments, campaign previews/approvals, and imports. Validate inputs and return typed schemas only.
- **Services:** metric definitions, KST date windows, segmentation rules, consent/opt-out checks, frequency caps, idempotent send orchestration, AI redaction and review workflows.
- **Stores:** all Supabase/PostgreSQL queries and transaction boundaries, pagination, bulk upserts, and aggregate queries.
- **Provider interfaces:** catalog/order source adapter, Supabase Auth verifier, SOLAPI sender, Gemini analysis provider, and optional coupon provider. Use fakes in tests and explicit configuration for model/tier changes.
- **Background jobs:** scheduled catalog/order sync and dormant-segment evaluation should run as separately observable jobs with retries, locks, idempotency, and run history. Do not put long jobs in HTTP request handlers.
- **Security:** verify Supabase JWTs server-side; enforce owner/manager/analyst permissions in API dependencies/services; audit exports, customer lookups, approvals, and sends.

Suggested API areas: `/api/v1/dashboard`, `/products`, `/sales`, `/customers`, `/segments`, `/campaigns`, `/imports`, and `/audit`. Keep public health separate from authenticated business data.

## 7. Admin frontend plan (Streamlit)

Streamlit pages call the backend only through `admin/eclado_admin/repositories/*_repository.py`; the shared package supplies transport and DTOs only.

- **Overview:** today, month-to-date, selected period, net/gross/discount/refund breakdown, order count, AOV, sync freshness, and comparison with prior period.
- **Sales:** date range, payment/order date toggle, trend, refunds/cancellations, channel/source, and CSV export gated by role.
- **Products:** catalog/search, category/line filters, current observed price with timestamp, units/net sales/unique buyers, and top-product rankings.
- **Customers:** new/active/dormant/loyal counts and aggregate cohorts by approved age band/gender/region; detail access separately permissioned and audited.
- **Segments and campaigns:** rule preview, estimated eligible audience, exclusion reasons, coupon/message draft, consent and frequency checks, human approval, dry-run, then staged send.
- **Reviews and AI insights:** sentiment/topics by product and period, representative redacted evidence, confidence/limitations, human correction; never state a causal churn reason as fact.
- **Operations/settings:** imports, failed rows, last-sync time, provider health, user roles, campaign approvals, and audit log.

## 8. AI and marketing guardrails

- Begin with aggregate product/review summaries and staff-assisted segment explanations. Keep deterministic business eligibility rules separate from model output.
- AI may summarize patterns that coincide with inactivity; it cannot establish why an individual became dormant. Display evidence window, sample size, uncertainty, and human review status.
- Redact direct identifiers and minimize purchase/review context sent to Gemini. Confirm provider retention/data-use settings, acceptable data classes, and the company's approval before sending any real customer content. Store model, prompt version, timestamp, and source IDs or privacy-safe references.
- SMS reactivation every two weeks is a proposed cadence, not permission to send. Before every send: re-check channel-specific consent and opt-out, legal/ad compliance, eligibility, frequency caps across all campaigns, quiet hours, recipient phone validity, coupon validity, and idempotency. Default to preview/dry-run; require human approval and a kill switch for initial releases.
- Loyalty gifts and coupons need inventory/budget caps, fulfillment tracking, and fraud/abuse controls.

## 9. Phased delivery

### Ver.1: trustworthy data and dashboard

- Confirm Cafe24 access method, metric definitions, consent fields, staff roles, and historical data availability.
- Import product catalog and timestamped price observations; import orders, lines, cancellations/refunds, customers, consent and reviews through an authorized feed.
- Validate reconciliation against Cafe24 admin totals for chosen days and months.
- Deliver authenticated overview, sales/product dashboards, sync status, and audit logging. No automated sends.

### Ver.2: customer analytics

- Add configurable new/active/dormant/loyal definitions and historical cohort reports.
- Add approved aggregate demographic/product affinity reports and review-topic summaries.
- Add AI-assisted churn hypothesis reports with redaction, confidence/evidence, and human review.

### Ver.3: controlled campaigns

- Add segment preview, coupon setup/validation, consent exclusions, frequency caps, approval flow, SOLAPI dry-run, and staged small-cohort sends.
- Track sends, delivery results, opt-outs, coupon redemption, and incremental performance with a control group where feasible.

### Ver.4: optimization and scale

- Tune segment thresholds/cadence from measured outcomes, add loyalty gift workflows, budget guardrails, improved attribution, and Gemini model/tier upgrades via configuration.
- Expand automation only when reconciliation, consent audit, failure recovery, and monitoring meet agreed acceptance criteria.

For each version, record acceptance criteria, schema migration and rollback, role/privacy review, tests, deployment, and change notes in `docs/CHANGE_REQUEST_TEMPLATE.md` and `CHANGELOG.md`.

## 10. Decisions needed from ECLADO before implementation

1. Is the mall hosted on Cafe24, and which authorized API/app credentials or scheduled exports can be provided for products, orders, refunds, members, consent, and reviews?
2. What is the source of truth for sales: payment date or order date; how are coupons, points, shipping, partial refunds, tax, and guest orders treated?
3. How far back can clean history be exported, and how are customer IDs reconciled across Cafe24, Naver Pay, and other channels?
4. What exact consent fields and proof are available for SMS marketing, what is the existing opt-out path, and who approves campaign content and sends?
5. Which staff roles may view PII, export customer lists, approve campaigns, or configure AI/provider settings?
6. What thresholds define dormant and loyal, and what budget, coupon, monthly send cap, and quiet-hour rules apply?
7. What customer/review data may be processed by Gemini, under which data-use/retention settings, and what must be redacted?
8. What hosting region, retention/deletion period, backup/recovery objective, and legal/privacy review owner are required?

## 11. Ver.1 preview request — 2026-10-20

The subsequent [2,000-record synthetic test](ver1-dummy-seed.md) persists 2,000 customers, 2,000 orders and 400 purchase-linked reviews in the local test store at the requester's direction. Region and review aggregates are available through the sales API and Streamlit. This is not Supabase production ingestion or a source of real sales/customer evidence.

The requester authorized a local Streamlit draft for iterative review, then requested official mall product names and prices instead of synthetic catalog entries. [Preview implementation and follow-up data flow](ver1-preview.md) records the resulting scope. Public catalog observations are real; preview sales/customer/refund/review scenarios are explicitly synthetic and optional. Production metric definitions and authorized data access remain subject to the linked contracts.

The intended operational system automatically stores authorized customer/account events, approved profile fields, purchases, cancellations/refunds and reviews in Supabase; derives auditable sales/product/customer reports; and supplies aggregate evidence for owner-reviewed AI marketing suggestions. Login data alone does not establish profile availability or purchase history. This preview does not implement production ingestion, Supabase persistence, staff authentication, Gemini generation or messaging.

The subsequent sales-analysis request adds sidebar summary/trends/customer-trends views and a validated synthetic JSON ingestion path, documented in [Ver.1 sales analysis](ver1-sales-analysis.md). Rolling windows, alerts and behavioral cohorts are explicit preview defaults; financial and production data access approvals remain separate. The 1,000-customer/order integration is tested without seeding the running app with generated records.
