# Architecture and operating rules

## Request and data flow

```text
Streamlit page -> admin/*_repository.py -> shared API client -> FastAPI router
             -> service (business rules) -> store (database and SQL)
```

- Routers handle HTTP, authentication dependencies, input validation, and response schemas. They do not contain business policy or SQL.
- Services own segmentation, eligibility, frequency-cap, campaign, and analysis decisions. They call stores and provider interfaces.
- Stores are the only backend layer allowed to execute SQL or access Supabase/PostgreSQL.
- Streamlit pages and components call backend APIs only through `admin/eclado_admin/repositories/*_repository.py`.
- `shared/` contains transport clients and DTOs only. It does not access Supabase or hold business rules.
- External systems (Supabase Auth/DB, SOLAPI, Gemini) belong behind small service-facing interfaces. Use fakes in unit tests; integration tests must be opt-in and credential-gated.

## Privacy, consent, and marketing controls

- Treat customer identifiers, contact information, purchases, reviews, and inferred attributes as sensitive. Collect only fields required for a defined purpose, restrict access by role, and define retention/deletion procedures before production use.
- Verify the current marketing consent and channel-specific opt-out status at send time, not only when a segment is created. A send must fail closed if consent is missing, stale, or unavailable.
- Enforce per-customer frequency caps and campaign eligibility in the service, then persist an auditable decision and idempotency key before dispatch. Retries must not duplicate messages. Honor opt-outs immediately and maintain a suppression record suitable for preventing accidental re-import/re-send.
- Keep credentials in a secret manager or deployment environment, never in source control, Streamlit page code, logs, or prompts. Use least-privilege service credentials and separate local, staging, and production projects.
- Apply Korean privacy, advertising, and communications requirements with qualified legal/privacy review before launch. This scaffold is not a compliance certification.

## AI analysis boundaries

- Use AI for assistive summaries and review/activity pattern hypotheses, not as the sole authority for consequential customer decisions or sensitive-trait inference.
- Do not send direct identifiers or unnecessary raw review/order details to a model. Minimize, redact or pseudonymize inputs, constrain retention, and confirm the provider's data-use settings before using customer content.
- Store model/provider, prompt/template version, time, input provenance, and output version for reproducibility. Label inferred explanations as uncertain; provide human review and correction paths.
- Do not claim AI can determine why an individual became inactive from reviews or purchase activity alone. Use validated aggregate evidence and treat explanations as hypotheses.

## Integration sequence

1. Implement Supabase Auth verification and role checks for owner and authorized sales managers.
2. Add store interfaces and migrations with explicit ownership, indexes, retention, and rollback plans.
3. Add SOLAPI through a provider adapter. Start in dry-run mode, then use a small approved test cohort after consent and suppression checks are reviewed.
4. Add Gemini through a provider adapter with model selection in configuration so a free-to-paid tier change does not alter business services.
5. Add import reconciliation, audit dashboards, monitoring, backup/restore exercises, and operational runbooks before production.
