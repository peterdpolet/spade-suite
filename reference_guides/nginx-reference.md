# Nginx Reference

> A curated, tiered reference for working developers. Updated 17 Jul
> 2026 — substantially revised from the June version, with a full
> real-incident SSL diagnosis added and the WebSocket routing section
> expanded significantly following the Nginx/Gunicorn/Daphne work this
> cycle.

---

## The three tiers

- **Must Know** — the config you'll write on day one.
- **Should Know** — needed the first time you deploy behind HTTPS or
  proxy to more than one backend.
- **Good to Know** — diagnostics for when Nginx won't start or won't
  route correctly.

---

## Must Know

### Basic server block
```nginx
server {
    listen 80;
    location / {
        proxy_pass http://backend:8000;
    }
}
```
`location` blocks match request paths; `proxy_pass` forwards matching
requests to another address — a container name on Docker's internal
network, or `127.0.0.1:port` on bare metal.

### `reload` vs `restart`
```bash
nginx -s reload          # re-reads config, no dropped connections
sudo systemctl restart nginx   # full restart, drops active connections
```
Prefer `reload` for config changes on bare metal; in Docker, this
usually means `docker compose restart nginx` (see the Docker reference
for when that's insufficient and a recreate is actually needed).

### Static file serving
```nginx
location /static/ {
    alias /staticfiles/;
}
```
`alias` maps the URL path directly to a directory — distinct from
`root`, which appends the URL path onto the given directory. Getting
this backwards is a common source of 404s that look like a permissions
problem.

---

## Should Know

### Proxying to multiple backends
```nginx
location /api/ {
    proxy_pass http://backend:8000;
}
location / {
    proxy_pass http://frontend:80;
}
```
More specific `location` blocks take precedence over less specific
ones regardless of order in the file — Nginx doesn't just match
top-to-bottom.

### SSL certificate paths
```nginx
ssl_certificate     /etc/letsencrypt/live/yourdomain.co.uk/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.co.uk/privkey.pem;
```
**Important structural detail:** everything under `live/` is a set of
**symlinks**, not the actual certificate files — the real files live
under `archive/`. Mounting only `live/` into a container without also
mounting `archive/` produces dangling symlinks that fail exactly like
a missing certificate, even though `live/` itself looks populated.
Mount the whole `/etc/letsencrypt` directory, not a curated subset.

### WebSocket proxying — the three headers that are not optional
```nginx
location /ws/ {
    proxy_pass http://daphne:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```
All three matter, and missing any one produces a **specific, sneaky
failure mode**: the request routes to the right backend, but never
actually upgrades to a WebSocket connection — it silently stays on
HTTP (status 200) instead of reaching 101 Switching Protocols. This is
more insidious than routing it to the wrong backend entirely, because
the routing itself looks correct; only the protocol upgrade quietly
fails.

---

## Good to Know — a real SSL crash-loop diagnosis, step by step

This is the actual sequence that resolved a genuinely confusing
production incident, kept here because the *order* of elimination
matters as much as any single fact.

**Symptom:** `docker compose ps` showed Nginx `Restarting (1)`,
repeatedly.

**Log output** (`docker compose logs nginx --tail=80`) showed:
```
cannot load certificate "/etc/letsencrypt/live/yourdomain.co.uk/fullchain.pem":
BIO_new_file() failed ... No such file or directory
```

**Step 1 — confirm the certificate files genuinely exist:**
```bash
sudo ls -la /etc/letsencrypt/live/yourdomain.co.uk/
sudo ls -la /etc/letsencrypt/archive/yourdomain.co.uk/
```
Both were present and correctly formed. Not the cause.

**Step 2 — confirm the mount Docker actually applied, not just what
the compose file says:**
```bash
docker inspect nginx_container --format '{{json .Mounts}}' | python3 -m json.tool
```
Matched the compose file exactly. Not the cause.

**Step 3 — isolate whether it's the mount itself, using a disposable
container:**
```bash
docker run --rm -v /etc/letsencrypt:/etc/letsencrypt:ro nginx:alpine \
  sh -c "cat /etc/letsencrypt/live/yourdomain.co.uk/fullchain.pem | head -3"
```
This succeeded — read the real certificate content. This was the
turning point: identical mount, identical image, and it worked fine in
isolation. The problem had to be specific to *that one running
container's state*, not the filesystem, the config, or the image.

**Step 4 — the actual fix:**
```bash
docker compose up -d --force-recreate nginx
```
Resolved instantly. Best-guess root cause: some timing wrinkle at the
exact moment that specific container was originally created left it in
a bad state that a plain `restart` could never fix, because `restart`
never re-establishes the container from scratch — see the Docker
reference for the general principle.

**The transferable lesson:** when every individual piece checks out
correct in isolation and the problem still won't go away, stop
re-verifying the same pieces and consider that the *container instance
itself*, not any of its ingredients, might be the thing that's broken.

### Bare-metal vs Docker — a deliberate teaching choice, not just a
config note

Nginx, Gunicorn, and Daphne are just Linux processes — Docker only
packages them. Understanding what each does *without* Docker in the
picture (manual `apt install`, systemd units, hand-edited config files)
gives a grounding that a Docker-first introduction skips past. Worth
doing once, deliberately, even if Docker is how you'll actually run
things day to day.
