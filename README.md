# mission-control

A minimal, reproducible two-tier agent orchestration: a human-driven **laptop gateway** + a 24/7
autonomous **remote resident session**, synced through GitHub-native primitives (issues as
directives, a pinned journal issue, PRs as work products).

**Clone it, open Claude Code in it, say "set me up" — `CLAUDE.md` is the installer, doctor, and
manual.** `orchestration.example.toml` holds the configuration as four layers of data: a **harness**
catalog (how a model is reached and who pays), a **pool** catalog (subscription vs metered), a
**model** catalog (taste/cost/intelligence), and a **role** schema (multi-seat committees, a
brain+hands implementation pair, explicit escalation) — plus guardrails.

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

First-class seats out of the box: **Opus 5** and **Fable 5** (Claude subscription) · **GPT-5.6 Sol**
(ChatGPT subscription, via prime-agent's `openai-codex` provider) · **Kimi K3**, **Qwen3.8 Max**,
and **DeepSeek V4 Flash** (OpenRouter). Swap any row; the roles follow.

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

~17 files, no framework: `agents/` (role prompts) · `bin/agent` (the dispatcher — resolves
role→model→pool→harness, enforces the billing rule, and carries a zero-dependency OpenRouter client
as a fallback) · `prime/` (settings, models, and the continual-harness bootstrap) ·
`remote/resident.sh.template` (the prime-agent resident supervisor) ·
`remote/tick.sh.template` (the stateless cron heartbeat) · `remote/fallback.sh.template` (the
ladder) · `remote/deadman.yml.template` (the off-box watcher) · `remote/mission.template.md` ·
`playbooks/` · `NOTES.md` (design rationale).

Acceptance bar: the kit must be able to re-provision the deployment it was extracted from — so when
a live deployment improves its harness, the generalized form lands here in the same pass.
