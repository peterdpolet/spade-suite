# miniApp — Session Log (Module 2 Auth → ongoing)

**Note:** kept as one continuous end-to-end log across modules, by
request — not split per-module, so the full build sequence and every
lesson learned along the way stays in one place.

**Context:** Module 1 scaffold downloaded and unpacked. Backend + skeleton
frontend in place, venv (`/home/envs/spadework`) set up with requirements
installed. Running venv-first, Docker later — side quest: understanding
*why* Docker footprints look smaller than a venv, for the Spadework
Docker/debugging documentation.

---

## Docker vs venv size investigation

**Point:** A venv looks "lean" but is actually a full, undeduplicated copy
of the interpreter + every dependency's unpacked wheel (compiled `.so`
files, dist-info, sometimes docs/test fixtures). Docker looks smaller for
three separate reasons:
1. No kernel/OS in the image — containers share the host kernel via
   namespaces/cgroups, so there's no "OS" to ship.
2. Layer deduplication — shared base layers (e.g. `python:3.12-slim`)
   exist once on disk via OverlayFS, reused across every image built
   from them. `docker images` shows logical size, which double-counts
   shared layers.
3. Multi-stage builds — build-time tooling (gcc, headers, pip cache)
   can be stripped from the final image, leaving only runtime artifacts.

**Measurements so far:**
- `du -sh /home/envs/spadework` → **175M** (venv, shared across projects,
  not miniApp-only, but the "everything unpacked, nothing shared"
  baseline)
- `docker images size-test` → **DISK USAGE 395MB / CONTENT SIZE 85.3MB**
  for an image built `FROM python:3.12-slim` + same `requirements.txt`.
  - DISK USAGE = full logical size (base layer + installed packages),
    as if this were the only image on the machine.
  - CONTENT SIZE = size unique to this image (the pip-install layer
    only) — the ~310MB base layer is stored once on disk and shared/
    reused by every other image built `FROM python:3.12-slim`.
  - **Key comparison:** venv 175M (interpreter + packages, nothing
    shared) vs Docker's 85.3MB unique content (packages only — the
    interpreter lives in the shared, amortized base layer).

**Commands run:**
```
mkdir -p /tmp/docker-size-test && cp /home/spadework/miniapps/miniapp/backend/requirements.txt /tmp/docker-size-test/
```
```
cat > /tmp/docker-size-test/Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EOF
```
```
cd /tmp/docker-size-test && docker build -t size-test .
```
(base layer was already CACHED from a prior pull — demonstrates layer
reuse directly)
```
docker images size-test
```

**`docker history size-test --no-trunc` results (correction to earlier claim):**
- `RUN pip install --no-cache-dir -r requirements.txt` → **176MB**
  (uncompressed layer size) — essentially matches the venv's 175M
  almost exactly. **Correction:** the packages themselves are NOT
  smaller in Docker — same packages, same disk cost. The earlier
  "CONTENT SIZE 85.3MB" from `docker images` doesn't match this; likely
  measuring compressed vs uncompressed size, but unconfirmed — treat
  the 85.3MB figure as unreliable pending clarification.
- Base image layers (the real story):
  - Python built from source (compile, headers, etc.) → 41.3MB
  - `ca-certificates`/`tzdata` install → 4.94MB
  - WORKDIR/ENV/CMD → 0B (metadata only)
  - Base Debian rootfs import (`debian.sh ... trixie`) → **size cut off
    in paste, need to re-check** — almost certainly the largest single
    layer, explaining most of the 395MB DISK USAGE total.
- **Revised conclusion:** the size saving isn't from packages taking
  less room in Docker — it's entirely that the *base* layer (Debian +
  compiled Python, ~46MB+ visible so far, likely more) is paid for once
  and reused across every image built from it, where a venv pays the
  full interpreter + package cost privately, every time.

**Still to confirm:** ~~size of the base rootfs import layer~~ CONFIRMED:
base Debian rootfs (`debian.sh ... trixie`) = **87.4MB**.

**Final layer breakdown (`docker history size-test`):**
| Layer | Size |
|---|---|
| Base Debian rootfs | 87.4MB |
| Python compiled from source | 41.3MB |
| ca-certificates/tzdata | 4.94MB |
| Symlinks + COPY + WORKDIR | ~36.9kB |
| ENV/CMD | 0B |
| `pip install` (the app layer) | 176MB |
| **Total (visible layers)** | **≈309.7MB** |

**RECONCILED — `docker inspect size-test --format='{{.Size}}'` → 85,288,449
bytes = 85.3MB.** Matches the earlier `CONTENT SIZE` column exactly.

**Final answer — three metrics, three questions:**
| Question | Command | Answer |
|---|---|---|
| Uncompressed cost of each build step | `docker history` | 176MB (pip), 87.4MB (base OS), 41.3MB (Python) |
| Total logical size, nothing pre-cached | `docker images` DISK USAGE | 395MB |
| Actual marginal disk cost, base already cached | `docker inspect .Size` / CONTENT SIZE | **85.3MB** (compressed; base layer contributes 0 since already on disk) |

Explanation for the 176MB→85.3MB gap: Docker stores/transfers layers
gzip-compressed; Python wheels (compiled binaries + text) commonly
compress to roughly half their uncompressed size, which lines up with
176MB → ~85MB.

**Docker size investigation: CLOSED.** Tutorial takeaway confirmed: the
saving isn't smaller packages — it's the base OS+Python cost (~129MB
uncompressed) being paid once and shared, vs a venv paying it privately
per project; and the compressed marginal cost of a *new* image once
that base is cached is ~85MB, not the full ~300-400MB.

---

## Back to Module 2 (Auth) build — resuming here

**Ran:**
```
cd /home/spadework/miniapps/miniapp/backend && source /home/envs/spadework/bin/activate && python manage.py makemigrations accounts
```
→ `accounts/migrations/0001_initial.py` created (Create model User).
RuntimeWarning about host "db" not resolving — expected, see below.

**Issue found:** no `.env` existed anywhere (only `.env.example` at
project root, sibling to `backend/`, `frontend/`, `docker-compose.yml`).
`config/settings/base.py` does `load_dotenv(BASE_DIR.parent / '.env')`
— `BASE_DIR` = `backend/`, so `.parent` = project root
(`/home/spadework/miniapps/miniapp/`). `.env` must live there, NOT
inside `backend/`.

`DATABASES['default']['HOST']` reads `DB_HOST` env var, defaulting to
`'db'` — the Docker Compose service name, unresolvable outside Docker's
network. Same problem exists for `REDIS_HOST` (defaults to `'redis'`)
but that only matters once Channels/ASGI is actually exercised — not
needed for `migrate`. **Redis not installed locally yet** — parked
until Module 2 needs a live server test with websockets.

**Native Postgres confirmed:** DB name/user/password set up locally to
match `.env.example` exactly.

**Fixed:**
```
cp /home/spadework/miniapps/miniapp/.env.example /home/spadework/miniapps/miniapp/.env
sed -i 's/^DB_HOST=db/DB_HOST=localhost/' /home/spadework/miniapps/miniapp/.env
```
Confirmed: `DB_HOST=localhost` in the real `.env`.

**Ran (SUCCESS):**
```
cd /home/spadework/miniapps/miniapp/backend && python manage.py migrate
```
All migrations applied cleanly against native Postgres (accounts, admin,
auth, contenttypes, sessions, token_blacklist) — `.env` fix confirmed
working.

**Ran (SUCCESS):** `python manage.py createsuperuser` — superuser created
(email-based login confirmed working, per Djoser LOGIN_FIELD='email').

**Ran (SUCCESS):** `python manage.py runserver` — started clean on
http://127.0.0.1:8000/, no Redis connection issues (channel layer is
lazy, not touched by plain HTTP auth). Server left running.

**Ran:** first curl attempt against `/api/auth/users/` → 404. Checked
`config/urls.py` — confirmed no `api/` prefix exists; Djoser (`djoser.urls`
+ `djoser.urls.jwt`) is mounted at `auth/` directly. Not a bug — this is
Module 1's scaffold as built (boards/issues/teams/etc URLs deliberately
not wired yet). My curl URL was wrong, not the code.

**Ran (SUCCESS):** registration with `re_password` added → user created,
id 2. Djoser + custom User model + native Postgres confirmed working
end-to-end.

**Ran (SUCCESS):** JWT login → valid `access` + `refresh` tokens
returned. Backend auth flow (registration + login) fully confirmed
working end-to-end against native Postgres, venv-only, no Docker.

## Module 2 (Auth) — Vue frontend build

Checked existing scaffold before writing anything: `main.ts` (Pinia +
Router already wired), `package.json` (axios already a dependency, no
install needed), `router/index.ts` (plain relative imports, no path
alias needed for imports though `@` alias exists in `vite.config.ts`),
`stores/` (empty, no existing convention to match).

**Files created:**
- `src/api/client.ts` — axios instance, base URL `http://127.0.0.1:8000`.
  Request interceptor attaches `Bearer` token from localStorage. Response
  interceptor does silent refresh on 401 (queues concurrent requests
  during refresh, retries once via `_retry` flag, clears storage and
  rejects if refresh itself fails).
- `src/stores/auth.ts` — Pinia store: `register`, `login`, `fetchUser`,
  `logout` actions; `isAuthenticated` getter; `access`/`refresh` held in
  both state (reactivity) and localStorage (survives reload, read
  directly by the axios client). Djoser field-keyed error responses
  flattened to one readable string via `formatDjoserError`.
- `src/views/LoginView.vue` — email/password form, shows `auth.error`,
  redirects to `dashboard` on success.
- `src/views/RegisterView.vue` — email/username/password/re_password
  form, redirects to `login` with email prefilled on success (Djoser's
  default create flow doesn't auto-login).
- `src/views/DashboardView.vue` — calls `fetchUser()` on mount if not
  already loaded, bounces to login if that fails; logout button.
- `src/router/index.ts` — rewritten in full: `login`/`register` routes
  (`meta: requiresGuest`), `/` → `dashboard` (`meta: requiresAuth`).
  Guard bounces unauthenticated users to login, authenticated users away
  from login/register. `ScaffoldPlaceholder.vue` no longer routed to but
  left on disk pending confirmation nothing else references it.

**Issue found:** `npm run dev` → `vite: not found` — `node_modules`
never installed, only `package.json` existed.

**Fixed:**
```
cd /home/spadework/miniapps/miniapp/frontend && npm install
```
→ 198 packages installed. 2 vulnerabilities flagged (1 moderate, 1
high) — noted, NOT fixed now (`npm audit fix --force` can bump major
versions unexpectedly; deferred to a dedicated look later).

**Issue found:** router rewrite from the earlier batch never actually
landed on disk (only `DashboardView.vue` from that same message did) —
`ScaffoldPlaceholder` was still rendering at `/`. Re-ran the `cat >`
heredoc for `router/index.ts` on its own — confirmed via Vite hot-reload,
browser now correctly bounces unauthenticated visitors to `/login` and
shows the login form.

**Ran (SUCCESS) — full manual browser test:** Register → Login →
Dashboard, showing logged-in user's real email and username. Confirmed
via actual UI, not curl.

**MODULE 2 (AUTH): COMPLETE.** Backend (Djoser + JWT + custom User model
+ native Postgres) and frontend (Pinia auth store, axios client with
silent refresh, Login/Register/Dashboard views, router guard) both
verified working end-to-end, venv-only, no Docker yet.

## Docker build — Module 2

Checked `docker-compose.yml` (standard 6-container layout: db, redis,
backend/gunicorn, daphne, frontend, nginx), `backend/Dockerfile` (plain
pip install, `manage.py migrate && gunicorn` on start — note:
`DJANGO_SETTINGS_MODULE` defaults to `config.settings.dev` per
`manage.py`, not overridden anywhere in this Dockerfile/compose — flagged
for later, not fixed), `frontend/Dockerfile` (proper multi-stage:
`node:22-slim` builder discarded, only `dist/` copied into final
`nginx:alpine` stage — good real example of the layer-sharing story from
earlier), `nginx/default.conf`.

**Bug found (before building):** nginx only proxies `/ws/`, `/api/`,
`/admin/` to backend — everything else (`location /`) goes to the
frontend container. But `config/urls.py` mounted Djoser at `auth/`
directly, no `/api/` prefix. Under Docker, `/auth/jwt/create/` etc. would
have matched `location /` and hit the frontend (returning HTML, not
JSON) instead of the backend — silent, confusing breakage rather than a
clean 404.

**Decision: fix `urls.py`, not nginx.** `/api/` is meant to be the single
catch-all for ALL backend REST endpoints (auth now, boards/issues/teams/
etc. later) — patching nginx per-app would recreate this same bug for
every future module.

**Fixed:**
- `backend/config/urls.py` — Djoser now mounted at `api/auth/` (both
  `djoser.urls` and `djoser.urls.jwt`)
- `frontend/src/api/client.ts` — refresh call updated to
  `/api/auth/jwt/refresh/`
- `frontend/src/stores/auth.ts` — `register`/`login`/`fetchUser` calls
  updated to `/api/auth/users/`, `/api/auth/jwt/create/`,
  `/api/auth/users/me/`
- All three confirmed landed on disk via `cat`.

**Ran (SUCCESS):**
```
docker compose build
```
All three custom images built clean (backend, daphne, frontend) —
~70s, base `python:3.12-slim` layer reused from earlier size-test pull,
no recompilation needed on this machine (confirmed: compilation happens
once upstream when the official image maintainers publish it, not
locally, ever).

**Issue found:** `docker compose up -d` failed on nginx — port 80 already
bound by a native nginx service running on the laptop (17 worker
processes, checked via `sudo ss -tlnp`). Decision: stop the native
service (Peter's call, dev laptop).

**Fixed:**
```
sudo systemctl stop nginx
docker compose up -d nginx
```
All 6 containers running: redis, frontend, db, daphne, backend, nginx.

**Ran:** `docker compose logs backend` — log shows 2 failed connection
attempts then success. NOT a real bug: `depends_on: db` only waits for
the container to *start*, not for Postgres inside it to be ready to
accept connections. Backend's `migrate` ran before Postgres finished
initializing twice, failed, `restart: always` brought it back, third
attempt succeeded once Postgres was actually ready. Migrations applied
cleanly, gunicorn started (`Listening at: http://0.0.0.0:8000`).

**Unintentional gotcha, worth keeping for the tutorial:** the stack
*appeared* to work via `restart: always` crash-looping until Postgres
happened to be ready — self-healing, but the wrong way to solve a
startup-ordering problem. `depends_on` (plain list form) only waits for
a container to *start*, not for the service inside it to be ready to
accept work. Relying on `restart: always` to paper over that is fragile:
it happened to succeed in 3 attempts here, but there's no guarantee of
that under different load/timing, and it produces alarming-looking
tracebacks in the logs for something that isn't actually broken — a
recipe for a support/debugging session chasing a "bug" that's really a
race condition.

**FIXED (not deferred) — `docker-compose.yml` rewritten in full:**
added `healthcheck` blocks to `db` (`pg_isready`) and `redis`
(`redis-cli ping` — each image's own built-in readiness check, testing
"can this service actually accept a connection now," not just "is the
process running"). Changed `backend`/`daphne`'s `depends_on` from a
plain list to `condition: service_healthy` on both `db` and `redis`, so
they now wait for real readiness instead of crash-looping to eventual
success.

**Ran (SUCCESS) — clean restart confirms the fix:**
```
docker compose down && docker compose up -d
```
`db`/`redis` showed "Healthy" before backend/daphne started — correct
ordering. `docker compose logs backend` → zero connection errors, single
clean attempt, migrations already applied (volume persisted through
`down`), gunicorn started first try. Race condition genuinely fixed, not
just observed.

**Ran (SUCCESS):** curl through nginx (port 80) to `/api/auth/users/` →
user created (id:1 — first user in this Docker Postgres volume, separate
DB instance from the native Postgres used during venv testing earlier).
Full Docker stack confirmed working end-to-end: nginx → backend →
Postgres, with correct `/api/` routing and healthy startup ordering.

**Bug found (manual browser test through Docker/nginx):** Login failed
with generic "Something went wrong" — dev tools Network tab showed the
real cause: `POST http://127.0.0.1:8000/api/auth/jwt/create/
net::ERR_CONNECTION_REFUSED`. NOT a re-registration issue. `client.ts`
had a hardcoded `baseURL: 'http://127.0.0.1:8000'` — worked fine when
Django's `runserver` was genuinely listening on that host port during
venv testing, but once the backend moved into Docker (`backend` service
in `docker-compose.yml` has NO `ports:` mapping to the host — port 8000
only exists inside the Docker network), nothing was listening there from
the browser's perspective. Confirmed via dev tools before assuming
anything.

**TUTORIAL-WORTHY LESSON — one code path, not environment branching:**
Fixed by making `client.ts` use a **relative** `baseURL: ''`, so requests
go to whatever origin served the page — same origin as nginx in Docker,
same origin as Vite's dev server in venv mode. This only works if
something forwards `/api/` to Django in BOTH environments: nginx already
does this in Docker (`nginx/default.conf`'s `/api/` location block); for
venv+Vite dev, added a matching **Vite dev proxy** (`vite.config.ts`,
`server.proxy: { '/api': 'http://127.0.0.1:8000' }`).

The point: this isn't "two different fixes for two environments" — it's
the SAME mechanism (something in front forwards `/api/` to Django)
implemented twice, once via nginx config and once via Vite config, so
the frontend code itself never needs to know or care which environment
it's running in. No `if (isDocker)` branching, no separate `.env.dev`
vs `.env.docker` base URLs — one relative-URL code path that works
unchanged in both places. Mirrors the "one project, one database"
discipline already established in `base.py`.

**Files changed:**
- `frontend/src/api/client.ts` — `baseURL: ''` (was hardcoded absolute
  URL); refresh call now `/api/auth/jwt/refresh/` (relative)
- `frontend/vite.config.ts` — added `server.proxy: { '/api':
  'http://127.0.0.1:8000' }`

**Ran (SUCCESS):**
```
docker compose up -d --build frontend
```
Rebuilt clean — good live example of layer caching: `npm install`
layer came from cache (package.json unchanged), only `COPY . .` and
`npm run build` re-ran since `client.ts` changed.

**Ran (SUCCESS) — full manual browser test through Docker/nginx:**
First login attempt with an existing venv-era email failed ("No active
account found") — expected, since Docker's Postgres volume is a
separate instance from native Postgres (same pattern as the earlier
`dockertest` id:1 observation). Registered fresh through the UI →
logged in → Dashboard showing real email + username, served entirely
via nginx on `http://localhost` (port 80).

**MODULE 2 (AUTH): FULLY COMPLETE — BOTH VENV AND DOCKER.**
Backend (Djoser + JWT + custom User model), frontend (Pinia auth store,
axios client with silent refresh, relative `/api/` URLs working
identically in both environments via Vite proxy / nginx), and the full
Docker Compose stack (6 containers, healthchecks fixing a real
startup-race bug) all verified working end-to-end through the actual
browser UI — not just curl.

## Module 3 (Boards + Status) — backend

Read `boards/models.py` scaffold stub (pointed to
`Spadework_Tier2_Kanban_Spec_v1.md`), then read the actual spec file
(uploaded). Key constraints for this module: single project/board, no
multi-project switching; fixed status columns — Todo / In Progress /
Blocked / Done — NOT user-editable/reorderable; `Status.order` fixed at
seed time via data migration.

**Files created:**
- `boards/models.py` — `Board` (name, description, created_at), `Status`
  (board FK, name, order — `unique_together` on board+order, default
  ordering by `order`)

**Ran (SUCCESS):**
```
cd /home/spadework/miniapps/miniapp/backend && source /home/envs/spadework/bin/activate && python manage.py makemigrations boards
```
→ `boards/migrations/0001_initial.py` (Create model Board, Create model
Status). Expected `DB_HOST=db` RuntimeWarning again (context-switching
back to venv from Docker work) — flipped `.env` back to
`DB_HOST=localhost` before applying:
```
sed -i 's/^DB_HOST=db/DB_HOST=localhost/' /home/spadework/miniapps/miniapp/.env && python manage.py migrate boards
```
→ applied cleanly against native Postgres.

**Ran (SUCCESS):**
```
python manage.py makemigrations boards --empty --name seed_board_and_statuses
```
→ `boards/migrations/0002_seed_board_and_statuses.py` scaffolded, then
filled with `RunPython` seed logic (uses `apps.get_model`, not direct
model imports, so the migration stays correct against the historical
schema even if `models.py` changes later). Seeds one `Board` ("miniJira
Board") + four `Status` rows (Todo=0, In Progress=1, Blocked=2, Done=3).
Reverse migration provided too (deletes the board, cascades to
statuses).

```
python manage.py migrate boards
```
→ applied cleanly.

**Verified:**
```
python manage.py shell -c "from boards.models import Board, Status; b = Board.objects.first(); print(b.name); print(list(b.statuses.values_list('name', 'order')))"
```
→ `miniJira Board`, `[('Todo', 0), ('In Progress', 1), ('Blocked', 2), ('Done', 3)]`
— confirmed correct.

**Files created:**
- `boards/admin.py` — `BoardAdmin` with `StatusInline` for eyeballing
  data in Django admin
- `boards/serializers.py` — `StatusSerializer`, `BoardSerializer`
  (nested statuses, read-only — Board/Status aren't created/edited
  through this API, they're fixed at seed time)
- `boards/views.py` — `BoardViewSet(ReadOnlyModelViewSet)`, with
  `prefetch_related('statuses')` to avoid N+1 queries (habit worth
  keeping before this pattern gets copied into issues/teams)
- `boards/urls.py` — `DefaultRouter` registering `boards`
- `config/urls.py` — added `path('api/', include('boards.urls'))`

**Ran (SUCCESS):**
```
python manage.py runserver
```
(missed first time, forgot to start it before testing — corrected)
```
curl http://127.0.0.1:8000/api/boards/ -H "Authorization: Bearer $(curl -s -X POST http://127.0.0.1:8000/api/auth/jwt/create/ -H "Content-Type: application/json" -d '{"email":"testuser@example.com","password":"TestPass123!"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")"
```
→ full board JSON returned correctly: id, name, description, nested
statuses (all 4, correct order), created_at.

## Module 3 — frontend

**Files created:**
- `stores/board.ts` — `fetchBoard()` action, single-board MVP (takes
  `data[0]` from the list endpoint)
- `views/BoardView.vue` — static 4-column grid from `board.statuses`,
  no drag-drop/cards yet (Issue CRUD is Module 5)
- `router/index.ts` — added `/board` route (`requiresAuth`)
- `views/DashboardView.vue` — added "View Board" link

Started `npm run dev`, tested in browser at `/board`.

**Bug found:** board page showed "Could not load the board." Dev tools
Network tab showed the real sequence: `/api/auth/users/me/` → 401
(access token expired — 30min lifetime, long session), correctly
triggered silent-refresh interceptor → `/api/auth/jwt/refresh/` ALSO
401 → `/api/boards/` request went out unauthenticated → 401.

**Root cause — genuine bug in code written this session, not a fluke:**
`base.py`'s `SIMPLE_JWT` has `ROTATE_REFRESH_TOKENS: True` +
`BLACKLIST_AFTER_ROTATION: True` — every successful refresh blacklists
the OLD refresh token and issues a NEW one. But `client.ts`'s refresh
interceptor only ever did `localStorage.setItem('access', data.access)`
— it never persisted `data.refresh` (the newly-rotated token). So the
first time ANY silent refresh succeeds in a session, the refresh token
still sitting in localStorage becomes stale/blacklisted, and the next
refresh attempt is guaranteed to 401. Almost certainly what happened
here, given how many hours/module-tests this same browser tab has been
open across.

**Fix applied — `client.ts` rewritten:** now persists `data.refresh`
after every successful refresh (previously only saved `data.access`).

Logged out and back in (fresh access+refresh pair, since the previously
blacklisted refresh token couldn't be un-blacklisted). Retested `/board`.

**Ran (SUCCESS) — full manual browser test:** Board renders correctly —
"miniJira Board" title + description, all four columns (Todo/In
Progress/Blocked/Done) in correct order, pulled live from the API.

**MODULE 3: COMPLETE.** Backend (Board/Status models, data-migration
seeding, read-only DRF API) and frontend (Pinia board store, static
column layout, routed from dashboard) both verified working via venv +
Vite dev. Docker rebuild/retest for this module not yet done — still
outstanding.

**Genuine bug caught and fixed this module (tutorial-worthy):** JWT
refresh-token rotation silently breaking itself after first use, because
the client only ever persisted the new access token, not the rotated
refresh token. Latent since Module 2 — would have surfaced eventually
regardless of what feature was being tested when it did.

**Next: Docker rebuild + retest for Module 3, or move to Module 4
(Teams + Team Membership) per the spec's build sequence.**

---

## Module 4 (Teams + Team Membership) — backend

Checked `teams/models.py` scaffold stub — matched spec exactly (Team +
TeamMembership through table, since a user can belong to more than one
team, needed for later "assignee must belong to assigned team" checks
on Issue).

**Files created:**
- `teams/models.py` — `Team` (name, description, created_at),
  `TeamMembership` (team FK, user FK via `settings.AUTH_USER_MODEL` —
  standard pattern, decouples `teams` from `accounts` internals,
  avoids circular-import risk; `unique_together` on team+user)

**Ran (SUCCESS):**
```
cd /home/spadework/miniapps/miniapp/backend && source /home/envs/spadework/bin/activate && python manage.py makemigrations teams && python manage.py migrate teams
```
→ `teams/migrations/0001_initial.py` (Create model Team, Create model
TeamMembership), applied cleanly. No `DB_HOST` warning this time —
`.env` already pointed at `localhost` from prior venv work.

**Files created:**
- `teams/admin.py` — `TeamAdmin` with `TeamMembershipInline`
- `teams/serializers.py` — `TeamMembershipSerializer` (nested
  username/email from the related user), `TeamSerializer` (nested
  memberships)
- `teams/views.py` — `TeamViewSet(ModelViewSet)` — full CRUD (Teams are
  user-managed, unlike Board/Status); custom `add_member`/`remove_member`
  actions. `add_member` uses `get_or_create` rather than plain `create`
  — `unique_together` on (team, user) would otherwise raise an
  uncaught `IntegrityError` (500) instead of a clean 400 if adding a
  duplicate member.
- `teams/urls.py` — `DefaultRouter` registering `teams`
- `config/urls.py` — added `path('api/', include('teams.urls'))`

**Ran (SUCCESS) — full curl test sequence:**
```
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/jwt/create/ -H "Content-Type: application/json" -d '{"email":"testuser@example.com","password":"TestPass123!"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")
curl -s -X POST http://127.0.0.1:8000/api/teams/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Core Team","description":"The main delivery team"}'
```
→ Team created (id:1).
```
curl -s -X POST http://127.0.0.1:8000/api/teams/1/members/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"user":2}'
```
→ membership created.
```
curl -s http://127.0.0.1:8000/api/teams/1/ -H "Authorization: Bearer $TOKEN"
```
→ nested membership shows correctly (username, email, joined_at).
```
curl -s -X POST http://127.0.0.1:8000/api/teams/1/members/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"user":2}'
```
→ duplicate add correctly rejected: `{"detail":"User is already a
member of this team."}` — 400, not a 500 crash. `get_or_create` guard
confirmed working as designed.

**MODULE 4 BACKEND: DONE.**

## Module 4 — frontend

**Files created:**
- `stores/teams.ts` — `fetchTeams`, `createTeam`, `addMember`,
  `removeMember` actions
- `views/TeamsView.vue` — create-team form, team list with nested
  member list + remove button, add-member-by-user-ID input (a proper
  user search/picker deferred — not needed to prove the API works)
- `router/index.ts` — added `/teams` route (`requiresAuth`)
- `views/DashboardView.vue` — added "Teams" nav link

**Ran (SUCCESS) — full manual browser test:** `/teams` page shows both
"Core Team" (from the earlier curl test) and a freshly-created "Test
team 1" through the UI, both correctly showing `testuser` as a member
with a working Remove button and add-member form.

**MODULE 4: COMPLETE.** Backend (Team/TeamMembership models, full CRUD
+ member add/remove with proper duplicate-guard error handling) and
frontend (Pinia store, create/list/member-management UI) both verified
working end-to-end via venv + Vite dev. Docker rebuild/retest not yet
done for Modules 3 or 4 — still outstanding, carried forward.

## Module 5 (Issue CRUD) — backend

Checked `issues/models.py` scaffold — matched spec's data model sketch.

**Files created:**
- `issues/models.py` — `Issue` model: board FK (CASCADE), status FK
  (PROTECT — statuses are fixed, shouldn't be deletable while
  referenced), title, description, priority (fixed choices:
  low/medium/high), team FK (SET_NULL, nullable), assignee FK
  (SET_NULL, nullable), target_completion_date, actual_completion_date
  (auto-set via overridden `save()` the moment status becomes Done —
  only if not already set, so manual correction isn't overwritten),
  `order` (CharField placeholder — fractional-key logic is Module 8,
  added the column now to avoid a second migration later), created_at,
  updated_at.

**Ran (SUCCESS):**
```
cd /home/spadework/miniapps/miniapp/backend && source /home/envs/spadework/bin/activate && python manage.py makemigrations issues && python manage.py migrate issues
```
→ `issues/migrations/0001_initial.py`, applied cleanly.

**Files created:**
- `issues/serializers.py` — `IssueSerializer`, `actual_completion_date`
  read-only (auto-set by model). Custom `validate()`: if both `team`
  and `assignee` are set, checks `team.memberships.filter(user=assignee)`
  and raises a field-level error if the assignee isn't actually on that
  team — falls back to `self.instance`'s existing value for any field
  missing from a partial/PATCH update.
- `issues/views.py` — `IssueViewSet(ModelViewSet)`, `select_related`
  (not `prefetch_related` — these are forward FKs, not reverse/many),
  basic `?board=` query param filtering (full search/filter is Module 7)
- `issues/urls.py` — `DefaultRouter` registering `issues`
- `config/urls.py` — added `path('api/', include('issues.urls'))`

**Ran (SUCCESS) — full curl test sequence:**
```
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/jwt/create/ -H "Content-Type: application/json" -d '{"email":"testuser@example.com","password":"TestPass123!"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")
curl -s -X POST http://127.0.0.1:8000/api/issues/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"board":1,"status":1,"title":"Set up CI pipeline","priority":"high","team":1,"assignee":2}'
```
→ issue created (id:1), `actual_completion_date` correctly null
(status isn't Done).
```
curl -s -X POST http://127.0.0.1:8000/api/issues/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"board":1,"status":1,"title":"Bad assignment test","team":1,"assignee":1}'
```
→ correctly rejected: `{"assignee":["Assignee must be a member of the
assigned team."]}` (user 1 = superuser, not a member of team 1).
```
curl -s -X PATCH http://127.0.0.1:8000/api/issues/1/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"status":4}'
```
→ status updated to Done (id 4), `actual_completion_date` auto-captured
correctly as `"2026-07-13"`.

**MODULE 5 BACKEND: DONE.** All three core behaviors verified: CRUD,
team/assignee validation, Done auto-completion-date. Session ended here
for the day — frontend for Module 5 (issue cards on the board, per-
status create/edit) deferred to next session.

## Module 5 — frontend

**Files created:**
- `stores/issues.ts` — `Issue` interface, `fetchIssues(boardId)`,
  `createIssue`, `updateIssue` actions.
- `components/IssueForm.vue` — reusable create/edit form. Assignee
  dropdown scoped to the selected team's members only (mirrors the
  backend's own validation, so the UI doesn't offer an invalid
  combination in the first place); `watch(team)` clears assignee if it
  changed team invalidates the current selection.
- `views/BoardView.vue` — rewritten: issue cards render per status
  column via `issuesForStatus()`, "+ Add" opens `IssueForm` inline in
  that column, clicking an existing card opens the same form pre-filled
  for editing.

**Terminal display issue during this build (not a real file-corruption
bug):** a very long heredoc paste caused garbled/interleaved text to
echo in the VS Code integrated terminal. Verified via `cat` immediately
after each write — actual file contents were correct both times; it was
purely a terminal echo artifact, not lost or corrupted writes. Kept
verifying with `cat` after each file as a precaution regardless.

**Ran (SUCCESS) — full manual browser test:** Created "Test ToDo
addition" via the Todo column's "+ Add" form — team/assignee dropdowns
correctly scoped (Test team 1 → testuser only), target date set, saved
successfully and rendered as a card in Todo. Last night's "Set up CI
pipeline" card (created via curl, later moved to Done) correctly shows
in the Done column. Both cards render with priority + assigned
indicator.

**MODULE 5: COMPLETE.** Backend (Issue model, CRUD, team/assignee
validation, Done auto-completion-date) and frontend (issue form
component with team-scoped assignee dropdown, cards per status column,
inline create/edit) both verified working end-to-end via venv + Vite
dev. Docker rebuild/retest still outstanding for Modules 3-4-5
together.

## Module 6 (Comments) — backend

**Files created:**
- `comments/models.py` — `Comment` (issue FK, author FK, body,
  created_at; `Meta.ordering = ['created_at']` — chronological, and the
  deliberate target of the Module 10 "comment ordering under concurrent
  posts" planted bug, the simpler/earlier example before the harder
  drag-drop race)
- `comments/serializers.py` — `CommentSerializer`, `author_username`
  nested read-only, `author` itself read-only (never client-supplied)
- `comments/views.py` — `CommentViewSet(ModelViewSet)`, `?issue=` query
  filter, `perform_create` sets `author=self.request.user` server-side
  — never trusts a client-supplied author (would let anyone post as
  someone else)
- `comments/urls.py` — router registration
- `config/urls.py` — added comments include

**Ran (SUCCESS):**
```
cd /home/spadework/miniapps/miniapp/backend && python manage.py makemigrations comments && python manage.py migrate comments
```
→ applied cleanly.

**Note on terminal garbling from earlier:** Peter diagnosed it —
happens specifically when using VS Code's "Copy" button on code blocks;
Ctrl+C/Ctrl+Shift+V doesn't have the issue. All three files this batch
(serializers/views/urls) pasted clean using the keyboard method.

**Ran (SUCCESS) — curl test:**
```
curl -s -X POST http://127.0.0.1:8000/api/comments/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"issue":2,"body":"Started looking into this."}'
```
→ comment created, `author` correctly server-set to testuser (id 2) —
never sent in the payload, confirming `perform_create` works as
designed.
```
curl -s "http://127.0.0.1:8000/api/comments/?issue=2" -H "Authorization: Bearer $TOKEN"
```
→ filter confirmed working.

**MODULE 6 BACKEND: DONE.**

## Module 6 — frontend

**Files created:**
- `stores/comments.ts` — `fetchComments(issueId)`, `postComment`
- `components/IssueForm.vue` — rewritten to add a comments section,
  only shown when editing an existing issue (`v-if="issue?.id"` — a
  new/unsaved issue has nothing to attach a comment to)

Run this batch showed the terminal-garbling artifact again despite
using Ctrl+C — Peter caught it live in the terminal (cursor landed after
EOF, backspaced to fix), so the diagnosis from the last batch isn't the
full story; verified via `cat` immediately after — file landed
correctly regardless.

**Ran (SUCCESS) — browser test, first pass:** opened "Test ToDo
addition," confirmed the earlier curl-posted comment showed correctly.

**BUG FOUND — real, not user error:** clicked "+ Add" in Todo while
"Test ToDo addition"'s edit form was ALSO still open. Both forms
rendered simultaneously (BoardView had no mutual-exclusion logic).
Typed new content ("Test creating issue 2") into what looked like a
fresh new-issue form, but it was actually still the EDIT form for the
existing issue — saved, and it silently overwrote "Test ToDo addition"
instead of creating a new issue (confirmed via curl: only 2 issues
existed in DB afterward, not 3). Comments also leaked between the two
open forms — same root cause, different symptom.

**Root cause 1:** `handleSave` in `BoardView.vue` decided create-vs-
update based on whichever of `openFormStatusId`/`editingIssue` was
CURRENTLY set globally, not which specific form instance actually
emitted the save event — with both open, `editingIssue` won every time.

**Root cause 2:** `commentsStore` held one single flat `comments` array
for the whole app — with two `IssueForm` instances mounted
simultaneously, both read/wrote the same shared list.

**FIXED — both files rewritten:**
- `BoardView.vue` — added `openAddForm()`/`openEditForm()` helpers;
  opening either now explicitly closes the other, so only one form can
  ever be open anywhere on the board at a time.
- `stores/comments.ts` — changed from a flat `comments: Comment[]` to
  `commentsByIssue: Record<number, Comment[]>`, keyed by issue id.
- `IssueForm.vue` — added `issueComments` computed, scoped to
  `props.issue.id`, replacing the old flat-list references.

Verified all three landed via `grep -c` for a distinguishing string in
each (`openAddForm`, `commentsByIssue`, `issueComments`) rather than
full `cat` — faster confirmation for a 3-file batch.

## Browsable API (DRF) — set up for teaching/debugging use

Per Peter's request: added `rest_framework.authentication.
SessionAuthentication` alongside JWT in `base.py`'s
`DEFAULT_AUTHENTICATION_CLASSES` (browsable API's own login uses Django
session auth, not JWT), and wired `path('api-auth/',
include('rest_framework.urls'))` into `config/urls.py` for the login/
logout views.

**Ran (SUCCESS):** logged into `http://127.0.0.1:8000/api/issues/` via
the browsable API's own "Log in" link (superuser account). Confirmed
working:
- GET request renders serializer output as pretty-printed JSON —
  directly maps to `IssueSerializer.Meta.fields`, good concrete
  teaching material for "what does a serializer actually do"
- Auto-generated HTML POST form, driven by the same serializer
- **First POST attempt hit the assignee/team validation error** — the
  browsable form's raw HTML select doesn't do client-side team-scoping
  (that's Vue-only convenience code), so it submitted an invalid
  team+assignee combo and the server-side `validate()` correctly
  rejected it. Excellent live demonstration that the validation is
  real and server-enforced, not just hidden by frontend UX.
- Second attempt with a valid combination succeeded — issue id 3
  created ("Adding a ToDo item through DRF api browser").

**Ran (SUCCESS):**
```
curl -s -X PATCH http://127.0.0.1:8000/api/issues/2/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"title":"Test ToDo addition","description":"First test of creating a to-do item"}'
```
→ restored correctly. Data now: issue 1 (Set up CI pipeline, Done),
issue 2 (Test ToDo addition, Todo, restored), issue 3 (Adding a ToDo
item through DRF api browser, Todo — from the browsable API test).

**MODULE 6: COMPLETE.** Backend (Comment model, CRUD, server-set
author) and frontend (comment list + post form embedded in IssueForm)
both verified working. Two genuine frontend bugs found via real usage,
fixed, and verified (form mutual-exclusion, comments store scoping).
Browsable API set up as a standing teaching/debugging tool going
forward — session auth added alongside JWT specifically for this.

## Module 7 (Labels + search/filter) — backend

**Files created:**
- `labels/models.py` — `Label` (board FK, name, `unique_together` on
  board+name — board-scoped, matching Status/Team's own scoping),
  `IssueLabel` (through table, `unique_together` on issue+label)
- `labels/serializers.py`, `labels/views.py` (board-scoped via `?board=`),
  `labels/urls.py`
- `issues/serializers.py` — rewritten: added `labels` via
  `SerializerMethodField`, importing `LabelSerializer` lazily INSIDE the
  method (not at module top) to avoid a circular import — `labels`
  imports `Issue` from `issues.models`, so a top-level import here
  would create a cycle at load time.
- `issues/views.py` — rewritten: `get_queryset` now does real search/
  filter per spec (status, assignee, label, text-match on title via
  `title__icontains`, all combine with AND, `?board=` still supported);
  `add_label`/`remove_label` custom actions, same `get_or_create` +
  clean-error pattern as Teams' member management; label model imports
  also deferred inside the action methods for the same circular-import
  reason.
- `config/urls.py` — added labels include

**Ran (SUCCESS):**
```
cd /home/spadework/miniapps/miniapp/backend && python manage.py makemigrations labels && python manage.py migrate labels
```
→ applied cleanly.

**Ran (SUCCESS) — full test sequence:**
- Created label via browsable API HTML form: id 1, "backend", board 1.
- Access token from earlier had expired (30min lifetime) — got a fresh
  one, minor reminder mid-session rather than a bug.
```
curl -s -X POST http://127.0.0.1:8000/api/issues/2/labels/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"label":1}'
```
→ label attached, correctly nested in the issue response's `labels`
array.
```
curl -s "http://127.0.0.1:8000/api/issues/?label=1" -H "Authorization: Bearer $TOKEN"
curl -s "http://127.0.0.1:8000/api/issues/?search=ToDo" -H "Authorization: Bearer $TOKEN"
```
→ `?label=1` correctly returned only the labeled issue; `?search=ToDo`
correctly matched both issues with "ToDo" in the title.

**MODULE 7 BACKEND: DONE.**

## Module 7 — frontend

**Files created:**
- `stores/labels.ts` — `fetchLabels`, `createLabel`,
  `addLabelToIssue`, `removeLabelFromIssue`
- `stores/issues.ts` — added `labels` field to `Issue` interface,
  `IssueFilters` interface, `fetchIssues` now accepts filters
- `views/BoardView.vue` — search box + label dropdown filter bar,
  `watch([searchText, labelFilter], reloadIssues)`, label chips shown
  on cards
- `components/IssueForm.vue` — label chip list with remove (×) button,
  add-label dropdown scoped to labels not already attached
  (`availableLabelsToAdd`)

**Ran (SUCCESS) — full manual browser test:** label chip shows on card
and in edit form; remove (×) button and add-label dropdown both work;
comments still correctly scoped per-issue alongside labels. Search
("CI") correctly narrowed to just the matching card.

**UX note found, not a bug — noted as end-of-session polish item:**
selecting "All labels" doesn't clear the search text box (they're
independent AND-combined filters, working as designed) — but the
combined effect can look like nothing happened if the person expects
one control to reset both. A "Clear filters" button would fix the
confusion. **Deferred to end-of-session follow-ups list.**

**MODULE 7: COMPLETE.** Backend and frontend both verified working
end-to-end: search, label filter, label attach/detach, all combining
correctly with existing status-column display.

## Module 8 (drag-and-drop reordering) — ordering-key algorithm

**File created:**
- `issues/ordering.py` — `key_between(before, after)`, hand-rolled per
  spec's explicit "not a library, more teachable" recommendation.
  Base-26 (lowercase a-z) lexicographic midpoint algorithm. Missing
  `before` char = lowest value (0/'a'); missing `after` char = one past
  highest (26, one past 'z') — this is what allows omitting either bound
  entirely (insert at start/end of a list) and gives a sensible
  first-ever key when both are omitted.

**Ran (SUCCESS) — standalone verification BEFORE wiring into any API,
by explicit request ("slowly slowly check"):**
```
python3 -c "from issues.ordering import key_between; ..."
```
Tested: first key in empty list (`'n'`), insert after (`'t'`), insert
before (`'g'`), insert between two ADJACENT keys `g`/`h` — the case that
forces the algorithm to recurse a character deeper since there's no
room at the first position (`'gn'`), then squeezed repeatedly into the
same shrinking gap 5 times in a row (`gn → gg → gd → gb → gan`) — proves
it never runs out of room and correctly grows key length exactly when
needed. All assertions passed.

## Module 8 — API wiring

**Files created/changed:**
- `issues/views.py` — rewritten. `perform_create` now auto-assigns
  `order` at the end of the target status column via
  `key_between(last.order, '')`. New `reorder` action — accepts target
  status + before_id/after_id (either/both omittable), computes the new
  key, updates status+order, only ever touches the ONE row being moved
  (the whole point of fractional keys vs integer resequencing — no
  renumbering cascade). Renamed the `status` module import to
  `http_status` to disambiguate from the new `status` field/param name
  colliding with it.

**REAL BUG FOUND — root cause traced to an earlier session, not new
code:** created two test issues via curl; issue A's auto-assigned order
came back as `"]"` — outside the a-z alphabet the algorithm assumes.
Root cause: back in the Module 7 browsable-API test, a literal `"?"`
character had been typed into the raw `Order` text field for issue 3 —
`order` was still client-writable at that point. `?` sits outside a-z,
so `ord('?') - ord('a')` goes negative, corrupting the character-math
in `key_between` for any issue computed against it as a neighbor.

**Real fix, not just cleanup:** `order` should never have been
client-settable in the first place — it's an internal algorithm
invariant, not user data. Added `'order'` to `IssueSerializer`'s
`read_only_fields`:
```
sed -i "s/read_only_fields = \['actual_completion_date'\]/read_only_fields = ['actual_completion_date', 'order']/" issues/serializers.py
```
Then deleted the three corrupted/throwaway test issues (ids 3, 4, 5)
to get a clean slate.

**Ran (SUCCESS) — clean re-test:**
```
curl -s -X POST http://127.0.0.1:8000/api/issues/ ... -d '{"board":1,"status":1,"title":"Order test A"}'
curl -s -X POST http://127.0.0.1:8000/api/issues/ ... -d '{"board":1,"status":1,"title":"Order test B"}'
```
→ A (id 6) got order `'n'`, B (id 7) got `'t'` — correctly placed after
A, matching the standalone algorithm test exactly.

**Terminology clarified during reorder testing:** `before_id` means
"this issue becomes my LEFT neighbor," `after_id` means "this issue
becomes my RIGHT neighbor" — Claude's first test instruction described
it backwards (asked for a call that was actually a no-op, recomputing
the same key), corrected on the next attempt:
```
curl -s -X POST http://127.0.0.1:8000/api/issues/7/reorder/ ... -d '{"status":1,"after_id":6}'
```
→ B's order became `'g'` (sorts before A's `'n'`) — matches
`key_between('', 'n')` from the standalone test exactly. Move confirmed
working correctly.

**MODULE 8 BACKEND (ordering algorithm + API): DONE.**

## Module 8 — frontend

**Files created:**
- `stores/issues.ts` — added `reorderIssue(id, statusId, beforeId?,
  afterId?)` action, calls the `reorder` endpoint
- `views/BoardView.vue` — rewritten: native HTML5 drag-and-drop
  (`draggable`, `dragstart`/`dragover`/`drop` — no external library, per
  the teaching-first/minimal-dependency approach). `sortedList()` sorts
  by `order` via string `localeCompare`. Todo column renders three
  Priority sub-boxes (High/Medium/Low per spec), every other column
  shows one flat sorted list. Dropping a card into a different Todo
  priority box also updates the issue's `priority` field to match
  (`maybeUpdatePriority`) — makes them genuine "priority boxes," not
  just a display grouping. `handleDropOnCard` computes the correct
  before/after neighbours from the current sorted (and dragged-issue-
  excluded) list; `handleDropAtEnd` handles dropping into empty space
  at the end of a list/column.

**Ran (SUCCESS) — full manual browser test:** dragged "Test ToDo
addition" High → Medium → Low within Todo (each move correctly updated
priority field AND re-sorted into the right box), then dragged from
Todo/Low into In Progress (correctly preserved its priority, moved
status, disappeared from Todo, appeared in In Progress as a flat-list
card showing "low · assigned").

**MODULE 8: COMPLETE.** Backend (hand-rolled fractional ordering-key
algorithm, verified standalone before integration; auto-assign on
create; reorder action) and frontend (native HTML5 drag-and-drop, no
external library; Priority-box sub-grouping within Todo; priority
auto-update on cross-box drop) all verified working end-to-end. One
real bug found and properly fixed along the way: `order` was briefly
client-writable, got corrupted by manual testing, fixed by making it
`read_only` — the correct fix, not just a data cleanup.

## Module 9 (real-time updates via Channels/Daphne) — environment setup

Real-time needs a working channel layer, which needs Redis — flagged
that Redis wasn't installed natively yet (Docker-only, per Module 2
follow-ups). Confirmed with Peter: install natively now, for consistent
venv-first testing rest of the build.

**Clarified:** Redis is OS-level software (installed via `apt`), not a
Python package — venvs only isolate Python packages, so Redis
installation is entirely independent of `spadework` venv being active
or not.

**Ran (SUCCESS):**
```
sudo apt update && sudo apt install -y redis-server
```
→ installed cleanly, auto-started via systemd (`redis.service` symlinked
to `redis-server.service`).
```
redis-cli ping
```
→ `PONG`, confirmed running and reachable.

**Fixed — same class of issue as `DB_HOST` back in Module 2:**
`.env`'s `REDIS_HOST=redis` is a Docker Compose service name, doesn't
resolve outside Docker's network.
```
sed -i 's/^REDIS_HOST=redis/REDIS_HOST=localhost/' /home/spadework/miniapps/miniapp/.env
```

**Files created:**
- `issues/consumers.py` — `BoardConsumer(AsyncWebsocketConsumer)`.
  Server-authoritative design: clients only ever RECEIVE broadcasts,
  they never send mutations over the socket — all writes still go
  through the REST API (which is what actually enforces validation like
  the team/assignee check). Joins a per-board group (`board_{id}`) on
  connect, relays whatever's broadcast to that group as JSON.
- `issues/realtime.py` — `broadcast_board_event()` helper, called from
  views after a successful mutation, never from inside a serializer or
  model, so it's obvious at each call site exactly when a broadcast
  fires.
- `issues/routing.py` — `websocket_urlpatterns`, `ws/board/<board_id>/`

**Wired in:**
- `config/asgi.py` — first attempt used a Python string-replace script
  to patch the file, which SILENTLY NO-OPPED (str.replace() doesn't
  error on no match — script printing "done" only confirmed it ran,
  not that anything changed; verified via `cat` immediately after and
  caught it). Rewrote the file directly instead — small enough that a
  full rewrite was safer than chasing the exact whitespace/escaping
  mismatch. Confirmed correct on the second `cat`.

**Files changed:**
- `issues/views.py` — rewritten: `broadcast_board_event` calls added
  after every successful mutation — `perform_create`, `perform_update`,
  `perform_destroy` (new — DRF's default `destroy` doesn't call a
  overridable hook the same way create/update do, so this needed adding
  explicitly), `reorder`, `add_label`, `remove_label`.

**Local testing setup — Daphne needed as a second process:**
`runserver` only serves plain HTTP; Daphne is what understands ASGI/
WebSockets, and in Docker it already runs as its own separate container
for exactly that reason. For venv testing, ran Daphne standalone on a
different port — deliberately mirrors the production WSGI/ASGI split
(nginx routes `/api/` → gunicorn, `/ws/` → daphne; same reasoning here,
two processes for two roles), which doubles as a live example for the
Nginx/Gunicorn/Daphne Foundations tutorial content planned for
Riverside Club.
```
cd /home/spadework/miniapps/miniapp/backend && source /home/envs/spadework/bin/activate && daphne -b 127.0.0.1 -p 8001 config.asgi:application
```
→ confirmed listening on 127.0.0.1:8001.

`vite.config.ts` — added a `/ws` proxy entry targeting
`ws://127.0.0.1:8001` with `ws: true`, alongside the existing `/api`
proxy.

**Frontend files created/changed:**
- `stores/issues.ts` — added `applyRealtimeEvent(event, issue)` action:
  handles created/updated/deleted broadcasts by patching the local
  array directly, no refetch needed.
- `views/BoardView.vue` — `connectSocket()` opens a WebSocket to
  `ws(s)://<same-origin>/ws/board/<id>/` (relative, same pattern as the
  `/api/` fix from Module 2 — works unchanged whether proxied by Vite
  in dev or nginx in Docker), routes incoming messages into
  `applyRealtimeEvent`, closes the socket in `onUnmounted`.

**Ran (attempted) — two-browser-window test:** dragged a card, updates
only appeared after a manual refresh in either window, not live in
either — genuine failure, not a UI quirk.

**Diagnosis, step by step (not guessed at):**
1. Checked WebSocket connection itself first (Network tab, filtered
   correctly to "All" after an initial false-negative from filtering to
   "Fetch/XHR" + a "WS" text filter, which mutually excluded WS
   connections) — confirmed genuinely connected: `1/` row, status 101
   (Switching Protocols, correct handshake), 5.79s open, not the
   problem.
2. Had Peter watch Network tab live while triggering a real mutation —
   found `reorder/` request itself returning **500**, not a broadcast/
   socket issue at all. No successful mutation → no broadcast → nothing
   live AND nothing even reflected until a full refetch-on-refresh
   bypassed the broken request.
3. Django's debug error page: `ConnectionError: Error -3 connecting to
   redis:6379. Temporary failure in name resolution.`

**Root cause — same class of bug as `DB_HOST` in Module 2, same
underlying reason:** `REDIS_HOST=redis` is cached in the ALREADY-RUNNING
`runserver` process's memory — `load_dotenv()` only runs once, at
process startup. We fixed `.env` on disk when installing Redis earlier
this session, but `runserver` had been running since before that fix,
so it was still using the stale value it read on launch.

**Fix:** restart `runserver` to pick up the corrected `.env`.

**Ran:** restarted `runserver` AND `daphne` (both had stale `.env` from
before the Redis fix, same reasoning). Reorder itself now succeeds
(200) with no ConnectionError. But: dragging window updated instantly
(its own local Pinia state, not dependent on the broadcast), the OTHER
window still didn't update without a manual refresh.

**Second, distinct bug — traced methodically, not guessed:**
1. Confirmed BOTH windows' WebSocket connections were genuinely open
   (status 101) via Network tab on each — ruled out a connection-level
   problem on either side.
2. Checked daphne's own terminal output at the moment of a drag —
   found the real error:
```
redis.exceptions.TimeoutError: Timeout reading from localhost:6379
```
   — raised inside `channels/consumer.py`'s `await_many_dispatch`,
   crashing the WebSocket handler and forcing a disconnect
   (`WSDISCONNECT` immediately follows in the log).
3. `pip show channels_redis redis channels` → `channels_redis 4.3.0`,
   `redis 8.0.1`, `channels 4.3.2`. Diagnosis: `redis` (the Python
   client) had been pulled in at a very recent major version (8.x) with
   no explicit pin anywhere — `channels_redis` 4.x's internal timeout/
   connection handling predates that major version; this class of
   async-timeout incompatibility across `redis-py` major bumps is a
   known issue pattern.

**Fixed:**
```
pip install "redis<5" --upgrade
```
→ downgraded cleanly to `redis 4.6.0`.

**Also fixed the ROOT cause, not just the symptom:** `requirements.txt`
had no explicit `redis` pin at all — it was purely a transitive
dependency of `channels-redis>=4.2`, which is how the incompatible 8.x
got silently installed in the first place. Added an explicit pin so
Docker builds (and anyone else setting this up) get the working
version:
```
echo 'redis<5' >> /home/spadework/miniapps/miniapp/backend/requirements.txt
```

**Ran (SUCCESS) — two-window live-sync test, after daphne restart with
fixed `redis` package:** dragged a card in one browser window, the
OTHER window updated live, no manual refresh needed. Confirmed working.

**Peter's own observation, worth keeping verbatim for the tutorial
framing:** "That is exactly the kind of thing that can drive a
developer mad and be nearly impossible to find. Hence... use Docker."
— ties directly back to the Module 2 Docker-size investigation: without
a pinned `redis` version, `pip install -r requirements.txt` resolves
"latest compatible" at install time, so the identical requirements file
can install a working stack today and a broken one next month with zero
code change. A built Docker image freezes that resolution permanently.
This bug is concrete, lived proof of exactly that value — not just an
abstract argument for Docker, a real bug it would have prevented.

**MODULE 9: COMPLETE.** Backend (BoardConsumer, server-authoritative
broadcast-only design, realtime helper wired into all Issue mutations)
and frontend (WebSocket client, same-origin relative URL pattern,
Vite/daphne proxy split mirroring the production nginx/gunicorn/daphne
split) verified working end-to-end with genuine two-client live sync.
THREE distinct real bugs found and fixed this module: stale `.env` in
already-running processes (same class as Module 2's DB_HOST issue),
and the `redis`/`channels_redis` version incompatibility (now
permanently fixed via an explicit pin in requirements.txt).

## Module 10 (planted teaching bugs)

**Scoping note (Peter's context: this directly informs the "unhappy
path"/debugging arc planned for Riverside Club — high value for PMP-
compliant methodology tutorial content):** spec says these bugs are
"not to fix now, to build in deliberately" — job here is to confirm
each vulnerable pattern is genuinely PRESENT (not accidentally already
safe), mark clearly for later EPC tracer content, verify reproducible
where possible. Reviewed current state of all four before doing
anything:
1. Drag-drop race — likely already present (reorder has no
   locking/transaction) — needed confirming, not building.
2. Optimistic UI rollback — NOT currently present. Frontend waits for
   API response before updating state at all, so there's nothing to
   roll back yet. Needs adding.
3. WebSocket reconnect desync — NOT currently present. `connectSocket()`
   has no reconnect logic — a dropped connection just stays dropped.
   Needs adding.
4. Comment ordering race — likely already present (Comments aren't
   wired into the Module 9 broadcast at all, only Issues are).

### Bug 1 — Drag-drop race (confirmed, already present)

Marked explicitly in `issues/views.py`'s `reorder` action with a
"PLANTED BUG (Module 10, deliberate)" docstring — explains the
read-then-write race in plain terms, explicitly warns against silently
fixing it with `select_for_update()`/`atomic` without updating this log
entry first.

**Ran (SUCCESS) — genuinely reproduced, not theoretical:** created two
throwaway issues (id 8, 9), fired two `reorder/` requests
simultaneously via shell backgrounding (`cmd1 & cmd2 & wait`), moving
both into "In Progress" with no before/after neighbours specified (both
computing the same empty-column midpoint):
```
curl ... /api/issues/8/reorder/ ... & curl ... /api/issues/9/reorder/ ... & wait
```
→ BOTH issues came back with **identical order key `'n'`** — confirmed
collision. Two cards now occupy the same position in the same column;
relative order between them is undefined until one is moved again. This
IS the exact "drag-drop race" scenario from the spec, genuinely
reproducible with real concurrent requests.

### Bug 2 — Optimistic UI rollback (added, didn't exist before)

**File changed:** `stores/issues.ts` — `reorderIssue` rewritten to
apply the status change to local state IMMEDIATELY (before the server
confirms), snapshot the previous state first, roll back to the
snapshot on any failure. Marked with a "PLANTED BUG" docstring —
explicitly notes the rollback itself is naive: it doesn't account for
other realtime events that might mutate the same issue DURING the
pending request, so a badly-timed rollback can clobber a legitimate
concurrent update with stale snapshot data. That's the real teaching
bug, not just "shows a spinner."

**Ran (SUCCESS) — genuinely forced failure, not simulated:** stopped
`runserver` mid-test (real network failure, not a mocked error), dragged
a card in the browser. Peter's own description: "it's like they're on
elastic — they move and snap back" — card moved instantly (optimistic),
then reverted when the request had nowhere to go. Confirmed working
exactly as designed. Restarted `runserver` after.

### Bug 3 — WebSocket reconnect desync (added, didn't exist before)

**File changed:** `views/BoardView.vue` — `connectSocket` given a
`socket.onclose` handler that auto-reconnects after 2s, but
DELIBERATELY does NOT refetch board state on reconnect. Marked with a
"PLANTED BUG" comment: the real bug isn't that reconnect fails — it
succeeds, silently, while skipping whatever happened during the gap.
No error, no visual sign anything's wrong.

**Ran (SUCCESS) — full real sequence, not simulated:**
1. Stopped daphne — browser correctly showed "Live updates
   disconnected" (screenshot confirmed; also incidentally showed Bug
   1's visible side effect — "Race test C"/"Race test D" both sitting
   in In Progress from the earlier collision).
2. While daphne was down, moved "Race test C" back to Todo via curl
   (simulating another user acting during the outage) — a real server-
   side change the disconnected browser had no way to know about.
3. Restarted daphne — auto-reconnect fired within ~2s as designed.
4. Browser continued showing "Race test C" in In Progress — STALE,
   despite looking fully reconnected and live. Only a manual page
   refresh revealed the true state (moved it to Todo/Medium).

Confirmed exactly as designed: reconnect "succeeds" while silently
losing the gap. Genuinely reproducible, not theoretical.

### Bug 4 — Comment ordering / missing realtime sync (confirmed gap)

**File changed:** `comments/views.py` — `CommentViewSet` marked with a
"PLANTED BUG" comment explaining the actual gap precisely: comments
aren't wired into ANY realtime broadcast — two people viewing the same
issue never see each other's comments live, only a manual refetch
reveals them.

**Ran (SUCCESS, and honestly scoped) — tested the actual database-level
ordering, not assumed:**
```
curl ... /api/comments/ -d '{"issue":8,"body":"Concurrent comment X"}' & curl ... -d '{"issue":8,"body":"Concurrent comment Y"}' & wait
```
→ comment X (id 3) got `created_at` `.553308`, Y (id 4) got `.555530` —
correctly ordered, NO collision at the database level (unlike the
order-key bug). Important distinction, stated precisely rather than
overclaimed: Comments have no genuine DATA race — `auto_now_add` +
sequential inserts keep true order intact. The actual bug is purely the
missing-realtime-sync PERCEPTION gap (Bug 3's same underlying pattern,
lower stakes, no data corruption) — exactly matching the spec's own
framing of this as "a simpler, second example... at lower stakes."

**MODULE 10: COMPLETE.** All four planted bugs confirmed genuinely
present and reproducible via real testing (not theoretical):
1. Drag-drop race — genuine data collision, reproduced (two issues, one
   order key)
2. Optimistic UI rollback — added, reproduced via a real forced server
   failure ("elastic" snap-back, Peter's own description)
3. WebSocket reconnect desync — added, reproduced via a full real
   sequence (disconnect → concurrent server-side change → reconnect →
   confirmed stale until manual refresh)
4. Comment ordering — confirmed as sync gap only, not a data race;
   precisely distinguished from Bug 1 rather than conflated with it

All four marked in code with explicit "PLANTED BUG" comments pointing
back to this log and the spec, so future-Claude/future-Peter doesn't
accidentally "fix" them without updating this record first.

## Module 11 (miniProject) — begins

Peter uploaded the companion spec (`Spadework_miniProject_Spec_v1.md`),
requested for this module since the Kanban spec alone didn't cover it.

**Design ambiguity flagged and confirmed before building:** spec's data
model sketch lists Activity/ActivityDependency/ActivityIssue plus
ScheduleBaseline/DecisionNode, but doesn't fully specify HOW a baseline
stores its snapshot of the computed schedule. Proposed interpretation:
`Activity.planned_duration` is live/mutable; creating a Decision Node
is what triggers the forward/backward pass AND creates an immutable
baseline snapshot, in one step, gated by writing the rationale.
**Confirmed correct by Peter before writing any code.**

**WORKFLOW CHANGE — paste corruption on long files:** a very long
heredoc paste for `scheduling.py` corrupted badly enough that the file
was never created at all (heredoc's closing `EOF` marker got lost in
the corruption, so bash never recognized where the block ended). Peter
suggested creating files directly in the VS Code editor for anything
this long, pasting there and saving with Ctrl+S — sidesteps
shell/heredoc parsing entirely. **Adopted as the approach for
longer/more complex files from here on**, verified via `cat` +
`python3 -c "import ..."` afterward same as always.

### Scheduling algorithm — built and verified standalone (same
discipline as Module 8's ordering-key)

**File created (via VS Code editor):** `activities/scheduling.py` —
`topological_order()` (Kahn's algorithm, cycle detection via "whatever
never got its in-edges fully removed"), `compute_schedule()` (forward
pass: ES/EF; backward pass: LS/LF; float = LS-ES). Kept independent of
Django models, same reasoning as `issues/ordering.py`.

**Ran (SUCCESS) — verified against a genuine hand-calculated worked
example BEFORE any database integration:**
```
python3 -c "from activities.scheduling import compute_schedule, CycleDetectedError; ..."
```
5-activity DAG (A,B parallel starts; C depends on A; D depends on B+C;
E depends on D — durations 3,4,2,5,1). Hand-calculated expected
critical path A→C→D→E (total 11), B carrying 1 day of float. **Computed
result matched the hand-calculated dict exactly, byte for byte** (`assert
result == expected` passed). Cycle test (A→B→C→A) correctly raised
`CycleDetectedError` naming all three involved activities.

**Files created (via VS Code editor):** `activities/models.py` — six
models: `Activity`, `ActivityDependency` (FS-only, no type field
needed), `ActivityIssue` (cross-tool link to `issues.Issue`),
`ScheduleBaseline`, `BaselineActivitySchedule` (the immutable snapshot
— captures duration-at-baseline-time AND computed ES/EF/LS/LF/float per
activity per baseline), `DecisionNode`.

**Verification note:** first attempt used a bare `python3 -c "from
activities.models import ..."` check — failed with
`ImproperlyConfigured` (Django settings not bootstrapped outside a
management command). Not a bug in the file — corrected to the real
verification: `makemigrations` itself, which fails loudly with a proper
traceback if anything's actually wrong.

**Ran (SUCCESS):**
```
python manage.py makemigrations activities
```
→ all 6 models generated correctly.
```
python manage.py migrate activities
```
→ applied cleanly.

**Files created (via VS Code editor):**
- `activities/serializers.py` — serializers for all 6 models.
  `ActivityDependencySerializer` validates against self-dependency
  (predecessor==successor). `ScheduleBaselineSerializer` nests its
  `BaselineActivitySchedule` rows, `is_active` is read-only (only ever
  set by the DecisionNode creation flow, never directly).
- `activities/views.py` — standard ViewSets for
  Activity/ActivityDependency/ActivityIssue.
  `ScheduleBaselineViewSet` is READ-ONLY — baselines are never edited
  directly, only created as a side effect of a DecisionNode.
  `DecisionNodeViewSet.create` is the actual trigger: validates
  board+rationale present, runs `compute_schedule()` against CURRENT
  Activity durations, returns a clean 400 with involved activity ids on
  `CycleDetectedError` (never lets a cycle silently produce garbage
  dates, per spec's explicit requirement), then inside one
  `transaction.atomic()` block: deactivates the previous baseline,
  creates the new one, snapshots a `BaselineActivitySchedule` row per
  activity, creates the `DecisionNode` row. Atomic specifically so a
  mid-way failure can't leave two baselines simultaneously active or a
  half-written snapshot.
- `activities/urls.py` — router registrations for all 5 endpoints.
- `config/urls.py` — added activities include.

**Process note:** Peter correctly flagged that `views.py` likely
already existed as a Django `startapp` stub before this — true, and
worth naming going forward: say "open" rather than "create" for files
likely to already have scaffold content, so it's clear whether
something's being overwritten vs. genuinely created fresh. No actual
problem here (end result correct either way), just a precision gap in
instruction wording.

**Ran (SUCCESS) — full end-to-end test, recreating the exact
hand-verified worked example through the real API:**
- Created 5 activities (A-E, ids 1-5), 4 dependencies (A→C, B→D, C→D,
  D→E).
- Triggered Decision Node creation:
```
curl -s -X POST http://127.0.0.1:8000/api/decision-nodes/ ... -d '{"board":1,"label":"Initial baseline","rationale":"First schedule for this project."}'
```
→ **every ES/EF/LS/LF/float value across all 5 activities matched the
standalone algorithm test exactly**, byte for byte. `is_active: true`
correctly set, `based_on: null` correctly reflecting this is the
first-ever baseline. Full chain (algorithm → API → database →
serialized response) proven correct end to end, not just at the
algorithm layer.

**Ran (SUCCESS) — cycle rejection test:** added a dependency E→A
(creating a genuine cycle A→C→D→E→A), then attempted a new Decision
Node → cleanly rejected with a descriptive error naming the cycle, not
a crash or silent bad-date output. Cleaned up the test dependency
afterward to restore a valid DAG.

**MODULE 11 BACKEND: DONE.** Data model, scheduling algorithm, and full
API (Activities, Dependencies, ActivityIssue links, read-only
Baselines, DecisionNode-triggers-recalculation-and-snapshot) all
verified working correctly, including the cycle-rejection requirement
the spec explicitly called out as "a real requirement, not an edge case
to skip."

## Module 11 — frontend

**Files created (via VS Code editor):**
- `stores/activities.ts` — `Activity`/`ActivityDependency`/
  `ScheduleBaseline`/`BaselineActivitySchedule` interfaces,
  `fetchAll` (parallel-fetches activities/dependencies/baselines via
  `Promise.all`, picks the active baseline), `createActivity`,
  `createDependency`, `createDecisionNode`, `scheduleFor(activityId)`
  helper.
- `views/ProjectView.vue` — activity/dependency add forms, Decision
  Node trigger form (label + required rationale, with a tooltip
  explaining "recalculating creates a new baseline, prior one kept, not
  overwritten" right at the point of use — per spec's "microcopy, not
  training" principle), Gantt/Node toggle. Gantt: bars positioned via
  `early_start`/`early_finish` scaled to pixels, critical-path
  activities (float===0) shown red vs. indigo for float. Node diagram:
  hand-rolled SVG (no external graph library, same low-dependency
  approach as drag-and-drop) — client-side longest-path level
  assignment purely for column layout (NOT the CPM calculation itself,
  clearly distinguished in code comments), arrows via SVG `marker`.
- `router/index.ts` — added `/project` route.
- `views/DashboardView.vue` — added "Project Schedule" nav link.

**Process note:** Peter asked to verify `router/index.ts` via `cat`
before trusting the VS Code paste, given the earlier corruption
incident — confirmed landed correctly and completely. Same for the
dashboard link edit (`grep -A5`). Reinforced: terminal DISPLAY
garbling and actual file corruption are often separate things —
verification after the fact is the reliable check either way, not
trying to visually parse a messy paste as it happens.

**Ran (SUCCESS) — full manual browser test, both view modes:**
- Gantt view: critical path (A, C, D, E) correctly shown in red, B
  correctly shown in indigo (has float), bar positions match the
  hand-verified calculation exactly (A@0, C@3, D@5, E@10).
- Node diagram: critical path flows straight across A→C→D→E in red,
  B correctly branches in separately (blue) and merges into D, arrows
  correctly directed.

**MODULE 11: COMPLETE.** Data model, scheduling algorithm (verified
standalone against a hand-calculated worked example before any
integration), full API (including atomic Decision-Node-triggers-
recalculation-and-snapshot flow, cycle rejection), and frontend (both
required display modes, toggleable, both driven by the same schedule
data) all verified working end-to-end.

---

# ALL 11 MODULES COMPLETE

Every module in `Spadework_Tier2_Kanban_Spec_v1.md` and
`Spadework_miniProject_Spec_v1.md`'s build sequence is now built,
tested, and verified working: Auth, Board/Status, Teams, Issue CRUD,
Comments, Labels/search, Drag-and-drop with fractional ordering keys,
Real-time via Channels/Daphne, the four planted teaching bugs
(confirmed genuinely reproducible), and the full miniProject scheduling
feature set (CPM forward/backward pass, Decision Nodes, dual Gantt/node
views).

**Outstanding items carried forward (not blocking, for a future
session):**
- Docker rebuild/retest for Modules 3 through 11 (only Modules 1-2 have
  been verified in Docker so far — everything since has been venv/Vite
  only)
- Carried-over polish items: "Clear filters" button (Module 7 UX note),
  token refresh never manually exercised, npm audit vulnerabilities,
  `DJANGO_SETTINGS_MODULE` defaulting to dev even in Docker builds,
  native nginx stopped manually rather than disabled
- `ActivityIssue` (the miniJira↔miniProject integration link) has a
  model, serializer, and API endpoint, but no frontend UI yet — spec
  lists it as in-scope but didn't specifically call out UI timing

## Side deliverable — Docker reproducibility tutorial script

Per Peter's request during a tea break: drafted a tutorial script
demonstrating exactly why Docker would have prevented the redis/
channels_redis version-drift bug just found. Saved separately as
`Docker_Reproducibility_Tutorial_Script.md` (not part of this build log
— a standalone deliverable). Framed carefully to avoid overclaiming:
pinning fixes THIS instance of the ambiguity; Docker's real value is
that a built image is a frozen, shareable, immutable artifact, so
dependency resolution only has to succeed once (at build time) rather
than separately on every machine that ever runs the app. Six-part
on-camera structure: cold open with the real traceback, root cause,
live-demonstrated drift, the pin fix, the deeper Docker point, tie-back
to the earlier venv-vs-image-size material as a companion episode.

---
### Carried-over follow-ups from Module 2 (still open)
- Token refresh endpoint not manually exercised (interceptor code
  exists, untested in practice)
- `ScaffoldPlaceholder.vue` — safe to delete, no longer routed to
- Redis not installed natively (only in Docker) — fine, not needed
  until Channels/websockets modules
- npm audit: 2 vulnerabilities flagged, not addressed
- `DJANGO_SETTINGS_MODULE` still defaults to `config.settings.dev` even
  inside the "production-style" Docker build (manage.py default, never
  overridden) — flagged, not fixed this session
- Docker Compose port 80 now depends on native nginx staying stopped
  (`sudo systemctl stop nginx` — not disabled, will restart on reboot)

---

### Reference: the two `docker-compose.yml` versions (tutorial record)

**BEFORE — hid the startup-race problem (self-healing via crash-loop):**
```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: miniapp_db
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME:-miniapp}
      POSTGRES_USER: ${DB_USER:-miniapp}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - miniapp_postgres_data:/var/lib/postgresql/data
  redis:
    image: redis:7-alpine
    container_name: miniapp_redis
    restart: always
  backend:
    build: ./backend
    container_name: miniapp_backend
    restart: always
    env_file: .env
    depends_on:
      - db
      - redis
  daphne:
    build: ./backend
    container_name: miniapp_daphne
    restart: always
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    env_file: .env
    depends_on:
      - db
      - redis
  frontend:
    build: ./frontend
    container_name: miniapp_frontend
    restart: always
  nginx:
    image: nginx:alpine
    container_name: miniapp_nginx
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
      - daphne
      - frontend
volumes:
  miniapp_postgres_data:
```
`depends_on` here (plain list) only waits for the container to *start*.
Backend/daphne raced Postgres's own startup, failed 2x, `restart: always`
silently papered over it by crash-looping to eventual success.

**AFTER — fixed, waits for real readiness:**
```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: miniapp_db
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME:-miniapp}
      POSTGRES_USER: ${DB_USER:-miniapp}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - miniapp_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-miniapp}"]
      interval: 2s
      timeout: 3s
      retries: 10
  redis:
    image: redis:7-alpine
    container_name: miniapp_redis
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 2s
      timeout: 3s
      retries: 10
  backend:
    build: ./backend
    container_name: miniapp_backend
    restart: always
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
  daphne:
    build: ./backend
    container_name: miniapp_daphne
    restart: always
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
  frontend:
    build: ./frontend
    container_name: miniapp_frontend
    restart: always
  nginx:
    image: nginx:alpine
    container_name: miniapp_nginx
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
      - daphne
      - frontend
volumes:
  miniapp_postgres_data:
```
`healthcheck` blocks use each image's own built-in readiness probe
(`pg_isready`, `redis-cli ping`) — "can this service actually accept work
now," not just "is the process running." `depends_on: condition:
service_healthy` makes backend/daphne genuinely wait rather than
crash-loop. Verified via clean `docker compose down && up`: healthy
status shown before dependents started, zero connection errors in logs,
single-attempt success.

---

## Module 2 (Auth) build

**Goal:** Get the `accounts` app (custom User model) migrated and the
auth system running venv-first, before moving to Docker.

**Commands run:** *(none yet — next step queued)*

**Next step (queued, not yet run):**
```
cd ~/miniapp/backend && source /home/envs/main_venv/bin/activate && python manage.py makemigrations accounts
```
*(Note: venv path used in earlier draft command was wrong — actual path
confirmed as `/home/envs/spadework`, project path confirmed as
`/home/spadework/miniapps/miniapp/backend`. Correct these before running.)*

---


---

# Session 2 (15 Jul 2026) — miniProject node-detail hierarchy addition

Peter's request before returning to Riverside Club: add ONE additional
level of node detail to miniProject — high-level view (grouped) and
operational-level view (leaf activities) — confirmed bounded to
exactly one level, not arbitrary nesting.

## Backend

**File changed:** `activities/models.py` — added `Activity.parent`
(self FK, nullable, `SET_NULL`, `related_name='children'`). `clean()`
enforces exactly one level: a parent activity cannot itself have a
parent — model-level validation (holds for admin/shell-created rows,
not just API requests), not just serializer-level.

**Ran (SUCCESS):**
```
python manage.py makemigrations activities && python manage.py migrate activities
```
→ `0002_activity_parent.py`, applied cleanly.

**File changed:** `activities/serializers.py` — `ActivitySerializer`
gained `validate_parent()`, mirroring `Activity.clean()` (DRF doesn't
call model `clean()` automatically).

**Ran (SUCCESS) — depth-cap test:** set C's parent to A (valid, one
level) → succeeded. Attempted setting D's parent to C (C already has a
parent) → correctly rejected: `{"parent":["Only one level of grouping
is allowed..."]}`. Cleaned up test relationship afterward.

**REAL BUG FOUND AND FIXED — CPM pollution by container activities:**
after creating a "Design Phase" parent grouping B+C, realized the
forward/backward pass would treat "Design Phase" as if it were real,
independently-schedulable work (it still has its own `planned_duration`
and no dependencies) — a phantom node polluting the actual schedule.
**Fixed in `activities/views.py`'s `DecisionNodeViewSet.create`:**
excludes any activity that has children from the CPM computation
entirely (`parent_ids_with_children` query, `.exclude()`), and filters
dependencies to only reference surviving leaf ids. Verified via a fresh
Decision Node: resulting baseline schedule had exactly 5 entries
(A,B,C,D,E) — "Design Phase" correctly excluded.

## Frontend

**Files changed:**
- `stores/activities.ts` — added `parent` to `Activity` interface,
  `createActivity` accepts optional `parent`, new `childrenOf()`,
  `rollupFor()` (high-level roll-up: min early_start/max early_finish
  across children, "critical" defined as "at least one child critical"
  — stated explicitly as a judgment call, not hidden), and
  `promotedDependencies()` (cross-group edges only for the high-level
  node diagram — same-parent dependencies dropped as not meaningful at
  that zoom level).
- `views/ProjectView.vue` — added detail-level toggle (High level /
  Operational level) alongside the existing Gantt/Node toggle; parent
  selector in the add-activity form (`availableParents` restricted to
  top-level activities only, mirroring the backend's one-level rule in
  the UI itself, not just relying on the API to reject bad input).

**BUG FOUND — container activity appearing as its own row/node at
BOTH levels:** first pass had `visibleActivities` show ALL activities
at operational level (including "Design Phase" itself, which should
never appear as if it were real work) — fixed:
`visibleActivities` at operational level now filters to
`childrenOf(a.id).length === 0` (genuine leaves only).

**BUG FOUND AND DIAGNOSED — Node diagram / Operational level combo
showing STALE collapsed content despite correct button state:**
reproduced genuinely (button highlighted "Operational level" but
diagram still showed the collapsed "Design Phase" node). Ruled out
simple browser caching first (`Ctrl+Shift+R` hard refresh did NOT fix
it — still broken after). Added a temporary debug readout
(`{{ viewMode }} {{ detailLevel }} {{ visibleActivities }}`) to see
actual reactive state directly rather than guessing from the code —
this alone (a real file edit, forcing Vite to fully recompile the
component) resolved it; all four Gantt/Node × High/Operational
combinations then matched their debug readout correctly. **Diagnosis:**
a Vite HMR module-state staleness issue distinct from browser caching —
a plain hard refresh reloads the PAGE but can still be served stale
module state by Vite's own dev-server HMR runtime if nothing in the
module graph technically changed; only an actual file edit (or a full
`npm run dev` restart) forces a genuine remount. **Noted as a live,
reproducible example of exactly the "ghost bugs" episode already on
Peter's Spadework tutorial backlog** (HTTP cache vs Vite HMR vs stale
container) — worth keeping this repro as the worked example. Debug
readout removed after diagnosis.

**MODULE 11 NODE-HIERARCHY ADDITION: COMPLETE.** Confirmed working
correctly across all four view combinations (Gantt/Node ×
High-level/Operational-level), backend CPM pollution bug fixed, and a
genuine Vite-HMR staleness bug found, diagnosed, and resolved along the
way — with a bonus: real content for the ghost-bugs tutorial episode.
