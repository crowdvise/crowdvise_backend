-- Run after schema.sql (experiments + rerun lineage)

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

-- Inserts/updates use service role from the API
