-- Draft foundation only. Review retention, access policies, and applicable law
-- with the data owner before applying to any shared or production database.
-- Assumes Supabase Auth owns the canonical customer identity in auth.users.

create table if not exists public.customer_marketing_preferences (
    customer_id uuid primary key references auth.users (id) on delete cascade,
    sms_marketing_consent boolean not null default false,
    sms_consent_at timestamptz,
    sms_consent_source text,
    sms_opted_out_at timestamptz,
    updated_at timestamptz not null default now(),
    constraint sms_consent_timestamp_required
        check (not sms_marketing_consent or sms_consent_at is not null)
);

create table if not exists public.marketing_message_outbox (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid not null references auth.users (id) on delete restrict,
    channel text not null check (channel in ('sms')),
    campaign_key text not null,
    idempotency_key text not null unique,
    eligibility_snapshot jsonb not null,
    status text not null default 'pending'
        check (status in ('pending', 'suppressed', 'sending', 'sent', 'failed')),
    provider_message_id text,
    suppression_reason text,
    created_at timestamptz not null default now(),
    dispatched_at timestamptz,
    constraint suppression_reason_for_suppressed
        check (status <> 'suppressed' or suppression_reason is not null)
);

create index if not exists marketing_outbox_customer_created_idx
    on public.marketing_message_outbox (customer_id, created_at desc);

create index if not exists marketing_outbox_pending_idx
    on public.marketing_message_outbox (created_at)
    where status = 'pending';

-- Deliberately no client-facing RLS policies are included in this draft.
-- Add least-privilege policies only after auth/role ownership is established.
-- Rollback: stop send workers; export/audit required records; then drop the
-- indexes and tables in reverse order after confirming retention obligations.
