# Spadework Master Baseline v1 — 10 July 2026

**Purpose of this document:** everything below is the settled state of
Spadework strategy as of this date. This is a deliberate freeze point —
from here forward, only *essential* variations to what's written here
should happen without a real reason. Everything else is a candidate for
a *later phase*, not immediate scope. See Section 10 for the explicit
parked list, and the governance rule at the very end.

---

**Companion document:** `Spadework_Business_Plan_v1.md` (15 Jul 2026) —
the commercial/strategic plan sitting above this baseline, formal enough
for evaluation by a future co-founder or early hire. Covers market
research (deployment-struggle evidence, PM-tool competitive landscape,
developer-education pricing comparables), the critical positioning
conclusion that Tier 2 must compete as *education with a real product
as proof*, not as a standalone PM-SaaS company, and an explicitly
incomplete financial framework awaiting real figures. Read that
document first for anyone evaluating Spadework from the outside; this
baseline remains the tactical/technical reference underneath it.

## 1. Strategic positioning

- **Tier 2 (commercial) is the actual flagship product**, not Tier
  1/Riverside Club. This is a deliberate pivot from earlier thinking,
  where `emillar_v2`/Riverside Club were the end commercial goal.
- **Tier 1 (free tier) and Riverside Club are the funnel and
  trust-builder** toward Tier 2 — their job is credibility, not being
  the commercial destination. This means Riverside Club's scope should
  stay disciplined: finished well, not over-invested.
- **`emillar_v2` is complete and in support mode.** It served its
  purpose as the original proof-of-concept/demo and real production
  system for Ewan Millar Ltd. Active feature development on it is done;
  only genuinely necessary support/maintenance continues (see Section
  9 for exactly what remains).
- **Standalone Foundations guides are a separate, dual-purpose
  investment**: genuine marketing reach (people who find Spadework via
  the topic itself, not searching for Spadework) *and* a reference
  resource for Riverside Club learners — not just top-of-funnel content
  with a side benefit.

---

## 2. Tier 1 — Riverside Club (baseline)

- **Stack:** Django 6 + DRF + SimpleJWT + Djoser + Channels/Daphne +
  Redis + Vue 3 + Vite + Pinia + Tailwind + TypeScript + PostgreSQL +
  Docker Compose + Nginx + DigitalOcean.
- **Structure:** 9 apps, 13-module build sequence, already locked.
  Preferred build rhythm: complete each module fully before moving to
  the next.
- **Positioning:** free tier / trust-builder, reframed around a
  bug-first narrative (failure → EPC trace → fix), not a general
  tutorial series.
- **Scope discipline going forward:** bring the current build to a
  genuine "finished for now" checkpoint. Do not keep expanding scope —
  anything beyond the locked 13-module sequence is a later-phase idea,
  not current work.
- **Prerequisite-checklist mechanism** (new, agreed this cycle): rather
  than embedding full Foundations guides inline in modules, each module
  intro carries a short bullet-point checklist of the 3-5 rules from
  the relevant guide. A learner who already knows the material reads
  three lines and moves on; one who doesn't clicks through to the
  standalone guide. Solves the "don't turn off people who already know
  some of this" concern at the course-structure level.

---

## 3. Tier 2 — "miniJira" (Kanban/Issue Tracker app) (baseline)

**Working name: miniJira.** Deliberate choice, not just a nickname — a
constant reminder that this is explicitly not a full-fat Jira
alternative. The "mini" is load-bearing; see MVP exclusions below.

Full detail lives in `Spadework_Tier2_Kanban_Spec_v1.md` — this section
is the summary of record.

- **Why this app, not another `emillar_v2`-style CRUD demo:** generates
  concurrency/state bugs (drag-drop races, optimistic UI rollback,
  WebSocket reconnect desync) — a richer, different EPC-tracer teaching
  category than `emillar_v2`'s data-shape bugs.
- **Stack:** identical to Riverside Club (see Section 2) — deliberate,
  for skill/content reuse across both.
- **MVP scope — in:** single board, fixed status columns, issue CRUD,
  comments, labels, basic search/filter, live updates via
  Channels/Daphne, drag-and-drop reordering.
- **MVP scope — explicitly out:** multi-project/workspaces, custom
  workflow states, epics/sprints/burndown/velocity, granular
  permissions, third-party integrations, notifications system, file
  attachments. The real risk here is scope-creeping into an actual Jira
  competitor — this exclusion list exists to be pointed back at when
  that temptation hits.
- **Ordering-key decision:** fractional/lexicographic keys (not integer
  resequencing) — more production-realistic, more concurrency-robust,
  and the key-generation problem is itself a good teaching moment.
  Deliberately built to be breakable under concurrency as planted
  content.
- **Planted teaching bugs:** drag-drop race (ordering-key collision),
  optimistic UI rollback failure, WebSocket reconnect desync, concurrent
  comment ordering (simpler/earlier example of the same bug class).
- **Build sequence (9 modules):** scaffold → auth → board/status models
  → issue CRUD → comments → labels/search → drag-drop (fractional keys)
  → real-time sync → planted bugs wired in and verified.
- **New this cycle — dual-approach demo, folded into Module 7
  (drag-drop):** build this feature both ways — a genuine, fair
  vibe/agentic-assisted pass *and* a fully disciplined,
  documented/tested/reviewed pass — as the live vehicle for the
  Tailoring Framework (Section 4) and the vibe-coding honesty piece
  (Section 6). Reuses already-spec'd planted-bug content rather than
  inventing a separate demonstration.
- **Simplified Gantt/planning tool — working name "miniProject":**
  parked as a candidate companion module, not committed. Same discipline
  as miniJira's MVP if it proceeds: finish-to-start dependencies only,
  no auto-rescheduling engine, visual dependency lines with manual bar
  adjustment. To be explored Monday/Tuesday next week, once the
  Docker/Nginx Foundations videos reach a good point — genuinely inside
  the pre-op design-lock window, not scope creep.
- **Companion tool: `consent` app** (see Section 7) is not part of the
  Kanban spec itself, but is available to drop into Tier 2 unchanged
  when needed.

---

## 4. The Tailoring Framework + Essential/Accidental Complexity (two
credentialed pillars, formalized this cycle)

**Pillar 1 — Tailoring (PMP):** covered below, unchanged from the
original entry.

**Pillar 2 — Essential vs. accidental complexity (Fred Brooks, "No
Silver Bullet," 1986), added this cycle:** essential complexity is
inherent to the problem and irreducible; accidental complexity comes
from tools/implementation choices and is avoidable. The founder's own
direct experience of ARIS/Jira/MS Project integrations failing is a
textbook case — three tools, three data models, none of that complexity
required by the actual work. This is the theoretical backbone for why
miniJira/miniProject exist, and pairs with Tailoring rather than
duplicating it: Tailoring decides *how much* process rigor a piece of
work needs; essential/accidental complexity explains *why* an
over-tooled stack actively harms even well-intentioned rigor.

**Positioning rule derived from this (applies to product, not
content):** miniJira/miniProject are never positioned against named
competitors (no "Jira alternative" framing) in product-facing material
— draft language: *"the tools to get from idea to delivery, without the
tool stack becoming the project."* Named competitors and real
integration-failure war stories remain fair game in *content*, since
that's genuine search intent and authentic storytelling — the rule is
name the pain in content, never frame the product against a competitor
in the product itself.

**Core idea (Tailoring specifically):** "horses for courses," not "one
size fits all," for vibe/agentic-assisted vs. fully disciplined
development — and this maps directly onto an existing, credentialed PMP
concept: **tailoring**
— deliberately adjusting process rigor to match a project's actual risk
profile, rather than applying one fixed process everywhere. This framing
matters because it turns "here's my opinion on AI coding" into
"here's recognized project management discipline applied to the
AI-coding question" — a stronger, more defensible position, and one that
reinforces Peter's own PMP study rather than being separate work.

**Decision criteria (first pass — refine, don't redesign, in later
phases):**

| Criterion | Low-rigor end (vibe/fast) | High-rigor end (disciplined) |
|---|---|---|
| Blast radius | Prototype, spike, internal tool | Production system touching money, customer data, compliance |
| Maintenance horizon | Throwaway / short-lived | Multi-person, multi-year maintenance |
| Reversibility of failure | Cosmetic bug | Data corruption, security hole, financial loss |
| Review capacity | Solo dev, no review | Team with real code review and CI |
| Time pressure vs. risk tolerance | Validate an idea fast | Being wrong is expensive |

**Why this appeals across all three target audiences at once:**
- **Solo developer** — permission to move fast where it's genuinely safe
  to, with explicit criteria for *when* that's true rather than always
  or never
- **Small agency** — language to justify to a client why one feature is
  quick-and-cheap and another needs the rigorous path
- **Large corporate** — plugs directly into governance frameworks
  they already recognize (PMP tailoring), rather than being "another AI
  coding opinion" that ignores how their compliance function works

**Content implications:**
- Feeds directly into the vibe-coding honesty piece (Section 6)
- Feeds directly into Tier 2 Module 7's dual-approach demo (Section 3)
- Worth its own standalone write-up/video eventually — parked as a
  distinct piece of content, not yet scripted

---

## 5. Foundations content series (baseline)

**Guiding principle:** any standalone guide that reaches people who
weren't specifically looking for Spadework — but land on it via the
topic itself — is a worthwhile marketing investment in its own right,
independent of conversion. Broad, topic-driven reach is the point.

**Branding rule:** standalone-first for public-facing titles/thumbnails
(zero Spadework branding, optimized for search/discovery). "Spadework
Foundations" exists only as connective tissue — a YouTube playlist name,
a description/end-card mention, a pinned-comment link — never in the
title itself.

**Guide list and status:**

| # | Guide | Status |
|---|---|---|
| 1 | Docker | Done |
| 2 | Nginx | Done |
| 3 | Terminal | Done |
| 4 | Gunicorn | Lesson brief written |
| 5 | TypeScript | Lesson brief + Vue demo files written |
| 6 | Tailwind | Lesson brief + Vue demo file written |
| 7 | Nginx + Gunicorn + Daphne (advanced/combined) | Lesson brief written — bare-metal-then-Docker structure |
| 8 | Cookie consent (PECR/UK GDPR + working code) | New, added this cycle — reusable `consent` app already built as the working example |

**Framing decision (applies to any future infra-adjacent guide, not just
#7):** bare-metal/SSH first, then Docker, for anything Riverside Club
actually runs in Docker. Reasoning: the tools are just Linux processes;
Docker only packages them. Teaching Docker-first risks making the tools
feel like "Docker magic." The Docker payoff only lands if the friction
it removes was genuinely felt first. Chaptered structure (raw, then
Docker) lets viewers who already know the raw tools skip ahead.

**Parked candidates, not committed:** Git/GitHub workflow standalone cut
(already covered by an existing curated guide, per Peter), Postgres
basics.

---

## 6. Content case studies / war stories (baseline — real incidents, not
constructed examples)

- **The Orphaned Script Block** (`Case_Study_Orphaned_Script_Block.md`)
  — an AI-assisted edit inserted a closing `</script>` tag mid-file,
  orphaning existing functions outside any script block. Passed diff
  review (each half looked correct in isolation), failed at build time.
  Named bug category: "orphaned block from a boundary-adjacent edit."
  Directly exemplifies applying diagnostic discipline to AI/vibe-coded
  output — a genuine same-night incident.
- **Restart vs. `--force-recreate`** — a real Nginx SSL crash loop where
  every individual ingredient (cert, mount, config) checked out
  correct in isolation, and the actual fix was recognizing that
  `restart` replays a bad container state while `--force-recreate`
  rebuilds fresh. Same "looks right in isolation, fails on whole-system
  state" shape as the script block incident — the two are natural
  companion pieces.
- **Vibe-coding honesty piece (new, this cycle):** a genuinely fair
  demonstration, not a rigged one — show vibe/agentic coding doing
  something it's legitimately good at (boilerplate, well-defined
  isolated functions), *then* where it quietly breaks (using the real
  orphaned-script-block incident, not a staged failure), *then* the
  diagnostic discipline that catches it. Ties directly to the Tailoring
  Framework (Section 4) and Tier 2 Module 7's dual demo (Section 3).

---

## 7. Reusable infrastructure already built (concrete deliverables, not
just plans)

- **`consent` Django app + Vue banner/store/script-gating composable**
  — built initially for `emillar_v2`, deliberately dependency-free so
  it drops unchanged into Riverside Club, Tier 2, and future
  customer/supplier portals. Becomes the working example the cookie
  consent Foundations guide walks through. Wiring into `emillar_v2`
  itself (settings.py, root urls.py, App.vue, main.js) still pending —
  needed files not yet supplied.
- **Deploy Bible** (`Deploy_Bible.md`) — the full, verified push/pull
  deploy runbook for `emillar_v2`, including the branch-check discipline
  learned this cycle, the `restart` vs `--force-recreate` distinction,
  and an appendix of exact real-output examples showing what to actually
  look for vs. what silently signals a problem.

---

## 8. Workplan / timeline (baseline)

Full detail in `Tier2_Workplan.md` and the accompanying Mermaid Gantt
chart. Summary:

- **Pre-op window (~4 weeks, provisional 10 Jul – 6 Aug):** design-lock
  work — finalize the Tier 2 spec's remaining open decisions, record the
  four remaining Foundations videos (Gunicorn, TypeScript, Tailwind,
  Nginx+Gunicorn+Daphne), bring Riverside Club to a genuine checkpoint,
  pre-op logistics (including a concrete question to surgeon/physio
  about desk/seating setup given hip flexion restrictions).
- **Surgery (~7 Aug, provisional)** + short recovery buffer, no work
  assumed.
- **Post-op window (~6 weeks):** execution against the already-locked
  spec, module by module, complete-before-moving-on. Front-loaded with
  lower-complexity modules; drag-drop (the heaviest module) sits
  mid-plan; final week reserved for wiring in and verifying the planted
  bugs.
- All dates provisional — adjust once the real surgery date is
  confirmed.

---

## 9. `emillar_v2` status (baseline — essentially closed)

**Done, verified working in production:**
- Full inventory restructure (8-table Stock schema) merged to `main`
- `createItem`/`updateItem`/`saveGemDetail` all correctly targeting
  Stock/StockSupplier/StockParams/StockPrice endpoints
- Item SKU autonumbering (`ItemSkuSequence`) — backend complete,
  frontend (`ItemFormModal.vue`) wired in
- SO and PO browser-print buttons — confirmed working in production,
  including actual printed output, on 10 Jul 2026
- Default PO currency corrected to GBP
- Server correctly on `main` branch (resolved a real, costly branch
  mismatch this cycle)

**Explicitly parked, not current work:**
- `CompanySettings` + lookup table extraction into a dedicated settings
  app (migration `state_operations` surgery — do as an isolated
  branch/PR when convenient, half-day to full-day estimate)
- Defaults/settings table for frontend defaults (default_currency etc.)
  — folds into the CompanySettings extraction work
- Old `ReferenceSequence` model cleanup in `inventory/models.py`
- TOTP stateless fix — designed, not yet deployed
- `revolution_pg` Layer 4 serializer paste errors — need rechecking
- `PurchaseOrderDetailView.vue` — confirmed orphaned (unrouted via
  normal navigation), same category as the old `ReferenceSequence`
  panel — cleanup candidate, not urgent
- Master data quality session with Ewan and Rebecca — outcomes not yet
  known/logged

---

## 10. Master parked-items list (everything, consolidated)

*This is the deliberate "not now" list. Nothing here is forgotten —
it's parked on purpose. Pull from this list for later phases rather
than letting any of it creep into current scope.*

- CompanySettings/lookup table extraction (`emillar_v2`)
- Old `ReferenceSequence` panel cleanup (`emillar_v2`)
- TOTP fix deployment (`emillar_v2`)
- `revolution_pg` Layer 4 rechecking
- `PurchaseOrderDetailView.vue` orphan cleanup
- Customer/supplier portals (post-core-app, PWA before native mobile)
- Simplified Gantt/planning tool ("miniProject" — Tier 2 candidate
  companion module, to explore Mon/Tue next week)
- Git/GitHub workflow standalone Foundations cut
- Postgres basics Foundations guide
- Tailoring Framework standalone write-up/video
- `consent` app wiring into `emillar_v2` (pending settings.py/urls.py/
  App.vue/main.js)
- Thumbnail template / intro bumper visual design for Foundations series
- Whether a 4th Kanban status column (e.g. Blocked) is MVP or fast-follow
- Whether Tier 2's `accounts` app is shared with Riverside Club or a
  separate copy
- Fractional ordering key: hand-rolled vs. existing library decision
- **Business plan Section 10 (financial framework)** — needs real
  cost/revenue/runway figures and ideally an accountant's input before
  the plan is shown externally
- **Tier 2 pricing model decision** — subscription vs. one-time vs.
  hybrid; currently only a comparable-market band ($18-49/month), not a
  committed price
- ICP prioritization among Tier 2's three buyer segments (solo
  developer / small agency / large corporate)
- Whether/when the Tailoring Framework becomes its own product line
  vs. staying purely content
- Hiring sequencing and compensation structure (deferred to the
  post-cycle honest review, per the business plan's Section 9)

---

## 11. Governance rule from this point forward

This document is the baseline. From here:

- **Essential variations** — genuine bugs, blocking dependencies, or
  something that makes an already-committed piece of work impossible as
  specified — get addressed directly, updating this document afterward.
- **Everything else** — new ideas, scope expansions, "while we're at it"
  additions — get added to Section 10's parked list, not built now.
- If something parked starts to feel urgent, that's a signal to
  explicitly re-open and re-baseline that one item, not to quietly
  expand current scope.
