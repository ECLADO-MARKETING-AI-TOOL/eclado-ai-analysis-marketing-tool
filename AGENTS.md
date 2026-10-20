# Codex Instructions for Eclado

Before making changes, read `docs/product-plan.md`, `docs/architecture.md`, and `.github/copilot-instructions.md`.

## Project goal

Build an internal AI-assisted marketing and sales analytics system for ECLADO using FastAPI, Streamlit, Supabase PostgreSQL/Auth, SOLAPI, and Gemini. The system is not production-ready until authentication, role enforcement, consent checks, data retention, and provider integrations are implemented and reviewed.

## Non-negotiable architecture

- Backend dependency direction: `api/routers -> services -> stores`.
- Runtime SQL and database access exist only in `backend/eclado_backend/stores/`.
- Streamlit pages call the backend only through `admin/eclado_admin/repositories/*_repository.py`.
- Shared code contains API transport and DTOs only; it never accesses the database.
- Keep Supabase, SOLAPI, and Gemini behind small interfaces. Unit tests must use fakes and need no credentials.
- No real messages are sent by default. Marketing sends require current consent, opt-out suppression, frequency-cap checks, idempotency, and an audit trail.

## Data and security rules

- Treat customer, order, review, consent, and inferred data as sensitive. Minimize collection, restrict access by role, and keep credentials out of source control and logs.
- Public ECLADO product pages can seed or refresh the product catalog and observed price snapshots only. They are not an order ledger and cannot be used to calculate sales or identify purchasing customers.
- Prefer authorized Cafe24/admin API access or official exports for customer, order, cancellation, refund, review, and consent data. Confirm access scope, terms, and business authorization before integration; do not bypass authentication or anti-bot controls.
- Use integer KRW for money. Preserve order-item purchase-time price/discount snapshots; do not recalculate historical revenue from current product prices.
- Do not infer age, gender, skin condition, or reasons for inactivity from names or review text. AI explanations are hypotheses and need aggregate evidence and human review.
- Make database migrations additive where practical and document rollback/forward-fix steps.

## Change and verification workflow

- Read existing code and tests before editing. Keep changes small and focused.
- Record client requests in `docs/CHANGE_REQUEST_TEMPLATE.md` and `CHANGELOG.md` using business versions such as Ver.1, Ver.2, etc.
- Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy` after implementation changes.
- Never commit secrets, customer exports, or production data. Do not make commits unless explicitly requested.
