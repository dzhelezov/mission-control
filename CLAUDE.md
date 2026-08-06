# mission-control

You are Claude Code, opened inside the mission-control kit. This repo installs and operates a
two-tier orchestration: a **laptop gateway** (human-driven, intermittent — observes, steers,
deep-dives, or takes over directly) and a **remote resident session** (24/7 autonomous executor
on a Linux box). You are the installer, the doctor, and the manual. Everything below is executable
by you; ask the human only for what you cannot obtain (tokens, ssh targets, choices).

`orchestration.example.toml` is the source of truth for harnesses, pools, models, roles, and
guardrails. On first setup, copy it to `orchestration.toml` (gitignored in instances that hold
real values) and fill it in with the human.

---

## The one rule that decides the architecture

**Harnesses are pluggable; billing is not.** A model runs on whichever harness the config names,
except for one hard constraint discovered by reading prime-agent's source:

> `packages/coding-agent/src/modes/interactive/auth-flows.ts` —
> *"Anthropic subscription auth is active. Third-party harness usage draws from extra usage and is
> billed per token, not your Claude plan limits."*

So Anthropic models (`opus`, `fable`, `sonnet`) run on the **`claude`** harness, where they draw on
Claude Pro/Max plan limits. Everything else — GPT on the ChatGPT subscription, and the OpenRouter
models — runs on **`prime-agent`**, which reaches the ChatGPT plan through its `openai-codex`
provider (`chatgpt.com/backend-api`, OpenAI's "Codex for OSS" path) at no marginal cost.

`bin/agent` enforces this and refuses to route an Anthropic model through a metered pool without
`--allow-metered`. Do not remove that check to "simplify" anything.

| | reaches | billing |
|---|---|---|
| `claude` | Anthropic models | Claude Pro/Max **plan limits** |
| `prime` (prime-agent) | ChatGPT sub, OpenRouter, ~15 more providers | subscription for `openai-codex`; per-token for the rest |
| `codex` | ChatGPT sub | plan limits (alternate path to the same place) |
| `http` | OpenRouter | per-token (built into `bin/agent`; no install needed) |

---

## Setup — laptop tier

1. Copy `agents/*.md` → `~/.claude/agents/` (the roster; keep frontmatter in sync with
   `orchestration.toml`).
2. Install `bin/agent` → a PATH dir (e.g. `~/.local/bin/agent`, chmod +x). It needs python 3.11+
   (it re-execs into `python3.13`/`3.12`/`3.11` if the system `python3` is older) and an
   `OPENROUTER_API_KEY` in `~/.config/orchestration/openrouter.env` (600) — ask the human for the
   key, write the file yourself, never echo it.
3. Install prime-agent: `curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh`
   (verifies a SHA-256 checksum). Then `prime-agent` → `/login` → **ChatGPT Plus/Pro (Codex)**.
   Do **not** log in with Claude Pro/Max here unless the human explicitly wants metered extra
   usage; explain the billing first.
4. Render `prime/settings.json.template` → `~/.prime/agent/settings.json` and
   `prime/models.json.template` → `~/.prime/agent/models.json`. The models file exists because
   prime-agent's built-in catalog does not yet carry `qwen/qwen3.8-max`; delete that block once a
   release ships it (`prime-agent model list qwen`).
5. Verify codex: `codex exec -m <models.sol.id> ... "reply OK"`. Verify `gh auth status`.
6. Smoke: `agent --list` (every row should show its harness and billing, no `[!!]` markers), then
   `agent --model flash --effort high "reply OK"`.

## Setup — remote tier

Ask for: ssh target, tenant username (default `claude-ops`), the project (target repos + mission +
human-reserved actions), and **which harness drives the resident loop**. Then, over ssh (root/sudo):

1. **Tenant**: create the user with its own home; scoped sudoers (systemctl/systemd-run/journalctl
   only, if needed); no membership in other users' groups. On a shared box this is the isolation
   boundary — never touch other tenants' files or services. It is also the *only* sandbox:
   prime-agent's IPython kernel and Claude Code's tool loop both execute model-generated code with
   this user's permissions, by design.
2. **Toolchain**: node 22+, python3, `gh`, `tmux`, plus the harnesses the config names — `claude`
   CLI, `prime-agent`, `codex` CLI; install `bin/agent` into the tenant's PATH.
3. **Auth** (ask only for what's missing; all secrets → `~/ops/secrets/*.env`, 600, never in argv):
   Claude Max credentials for headless use (`~/.claude/.credentials.json`); prime-agent OAuth
   (`~/.prime/agent/auth.json` — log in on the laptop and copy the file over, 600; tokens
   auto-refresh); codex auth; a **fine-grained gh PAT** scoped to exactly the control + target
   repos (Contents/PRs/Issues read-write, Actions read-only, **no workflow scope** — workflow-file
   pushes stay human); OpenRouter key.
4. **Mission**: render `remote/mission.template.md` → `<project>/CLAUDE.local.md` (prime-agent reads
   `CLAUDE.md`/`AGENTS.md` as context files, so one doc serves both harnesses), filling `{{...}}`
   from `orchestration.toml` + the human's answers. Read the result back to the human for sign-off —
   it contains the guardrails.
5. **Loop** — pick by harness:
   - **prime (native, preferred)**: render `remote/resident.sh.template` → `~/ops/resident.sh`,
     chmod +x, cron every `{{SUPERVISOR_MINUTES}}`. It starts one daemon-backed resident session
     under tmux with a **persistent goal**, registers the ops tick as a **native schedule**, and
     otherwise costs zero tokens. Two greps in it depend on `prime-agent list` / `schedule list`
     output — run those commands once on the box and confirm the matches before trusting cron.
   - **claude (or a deliberately stateless prime run)**: render `remote/tick.sh.template` →
     `~/ops/tick.sh`, chmod +x, cron `*/45` or per config.
6. **Harness bootstrap** (prime only): in the resident session, `%run ~/mission-control/prime/
   bootstrap.py` then `await bootstrap()`. This installs the roster into prime-agent's **continual
   harness** as global subagent specs, plus a routing memory and the billing-guard prompt note, with
   every model id resolved to a live `rlm.find_models` selector. Re-run after catalog edits.
7. **Smoke**: force one run by hand; confirm it reaches the model, reads the mission, journals, and
   exits cleanly.

## Prefer native capability over hand-rolled loops

When the harness is prime-agent, do not re-implement what it already owns:

| Need | Native mechanism | Not |
|---|---|---|
| standing mission | persistent **goal** (`--goal`, `goal.get()`, `goal.complete()`) | re-reading a doc every cold start |
| cadence | `prime-agent schedule add` (claims before delivery, coalesces misses) | a cron LLM invocation per tick |
| watch loops | `rlm_heartbeat.create(..., interval="10m")` | sleeping inside a turn |
| "not done until it builds" | `--autonomous --autonomous-gate "<cmd>"` | a hand-written retry wrapper |
| the roster | harness **subagent specs** + `await rlm(task, name=…, model=…)` | one subprocess per delegation |
| results from children | `agent_message.send(..., receiver_role="parent")` | polling for a return value |
| steering from the laptop | `prime-agent send <agent> "…"` | ssh |
| learning from repetition | `refine.run()` → memory / skill / subagent spec | prompt drift |

`bin/agent` stays the right tool for one-shot, cross-harness calls — peers, committee seats, and
every Anthropic seat — because it is the thing that knows the billing rule.

## Doctor (run anytime; idempotent)

Laptop: agents present · `agent --list` clean · one round-trip per installed harness
(`agent --model opus`, `--model sol`, `--model flash`) · `prime-agent model list` shows
`qwen/qwen3.8-max` · `gh auth status`.

Remote (via ssh): resident alive (`prime-agent list`) or tick lock + last-run age · native schedule
present (`prime-agent schedule list --all`) · goal state sane (`prime-agent send <agent> "/goal
status"`) · model probe per pool · `gh` capability probes on control + target repos (issue read,
PR read, push dry-run) · secrets 600 and env-only · harness bootstrap present
(`rlm.harness.overview(global_=True)` lists `mc-*`) · **directive round-trip**: open a test issue
labeled per config on the control repo → next tick consumes + journals it → close it.

Report a green/red table; fix what you can, surface what you can't.

## Sync conventions (GitHub-native; no bespoke ledger)

- **Control repo** = the private instance of this kit. **Directives** = issues labeled per config
  (default `directive`; `priority:high` escalates). The laptop/human opens them; the remote consumes
  them — the tick fingerprint includes open-directive state, so a queued directive always triggers a
  run (no starvation).
- **Journal** = the remote appends a per-tick report comment on the pinned issue titled `journal`
  (created at setup). Operational detail is fine there — the control repo is private.
- **Work products** = PRs on target repos, committee-gated (see roles), driven to merge unless the
  repo is on the human-reserved list.
- Public-surface rule: never post infra internals (hosts, paths, tenant names, budgets) on public
  repos. ssh is break-glass only; routine steering happens through issues or `prime-agent send`.

## Routing principles (re-derive role assignments when the model catalog changes)

For anything that ships: **intelligence > taste > cost**; taste ≥ 7 for final authorship. Judge the
output, not the price tag — escalate on a miss without asking. Volume/mechanical → the cheapest
capable seat, which is what keeps the subscription pools' *rate* caps free for judgment work.
Judgment (architecture, arbitration, final gates) → the best brain, over distilled packets, never
raw dumps. Review = a committee of blind seats with distinct lenses **and distinct model lineages**
+ an arbiter for splits. High-stakes = blind multi-track, then judge. Review must **exercise the
built artifact** — build it, run it from fresh, click it; a diff read alone is not review.

## Security rules (non-negotiable)

Secrets only in 600 env files; never in argv, logs, commits, or issues. Secret-scan before every
commit/push. Never push to protected/default branches of production repos — PR + human merge for
anything human-reserved. Neither harness is a sandbox: the tenant boundary is the isolation, so
never reach outside the project dir, `~/ops`, and the tenant's home. When uncertain whether an
action is routine or consequential: treat it as consequential and surface it.
