# mission-control

A minimal, reproducible two-tier Claude Code orchestration: a human-driven **laptop gateway** +
a 24/7 autonomous **remote session**, synced through GitHub-native primitives (issues as
directives, a pinned journal issue, PRs as work products).

**Clone it, open Claude Code in it, say "set me up" — `CLAUDE.md` is the installer, doctor, and
manual.** `orchestration.example.toml` holds the configuration: a model catalog
(taste/cost/intelligence as editable data), a role schema (multi-seat committees, a brain+hands
implementation pair, explicit escalation), and guardrails. Defaults are extracted from a
production deployment and reflect a proven cost/value mix: Claude Max (fable = judgment, opus =
dispatch/escalation) + Codex sub (hands) + OpenRouter glm (brain/taste seat).

~10 files, no framework: `agents/` (the roster) · `bin/glm` (OpenRouter peer CLI) ·
`remote/tick.sh.template` (the idle-gated, directive-aware heartbeat) ·
`remote/mission.template.md` (the operating doc rendered per project) · `NOTES.md` (design
rationale). Acceptance bar: the kit must be able to re-provision the deployment it was extracted
from.
