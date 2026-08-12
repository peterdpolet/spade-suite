# Docker Reference

> A curated, tiered reference for working developers. Updated 17 Jul
> 2026 — substantially revised from the June version; the single
> biggest addition is the `restart` vs `--force-recreate` distinction,
> which resolved a genuinely baffling production incident this cycle.

---

## The three tiers

- **Must Know** — daily-driver commands.
- **Should Know** — needed within the first week of a real project.
- **Good to Know** — diagnostics and recovery for when something's
  actually wrong.

---

## Must Know

### `docker compose build [service]`
Build (or rebuild) an image from its Dockerfile. Omit the service name
to build everything.

### `docker compose up -d`
Start all services in the background (detached).

### `docker compose down`
Stop and remove containers. Add `-v` **only** when you genuinely want
to destroy volumes (database data included) — this is not a routine
flag.

### `docker compose ps`
Shows every service's status. **Read the STATUS column every time** —
`Up` and `Restarting` look similar at a glance and mean completely
different things.

### `docker compose logs [service]`
View a service's logs. Add `--tail=80` to avoid an overwhelming dump
on a long-running service, and `-f` to follow in real time.

### `docker compose exec <service> <command>`
Run a command inside an already-running container — this is how
Django management commands, `psql`, and one-off debugging happen.

### `docker compose restart <service>`
Relaunches an existing container's process. See **Good to Know** for
the critical limitation of this command that cost real debugging time
this cycle.

---

## Should Know

### `--no-cache`
Forces a rebuild ignoring cached layers. **Required for frontend
builds specifically** in this stack — the npm/Vite build layer caches
in a way that can silently serve stale JS otherwise. Not generally
needed for backend builds, where cached layers are usually correct.

### `docker compose exec` vs `docker run`
`exec` runs inside a container that's already part of your compose
stack, sharing its network/volumes. `docker run` spins up a brand new,
disposable container — useful specifically for isolating whether a
problem is with your actual service or something more fundamental (see
the mount-testing technique below).

### Bind mounts vs named volumes
A bind mount (`./nginx/default.conf:/etc/nginx/conf.d/default.conf`)
maps a specific host path into the container — changes on the host
show up immediately. A named volume (`miniapp_postgres_data:/var/lib/
postgresql/data`) is Docker-managed storage, not tied to a specific
host path — the right choice for data that should outlive container
recreation (databases), wrong for config you want to edit directly on
the host.

### `env_file` in `docker-compose.yml`
Loads a `.env` file's contents as real environment variables *inside
the container*. This only applies inside containers — it does nothing
for commands run directly on the host. See the `.env` gotcha below.

### `docker compose images`
Shows the actual image ID, tag, and build time for each service —
useful for confirming a rebuild genuinely produced something new.

---

## Good to Know

### `restart` vs `--force-recreate` — the distinction that resolved a
genuinely baffling incident

`docker compose restart <service>` relaunches the **existing**
container's process in its **existing** state. It does **not**:
- re-read `docker-compose.yml` for config changes
- re-attach mounts fresh
- fix a container that was created in a bad state to begin with

If a service is crash-looping and `restart` doesn't fix it, that's the
signal to stop restarting and recreate instead:

```bash
docker compose up -d --force-recreate <service>
```

This resolved a real Nginx SSL crash loop where every individual
ingredient — the certificate files, the bind mount, the config content
— was independently verified correct via multiple diagnostic passes,
and the actual fix was simply that the specific running container
instance had gotten into a bad state at creation and kept replaying it
on every restart attempt. A full recreate fixed it in seconds once
identified. The lesson generalises: **`restart` assumes the container
itself is fine and just needs restarting; `--force-recreate` assumes
nothing and rebuilds from the current state of everything.**

### Testing a mount or image in isolation with a throwaway container

When something's not working and you're not sure if it's the mount, the
image, or the specific running container, a disposable container with
the exact same mount isolates the variable cleanly:

```bash
docker run --rm -v /etc/letsencrypt:/etc/letsencrypt:ro nginx:alpine \
  sh -c "cat /etc/letsencrypt/live/yourdomain.co.uk/fullchain.pem | head -3"
```

If this works but your real service still fails, the problem is
specific to that container's state, not the mount or the image — a
strong pointer toward `--force-recreate` rather than further
config-chasing.

### Inspecting what's actually mounted on a live container

Don't trust what the compose file *says* is mounted — confirm what
Docker actually applied to the running container:

```bash
docker inspect <container_name> --format '{{json .Mounts}}' | python3 -m json.tool
```

### The `.env` / host vs container environment gotcha

Environment variables defined in `.env` and referenced via `env_file:`
in `docker-compose.yml` **only exist inside the container**. Running a
command directly on the host (e.g. `python manage.py migrate` in a
bare venv, not via `docker compose exec`) has no access to them unless
something on the host side also loads `.env` explicitly (e.g.
`python-dotenv`'s `load_dotenv()` called in Django settings). Without
that, host-run commands silently fall back to whatever defaults are
coded in `settings.py` — commonly surfacing as a confusing `no
password supplied` database connection error that looks like a broken
database, not a missing environment variable.

### `docker compose build backend` costs almost nothing when nothing
changed

If you're ever unsure whether a change affects the backend, it's safe
to rebuild defensively — Docker's layer caching means an unaffected
build completes in seconds with everything marked `CACHED`, rather than
actually re-doing the work.
