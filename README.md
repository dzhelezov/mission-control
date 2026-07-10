# mission-control

A reproducible two-tier Claude Code orchestration: a human-driven **laptop gateway** + a 24/7
autonomous **remote session**, coordinated through GitHub-native primitives (issues as directives,
a pinned journal issue, PRs as work products). Clone it, open Claude Code in it, and it completes
its own setup — asking for tokens and access only when and where needed.

**Status: P0 (scaffold).** Read [`DESIGN.md`](DESIGN.md). Shipped defaults are extracted from a
production deployment; `extracted/` holds the raw battle-tested artifacts pending generalization (P1).

Defaults (all configurable in `config/orchestration.example.toml`): Claude Max (fable = judgment,
opus = dispatch/escalation) + Codex sub (gpt-5.5 hands) + OpenRouter (glm-5.2 brain/taste-seat);
3-seat review committee; brain-and-hands implementation pair.
