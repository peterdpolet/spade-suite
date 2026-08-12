# Spadework Tier 2 — miniProject Spec v1

**Working name: "miniProject"** — same deliberate naming principle as
miniJira: a constant reminder this is not an attempt to rebuild MS
Project. **Companion document:** `Spadework_Tier2_Kanban_Spec_v1.md`
(miniJira). Together these form "the miniPM suite."

**Status: LOCKED 15 Jul 2026, refined 16 Jul 2026 (Decision Nodes
mechanism added — see below; this is a refinement of how the already-
locked forward/backward pass gets triggered, not new feature scope).**
Previously a parked candidate — now a committed, in-scope part of
Tier 2, with the feature set below being the complete list. No further
additions without explicitly reopening this document.

## A note on scope, since this reverses an earlier recommendation

Earlier guidance on this tool explicitly recommended against building
an auto-rescheduling engine, for good reason: that recommendation was
about an **open-ended, continuously-live constraint solver** — the
MS Project-style system that has to cascade changes in real time,
handle resource leveling, support multiple dependency types (SS/FF/SF
plus lag), and reconcile manual overrides against recalculated dates on
the fly. That's genuinely unbounded, fuzzy scope, and still correctly
excluded here.

**What's now locked in is different in kind, not a reversal of that
reasoning:** a classic, well-defined, **on-demand** Critical Path Method
calculation — forward pass, backward pass, float — over a fixed
finish-to-start dependency network. This is two linear passes over a
DAG doing simple max/min arithmetic, not a live solver. It's bounded,
textbook, and genuinely strong content for teaching real graph/tree
traversal on a practical problem — the reason it's back in scope.

## MVP scope

**In scope:**
- **Two display modes, toggleable** — a Gantt bar-chart view and a
  node-based network diagram view (Activity-on-Node style: boxes for
  activities, arrows for finish-to-start dependencies), both rendering
  the same underlying schedule data
- **Activities** — the core planning unit, each with a planned
  duration and (once work has actually started/finished) an actual
  duration, for plan-vs-actual comparison
- **Finish-to-start dependencies only** (already established
  principle, carried over unchanged) — no start-to-start, finish-to-
  finish, start-to-finish, and no lag/lead time
- **Allocating miniJira issues to activities** — the integration seam
  between the two tools: an activity can have one or more miniJira
  issues attached, representing the actual granular work that makes up
  that activity
- **Forward pass** — Early Start (ES) and Early Finish (EF) for every
  activity, computed in topological order
- **Backward pass** — Late Start (LS) and Late Finish (LF) for every
  activity, computed in reverse topological order
- **Float/slack** — LS − ES (equivalently LF − EF) per activity; zero
  float identifies the critical path
- **Dependency cycle validation** — the dependency graph must be
  validated as a genuine DAG *before* either pass runs; a cycle must be
  detected and rejected/flagged clearly, not silently produce garbage
  dates. This is a real requirement, not an edge case to skip.

## Decision Nodes — how deviation from plan gets handled (added 16 Jul
2026, refines the "on-demand, not live" principle above)

**The problem this solves:** auto-rescheduling assumes tracking
accuracy that rarely exists in practice — people can't record progress
precisely enough for continuous automatic recalculation to stay
meaningful, and within a few iterations the "plan" and what's actually
driving the work quietly diverge. This isn't just a design preference —
it's PMBOK's own formal position: a schedule baseline is the approved
version of a schedule model that can be changed only through formal
change control procedures, and the live schedule may drift, but the
baseline itself moves only on a deliberate, approved decision, keeping
prior versions for reference rather than silently overwriting them. A
10%+ variance is a commonly used trigger threshold for when that formal
review should actually happen, worth adopting as a starting default
here rather than leaving it as an unbounded judgment call.

**Mechanism:**
- Activities record `actual_duration` as work happens — this **never**
  automatically triggers recalculation of dates elsewhere in the
  schedule.
- The forward/backward pass runs against one specific, named baseline
  at a time — recorded actuals sit visibly alongside the plan (variance
  is visible) but don't feed back into it on their own.
- A **Decision Node** is an explicit, user-triggered event: review the
  current variance, write a short rationale, and generate a **new
  baseline** — the forward/backward pass re-runs using updated
  durations for remaining activities, becoming the new active plan.
  The prior baseline is kept, not discarded.
- This is a deliberate, minimal narrowing of the "no baseline
  snapshots/versioning" exclusion below — just enough history to make a
  Decision Node meaningful (what changed, why, from what), not a full
  baseline-comparison/EVM reporting suite.

**Data model addition:**
- `ScheduleBaseline` — board reference, label, created_at, based_on FK
  (prior baseline, nullable for the first), is_active (only one active
  baseline drives the live view at a time)
- `DecisionNode` — board reference, triggered_by FK (user), created_at,
  rationale (free text), resulting_baseline FK (the new
  `ScheduleBaseline` it produced)
- The forward/backward pass (below) always runs scoped to a specific
  `ScheduleBaseline`, never globally

## Revised scope exclusion (supersedes the blanket exclusion below)

**Correction to the original reasoning (16 Jul 2026):** the initial
"no baseline snapshots/versioning" exclusion was aimed at the wrong
target. The actual thing to avoid was always auto-scheduling — an
unbounded, continuously-live recalculation engine — not the ability to
track back through previous plan versions to make a decision or
rebaseline. That tracking-back capability is genuinely simple to build
(closer to copy-on-write than reconciliation — snapshot the current
state immutably, point a new row back at it) and was never the actual
risk. It got excluded by an overly broad first pass, not by a real
complexity concern. **Baseline snapshots/versioning are fully in
scope**, not a narrow grudging exception — Decision Nodes are exactly
this mechanism.

**What remains genuinely, separately excluded** — not because of the
original (mistaken) reasoning, but because it's a real, distinct,
heavier analytical layer on top of version history rather than what's
needed to demonstrate the core concept: a full baseline-comparison
reporting UI, Earned Value Management calculations (SV/SPI/CPI), or
trend analytics across multiple baselines.

**Explicitly excluded from MVP:**
- Resource leveling / resource-constrained scheduling
- Any dependency type beyond finish-to-start; no lag/lead time
- Live, continuous auto-rescheduling as data changes — recompute is
  on-demand (e.g. a "Recalculate" action), not a background process
- Multiple calendars / non-working-day exceptions
- Baseline comparison *reporting* (dashboards, EVM metrics like
  SV/SPI/CPI) beyond what a Decision Node needs to function — see the
  narrowed exclusion above
- Multi-project scheduling (mirrors miniJira's single-board scope)

## Architecture principle: one project, not two integrated services
(locked 17 Jul 2026 — see `Spadework_Tier2_Kanban_Spec_v1.md` for the
full statement)

miniJira and miniProject share one Django project and one database from
the first migration — this is a deliberate application of the
ARIS/Jira/MS Project lesson to Spadework's own architecture, decided
*before* building rather than discovered afterward. `ActivityIssue`
below is a normal Django through-table within a single schema, not an
API contract between separate systems. Only the *feature rollout* is
staged (see sequencing note at the end of this document) — the
underlying system is singular throughout.

## Data model sketch

- `Activity` — board/project reference, name, planned_duration,
  actual_duration (nullable), computed fields: early_start,
  early_finish, late_start, late_finish, float (these four are
  recomputed on demand, not stored as the source of truth — store the
  *inputs*, treat the schedule outputs as derived)
- `ActivityDependency` — predecessor FK, successor FK (both → Activity),
  enforced finish-to-start only, no type field needed since it's the
  only supported type
- `ActivityIssue` — Activity↔Issue (miniJira) through table — the
  cross-tool integration link

## The forward/backward pass algorithm — design notes

All steps below run scoped to one specific `ScheduleBaseline` — never
across baselines, and never automatically triggered by an
`actual_duration` update (see Decision Nodes above).

1. **Validate the graph is a DAG first.** Attempt a topological sort
   (Kahn's algorithm is a natural fit — repeatedly remove nodes with no
   incoming edges). If any activities remain un-orderable once no more
   nodes can be removed, that's a cycle — reject clearly, name which
   activities are involved if possible, don't proceed to either pass.

2. **Forward pass**, walking activities in topological order:
   - `ES = max(EF of all predecessors)`, or `0` if no predecessors
   - `EF = ES + planned_duration`

3. **Backward pass**, walking activities in *reverse* topological
   order:
   - `LF = min(LS of all successors)`, or `= project's overall EF`
     (the max EF across all activities with no successors) if the
     activity has no successors itself
   - `LS = LF - planned_duration`

4. **Float**, per activity: `LS - ES` (or equivalently `LF - EF`).
   Activities with float `== 0` are on the critical path.

This is intentionally the whole algorithm — no resource leveling, no
calendar exceptions, no lag. Recompute on demand rather than live, per
the excluded-scope list above.

## Design principle: microcopy, not training

Per the broader "the tool is the training" positioning — the workflow
itself (Decision Nodes gating any plan change) needs no introduction,
but a few PMBOK terms the UI necessarily surfaces (float, critical
path, Decision Node) should carry a one-line contextual explanation on
hover, exactly where they appear. Not a separate guide or onboarding
flow — the explanation lives in the interface itself, at the point of
use.

## Teaching hook

This is a genuinely strong vehicle for real tree/graph-structure
processing content: topological sort, cycle detection, and two-pass DAG
traversal, applied to something immediately practical rather than an
abstract CS-exercise graph. Worth its own dedicated content piece once
built, separate from the miniJira EPC-tracer bug content — this is
"here's a real algorithm, here's why it's structured this way" content,
a different teaching mode than the bug-first material.

**Second, independent hook (Decision Nodes):** most mainstream PM
tooling's auto-rescheduling quietly works around PMBOK's own formal
change-control methodology rather than implementing it — a sharp,
credentialed angle for content that isn't just "we chose not to build
auto-rescheduling," but "here's the industry's own standard practice,
and here's how mainstream tools engineer it away by default."

## Build sequencing note (feature delivery, not system architecture)

The underlying system is one project from the first migration (see
Architecture principle above) — this note is about UI/feature rollout
order only. Since `ActivityIssue` references miniJira's `Issue` model,
miniProject's *user-facing features* naturally land after miniJira's
core (through at least Issue CRUD) rather than in parallel — but the
`activities` app itself, and its relationship to `issues`, should be
part of the initial schema design, not retrofitted once miniJira
"exists." Exact rollout sequencing to be folded into the overall Tier 2
module plan.
