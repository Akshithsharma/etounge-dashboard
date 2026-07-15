-- PayRecover AI — Supabase schema
-- Run this in the Supabase SQL editor for your project.

create extension if not exists "uuid-ossp";

create table if not exists public.recovery_events (
  id uuid primary key default uuid_generate_v4(),
  merchant_id text not null,
  customer_name text not null,
  amount numeric not null,
  currency text not null default 'INR',
  failure_reason text not null,
  payment_method text not null,
  agent_reasoning text not null,
  strategy text not null,
  recovery_message text not null,
  recovery_link text not null,
  status text not null default 'sent',
  created_at timestamptz not null default now()
);

create index if not exists idx_recovery_events_merchant on public.recovery_events (merchant_id);
create index if not exists idx_recovery_events_created on public.recovery_events (created_at desc);

-- Row Level Security: each merchant (authenticated user) only sees their own events.
alter table public.recovery_events enable row level security;

-- The backend uses the service_role key (bypasses RLS) to insert events from
-- webhooks, so no insert policy is needed for anon/authenticated roles.

create policy "Users can view their own merchant recovery events"
  on public.recovery_events
  for select
  using (auth.uid()::text = merchant_id);

-- Merchants table linking auth.users to a merchant_id / Razorpay account
create table if not exists public.merchants (
  id uuid primary key references auth.users (id) on delete cascade,
  business_name text,
  razorpay_key_id text,
  created_at timestamptz not null default now()
);

alter table public.merchants enable row level security;

create policy "Users can view their own merchant profile"
  on public.merchants
  for select
  using (auth.uid() = id);

create policy "Users can update their own merchant profile"
  on public.merchants
  for update
  using (auth.uid() = id);

create policy "Users can insert their own merchant profile"
  on public.merchants
  for insert
  with check (auth.uid() = id);
