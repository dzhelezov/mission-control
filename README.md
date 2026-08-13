# mission-control

A minimal, reproducible two-tier agent orchestration: a human-driven **laptop gateway** + a 24/7
autonomous **remote resident session**, synced through GitHub-native primitives (issues as
directives, a pinned journal issue, PRs as work products).

**Clone it, open Claude Code in it, say "set me up" — `CLAUDE.md` is the installer, doctor, and
manual.** Already running something? Say **"adopt this deployment"** instead — `playbooks/adoption.md`
compares an existing loop against the kit and produces a ranked migration, without installing anything. `orchestration.example.toml` holds the configuration as layers of data: a **harness**
catalog (how a model is reached and who pays), a **pool** catalog (what runs out, when, and what it
takes down with it), a **model** catalog (taste/cost/intelligence), a **role** schema (multi-seat
committees, a brain+hands implementation pair, explicit escalation), a **dispatch** policy, and the
**coded routines** that keep all of it current — plus guardrails.

## Harness-agnostic, provider-agnostic

Roles name models; models name pools; pools name harnesses. Nothing downstream hardcodes a vendor.
Two harnesses ship configured:

- **[prime-agent](https://github.com/PrimeIntellect-ai/prime-agent)** — the default. One
  model-facing tool (a persistent IPython kernel), ~20 providers, daemon-backed resident sessions,
  persistent goals, native cron schedules, heartbeats, autonomous quality gates, recursive `rlm()`
  subagents, and a continual harness that stores the roster as refinable specs.
- **Claude Code** — retained for Anthropic models only, because it is the only harness where they
  draw on **Claude Pro/Max plan limits** instead of per-token extra usage. prime-agent says so
  itself (`auth-flows.ts`), so `bin/agent` refuses to route around it.

First-class seats out of the box, grouped by what runs out: **Opus 5** and **Fable 5** (Claude
subscription — *rate*) · **GPT-5.6 Sol** (ChatGPT subscription via the `openai-codex` provider —
*rate*, own clock) · **Qwen3.8 Max** (prepaid vendor token-plan — *tokens*, own clock) · **Kimi K3**,
**GLM 5.2** and **DeepSeek V4 Flash** (metered credit — *dollars*). Swap any row; the roles follow.

## Built to survive its own model dying

An autonomous loop fails *quietly* — no user is staring at a blank screen. So continuity ships in
the box, not as an exercise:

- **Fallback ladder** — the primary is retried every run and falls through to progressively cheaper,
  independently-billed seats, ending at a flash-class model at cents per run. Per-invocation and
  never sticky, so the loop returns to the good seat by itself when quota resets.
- **Three-leg dead-man** — the loop writes a heartbeat *even on failure*; an off-box job parses it
  strictly and fails closed; a local sidecar covers wedged-but-alive.
- **Perception that cannot lose work** — full enumeration with a per-item disposition and an
  asserted count, because a "what changed" sweep makes an ignored item invisible forever.

`playbooks/continuity.md` is the operational core: every rule in it is traced to the outage or wrong
decision that produced it, including the probe shape that certifies a dead model as healthy and the
five separate sensors that once read green through a real failure.

## Cost, skill and quota are three separate budgets

Most setups either run everything on the best model — burning a subscription's *rate* cap on
boilerplate, so the judgment call hits a wall later — or run everything on the cheapest, and ship
taste-critical work at bargain quality. `playbooks/dispatch.md` treats them as three axes:

- **Three scarcities, not one.** Subscriptions run out of *rate*, prepaid plans run out of *tokens*,
  metered credit runs out of *dollars* and never resets. Pools declare `scarcity`, `resets`, and
  `blast_radius`, because **a fallback that doesn't cross the axis isn't a fallback** — two seats on
  the same subscription go dry in the same hour.
- **Cheap seats protect the caps.** Pushing volume to a $0.09/M model isn't mainly about the dollars;
  it's about the weekly allowance still being there when something needs judgment.
- **Quota is dynamic, so don't probe — fall through.** Trying a seat is free when it works, and a
  probe against a thinking model certifies dead seats as healthy.
- **It goes stale, so a routine re-derives it.** `[dispatch]` holds the policy and the role table is
  the derived answer — refreshed monthly from live prices by the `catalog-refresh` routine, which
  opens a PR rather than editing anything itself.

## The harness maintains itself

The retro, the roadmap pass, seat re-election and catalog re-derivation are **coded routines**, not
documented intentions — each with a cron cadence, a non-author reviewer, a fail-closed page when it
does not run, and an artifact that is the only accepted evidence the cycle happened. So the roster
and the dispatch policy get re-derived from live prices and real seat performance on a schedule,
instead of decaying into what someone believed at install.

The bound that makes that safe: **a routine proposes via PR and never self-applies.** A loop that can
silently rewrite its own review rules has no review rules. `playbooks/self-improvement.md`.

**New here? `QUICKSTART.md`** — four tiers, install only as far as you need. Tier 2 (fallback +
dead-man, both drilled) is the line between a demo and something you can leave running.

~20 files, no framework: `QUICKSTART.md` (tiered install) · `agents/` (role prompts) · `bin/agent`
(the dispatcher — resolves role→model→pool→harness, enforces the billing rule, and carries a
zero-dependency OpenRouter client as a fallback) · `prime/` (settings, models, continual-harness
bootstrap) · `remote/resident.sh.template` (resident supervisor) · `remote/tick.sh.template` (the
cron loop) · `remote/fallback.sh.template` (the ladder) · `remote/deadman.yml.template` (off-box
watcher) · `remote/routine.sh.template` (coded governance routines) · `remote/mission.template.md` ·
`playbooks/{continuity,dispatch,self-improvement,upstream-contribution}.md` · `NOTES.md`.

Acceptance bar: the kit must be able to re-provision the deployment it was extracted from — so when
a live deployment improves its harness, the generalized form lands here in the same pass.
