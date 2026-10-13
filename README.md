# FitGenix

Multi-tenant fitness business SaaS. Django + DRF API (`backend/`), Next.js 14 app (`frontend/`).
One gym = one tenant = one subdomain (`hulkzone.fitgenix.com`). Shared database, `tenant_id` on every gym table.

## Run it locally (sqlite, 2 minutes)

```bash
# 1) API
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed            # plans + demo gym: owner@hulkzone.com / password123 (tenant: hulkzone)
python manage.py runserver 8000
python manage.py test apps       # 9 tests, incl. tenant isolation

# 2) Web
cd ../frontend
npm install
npm run dev                      # http://localhost:3000
```

Open `http://hulkzone.localhost:3000/login` (Chrome resolves `*.localhost`), or plain `http://localhost:3000/login` and type `hulkzone` in the Workspace field.

## Moving to Postgres (your "migrate later")

Set `DATABASE_URL=postgres://user:pass@host:5432/fitgenix`, then `python manage.py migrate && python manage.py seed`.
Migrations are already generated and committed (`apps/*/migrations`). `docker-compose up db backend` gives you Postgres + API.

## Production domain

Backend: `BASE_DOMAIN=fitgenix.com`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`.
Frontend: `NEXT_PUBLIC_BASE_DOMAIN=fitgenix.com`, `BACKEND_URL=https://api...`.
DNS `*.fitgenix.com` + wildcard TLS (Cloudflare). The app derives the tenant from the hostname and sends it as `X-Tenant`;
the API re-checks it against the token and the user's membership, so the header alone grants nothing.

## How the pieces map to the design doc

| Concern                                                  | Where                                                                           |
| -------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Tenant resolution                                        | `backend/apps/core/middleware.py`                                               |
| Tenant-scoped ORM, fails closed                          | `backend/apps/core/tenancy.py` (`objects` = scoped, `unscoped` = platform only) |
| Plans, trial, add-ons, hide toggles                      | `backend/apps/billing/` (`effective_features = (plan + grant) - hide`)          |
| API-enforced feature gates + roles + read-only on expiry | `backend/apps/core/permissions.py`                                              |
| `/auth/me` with `enabled_features`                       | `backend/apps/core/views.py`                                                    |
| Dashboard aggregates                                     | `DashboardView` in `apps/core/views.py`                                         |
| Nav registry filtered by features/role                   | `frontend/app/(app)/layout.tsx`                                                 |
| Generic CRUD screens                                     | `frontend/components/ResourcePage.tsx`                                          |

## Known gaps (be honest before launch)

- **Postgres RLS is not added yet.** Isolation today = scoped ORM that returns nothing without a tenant + tests. Add RLS as defense in depth once on Postgres.
- **No payment gateway.** `POST /billing/subscription` switches plans without charging. Add SaaS invoices + SSLCommerz/bKash webhooks (idempotent) before taking money. No dunning/Celery jobs yet; trial expiry is lazy (checked on request).
- **Tokens live in localStorage** (simple, but XSS-exposed). Move refresh token to an httpOnly cookie via Next route handlers.
- **Not built yet:** POS, classes, instructors, reports/exports, email config, invoices PDF, ZKTeco iclock endpoint, QR check-in, member portal, Next `middleware.ts`.
- Member codes are count-based (can race under heavy concurrency): swap for a locked counter row.
- Refresh tokens rotate but are not blacklisted. Dashboard queries run live; add the `DailyRollup` table when a gym passes ~20k check-ins.
- Demo seed has no renewals, so demo retention shows 0%.
