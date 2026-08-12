# miniJira + miniProject

The Spadework Tier 2 "miniPM suite". See the full specs before touching
this code:

- `Spadework_Tier2_Kanban_Spec_v1.md` — miniJira
- `Spadework_miniProject_Spec_v1.md` — miniProject
- `Spadework_Business_Plan_v1.md` / `Spadework_Master_Baseline_v1.md` —
  positioning and strategy

## Module 1 status: scaffold complete

What's here: Django project structure, all apps registered in
`INSTALLED_APPS` (including `activities`, per the one-project
architecture principle — see the miniProject spec), Docker Compose,
Nginx reverse proxy (with the WebSocket routing already correct, ready
for Module 9), a custom `accounts.User` model, and a minimal Vue shell.

**Deliberately not here yet:** any real models beyond `accounts.User`,
any API endpoints, any real frontend views. Those land module by module
— see each spec's "Suggested build sequence" / "Build sequencing note".
Don't add functionality ahead of its module; that's the whole point of
building this way.

## Environment variables

`.env` is loaded two ways, deliberately kept consistent:
- **Inside Docker:** `docker-compose.yml`'s `env_file: .env` on the
  `backend`/`daphne` services
- **On the host** (e.g. running `python manage.py migrate` directly for
  local debugging, outside Docker): `config/settings/base.py` calls
  `load_dotenv()` explicitly — without this, host-based commands would
  silently fall back to the `os.environ.get()` defaults instead of
  erroring clearly, the same "no password supplied" trap documented in
  `emillar_v2`'s Deploy Bible.

## Running it locally

```bash
cp .env.example .env    # fill in real values, especially DB_PASSWORD
docker compose build
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

Then visit `http://localhost` — you should see the scaffold placeholder
page, and `http://localhost/admin/` for the Django admin.

## Deploy discipline

Same rules as `emillar_v2`'s Deploy Bible apply here once this is on a
real server: never run `makemigrations` on the server, only `migrate`;
confirm you're on the right git branch before deploying; use
`--force-recreate` rather than `restart` if a container won't come up
clean; `--no-cache` is required for the frontend rebuild specifically.
