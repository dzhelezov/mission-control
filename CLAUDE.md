# mission-control

You are Claude Code, opened inside the mission-control kit. This repo installs and operates a
two-tier orchestration: a **laptop gateway** (human-driven, intermittent — observes, steers,
deep-dives, or takes over directly) and a **remote resident session** (24/7 autonomous executor
on a Linux box). You are the installer, the doctor, and the manual. Everything below is executable
by you; ask the human only for what you cannot obtain (tokens, ssh targets, choices).

`orchestration.example.toml` is the source of truth for models, roles, and guardrails. On first
setup, copy it to `orchestration.toml` (gitignored in instances that hold real values) and fill it
in with the human.

---

## Setup — laptop tier

1. Copy `agents/*.md` → `~/.claude/agents/` (the roster: cto, deep-reasoner, coder, reviewer,
   fast-worker; keep their model/effort frontmatter in sync with `orchestration.toml`).
2. Install `bin/glm` → a PATH dir (e.g. `~/.local/bin/glm`, chmod +x). It needs
   `OPENROUTER_API_KEY` in `~/.config/orchestration/openrouter.env` (600) — ask the human for the
   key, write the file yourself, never echo it.
3. Verify codex: `codex exec -m <models.codex.id> ... "reply OK"` — on auth failure, have the human
   run the codex login. Verify `gh auth status`.
4. Smoke: `glm --effort low "reply OK"`.

## Setup — remote tier

Ask for: ssh target, tenant username (default `claude-ops`), the project (target repos + mission +
human-reserved actions). Then, over ssh (root/sudo):

1. **Tenant**: create the user with its own home; scoped sudoers (systemctl/systemd-run/journalctl
   only, if needed); no membership in other users' groups. On a shared box this is the isolation
   boundary — never touch other tenants' files or services.
2. **Toolchain**: node 22+, `claude` CLI, `codex` CLI, `gh`, python3; install `bin/glm` into the
   tenant's PATH.
3. **Auth** (ask only for what's missing; all secrets → `~/ops/secrets/*.env`, 600, never in argv):
   Claude Max credentials for headless use; a **fine-grained gh PAT** scoped to exactly the
   control + target repos (Contents/PRs/Issues read-write, Actions read-only, **no workflow
   scope** — workflow-file pushes stay human); codex auth; OpenRouter key.
4. **Mission**: render `remote/mission.template.md` → `<project>/CLAUDE.local.md`, filling `{{...}}`
   from `orchestration.toml` + the human's answers. Read the result back to the human for sign-off —
   it contains the guardrails.
5. **Tick**: render `remote/tick.sh.template` → `~/ops/tick.sh` (fill `{{OPS_DIR}}`,
   `{{PROJECT_DIR}}`, `{{MODEL_ID}}`, `{{EFFORT}}`, `{{CONTROL_REPO}}`, `{{DIRECTIVE_LABEL}}`,
   `{{UNITS}}`), chmod +x, install cron (`*/45 * * * *` or per config).
6. **Smoke tick**: run `~/ops/tick.sh` once by hand; confirm it reaches the model, reads the
   mission, journals, and exits cleanly.

## Doctor (run anytime; idempotent)

Laptop: agents present · `glm` round-trip · codex round-trip · `gh auth status`.
Remote (via ssh): tick lock + last-run age · model probe (`claude -p "OK" --model <id>`) · glm/codex
probes · `gh` capability probes on control + target repos (issue read, PR read, push dry-run) ·
secrets 600 and env-only · **directive round-trip**: open a test issue labeled per config on the
control repo → next tick consumes + journals it → close it. Report a green/red table; fix what you
can, surface what you can't.

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
  repos. ssh is break-glass only; routine steering happens through issues.

## Routing principles (re-derive role assignments when the model catalog changes)

For anything that ships: **intelligence > taste > cost**; taste ≥ 7 for final authorship. Judge the
output, not the price tag — escalate on a miss without asking. Volume/mechanical → the free/flat
pools (codex, glm). Judgment (architecture, arbitration, final gates) → the best brain, over
distilled packets, never raw dumps. Review = a committee of blind seats with distinct lenses + an
arbiter for splits. High-stakes = blind multi-track, then judge. Review must **exercise the built
artifact** — build it, run it from fresh, click it; a diff read alone is not review.

## Security rules (non-negotiable)

Secrets only in 600 env files; never in argv, logs, commits, or issues. Secret-scan before every
commit/push. Never push to protected/default branches of production repos — PR + human merge for
anything human-reserved. When uncertain whether an action is routine or consequential: treat it as
consequential and surface it.
