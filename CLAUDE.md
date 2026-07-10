# mission-control — agent instructions

This repo is an installable two-tier orchestration kit. **Status: P0 scaffold — the setup skill
does not exist yet.** Read `DESIGN.md` before doing anything; `config/orchestration.example.toml`
is the source of truth for roles/models/guardrails. `extracted/` = raw production artifacts:
generalize them (P1), never edit them in place as if they were the kit.

Build rules: every phase lands as a committee-gated PR against this repo; no secrets ever (env-file
references only; secret-scan before commit); the P4 acceptance is re-provisioning the original
deployment from this kit alone.
