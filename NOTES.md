# mission-control — design

**A reproducible, installable two-tier Claude Code orchestration: a human-driven laptop gateway +
a 24/7 autonomous remote session, coordinated through GitHub-native primitives.**

Clone the repo, open Claude Code in it, and it completes its own setup — asking for tokens and
access only when and where needed. Then the remote tier works autonomously on goals the laptop
tier sets; the laptop observes, steers, deep-dives, or takes over for direct work when online.

This kit is *extracted from a production deployment* (the portal-ponder campaign, 2026-07): every
default, guardrail, and discipline here survived contact with real work. `extracted/` holds the
raw artifacts from that deployment; the build generalizes them.

---

## 1. The two tiers

| | Laptop (gateway) | Remote (resident) |
|---|---|---|
| Availability | Intermittent — goes on/offline | 24/7 (cron/systemd tick loop) |
| Driver | Human in the loop | Autonomous against standing directives |
| Role | Observe · steer/prioritize · expert deep-dives · direct takeover (vibecoding) | Primary executor: implementation, chores, PRs driven to merge, release prep |
| Both tiers share | The role roster, the model policy, the harness catalog, the disciplines (committee review, evidence gates) | |

The remote tier installs onto **a fresh Linux box** or as **a new tenant (dedicated user +
systemd slice) on an existing box** — isolated home, scoped sudoers, own secrets dir, own cron.

## 2. Configuration is data (four layers, one file)

`orchestration.toml` — see `orchestration.example.toml` for the shipped defaults.

0. **Harness catalog** — how a model is actually reached: the CLI, its auth file, its one-shot
   invocation template, and which providers it can serve. `bin/agent` composes argv from this row,
   so swapping a harness moves every role that uses it without touching a role definition.
1. **Pool + model catalog** — pools carry the *billing surface* (subscription vs metered); models
   carry the taste/cost/intelligence matrix and point at a pool. When the market moves (new model,
   price change, a provider you'd rather route around), edit the row.
2. **Role schema** — roles are declared, not hardcoded, and seats can be N-wide:
   judgment roles (cto, deep-reasoner), dispatch (orchestrator), implement (a *pair*: brain +
   hands), review (a *committee* with per-seat lenses + an arbiter), mechanical. Escalation
   rules (`when=`) are part of the schema.
3. **Routing principles** — the policy that re-derives assignments when the catalog changes:
   ship-quality ordering intel > taste > cost · taste ≥ 7 for anything that ships · judge the
   output, not the price tag · volume → free/flat pools · judgment → the best brain · blind
   multi-track for high-stakes. Documented in `docs/routing.md` so a future maintainer can
   re-tune defaults by the same reasoning that produced them.

**Shipped defaults** (proven cost/value: Claude Max + ChatGPT sub + OpenRouter credits):
fable = CTO/deep-reasoner (judgment); opus = orchestrator + escalation coder + committee-judgment
seat; **implementation default = kimi-k3 (brain) + deepseek-v4-flash (hands)** — a frontier drafter
over a near-free executor; **review = 4-seat committee** — kimi (taste + whole-repo) ∥ sol
(adversarial-empirical) ∥ qwen3.8-max (independent lineage) ∥ opus (judgment, on substantive PRs)
with fable as arbiter on splits; mechanical + compression → deepseek-v4-flash; long-context sweeps
→ kimi-k3. glm-5.2 was the metered brain until 2026-08 and is now retired in favour of kimi-k3.

## 2b. Why two harnesses (the finding that shaped this kit)

prime-agent is the better executor: one model-facing tool (a persistent IPython kernel), ~20
providers behind one config, daemon-backed resident sessions, persistent goals, native cron
schedules, heartbeats, autonomous quality gates, recursive `rlm()` subagents, and a continual
harness that stores the roster as refinable specs. The obvious move is to run everything on it.

The obvious move is wrong for one pool. prime-agent's own source says Anthropic subscription auth
"draws from extra usage and is billed per token, not your Claude plan limits"
(`packages/coding-agent/src/modes/interactive/auth-flows.ts`), and it ships a
`warnings.anthropicExtraUsage` setting to nag about exactly that. A wholesale swap would silently
convert a flat Max plan into a metered API bill. The ChatGPT side has no such caveat: the
`openai-codex` provider posts to `chatgpt.com/backend-api` under OpenAI's "Codex for OSS" path, so
prime-agent rides that subscription for real.

Hence: harness is a config row, and exactly one guardrail is non-negotiable — Anthropic models run
on the `claude` harness. `bin/agent` refuses otherwise unless `--allow-metered` is passed. This is
the difference between "provider-agnostic" and "vendor-blind": the kit knows what each route costs.

Second-order consequence worth stating: scarcity is now two-dimensional. Subscription pools are
capped by *rate* (weekly caps that do get hit); metered pools are capped by *dollars*. Pushing
volume onto a $0.09/M seat is not primarily about saving money — it is about keeping the
subscription caps available for judgment work.

## 2c. Native over hand-rolled

Everything the old tick loop emulated by hand, prime-agent owns natively, so the resident tier uses
the native mechanism and cron degrades to a supervisor that notices death: persistent **goal** for
the standing mission · native **schedule** for the tick (claims before delivery, coalesces missed
ticks) · **heartbeats** for watch loops · **autonomous gates** for "not done until it builds" ·
**harness subagent specs** + `rlm()` for the roster · `prime-agent send` for laptop steering without
ssh · `refine.run()` to turn repeated failures into durable harness state. `prime/bootstrap.py`
compiles `orchestration.toml` + `agents/*.md` into that harness state, resolving every model id to a
live `rlm.find_models` selector so an unreachable model fails at bootstrap, not mid-mission.

## 3. Sync: GitHub-native (no bespoke ledger)

Each deployment instance is a **private clone of this repo = the control repo**. Coordination:

- **Directives** — issues on the control repo labeled `directive` (+ `priority:*`). The laptop
  (or the human directly) opens them; the remote tick treats open directives as work sources.
  *The tick's idle-gate fingerprint includes open-directive state*, which structurally fixes the
  directive-starvation failure mode observed in production (a queued directive could idle-wait
  behind an unchanged repo).
- **Journal** — the remote appends tick reports as comments on a pinned `journal` issue.
  Private repo ⇒ operational detail is safe; the "never post infra internals to public surfaces"
  rule still applies to all *public* target repos.
- **Work products** — PRs on the target project repos (committee-gated, driven to merge).
- **Releases / CI** — optional per-project modules: the examples-freshness e2e gate and the
  release-automation loop ship as reusable workflow templates in `sync/workflows/`.
- ssh remains the break-glass path only; routine steering never needs it.

## 4. Install flow (the repo is the installer)

`CLAUDE.md` routes a fresh Claude Code session into `skills/setup` — an interview:

1. Which tier(s) to set up here?
2. **Laptop**: install `agents/` → `~/.claude/agents/` and `bin/agent` → PATH; install prime-agent
   and log it in to the **ChatGPT** subscription (explicitly *not* Claude — explain the billing);
   render `prime/settings.json` + `prime/models.json`; verify codex and `gh` auth.
3. **Remote**: ask for ssh target + tenant name + which harness drives the loop → provision
   user/slice + toolchain (node, python3, tmux, gh, and the named harnesses) → auth dance, asking
   only for what's missing: Claude credentials (Max, headless pattern), prime-agent `auth.json`
   (log in on the laptop, copy at 600), codex auth, `gh` fine-grained PAT (scoping guidance baked
   in: Contents/PRs/Issues write, Actions read, **no workflow scope**), OpenRouter key → write
   `~/ops/secrets/*.env` (600) → seed the mission doc from `remote/mission.template.md` → install
   the resident supervisor (prime) or the cron tick (claude) → `prime/bootstrap.py` to compile the
   roster into the continual harness → run a **smoke run** end-to-end.
4. `skills/doctor` — idempotent verification, re-runnable anytime: per-harness round-trips, model
   probes per pool, `qwen3.8-max` present in `prime-agent model list`, resident alive + native
   schedule registered + goal state sane, gh capability probes (push/PR/issue on the intended
   repos), secrets permissions, directive round-trip (open a test issue → see it consumed).

## 5. Guardrail catalog (shipped, parameterized per deployment)

- Human-reserved actions list (template: publish to registries, outreach, prod-site merges,
  spend > $X) — the mission doc renders it; the classifier principle: *when uncertain → surface*.
- Secret hygiene: env-file-only keys (600), secret-scan pre-commit + pre-push, keys never in argv.
- Public-surface rule: no infra internals on public repos (hostnames, paths, DB names, budgets).
- PAT scoping guidance + the workflow-scope boundary (workflow-file changes stay human-pushed).
- Prod-safety: never push to protected/prod branches; PR + human merge for designated repos.
- Review discipline: **exercise the built artifact** (build it, run it from fresh, click it) —
  committee review + acceptance gates that run the real thing, not read the diff.

## 6. Build plan

- **P0 — scaffold** (done, laptop): this design, example config, seeded `extracted/`.
- **P1 — extract & generalize**: `extracted/*` → real kit locations; parameterize tick.sh
  (paths/models/cadence from config; directive-aware idle-gate), generalize the mission template
  (portal-ponder specifics out, template variables in), agents unchanged, peer CLI config-driven.
- **P1b — harness-agnostic** (this branch): harness/pool catalogs; `bin/agent` replaces `bin/glm`
  and enforces the Anthropic billing rule; prime-agent as the default executor with a resident
  supervisor, native goal/schedule/gates, and `prime/bootstrap.py` compiling the roster into the
  continual harness; roster prompts de-hardcoded to roles. Acceptance: `agent --list` green on a
  fresh box, and a resident session consuming a directive with the laptop offline.
- **P2 — setup + doctor skills**: the interview + verification, per §4. Acceptance: a fresh
  container/VM reaches a green doctor from nothing but the repo + credentials.
- **P3 — GitHub-native sync**: directive/journal conventions, labels, issue templates, the
  tick fingerprint extension; workflow templates (freshness-gate, release-automation) in
  `sync/workflows/`. Acceptance: a directive opened on the control repo is consumed by the next
  tick and journaled, laptop fully offline.
- **P4 — dogfood (the real acceptance)**: re-provision the existing OVH deployment as an
  *instance of this kit* (new tenant beside the current one, then cut over). If the kit cannot
  reproduce the deployment it was extracted from, it is not done.

Build owner: the remote (box) session, committee-gated PRs into this repo. The laptop scaffolded
P0 and judges P4. Every phase lands as a PR with the standard evidence gates.

## 7. Non-goals (v1)

Multi-box fleets; non-GitHub forges; Windows laptops; secrets managers beyond env-files (pluggable
later); UI dashboards (the journal issue + `gh` are the dashboard); local/self-hosted inference
(prime-agent supports it via `models.json`, but nothing here is tuned for it).
