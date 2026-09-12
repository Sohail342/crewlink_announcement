# CrewLink

Union leadership can create and send announcements to **active** members of their own local (entire local or one work classification). Members can read and acknowledge. Leadership can watch sent / read / acknowledged counts. Isolation and delivery idempotency are enforced in the API.

The API is two Django instances behind nginx. Sends are queued in Redis and processed by a Celery worker. Delivery is a database/log record (`PushService`); there is no real push provider.

## Setup

Copy env files, then build and start Compose from the repo root:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose build
```

nginx listens on **http://localhost:8080** and load-balances `/api/`, `/admin/`, and `/static/` across `backend-1` and `backend-2` (round-robin). Responses include `X-Upstream` so you can see which instance answered.

Leadership UI:

```bash
cd frontend
npm install
npm run dev
```

The Next.js rewrite sends `/api/*` to `API_ORIGIN` (default in `frontend/.env.example` is `http://127.0.0.1:8080`).

## Environment

### `backend/.env`

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret |
| `DJANGO_DEBUG` | `True` / `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts. Must include `localhost,127.0.0.1` so nginx (`Host: localhost`) is accepted |
| `CELERY_BROKER_URL` | Redis broker. Compose overrides this to `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis results. Compose overrides this to `redis://redis:6379/1` |
| `POSTGRES_DB` | Database name (`crewlink`) |
| `POSTGRES_USER` | Database user (`crewlink`) |
| `POSTGRES_PASSWORD` | Database password (`crewlink`) |
| `POSTGRES_HOST` | Hostname (`db` inside Compose) |
| `POSTGRES_PORT` | Port (`5432`) |
| `GEMINI_API_KEY` | Optional. Required for `POST /api/announcements/ai-draft/` |
| `GEMINI_MODEL` | Optional Gemini model name |

See [backend/.env.example](backend/.env.example). Compose also sets `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` on the API containers.

### `frontend/.env`

| Variable | Purpose |
|---|---|
| `API_ORIGIN` | Django origin used by Next.js rewrites (`http://127.0.0.1:8080`) |

See [frontend/.env.example](frontend/.env.example).

# Run these commands in root directory 
## Migrate

```bash
docker compose run --rm backend-1 python manage.py migrate
```

## Seed

```bash
docker compose run --rm backend-1 python manage.py seed_data
```
## Run the Docker Containers after seed

```bash
docker compose up -d
```

## Run Test Suit

```bash
docker compose exec backend-1 uv run python manage.py test apps.announcements apps.locals apps.accounts
```

Expected data (idempotent; re-run skips bulk members if counts already match):

- **Local 100** — about 2000 members
- **Local 200** — about 200 members
- Classifications: `electrician`, `plumber`, `carpenter`, `operator`
- Mix of `active`, `retired`, and `suspended` members
- One `LEADERSHIP` user and one `MEMBER` user per local
- One already-sent announcement in Local 100: **"Saturday overtime callout"** (`needs_ack=true`)
- `AnnouncementRecipient` rows for that announcement’s **active** Local 100 members (`delivery_status=sent`, some `read_at` / `acknowledged_at`)

The command prints the created announcement id, for example: `Created sent announcement 1 with … recipients.`

## Test accounts

Password for every demo login is `demo-password`.

```json
{
  "password": "demo-password",
  "accounts": [
    {
      "email": "leader@local100.example",
      "role": "LEADERSHIP",
      "local": "Local 100"
    },
    {
      "email": "member@local100.example",
      "role": "MEMBER",
      "local": "Local 100",
      "full_name": "Alex Rivera",
      "classification": "electrician"
    },
    {
      "email": "leader@local200.example",
      "role": "LEADERSHIP",
      "local": "Local 200"
    },
    {
      "email": "member@local200.example",
      "role": "MEMBER",
      "local": "Local 200",
      "full_name": "Jordan Hale",
      "classification": "plumber"
    }
  ]
}
```

Auth header after login: `Authorization: Token <token>`.

## Existing announcement ID

On a first-time seed against an empty database, the already-sent Local 100 announcement is:

| Field | Value |
|---|---|
| **id** | `1` |
| title | `Saturday overtime callout` |
| local | Local 100 |
| status | `sent` |
| needs_ack | `true` |

Confirm (or read the id printed by `seed_data`):

```bash
curl -s -X POST http://localhost:8080/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"leader@local100.example\",\"password\":\"demo-password\"}"
```

```bash
curl -s http://localhost:8080/api/announcements/1/ \
  -H "Authorization: Token <LEADER_100_TOKEN>"
```

```bash
curl -s http://localhost:8080/api/announcements/1/counts/ \
  -H "Authorization: Token <LEADER_100_TOKEN>"
```

Counts are `{ "sent", "read", "acknowledged" }`.

## Member read / acknowledge

`needs_ack` is true on announcement `1`. Recipients are scoped to the logged-in member.

```bash
curl -s -X POST http://localhost:8080/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"member@local100.example\",\"password\":\"demo-password\"}"
```

```bash
curl -s http://localhost:8080/api/recipients/ \
  -H "Authorization: Token <MEMBER_100_TOKEN>"
```

Use a recipient `id` from that list (the row whose `announcement` is `1`):

```bash
curl -s -X POST http://localhost:8080/api/recipients/<RECIPIENT_ID>/read/ \
  -H "Authorization: Token <MEMBER_100_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{}"
```

```bash
curl -s -X POST http://localhost:8080/api/recipients/<RECIPIENT_ID>/acknowledge/ \
  -H "Authorization: Token <MEMBER_100_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{}"
```

Acknowledge returns `400` if `needs_ack` is false. Seed may already have set `read_at` / `acknowledged_at` on some rows; a second call is a no-op and still returns the recipient.

## Cross-local access denial

Local 200 leadership cannot read Local 100’s announcement `1` (queryset is scoped to `request.user.local_id`; expect **404**).

```bash
curl -s -X POST http://localhost:8080/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"leader@local200.example\",\"password\":\"demo-password\"}"
```

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8080/api/announcements/1/ \
  -H "Authorization: Token <LEADER_200_TOKEN>"
```

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8080/api/announcements/1/counts/ \
  -H "Authorization: Token <LEADER_200_TOKEN>"
```

A Local 100 **member** cannot create or send (expect **403**):

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8080/api/announcements/ \
  -H "Authorization: Token <MEMBER_100_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"x\",\"body\":\"x\",\"push_preview\":\"x\",\"needs_ack\":false}"
```

## Retry / no double delivery

Recipients are created in the send request, then a Celery task runs. Unique constraint: `(announcement_id, member_id)`. The worker only processes `pending` rows (`select_for_update`) and skips `sent`. Send is allowed only when status is `draft` or `queued`; `sending` / `sent` cannot be re-queued.

Create a draft, send it twice. The first send queues delivery. After the worker marks it `sent`, the second send is rejected and the recipient count stays the same.

```bash
curl -s -X POST http://localhost:8080/api/announcements/ \
  -H "Authorization: Token <LEADER_100_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Retry check\",\"body\":\"Same members once\",\"push_preview\":\"Retry check\",\"needs_ack\":false}"
```

```bash
curl -s -X POST http://localhost:8080/api/announcements/<DRAFT_ID>/send/ \
  -H "Authorization: Token <LEADER_100_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{}"
```

First send returns `{"detail":"sending to members","status":"sending"}`. Recipients exist as `pending` immediately (before the worker finishes).

```bash
curl -s http://localhost:8080/api/recipients/ \
  -H "Authorization: Token <LEADER_100_TOKEN>"
```

After status is `sent`, the same send URL returns **400** (`Only draft or queued announcements can be sent.`) and does not create another `AnnouncementRecipient` row.

A **queued** retry (worker crash before those rows were marked `sent`) is allowed: the same unique constraint and `ignore_conflicts` keep one row per member; already-`sent` recipients are skipped.

Optional classification on send (one value, or omit for the entire local):

```bash
curl -s -X POST http://localhost:8080/api/announcements/<DRAFT_ID>/send/ \
  -H "Authorization: Token <LEADER_100_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"classification\":\"electrician\"}"
```

## API map

Base URL: `http://localhost:8080`

| Method | Path | Who |
|---|---|---|
| POST | `/api/auth/login/` | public |
| POST | `/api/auth/logout/` | authenticated |
| GET | `/api/auth/me/` | authenticated |
| GET | `/api/locals/` | own local only |
| GET | `/api/members/` | leadership, own local |
| GET, POST | `/api/announcements/` | leadership create; list scoped by role |
| GET, PATCH | `/api/announcements/{id}/` | PATCH drafts only |
| POST | `/api/announcements/{id}/send/` | leadership; `draft` or `queued` only |
| GET | `/api/announcements/{id}/counts/` | leadership |
| POST | `/api/announcements/ai-draft/` | leadership; `{ "note": "..." }` |
| GET | `/api/recipients/` | leadership: own-local rows; member: own rows |
| POST | `/api/recipients/{id}/read/` | member |
| POST | `/api/recipients/{id}/acknowledge/` | member; requires `needs_ack` |

Admin: `http://localhost:8080/admin/`

## Design notes

- Only **active** members receive a send.
- `local_id` is the tenant boundary. The API ignores a client-supplied local on create.
- AI drafts are never auto-sent. If `GEMINI_API_KEY` is missing, `POST /api/announcements/ai-draft/` returns **503** and leadership can still create a draft by hand.
- Real push, a member UI, RSVP, and production monitoring are out of this build.