# mission-control — design

**A reproducible, installable two-tier agent orchestration: a human-driven laptop gateway +
a 24/7 autonomous remote session, coordinated through GitHub-native primitives.**

Clone the repo, open a coding agent in it, and it completes its own setup — asking for tokens and
access only when and where needed. Then the remote tier works autonomously on goals the laptop
tier sets; the laptop observes, steers, deep-dives, or takes over for direct work when online.

This kit is *extracted from production deployments*: every default, guardrail, and discipline here
survived contact with real work, and most of them exist because something failed first. Where a rule
looks oddly specific, that is why — `playbooks/continuity.md` carries the operational ones with the
failure that produced each. Nothing here is tied to a particular project; the kit ships only the
generalized mechanism.

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

## 2. Configuration is data (one file, layered)

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
3. **Dispatch policy** (`[dispatch]`) — capability floors per work class and an ordered candidate
   list, so the role table above is a *derived answer* rather than a decree: ship-quality ordering
   intel > taste > cost · taste ≥ 7 for anything that ships · judge the output, not the price tag ·
   volume → cheap metered (to protect subscription rate caps) · judgment → the best brain. Method
   and the monthly re-derivation in `playbooks/dispatch.md`.
4. **Coded routines** (`[routines]`) — the retro, roadmap pass, catalog refresh and seat election,
   each with cadence, non-author reviewer, fail-closed miss-page and an artifact. This is the layer
   that keeps layers 1–3 from going stale on their own (`playbooks/self-improvement.md`).

**Shipped defaults** (proven cost/value: Claude Max + ChatGPT sub + OpenRouter credits):
fable = CTO/deep-reasoner (judgment); opus = orchestrator + escalation coder + committee-judgment
seat; **implementation default = kimi-k3 (brain) + deepseek-v4-flash (hands)** — a frontier drafter
over a near-free executor; **review = 4-seat committee** — kimi (taste + whole-repo) ∥ sol
(adversarial-empirical) ∥ glm-5.2 (conformance) ∥ kimi (taste + whole-repo) ∥ opus (judgment, on
substantive PRs, failing over to glm when the plan is dry) with fable as arbiter on splits; mechanical + compression → deepseek-v4-flash; long-context sweeps
→ kimi-k3; glm-5.2 as the cheap challenger and as the standing failover for the subscription
seats — when the plan allowance is dry it is what keeps a challenger on the committee at all.
Treat every one of these as a snapshot: `playbooks/dispatch.md` carries the method that re-derives
them, and the catalog moves about monthly.

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

Second-order consequence worth stating: scarcity is **three-dimensional**. Subscription pools are
capped by *rate* (weekly caps that do get hit); prepaid vendor plans are capped by *tokens* on their
own clock; metered pools are capped by *dollars* and do not reset at all. Pushing volume onto a
$0.09/M seat is not primarily about saving money — it is about keeping the subscription caps
available for judgment work.

The axis matters more than the vendor, because **a fallback that does not cross the axis is not a
fallback**: two rate-capped seats will be dry in the same window eventually, and eventually in the
same hour. Pools therefore carry `scarcity`, `resets`, and `blast_radius` fields so "put the
fallback on a different clock" is checkable rather than a matter of taste — and so the question
"what does emptying this pool actually take down?" has a written answer before you find out. The
allocation method across all three axes lives in `playbooks/dispatch.md`, and re-deriving it when
prices move is a coded monthly routine rather than something anyone has to remember.

## 2c. Native over hand-rolled

Everything the old tick loop emulated by hand, prime-agent owns natively, so the resident tier uses
the native mechanism and cron degrades to a supervisor that notices death: persistent **goal** for
the standing mission · native **schedule** for the tick (claims before delivery, coalesces missed
ticks) · **heartbeats** for watch loops · **autonomous gates** for "not done until it builds" ·
**harness subagent specs** + `rlm()` for the roster · `prime-agent send` for laptop steering without
ssh · `refine.run()` to turn repeated failures into durable harness state. `prime/bootstrap.py`
compiles `orchestration.toml` + `agents/*.md` into that harness state, resolving every model id to a
live `rlm.find_models` selector so an unreachable model fails at bootstrap, not mid-mission.

## 2d. Continuity: the loop must outlive its own model

The single largest gap between "a cron job that calls a model" and something you can leave running
is that **the model path dies on a schedule you do not control**, and when it does, an autonomous
loop fails *quietly* — there is no user staring at a blank screen. Three mechanisms close it, and
all three ship here rather than being left as an exercise:

- **A fallback ladder** (`remote/fallback.sh.template`). Per-invocation, never sticky: the primary
  is tried every run, so the primary attempt *is* the availability check and the loop self-returns
  when quota resets. The bottom rung is a flash-class seat at cents per run whose only job is to
  keep the heartbeat alive and refuse to fabricate. Two token-plan seats can and do go dry in the
  same window, so the ladder must end somewhere that cannot quota out.
- **A three-leg dead-man** (`remote/deadman.yml.template` plus the heartbeat writer in the tick).
  The loop reports on itself *including on failure*; something off the box parses that strictly and
  fails closed; a local sidecar covers the wedged-but-alive case. On-box monitoring cannot report
  that the box is gone.
- **A staged idle gate.** The model writes its "nothing to do" assertion to a staging file and the
  tick promotes it only on a clean exit, re-confirmed against a live health read. A run that
  crashed has not earned the right to declare the queue empty.

The design bias throughout: **prefer a cheap unconditional attempt over a clever probe.** Probes go
stale, probes lie, and a probe against a thinking model is actively dangerous (`playbooks/
continuity.md` §4). Trying the thing costs nothing when it works.

## 2e. Self-improvement is a subsystem, not a good intention

The kit's own rule is that a standing routine with no cadence, owner and mechanical check is
decoration — so the governance loop is coded rather than written down. `remote/routine.sh.template`
plus `[routines.*]` runs the retro, the daily roadmap/issue pass, monthly catalog re-derivation, and
monthly seat re-election, each with a non-author reviewer and a fail-closed page on a missed cycle.
Only a produced artifact counts as a cycle having happened; otherwise a crashing routine is
indistinguishable from a quiet healthy one and the miss-page never fires.

That means the model roster and the dispatch policy are **derived artifacts refreshed on a cadence**,
not static config a human maintains — which matters because catalogs and prices move about monthly,
and the failure mode is silent: nothing breaks, you just overpay and under-perform for months.

The bound: **routines propose via PR, never self-apply.** A harness that can rewrite its own
governance has no governance, so every change to how the system judges itself arrives as a reviewable
diff with a stated reason, gated by committee plus human. Same shape as the public-surface rule — the
loop drafts, a gate publishes.

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
- **Heartbeat** — one issue whose **body** the loop machine-edits each run (never a comment per run;
  that is thousands of comments a month). Titled so humans leave it alone. The off-box dead-man
  reads it.
- **Ranked queue** — one small file in the target repo holding the current ordered priorities,
  re-ranked in the same tick as any material change. The journal's "next" is a pointer at it. Two
  competing lists is the failure this prevents: a plan that names a source of truth and then ranks
  something else looks governed and is not.
- **Work products** — PRs on the target project repos (committee-gated, driven to merge).
- ssh remains the break-glass path only; routine steering never needs it.

## 4. Install flow (the repo is the installer)

There is no scaffold ceremony and no separate skills tree: **`CLAUDE.md` is the installer, the
doctor, and the manual.** Open an agent in the repo and say "set me up"; it runs the interview,
provisions both tiers, and can re-run its doctor section idempotently at any time. The full step
list lives there rather than being duplicated here — including the continuity install (fallback
ladder, heartbeat issue, off-box dead-man) and the two drills that must pass before the deployment
counts as done.

## 5. Guardrail catalog (shipped, parameterized per deployment)

- Human-reserved actions list (template: publish to registries, outreach, prod-site merges,
  spend > $X) — the mission doc renders it; the classifier principle: *when uncertain → surface*.
- Secret hygiene: env-file-only keys (600), secret-scan pre-commit + pre-push, keys never in argv.
- Public-surface rule: no infra internals on public repos (hostnames, paths, DB names, budgets).
- PAT scoping guidance + the workflow-scope boundary (workflow-file changes stay human-pushed).
- Prod-safety: never push to protected/prod branches; PR + human merge for designated repos.
- Review discipline: **exercise the built artifact** (build it, run it from fresh, click it) —
  committee review + acceptance gates that run the real thing, not read the diff.
- Governance floor: two live challengers of distinct lineage; no seat challenges itself or is its
  own fallback; a decision is a proposal until objections are folded or refused with a reason.
- Continuity floor: a fallback leg that cannot quota out, a heartbeat written even on failure, and
  an off-box watcher that fails closed. All three drilled at install (`playbooks/continuity.md`).

## 6. Keeping this kit current

**The blueprint is downstream of the deployments.** Every time a live deployment improves its
harness — a new fallback leg, a seat change, a sensor that turned out to lie, a cadence that had to
move — the generalized form of that change belongs here, in the same pass. A lesson that stays in
one deployment's private notes is a lesson the next deployment pays for again.

Two hard rules for what lands:

1. **Nothing project-specific, ever.** No hostnames, tenant names, repo names, issue numbers,
   product details, infrastructure topology, or business context. If a rule cannot be stated without
   naming the deployment that produced it, state the *mechanism* and drop the specifics — the
   failure is the transferable part, not who suffered it. This repo is public.
2. **Mechanism over anecdote.** Ship the template, the gate, or the check. Prose describing good
   behaviour is the weakest form of this kit; a harness enforces a gate and only reads a paragraph.

Acceptance bar, unchanged: **the kit must be able to re-provision the deployment it was extracted
from.** If a running deployment has a mechanism this repo cannot reproduce, the repo is behind.

## 7. Non-goals (v1)

Multi-box fleets; non-GitHub forges; Windows laptops; secrets managers beyond env-files (pluggable
later); UI dashboards (the journal issue + `gh` are the dashboard); local/self-hosted inference
(prime-agent supports it via `models.json`, but nothing here is tuned for it).
