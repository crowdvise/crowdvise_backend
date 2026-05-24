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

-- Experiments + reruns (see migrations/002_experiments_and_reruns.sql for ALTER on existing DBs)
create table if not exists public.simulation_experiments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  product_description text not null,
  target_segment text not null,
  panel_size integer not null check (panel_size in (10, 25, 50)),
  panel_profiles jsonb not null default '[]'::jsonb,
  fix_suggestions jsonb,
  baseline_run_id uuid,
  created_at timestamptz not null default now()
);

create index if not exists simulation_experiments_user_id_created_at_idx
  on public.simulation_experiments (user_id, created_at desc);

alter table public.simulation_runs
  add column if not exists experiment_id uuid references public.simulation_experiments (id) on delete cascade,
  add column if not exists run_kind text not null default 'baseline'
    check (run_kind in ('baseline', 'rerun')),
  add column if not exists run_index integer not null default 0
    check (run_index >= 0 and run_index <= 2),
  add column if not exists applied_fix jsonb,
  add column if not exists parent_run_id uuid references public.simulation_runs (id) on delete set null;

create index if not exists simulation_runs_experiment_id_run_index_idx
  on public.simulation_runs (experiment_id, run_index);

alter table public.simulation_experiments enable row level security;

create policy "Users read own simulation experiments"
  on public.simulation_experiments
  for select
  to authenticated
  using (auth.uid() = user_id);

-- User profiles (signup: first name, last name, industry)
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  first_name text not null,
  last_name text not null,
  industry text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists profiles_industry_idx on public.profiles (industry);

alter table public.profiles enable row level security;

create policy "Users read own profile"
  on public.profiles
  for select
  to authenticated
  using (auth.uid() = id);

create policy "Users update own profile"
  on public.profiles
  for update
  to authenticated
  using (auth.uid() = id)
  with check (auth.uid() = id);

create policy "Users insert own profile"
  on public.profiles
  for insert
  to authenticated
  with check (auth.uid() = id);

