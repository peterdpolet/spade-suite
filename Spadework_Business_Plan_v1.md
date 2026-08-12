# Spadework — Business Plan v1

**Prepared:** 15 July 2026
**Status:** Working document, formal enough for evaluation by a future
co-founder or early hire. Financial projections section is explicitly a
framework awaiting real figures — see Section 10.

---

## 1. Executive Summary

Spadework is a developer-education business built around a deliberately
different premise from most coding-education platforms: teaching through
**real production bugs, traced and fixed with real diagnostic
discipline**, rather than idealized happy-path tutorials. It operates
across two tiers:

- **Tier 1 (free):** Riverside Club — a bug-first tutorial series built
  on a real, working application — plus a growing library of standalone
  "Foundations" guides (Docker, Nginx, TypeScript, Tailwind, cookie
  consent, etc.) that reach people via the topic itself, not by
  searching for Spadework.
- **Tier 2 (commercial):** a paid tier built around **miniJira**, a
  deliberately-scoped, teaching-first Kanban/issue tracker, and its
  planned companion **miniProject**, a simplified Gantt tool. The
  product is the *education*, not the software — miniJira is a proof-of-
  work vehicle and teaching artifact, not a standalone SaaS competing
  with Linear or Jira.

Tier 1 is the funnel and trust-builder; Tier 2 is the actual commercial
product. This is a deliberate, recent repositioning — earlier thinking
treated Tier 1 as the end goal; it now exists to build the credibility
that makes Tier 2 conversions honest rather than cold.

A second emerging pillar, not yet fully scoped, is a **"tailoring"
framework** — applying PMP's own concept of matching process rigor to
project risk, specifically to the vibe/agentic-coding-vs-disciplined-
development question. This has genuine cross-audience appeal (solo
developers, small agencies, large corporates) and ties Spadework's
content directly to a credentialed, recognized methodology rather than
an opinion piece on AI coding.

---

## 2. The Problem / Market Opportunity

**Deployment and DevOps struggle is real, documented, and not limited to
beginners.** A Vanson Bourne survey found that
39% of a 40-hour workweek is typically spent on manual DevOps tasks that
respondents themselves say are largely wasted, with 76% citing waiting for pipelines, 74% waiting for
builds/tests, and 71% citing pipeline setup/maintenance/debugging as top
frustrations. This isn't a junior problem: a 2024 study of 2,000+ IT professionals found 93% of
platform engineering teams — people whose actual job is managing this
infrastructure — face persistent Kubernetes complexity challenges.

**Project/reporting overhead is separately, enormously documented.**
The average knowledge worker spends 15-17 hours
per week in meetings, and Gallup
found 60% of knowledge-worker time goes to "work about work" — status
chasing, unnecessary meetings, tool-switching. Separately,
71% of companies believe employees need more
project management skills and roughly a fifth of individual
contributors don't feel comfortable with their own PM tooling. (Honest
note: no single study directly proves the causal chain "meetings go to
the wrong topic *because* of tool illiteracy" — the above are two
well-documented, adjacent problems, presented as such rather than as one
proven causal claim.)

**Why existing tools haven't fixed this — the actual opening.** The PM
software market is large and mature (exceeding $10 billion in 2026) and full of genuinely good
"simple Jira" alternatives — Linear, Plane, Shortcut, Height, Huly,
GoodDay. None of them teach. They assume competence and sell speed to
people who already have it. The actual gap isn't "a better tool" — it's
**a tool built as, and alongside, the education that produces the
competence to use tooling discipline correctly in the first place.**
That's a materially different competitive category than "another PM
SaaS company," and it's why Section 4 concludes Spadework should not
compete head-to-head against Linear/Plane on tool features.

---

## 3. Product & Positioning

### Tier 1 — free, funnel
- Riverside Club: bug-first tutorial series, real application, real EPC
  (error → pattern → cause) tracing
- Foundations guides: standalone, discoverable via search, zero
  Spadework branding in titles — genuine top-of-funnel reach, valuable
  independent of conversion
- Job: credibility and reach, not revenue

### Tier 2 — commercial
- **miniJira**: deliberately-scoped Kanban/issue tracker (see
  `Spadework_Tier2_Kanban_Spec_v1.md` for full technical spec). Chosen
  specifically because it generates concurrency/state bugs (drag-drop
  races, optimistic UI rollback, WebSocket desync) — a richer teaching
  category than data-shape bugs.
- **miniProject** (parked candidate): simplified Gantt tool, same
  disciplined-scope philosophy — finish-to-start dependencies only, no
  auto-rescheduling engine.
- **The "mini" is deliberate positioning, not just naming** — an
  explicit, constant signal that these are not attempts to rebuild
  Jira or MS Project, which matters both technically (keeps scope sane)
  and commercially (avoids inviting direct comparison to well-funded
  incumbents).
- Job: the actual revenue product, and the credible proof-of-work that
  differentiates Spadework from "another course platform."

### The Essential/Accidental Complexity Framework (new — second credentialed
pillar alongside Tailoring)

Fred Brooks's 1986 essay "No Silver Bullet" distinguishes **essential
complexity** — inherent to the problem itself, irreducible — from
**accidental complexity** — introduced by tools and implementation
choices, theoretically avoidable. This is the theoretical backbone for
why miniJira/miniProject exist at all: the well-documented failure mode
of linking ARIS/Jira/MS Project together (drawn from the founder's own
direct experience) is a textbook case of accidental complexity actively
obscuring the actual drivers of a project — three tools, three data
models, three sources of truth, none of it required by the underlying
work.

This pairs with, rather than duplicates, the Tailoring Framework:
**tailoring decides how much process rigor a given piece of work
actually needs; essential/accidental complexity explains why an
over-tooled stack actively harms even well-intentioned rigor.** Together
they give Spadework two independent, credentialed reference points
(PMP methodology and a foundational software-engineering essay) rather
than one opinion repeated twice.

**Positioning implication — deliberately not framed against named
competitors:** miniJira/miniProject are never positioned as "a Jira
alternative" or "simpler than X" in product-facing material (landing
page, in-app copy, marketing headlines). That framing invites a
feature-by-feature comparison the product will lose on depth every
time, and implicitly casts it as a lesser version of something else.
Instead, the positioning is built around *removing accidental
complexity* on its own terms — draft language, not final: **"the tools
to get from idea to delivery, without the tool stack becoming the
project."**

**Important nuance — this rule applies to product positioning, not
content.** War-story content (the ARIS/Jira/MS Project integration
failure, the real production incidents already used elsewhere in
Spadework's content strategy) can and should name real tools and real
pain, since that's genuine search intent and an authentic story
consistent with Spadework's existing differentiator. The rule is: name
the pain in content, never frame the product against a competitor.


Applies PMP's tailoring concept to the vibe/agentic-vs-disciplined
development question, with concrete decision criteria (blast radius,
maintenance horizon, reversibility of failure, review capacity, time
pressure vs. risk tolerance). Appeals across solo developer, small
agency, and enterprise audiences simultaneously because each gets a
different, real use for it (permission to move fast safely; client
justification language; governance-framework alignment). Currently
content-stage, not productized — worth its own line in future roadmap
discussions with a co-founder/hire.

---

## 4. Competitive Landscape

**Direct PM-tool competitors (Linear, Plane, Shortcut, Huly, Height,
GoodDay, ClickUp, Asana, Monday.com):** mature, well-executed, in some
cases well-funded. Linear alone has become the
default choice at hundreds of fast-growing startups.
**Conclusion: do not compete here as a standalone tool company.**
miniJira's value is as a teaching artifact bundled with education, not
as a fourth "simple Jira" entrant fighting on features/speed against
products that have already won that fight.

**One real tailwind, not to be over-relied on:** Atlassian's Jira Data Center end-of-life (announced Sept 2025,
full sunset by March 2029) is forcing a real, dated wave of teams to
evaluate alternatives. Useful context for content timing,
not a direct sales opportunity for miniJira itself.

**Developer education competitors (Frontend Masters, Scrimba,
Educative, Codecademy, Udemy, freeCodeCamp):** pricing clusters tightly at $18-49/month across the
category. Differentiation among them is curriculum format and
curation, not price. **Spadework's differentiation vs. this group:**
bug-first, real-production teaching methodology (not idealized
tutorials) and a genuine working product as the vehicle, not just
video content. None of the researched competitors combine "learn to
code" with "here is a real, production-grade tool you helped build and
can point to."

**Combined conclusion:** Spadework's actual competitive position is
the intersection of two categories neither incumbent fully occupies —
developer education with a real shipped product as proof, positioned
explicitly against the "vibe coding vs. disciplined delivery" question
that neither the PM-tool vendors nor the education platforms are
addressing directly.

**Refinement (this cycle):** product-facing positioning should not name
Jira, Linear, or any competitor at all — see Section 3's
essential/accidental complexity framework for the reasoning. Named
competitors and specific integration-failure war stories remain fair
game in *content* (videos, case studies), where they serve real search
intent and authentic storytelling, but the product itself is positioned
on its own terms, not as an alternative to anything.

---

## 5. Target Customers

**Individual learners (Tier 1 → Tier 2 funnel):** developers who
weren't looking for Spadework specifically, arrive via a Foundations
guide topic, and convert into Riverside Club / Tier 2 over time.

**Tier 2 commercial buyers — three segments, per the Tailoring
Framework's own audience mapping:**
- **Solo developers:** want permission and criteria for moving fast
  safely, plus a credible teaching product to learn from
- **Small agencies:** want language and criteria to justify rigor
  decisions to clients
- **Large/enterprise organizations:** want something that plugs into
  governance frameworks they already recognize (PMP tailoring), not
  another isolated "AI coding tips" resource

*(Note for a co-founder/hire conversation: exact ICP prioritization —
which of these three to go after first — is not yet decided and is a
genuinely open strategic question, not an oversight.)*

---

## 6. Business Model & Monetization Framework

**This section is a framework with real comparables, not a set of
committed prices — pricing decisions are explicitly not yet made (per
direct confirmation from the founder as of this document's writing).**

- **Tier 1:** free, always. No monetization intent — its ROI is
  reach and funnel conversion, not direct revenue.
- **Tier 2 pricing anchor:** the developer-education comparable set
  (Section 4) clusters at $18-49/month. A Spadework Tier 2 subscription
  sitting in or near that band is the most defensible starting
  hypothesis, given it's competing for the same buyer attention and
  budget line as those platforms — but this needs to be stress-tested
  against Spadework's actual differentiation (bundled real product,
  bug-first methodology) rather than assumed by default.
- **Open questions requiring a real decision, not present in this
  document:** subscription vs. one-time purchase vs. hybrid (e.g. free
  core content + paid deep modules, similar to Scrimba's free-tier-then-
  paywall model); whether miniJira/miniProject themselves ever carry a
  separate SaaS price if usage outgrows the "teaching artifact" framing;
  enterprise/team pricing for the large-corporate segment specifically,
  given that segment's willingness to pay is structurally different
  from individual learners.

---

## 7. Go-to-Market

Already substantially built out in existing Spadework planning
documents (`Spadework_Foundations_Content_Plan.md`,
`Spadework_Master_Baseline_v1.md`) — summarized here for a co-founder/
hire audience:

- Standalone Foundations guides, zero Spadework branding in
  public-facing titles/thumbnails, "Spadework Foundations" as
  connective tissue only (playlist, description, pinned comment)
- Guiding principle: any guide reaching people who weren't specifically
  searching for Spadework is a worthwhile investment independent of
  conversion — broad reach is the point, not just a funnel side-effect
- Real, documented production incidents (the orphaned script block, the
  Nginx restart-vs-recreate crash loop) used as genuine case-study
  content rather than constructed examples — a differentiator in
  authenticity that's hard for competitors to fabricate
- Bare-metal-then-Docker framing principle for infrastructure guides,
  chaptered so experienced viewers can skip ahead

---

## 8. Product Roadmap

Full detail in `Spadework_Tier2_Kanban_Spec_v1.md` and
`Tier2_Workplan.md`. Summary for this audience:

- **Now:** `emillar_v2` complete and in support mode — served its
  purpose as proof-of-concept and real production system
- **Pre-op window (~4 weeks):** finalize Tier 2/miniJira spec's open
  decisions, produce remaining Foundations videos, bring Riverside Club
  to a genuine checkpoint
- **Post-op window (~6 weeks):** execute miniJira's 9-module build
  sequence against the locked spec
- **Parked, explicitly not committed:** miniProject (Gantt companion),
  to be explored once Foundations content reaches a good point

---

## 9. Team & Resourcing

**Current state: solo.** All work to date — technical build,
content strategy, deployment operations, this business plan — has been
done by one person.

**The "bring in people" question, addressed honestly:** this was
explicitly deferred until after an honest review at the end of the
pre-op/post-op cycle (~10 weeks from mid-July 2026), contingent on
cash flow. This document doesn't pre-empt that review, but does note,
for a prospective co-founder/hire's benefit, the likely shape of future
need based on what's been built so far:

- **Content production** (video editing, thumbnail/visual design) is
  the most mechanically time-consuming piece not requiring deep
  technical judgment — a plausible first hire/contractor role if cash
  flow allows before a technical co-founder is needed
- **A technical co-founder or senior hire** would matter most once
  Tier 2 development needs to run in parallel with content production
  and business development — not needed for the current single-person
  execution of the locked pre-op/post-op plan
- **Sales/business development for the enterprise segment**
  specifically (Section 5) would be a distinct, later need if that
  segment is prioritized

*(Compensation, equity, and role-specific expectations are deliberately
not addressed in this version — a real conversation with a specific
prospective person, not a template value.)*

---

## 10. Financial Plan — FRAMEWORK ONLY

**This section is intentionally incomplete.** Populating it with
invented figures would make the document look more finished while
making it less honest — exactly the wrong trade-off for something
meant to be evaluated by a real prospective co-founder or hire. The
founder should complete this section with real numbers before this
document is shared externally. This is not financial advice, and
input from an accountant is worth getting before finalizing anything
here.

**Costs to quantify (structure, not numbers):**
- Hosting/infrastructure (DigitalOcean droplets, domains — likely
  already known from current `emillar_v2`/Spadework running costs)
- Tooling/software subscriptions
- Content production costs (equipment already owned per prior
  context — autocue, camera — so likely low marginal cost per video)
- Time cost — the founder's own time is the largest real input and
  should be valued explicitly, not treated as free, even pre-revenue

**Revenue to project (structure, not numbers):**
- Tier 2 subscriber count assumptions at various stages, cross-
  referenced against the $18-49/month comparable band (Section 6)
  once a real price point is chosen
- Realistic Tier 1 → Tier 2 conversion rate assumption (industry
  comparables for free-to-paid content platform conversion should be
  researched specifically before this is filled in — not yet done in
  this document)

**Runway:**
- Current savings/runway available to fund the pre-op/post-op period
  and beyond, until Tier 2 revenue (if any) becomes material
- The hip replacement recovery timeline (Section 8) is a real
  constraint on capacity during part of this runway period, worth
  factoring explicitly rather than assuming constant output

---

## 11. Risks & Mitigations

| Risk | Mitigation already in place / worth strengthening |
|---|---|
| Competing head-on with well-funded PM tools | Explicitly avoided by positioning (Section 4) — worth stress-testing with a co-founder/hire before any pivot toward "selling miniJira as a tool" |
| Tier 2 scope creep (building a real Jira/MS Project) | MVP exclusion list already locked in the Tier 2 spec; "mini" naming is a deliberate constant reminder |
| Solo-founder capacity, especially during recovery period | Pre-op/post-op plan already accounts for this explicitly; honest review point built in rather than assumed away |
| Pricing set without real market-testing | Section 6 flags this as genuinely open; recommend validating against actual target-audience willingness-to-pay before committing, not just competitor anchoring |
| Content strategy dependent on one person's voice/delivery | Real risk for a co-founder/hire to weigh — no mitigation currently in place; worth an honest conversation rather than a false reassurance here |

---

## 12. Milestones & Decision Points

- **~10 weeks from mid-July 2026** (end of pre-op + post-op windows):
  honest review of progress, cash flow, and whether/what kind of
  hiring makes sense — already planned, not new
- **Tier 2 spec's remaining open decisions** (4th Kanban column,
  `accounts` app sharing, ordering-key implementation approach) — to
  be resolved during the pre-op window, per the Tier 2 spec document
- **Pricing decision** (Section 6) — not yet scheduled; recommend
  attaching a real decision date rather than leaving indefinitely open

---

## 13. Explicitly Open Items (for a real co-founder/hire conversation,
not resolved unilaterally in this document)

- ICP prioritization among the three Tier 2 buyer segments
- Actual pricing/monetization model
- Whether/when to formalize the Tailoring Framework as its own
  product line vs. purely content
- Hiring sequencing and compensation structure
- Whether miniProject proceeds at all
