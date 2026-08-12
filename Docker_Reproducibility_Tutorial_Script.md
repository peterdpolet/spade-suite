# Tutorial Episode: "Works Today, Broken Next Month" — Why Docker Fixes What Pinning Alone Can't

## The real bug this is based on

While building miniApp's Module 9 (real-time updates), we hit this:

```
redis.exceptions.TimeoutError: Timeout reading from localhost:6379
```

`requirements.txt` had:
```
channels-redis>=4.2
```

No explicit `redis` pin anywhere. `channels-redis` depends on the
`redis` Python package but doesn't pin it tightly, so `pip` resolved
"whatever the latest compatible `redis` is *right now*" — which, on the
day we ran `pip install`, was `redis 8.0.1`. `channels_redis 4.3.0`'s
internal connection/timeout handling predates that major version, and
the two don't get along: the websocket consumer crashed on every
attempt to read from the channel layer.

The fix was two-part:
1. Pin `redis<5` — removes the ambiguity for `pip`.
2. **The deeper lesson: even a perfect pin doesn't fully solve the
   underlying problem.** This script demonstrates why.

---

## Part 1 — Recreate the drift (bare pip, unpinned)

Show that the SAME `requirements.txt`, run today vs. resolved at some
future point after upstream releases a new major version, can silently
produce two different, incompatible environments — with zero code
changes on your end.

```bash
# Fresh venv, simulating "Developer A, installing today"
python3 -m venv /tmp/dev-a-venv
source /tmp/dev-a-venv/bin/activate
pip install channels-redis>=4.2
pip show redis | grep Version
# → whatever pip resolves to RIGHT NOW (was 8.0.1 for us)
deactivate
```

**On-camera narration point:** this isn't hypothetical — it's exactly
what happened to us live, mid-build. Show the actual traceback here.

```bash
# Fresh venv, simulating "Developer B, installing months later,
# after redis-py has released a new major version"
python3 -m venv /tmp/dev-b-venv
source /tmp/dev-b-venv/bin/activate
pip install "channels-redis>=4.2" "redis==8.0.1"   # standing in for
                                                     # "whatever's latest
                                                     # at some future date"
deactivate
```

**The point to land:** `requirements.txt` is a *recipe*, not a
*result*. Every time `pip install -r requirements.txt` runs, it
re-resolves from whatever's currently on PyPI. Two people — or the same
person, six months apart — running the identical command against the
identical file can get genuinely different, incompatible environments.
That's not a hypothetical edge case; it's what just happened to us.

---

## Part 2 — The pin fixes THIS instance of the ambiguity

```bash
echo 'redis<5' >> requirements.txt
```

Show that now, both "Developer A" and "Developer B" venvs above would
resolve to the same `redis` major version, regardless of when they
installed. Good — but flag explicitly for the tutorial:

**Pinning is necessary but not sufficient.** It only helps for the
packages you remembered to pin. `channels-redis` itself isn't pinned to
an exact version (`>=4.2` — open-ended upward). Every OTHER unpinned
transitive dependency in the file has the exact same latent risk we
just lived through. You can't reasonably audit and hand-pin every
transitive dependency of every package, forever, by hand.

---

## Part 3 — What Docker actually adds on top of pinning

The key distinction, worth stating explicitly on camera:

> A `requirements.txt` is instructions for BUILDING an environment.
> A Docker image is the BUILT environment itself, frozen.

```bash
# Build once, today, with the (now-pinned) requirements.txt
docker build -t miniapp-backend:demo .

# Get its content-addressed ID — this is the actual proof
docker inspect miniapp-backend:demo --format='{{.Id}}'
```

**On-camera demonstration:** build the SAME image again right now —
same Dockerfile, same requirements.txt, nothing changed:

```bash
docker build -t miniapp-backend:demo2 .
docker inspect miniapp-backend:demo2 --format='{{.Id}}'
```

Point out: if nothing in the build context changed, Docker's layer
cache means this second build doesn't even re-run `pip install` at
all — it reuses the exact cached layer from the first build, byte for
byte. Show `docker history` on both images side by side if useful —
identical layer hashes for the `pip install` step.

**The real point to land, worded carefully — don't overclaim:**

Docker does NOT magically make `pip install` deterministic. If you ran
`docker build` today vs. six months from now with an unpinned
`requirements.txt`, you'd hit the SAME resolution drift inside the
container that you'd hit in a bare venv — the container isn't immune to
that on its own.

**What Docker actually guarantees is different and arguably more
important:** once you HAVE built an image — whether that build happened
to resolve well or badly — that exact image is now a permanent,
shareable, immutable artifact. Every teammate, every CI run, every
production deploy that pulls `miniapp-backend:demo` gets IDENTICAL
bits, forever, without ever re-running dependency resolution again. The
image is the unit of distribution, not the recipe. `requirements.txt`
only has to resolve correctly ONCE, at build time, by whoever built the
canonical image — not separately, and potentially differently, on every
single machine that ever needs to run the app.

That's why "use Docker" is a genuinely good instinct in response to
this exact bug: not because Docker is smarter about dependency
resolution, but because it turns a repeat, per-machine risk (bare
`pip install`, run N times across N environments, N chances to drift)
into a one-time risk (build once, distribute the verified result
everywhere).

---

## Suggested on-camera structure

1. Cold open: show the actual `TimeoutError` traceback from our real
   session — it's dramatic and it's real, not staged.
2. Explain the root cause: unpinned transitive dependency + upstream
   major version bump.
3. Live-demonstrate Part 1 (the drift) — even faking "future" via an
   explicit older/newer version install is honest and clear enough on
   camera, framed correctly as a stand-in.
4. Fix with the pin — show it working.
5. Land the deeper point with Part 3 — pinning helps, Docker's
   immutable-artifact model is the structural fix.
6. Close on the size/layer-caching material from the earlier Docker
   session (venv vs image size, layer sharing) as a natural companion
   episode — both are really the same underlying idea: Docker's value
   isn't raw size, it's that the built artifact is authoritative and
   shared, not re-derived per machine.
