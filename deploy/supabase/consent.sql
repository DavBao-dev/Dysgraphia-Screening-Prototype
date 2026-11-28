-- Run in the private project's SQL editor. Never expose the service role key to the browser.
create table if not exists public.data_consents (
  id text primary key, accepted_at timestamptz not null, expires_at bigint not null,
  role text not null, guardian_reference text not null default '', version text not null,
  policy_hash text not null, purpose text not null check (purpose = 'screening'),
  accepted boolean not null, child_assent boolean not null, authority_confirmed boolean not null,
  document jsonb not null
);
alter table public.data_consents enable row level security;
revoke all on public.data_consents from anon, authenticated;
grant insert on public.data_consents to service_role;
-- Schedule daily using your controlled operations process, and delete earlier when legally required:
-- delete from public.data_consents where accepted_at < now() - interval '24 months';

create table if not exists public.screening_consent_links (
  session_id text primary key,
  receipt_id text not null references public.data_consents(id) on delete cascade
);
alter table public.screening_consent_links enable row level security;
revoke all on public.screening_consent_links from anon, authenticated;
grant insert on public.screening_consent_links to service_role;
