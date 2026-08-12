# Spadework Tier 2 — miniJira Spec v1

**Working name: "miniJira"** — deliberate naming choice: a constant
reminder that this is explicitly *not* a full-fat Jira/MS Project
alternative. The "mini" is load-bearing.

**Companion document:** `Spadework_miniProject_Spec_v1.md` — the
simplified Gantt/scheduling tool, now a locked, in-scope companion (as
of 15 Jul 2026), not a parked candidate. Together, miniJira +
miniProject form "the miniPM suite" — see that document for its own
locked scope, data model, and the forward/backward-pass scheduling
algorithm design.

## Positioning

Tier 2 commercial product — not a supplementary demo alongside `emillar_v2`,
but the actual flagship teaching app going forward. Tier 1 (free) and
Riverside Club become the funnel that builds trust toward this, rather
than the end goal in themselves. Riverside Club's scope should stay
disciplined — finished well, not over-invested — since its job is
credibility, not completeness.

**Why this app, not another `emillar_v2`-style CRUD app:** inventory/PO
bugs are mostly data-shape mismatches (wrong field, wrong endpoint, wrong
serializer). A Kanban board generates a genuinely different, richer bug
category — concurrency and state bugs: drag-and-drop reordering races,
optimistic UI needing rollback on failure, WebSocket reconnection
handling, stale card position after a concurrent move. That's a stronger,
more varied teaching surface for the EPC tracer than another data-shape
demo would be.

## Stack

Same core stack as Riverside Club, deliberately — maximises content and
skill reuse across both:

Django 6 + DRF + SimpleJWT + Djoser + Channels/Daphne + Redis + Vue 3 +
Vite + Pinia + Tailwind + TypeScript + PostgreSQL + Docker Compose +
Nginx + DigitalOcean.

## MVP scope

**LOCKED 15 Jul 2026 — this is the complete feature set for the miniPM
suite. No further additions without explicitly reopening this document.**
This bound exists specifically to demonstrate that a genuinely
full-featured, intuitive PM suite is achievable with very little
learning overhead — adding more would undermine the point being proven,
not strengthen it.

**In scope:**
- Single project/board (no multi-project switching)
- **Fixed status columns, confirmed 17 Jul 2026 — four, not three:**
  Todo / In Progress / Blocked / Done. Blocked sits between In Progress
  and Done in the board layout, reachable from either. Priority boxes
  (below) stay scoped to Todo only — Blocked doesn't get the same
  sub-grouping, to keep this the easy win it's meant to be rather than
  a larger redesign.
- **Priority boxes within the Todo column** — 2-3 fixed priority tiers
  (not user-configurable) as visual sub-groupings inside Todo only, so
  what's actually next is visible at a glance without a separate
  priority field/filter mechanism. Once something moves to In Progress
  or Done, priority triage is moot, so this doesn't extend to those
  columns.
- **Teams and Team Members** — a `Team` model and membership, so issues
  can be allocated at the team level and, optionally, to a specific
  member within that team
- **Task allocation to teams/members** — an issue can be assigned to a
  team, a specific member, or both (member should belong to the
  assigned team)
- **Completion date — two fields, confirmed 17 Jul 2026:** a
  user-set **target** completion date (planned, settable on
  create/edit) plus an **actual** completion date that auto-captures on
  transition to Done. The actual date wasn't originally planned, but
  directly strengthens Decision Node variance review in miniProject by
  giving a genuine planned-vs-actual comparison at the issue level, not
  just the Activity level.
- Issue CRUD: title, description, status, assignee, labels
- Comments on issues
- Labels (simple tagging, no colour-coding system beyond basics)
- Basic search/filter (by status, label, assignee, text match on title)
- Live updates across connected clients (Channels/Daphne — reuse the
  chat feature's existing pattern)
- Drag-and-drop reordering within and across columns

**Explicitly excluded from MVP** (the real risk here is scope creep into
an actual Jira competitor — resist it):
- Multiple projects/workspaces
- Custom/configurable workflow states
- Epics, sprints, burndown charts, velocity tracking
- Granular permissions/roles beyond basic auth (Teams/Team Members
  above is organizational allocation, not an RBAC/permissions system —
  worth keeping that distinction clear during build)
- Third-party integrations (Slack, GitHub, etc.)
- Notifications system
- File attachments on issues

## The ordering-key decision — worth its own teaching episode

Two real approaches to persisting drag-drop order, with a genuine
trade-off worth surfacing to learners rather than picking silently:

**Integer resequencing** — each card has an integer position; moving a
card means renumbering every card after it. Simple to reason about, but
a classic source of race conditions when two people reorder concurrently
(two simultaneous moves can both read the same "before" state and write
conflicting renumbered positions).

**Fractional/lexicographic ordering keys** (LexoRank-style) — each card
gets a string/fractional key that sorts between its neighbours; moving a
card only touches that one row, no renumbering cascade. More robust
under concurrency, but the key-generation logic itself (what happens
when you run out of room between two adjacent keys) is a genuinely
interesting problem worth teaching in its own right.

**Recommendation: fractional/lexicographic.** It's more production-
realistic (this is what Jira, Trello, and Linear actually do), and the
concurrency robustness matters more here than the added complexity,
given this app's whole point is generating real concurrency bugs to
trace. Build it deliberately breakable — a bug where two near-simultaneous
moves produce colliding keys is exactly the kind of EPC-traceable bug
this app exists to create.

## Architecture principle: one project, not two integrated services
(locked 17 Jul 2026)

miniJira and miniProject are **one Django project, one database, from
the first migration** — not two independently-built systems that talk
to each other over an API later. This is a deliberate application of
the ARIS/Jira/MS Project lesson (see Business Plan, Essential/Accidental
Complexity section) to Spadework's own architecture, made explicit
*before* building rather than discovered the hard way after: `Activity`
(miniProject) and `Issue` (miniJira) hold a direct relationship because
they share a schema, not because two separate systems agreed on a
contract. Feature *delivery* can still be staged — miniJira's core
ships before miniProject's — but the underlying system is singular from
day one.

## Suggested Django apps

- `boards` — Board, Column/Status models
- `issues` — Issue model, CRUD, ordering keys, priority tier, completion
  date
- `teams` — Team, TeamMembership models — new, added 15 Jul 2026
- `activities` — Activity, ActivityDependency, ScheduleBaseline,
  DecisionNode models (miniProject) — part of the same project from the
  start, even though its UI ships later in the build sequence; see
  `Spadework_miniProject_Spec_v1.md`
- `comments` — Comment model, tied to Issue
- `labels` — Label model, Issue↔Label M2M
- `accounts` — **separate copy, confirmed 17 Jul 2026** — starts from
  the same SimpleJWT + Djoser pattern as Riverside Club, but kept
  independent since this is a reusable tool, not tied to a specific
  project's auth
- Dedicated settings/admin app from day one, per your standing convention

## Rough data model sketch

- `Board` — name, description
- `Status` — board FK, name, order (fixed set for MVP, not user-editable)
- `Team` — name, description
- `TeamMembership` — team FK, user FK (through table, one user can
  belong to more than one team)
- `Issue` — board FK, status FK, title, description, priority (fixed
  tier — see Priority boxes above), team FK (nullable), assignee FK
  (nullable, must belong to `team` if both set), **target_completion_date**
  (nullable, user-set — when the team expects this done by),
  **actual_completion_date** (nullable, added 17 Jul 2026 — auto-set the
  moment an issue's status transitions to Done, editable afterward if
  the auto-captured date needs correcting; feeds Decision Node variance
  review in miniProject by comparing target vs. actual across allocated
  issues, not just at the Activity level), order key (fractional),
  created_at, updated_at
- `Comment` — issue FK, author FK, body, created_at
- `Label` — board FK, name
- `IssueLabel` — Issue↔Label through table

## Design principle: microcopy, not training

Per the broader "the tool is the training" positioning (see Business
Plan Section 3) — the sparse issue form and fixed columns need no
introduction, since the workflow itself teaches "no field exists that
isn't earning its place" just by being used. Keep it that way: resist
adding an onboarding flow or help guide as a substitute for keeping the
product itself simple enough not to need one.

## Planted teaching bugs (for later EPC tracer content — not to fix now,
to build in deliberately)

- Drag-drop race: two clients reorder the same column simultaneously —
  demonstrates the ordering-key collision problem directly
- Optimistic UI rollback: a card move that appears to succeed
  client-side, then fails server-side (e.g. a stale status) — teaches
  handling the rollback correctly rather than leaving the UI lying
- WebSocket reconnect desync: a client that drops connection mid-drag
  and reconnects — does it get the current board state, or a stale one?
- Comment ordering under concurrent posts — a simpler, second example
  of the same underlying class of bug as the drag-drop race, at lower
  stakes, useful as an earlier/easier episode before the harder one

## Suggested build sequence

Same "complete each module fully before moving on" rhythm as Riverside
Club:

1. Project scaffold — Django + DRF + Vue skeleton, settings/admin app,
   Docker Compose, Nginx, deploy pipeline (mostly reusable from
   Riverside Club/`emillar_v2` patterns). Includes creating the
   `activities` app's initial schema alongside `boards`/`issues` at this
   stage (empty of UI, but present in `INSTALLED_APPS` and migrations
   from the start) — per the one-project architecture principle above,
   not deferred until miniProject's own build begins.
2. Auth (reuse/adapt Riverside Club's SimpleJWT + Djoser setup)
3. Board + Status models, basic board view (no drag-drop yet, no
   real-time yet — just CRUD and a static column layout)
4. Teams + Team Membership — added 15 Jul 2026, sequenced before Issue
   CRUD since issue allocation depends on teams/members existing first
5. Issue CRUD — create/edit/delete, priority tier, team/assignee
   allocation, completion date, board-scoped
6. Comments
7. Labels + search/filter
8. Drag-and-drop reordering — fractional key implementation, plus the
   Priority-boxes sub-grouping within Todo
9. Real-time updates via Channels/Daphne — live board sync across clients
10. Deliberately wire in the planted bugs above, verify each is genuinely
    reproducible and traceable via the EPC tracer before considering the
    MVP done
11. miniProject's user-facing features (Activities, node/Gantt views,
    forward/backward pass, Decision Nodes) — see
    `Spadework_miniProject_Spec_v1.md` for full detail. Ships after the
    above, but builds on the `activities` schema already present since
    Module 1, not a retrofit.

## Timeline shape (not a commitment, just a working assumption)

- **Pre-op window (~4 weeks):** design-lock work, not build work —
  attention will be split with pre-op logistics regardless. Lock this
  spec fully (stack decisions, explicit MVP boundaries, module sequence,
  data model) the same way Riverside Club's spec was locked before
  building started. Also a good window for recording the already-planned
  Foundations videos (Gunicorn, TS, Tailwind, Nginx/Gunicorn/Daphne) —
  lower physical demand than sustained coding.
- **Post-op window (~6 weeks):** execution against the already-locked
  spec, module by module. Better suited to uneven energy/focus days than
  open-ended design decisions would be.
- Worth checking with your surgeon/physio on desk setup ahead of time
  (hip flexion angle restrictions in early recovery can affect seating
  position) rather than discovering it's uncomfortable a few days in.

## Open decisions (not blocking — settle during build)

**All open decisions resolved as of 17 Jul 2026 — this spec is fully
locked.**

**Resolved 17 Jul 2026:**
- ~~Whether a 4th status column (e.g. Blocked) is in MVP~~ — **yes,
  in MVP.** Todo / In Progress / Blocked / Done. Easy win, low
  implementation cost given `Status` was already a fixed-set model, not
  worth deferring.
- ~~Whether `accounts` is shared/reused from Riverside Club~~ —
  **separate copy.** miniJira/miniProject is a reusable tool, not tied
  to a specific project's auth setup — keeping `accounts` independent
  avoids coupling Tier 2's auth to Riverside Club's, even though both
  start from the same SimpleJWT + Djoser pattern.
- ~~Exact fractional-key scheme~~ — **hand-rolled**, not a library —
  more teachable, consistent with the ordering-key section above.
- ~~Completion date interpretation~~ — **both target and actual are in
  scope**, not an either/or — see the MVP scope and data model sections
  above.
  — affects whether it's user-editable at any time or gets set once
  automatically on move-to-Done
