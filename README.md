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

~14 files, no framework: `agents/` (role prompts) · `bin/agent` (the dispatcher — resolves
role→model→pool→harness, enforces the billing rule, and carries a zero-dependency OpenRouter client
as a fallback) · `prime/` (settings, models, and the continual-harness bootstrap) ·
`remote/resident.sh.template` (the prime-agent resident supervisor) ·
`remote/tick.sh.template` (the stateless cron heartbeat) · `remote/mission.template.md` ·
`NOTES.md` (design rationale).

Acceptance bar: the kit must be able to re-provision the deployment it was extracted from.
