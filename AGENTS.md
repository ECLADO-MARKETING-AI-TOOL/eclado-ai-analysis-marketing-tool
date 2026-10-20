# ECLADO Marketing AI — Agent Development Rules

> Mandatory instructions for Codex, Copilot, and all AI development agents. The latest approved `README.md` is the source of truth for product scope. Do not mistake a prototype for a production-ready system.

## 1. Read before changing anything

Read in order: `README.md`, this `AGENTS.md`, `docs/architecture.md`, `docs/product-plan.md`, then relevant source files and tests. Read `.github/copilot-instructions.md` only if the file exists.

**Document precedence:** `README.md` defines the approved vision and scope; `AGENTS.md` and `docs/architecture.md` define engineering and safety safeguards; `docs/product-plan.md` provides supporting detail. If older plans disagree with the latest README, surface the conflict for user review instead of silently following outdated requirements. Never weaken security safeguards to resolve a conflict.

## 2. Mission and approved scope

Build an **ECLADO AI marketing, CRM and sales-intelligence web service** that connects accurate sales and customer insights to explainable AI recommendations, churn prevention, carefully controlled marketing activities and measurable outcomes. It is not merely a chart dashboard or a generic chatbot.

Only the following **ten README sections (2.1–2.10)** are approved:

1. **Sales intelligence:** daily/monthly/yearly sales; item/category performance, discounts/refunds, abnormal increases/decreases, evidence-backed explanations and possible solutions.
2. **Customer intelligence:** approved account/member attributes, orders, purchasing frequency, repeat-purchase patterns, segmentation, loyalty and dormancy.
3. **Personalized recommendations and timely campaigns:** justified product suggestions, birthdays, repurchase timing, draft coupons/events/messages.
4. **Negative review recovery:** detect declining reviews, summarize issues, suggest suitable alternatives, apology/support drafts, possible gifts/coupons subject to human approval.
5. **Brand management dashboard:** integrated metrics, issues, actions, AI explanations, sync health and campaign outcomes.
6. **Approved extension 1 — AI reorder timing / inventory depletion estimates:** infer possible restocking periods from order history; never claim real stock or consumption is known without that data.
7. **Approved extension 2 — Early churn warning:** transparent signals such as purchase delay, reduced spend/frequency and verified complaints; do not present unvalidated scores as measured churn probabilities.
8. **Approved extension 4 — Marketing effectiveness:** campaigns, delivery, redemptions, net sales, costs and possible incremental effect; separate before/after associations from causal lift and use comparison/control cohorts where feasible.
9. **Approved extension 3 — Cross-sell:** products commonly bought together and customer-specific purchase patterns, with rationale, sample size and product suitability checks.
10. **Approved extension 5 — External market signals and anomalies:** lawful, authorized external price/promotion/review/trend data correlated with sales/review changes; cite sources and timing, distinguish hypotheses from proven causes.

The five extensions above are **already user-approved**, not suggestions awaiting permission. **Any other proposed feature remains unapproved** until explicitly accepted. No new storefront, general chatbot or unrelated side project.

## 3. Data sources and prototype-to-production transition

- Intended **future** source of confidential business-member, order, sales and review data: ECLADO business mall **`laonmall.co.kr`**, through a business-authorized administrator API or approved export only. API availability, platform, fields, permissions and refresh intervals are **not yet verified**.
- Public **`ecladomall.co.kr`** product pages and observed list/sale prices may support **catalog snapshots only**. Never infer transactions, actual sales, stock truth or customer purchases from them.
- **Until business approval, use only clearly labeled synthetic data** linking business accounts/customers, products, orders, order items, discounts, refunds, reviews, consent, marketing events and outcomes. Never claim synthetic values are actual ECLADO results.
- Create replaceable provider adapters and a normalized data contract, so switching a synthetic source to an authorized mall feed does not require rewriting analytics or UI.
- Preserve source IDs, timestamps, import provenance, mapping status, retry-safe upserts, audit trails, batch state and reconciliation. Do not guess links between identities. Show missing history as missing, **not zero sales**.
- Refresh frequency depends on the actual approved provider's API and operational limits; do not promise unconditional real-time sync.
- **API connection alone does not constitute production readiness.** Authentication, access control, financial reconciliation, consent, data handling, reliability, performance and owner acceptance must pass before launch.

## 4. Architecture: non-negotiable

- Maintain the existing **Python / FastAPI / Streamlit** architecture and planned **Supabase PostgreSQL/Auth, Gemini and SOLAPI** provider boundaries. Do not replace the stack or perform a sweeping refactor without approval.
- Backend dependencies flow `api/routers -> services -> stores`.
- All runtime SQL and Supabase/PostgreSQL access belong only in `backend/eclado_backend/stores/`.
- Streamlit pages use `admin/eclado_admin/repositories/*_repository.py` for backend requests. Shared code contains typed transport/DTO schemas only and performs no DB access.
- Put synthetic/live source adapters, Gemini, messaging and coupon systems behind small interfaces. Unit tests must use fakes and require no external credentials.
- Review existing code/tests before making focused changes; preserve existing functionality, project layout and contracts unless change is approved.
- Prefer additive, versioned DB migrations with documented rollback/forward-fix plans.

## 5. Correctness, privacy and responsible AI

- Store KRW money as integer won; preserve **purchase-time** prices/discounts. Distinguish gross sales, discounts, refunds, shipping and net. Define payment/refund reporting dates (business timezone: **Asia/Seoul**).
- Business-mall members may be beauty salons, clinics or other **business customers**. Do not confuse the buyer, staff contact and ultimate product user.
- Collect/import names, numbers, birthday, gender, preferences and other personal data only with business authorization, proper legal basis and appropriate use restrictions. Restrict access, minimize retention, protect identifiers and support deletion and audit.
- Never infer a person's skin type, health condition, age, gender, motive for not purchasing, or reason for churn **as a fact** from a name, purchase or review. Never present unverified product suitability/medical claims.
- AI output must identify evidence period, sources, sample size when relevant, confidence/limitations, and distinguish **observation → possible cause → suggested response → human-approved action**. If evidence is insufficient, say so.
- Do not send unnecessary identifiable customer data or raw reviews to external AI providers. Confirm lawful processing, contractual scope and retention settings before using real records.
- Negative reviews must not lead to gifts in exchange for deleting/editing reviews; compensation and personal messages require authorized customer-service/marketing processes.

## 6. Access and messaging protections

- Existing demo login and preview session **do not authorize access to real data**. Before live-data access, implement verified server-side JWT validation, role checks (owner / manager / analyst), least-privilege access, RLS where applicable and audited exports/lookups.
- All outbound marketing, coupon issuance, gifts and reorder transactions are **OFF by default**; the prototype offers draft suggestions, review and dry-run only.
- Before any real marketing send: validate purpose/channel-specific consent, unsubscribe status, appropriate message type, sending hours, frequency cap, recipient validity, budget/inventory, approval, idempotency and audit logs. Fail closed; offer a kill switch and safe retry behavior.
- Keep credentials/secrets and actual customer exports out of GitHub, source code, logs and AI prompts. Observe applicable Korean privacy and advertising rules with qualified review before production.

## 7. Implementation order and checks

1. Complete realistic, coherent **synthetic** datasets, contracts and dashboards.
2. Improve sales/refund correctness, customer behaviors, review signals and anomaly detection with unit tests.
3. Implement **all five approved extensions** in explainable demo mode using synthetic data.
4. Add **dry-run** campaign journeys including birthdays, review recovery, churn prevention, reorder reminders, cross-sell, and observed-vs-incremental performance demos.
5. After ECLADO approval, integrate authorized `laonmall.co.kr` sources, reconcile totals, implement Supabase persistence/auth, monitoring and reliability controls; enable messaging only after separate approval and safeguards.

After code changes run: `uv run pytest`, `uv run ruff check .`, `uv run mypy`. Report unrun checks and failures truthfully. Add tests for order/customer joins, refunds, duplicate imports, missing-data handling, roles, consent, suppression and cohort privacy.

Record material requirements in `docs/CHANGE_REQUEST_TEMPLATE.md` and `CHANGELOG.md` with business versions (Ver.1, Ver.2, etc.). Do not commit unapproved additions, customer data or secrets. **Do not commit/push project implementation changes without explicit user instruction.**

## 8. Approval gates

Ask for explicit approval before: adding anything outside README 2.1–2.10; activating actual mall data integrations; contacting customers or issuing coupons/gifts/purchase orders; changing metric definitions or core technology; exposing real customer details to a third-party AI model.

**Success criterion for the current phase:** an accurate, explainable, coherent **prototype using synthetic data** which can move toward production through **authorized source adapters and necessary production hardening**, not through unsupported claims of instant production readiness.
