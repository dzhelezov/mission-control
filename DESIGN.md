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
| Both tiers share | The agent roster, the model policy, the peers (glm/codex), the disciplines (committee review, evidence gates) | |

The remote tier installs onto **a fresh Linux box** or as **a new tenant (dedicated user +
systemd slice) on an existing box** — isolated home, scoped sudoers, own secrets dir, own cron.

## 2. Configuration is data (three layers, one file)

`config/orchestration.toml` — see `config/orchestration.example.toml` for the shipped defaults.

1. **Model catalog** — the taste/cost/intelligence matrix as editable data. Each model: pool
   (claude-max / codex-sub / openrouter / api), cost, intel, taste scores. When the market moves
   (new model, price change), edit the row.
2. **Role schema** — roles are declared, not hardcoded, and seats can be N-wide:
   judgment roles (cto, deep-reasoner), dispatch (orchestrator), implement (a *pair*: brain +
   hands), review (a *committee* with per-seat lenses + an arbiter), mechanical. Escalation
   rules (`when=`) are part of the schema.
3. **Routing principles** — the policy that re-derives assignments when the catalog changes:
   ship-quality ordering intel > taste > cost · taste ≥ 7 for anything that ships · judge the
   output, not the price tag · volume → free/flat pools · judgment → the best brain · blind
   multi-track for high-stakes. Documented in `docs/routing.md` so a future maintainer can
   re-tune defaults by the same reasoning that produced them.

**Shipped defaults** (proven cost/value: Claude Max + Codex sub + OpenRouter credits):
fable = CTO/deep-reasoner (judgment); opus = orchestrator + escalation coder + committee-judgment
seat; **implementation default = glm-5.2 (brain) + gpt-5.5/codex (hands)** — the free-pool pair;
**review = 3-seat committee** — glm (taste) ∥ codex (adversarial-empirical) ∥ opus (judgment, on
substantive PRs) with fable as arbiter on splits; mechanical → codex (sonnet available, near-
dominated). The codex model is a knob (`gpt-5.5` default; e.g. `sol` selectable).

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
2. **Laptop**: install `agents/` → `~/.claude/agents/`, `peers/glm` → PATH, verify codex CLI +
   auth, verify `gh` auth, write the laptop-side config, bootstrap memory pointers.
3. **Remote**: ask for ssh target + tenant name → provision user/slice + toolchain (node, claude,
   codex, gh, glm) → auth dance, asking only for what's missing: Claude credentials (Max
   subscription, headless pattern), codex auth, `gh` fine-grained PAT (scoping guidance baked in:
   Contents/PRs/Issues write, Actions read, **no workflow scope**), OpenRouter key → write
   `~/ops/secrets/*.env` (600) → seed the mission doc from `remote/mission.template.md`
   (parameterized: project, goals, guardrails, human-reserved list) → install tick
   (cron/systemd) → run a **smoke tick** end-to-end.
4. `skills/doctor` — idempotent verification, re-runnable anytime: model probes per pool, glm/codex
   round-trips, gh capability probes (push/PR/issue on the intended repos), tick lock/idle-gate
   sanity, secrets permissions, directive round-trip (open a test issue → see the tick consume it).

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
  (portal-ponder specifics out, template variables in), agents unchanged, glm CLI config-driven.
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
later); UI dashboards (the journal issue + `gh` are the dashboard).
