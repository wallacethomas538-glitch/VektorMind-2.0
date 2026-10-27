-- Hackathon 2026 mission schema. New Supabase project only.
-- RLS is enabled and deny-by-default: the API writes with a service-role key.
-- Do not point this at the frozen VektorFlow-15xr project.

create table if not exists public.missions (
    id text primary key,
    objective jsonb not null default '{}'::jsonb,
    status text not null default 'staged_for_approval',
    plan jsonb not null default '[]'::jsonb,
    risk jsonb not null default '{}'::jsonb,
    kill_switch boolean not null default false,
    meta_served boolean not null default false,
    image_served boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.mission_receipts (
    mission_id text primary key references public.missions(id) on delete cascade,
    receipt jsonb not null,
    status text not null default 'staged_for_approval',
    meta_served boolean not null default false,
    image_served boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.approvals (
    id uuid primary key default gen_random_uuid(),
    mission_id text not null references public.missions(id) on delete cascade,
    approver text not null,
    role text not null default 'final tap',
    status text not null default 'pending',
    scope text not null default '',
    requested_at timestamptz not null default now(),
    decided_at timestamptz,
    unique (mission_id, approver)
);

alter table public.missions enable row level security;
alter table public.mission_receipts enable row level security;
alter table public.approvals enable row level security;

-- No anon/authenticated policies: deny by default. Service-role bypasses RLS.
revoke all on public.missions from anon, authenticated;
revoke all on public.mission_receipts from anon, authenticated;
revoke all on public.approvals from anon, authenticated;

comment on table public.missions is 'VektorMind 2.0 Hackathon 2026 mission state. RLS on, service-role writes only.';
comment on table public.mission_receipts is 'Staged mission receipts. meta_served/image_served stay false until second approval.';
comment on table public.approvals is 'Human approvals. Wallace is the final tap.';
