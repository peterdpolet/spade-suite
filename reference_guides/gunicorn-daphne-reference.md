# Gunicorn / Daphne Reference

> A curated, tiered reference for working developers. Updated 17 Jul
> 2026 — substantially expanded from the June version, which covered
> Gunicorn alone. Daphne is now a first-class part of this guide,
> reflecting a real project's move from HTTP-only to a chat/real-time
> feature needing WebSockets.

---

## The three tiers

- **Must Know** — why you need this instead of `runserver`.
- **Should Know** — configuration you'll actually touch.
- **Good to Know** — the WSGI/ASGI split, and why a chat feature
  changes the picture.

---

## Must Know

### Why not just `python manage.py runserver`?
Django's own development server prints its own warning: *"This is a
development server. Do not use it in a production setting."* It's
single-process, has no crash recovery, and isn't built for concurrent
real traffic. Gunicorn exists to fill exactly that gap.

### Basic Gunicorn invocation
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```
`config.wsgi:application` points at your project's WSGI entrypoint —
the thing that actually imports your Django project and calls it for
every request.

### `--workers`
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```
A starting rule of thumb: `(2 × CPU cores) + 1`. Too few workers means
one slow request blocks everything else queued behind it; too many
wastes memory without a proportional throughput gain.

---

## Should Know

### The request lifecycle in this stack
```
Browser → Nginx → Gunicorn (WSGI) → Django views → DB
```
Nginx is the front door — TLS termination, static files, routing.
Gunicorn is the thing that actually runs your Python code. Static
files never touch Gunicorn at all — that's Nginx's job, and expecting
Gunicorn to serve them is a common point of confusion for people new to
the pairing.

### Gunicorn doesn't manage crash recovery for itself
The master process respawns dead workers — this is the actual
production-grade behaviour `runserver` never had. Killing a worker
process manually and watching it come back automatically is a genuine,
useful way to confirm this is actually working.

### Why a chat feature needs a second process entirely

HTTP is request → response → connection closes. A chat feature needs
the opposite: a connection that stays open in both directions
indefinitely. That's WebSocket, and Gunicorn (WSGI) has no concept of
it. **Daphne is Django Channels' ASGI server** — built specifically for
that persistent-connection shape.

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Gunicorn and Daphne run as **separate processes**, from **separate
entrypoints** (`wsgi.py` vs `asgi.py`), usually on separate ports — two
processes serving the same codebase in two fundamentally different
ways.

### Redis's role
Django Channels needs a **channel layer** — a shared message bus that
lets a message sent by one Daphne worker reach clients connected to a
*different* Daphne worker. Without it, a broadcast message would only
reach whichever single worker happened to handle that particular
client's connection.

---

## Good to Know

### Nginx has to know both shapes of traffic exist
```nginx
location /ws/ {
    proxy_pass http://daphne:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
location / {
    proxy_pass http://backend:8000;
}
```
Two real, distinct failure modes if this is wrong, worth knowing the
difference between:

1. **Misrouted entirely** — WebSocket traffic sent to Gunicorn instead
   of Daphne. Fails immediately; the connection never upgrades, because
   Gunicorn has no idea what a WebSocket upgrade request even is.
2. **Routed correctly, still broken** — routed to Daphne, but missing
   one of the three upgrade headers above. This is the sneaky one:
   Nginx defaults to HTTP/1.0 proxying and strips the Upgrade header
   unless told otherwise, so the connection stays on HTTP/200 instead
   of reaching 101 Switching Protocols — even though the routing itself
   was correct.

### Verifying it's actually working
```bash
curl -I http://localhost/api/some-endpoint/     # confirm ordinary HTTP still works via Gunicorn
```
Then open the chat feature in two separate browser windows and send a
message — seeing it appear in both proves the Redis/Channels broadcast
path is genuinely working, independent of whether the HTTP path works.
Check the browser's Network tab, WS filter, for a `101` status and live
message frames — that's the connection that never closes, and it's
Daphne's job, not Gunicorn's, to hold it open.

### Bare metal first, then Docker — worth doing once deliberately
Installing Gunicorn/Daphne directly via SSH (systemd units, hand-edited
Nginx config, manual `systemctl reload`) before ever touching Docker
grounds the concepts in real files and real processes, rather than
having Docker's abstraction sit between you and what's actually
happening. Once the friction of doing it by hand is genuinely felt,
`docker-compose.yml` replacing all of it stops being an abstract claim
and becomes an earned relief — same commands, same entrypoints, same
Nginx config content, just packaged and made reproducible.
