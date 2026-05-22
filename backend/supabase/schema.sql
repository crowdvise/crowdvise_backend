-- Run once in Supabase

create table if not exists public.simulation_runs (
  id uuid primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  product_description text not null,
  target_segment text not null,
  panel_size integer not null check (panel_size in (10, 25, 50)),
  journey_stages jsonb not null,
  result jsonb not null,
  overall_conversion_rate double precision not null,
  overall_dropout_rate double precision not null,
  overall_delayed_rate double precision not null,
  readiness_score integer not null,
  created_at timestamptz not null default now()
);

create index if not exists simulation_runs_user_id_created_at_idx
  on public.simulation_runs (user_id, created_at desc);

alter table public.simulation_runs enable row level security;

create policy "Users read own simulation runs"
  on public.simulation_runs
  for select
  to authenticated
  using (auth.uid() = user_id);

