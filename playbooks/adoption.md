# Adoption — pointing this kit at a deployment that already exists

`CLAUDE.md` installs a deployment. This playbook is the other case, and after the first deployment
it is the only case: **there is already a loop running, it has its own conventions, some of them are
better than the kit's, and it must not stop.**

Read this before touching anything. The install path and the adoption path share templates and share
nothing else.

---

## 0. The rule that prevents the obvious disaster

> **Adoption never installs. It compares, ranks, and migrates one mechanism at a time.**

Do **not** run the setup interview. Do **not** render `remote/*.template` over files that exist. Do
**not** create a tenant, rewrite cron, or seed issues. A running deployment's state — its ledger,
its queue, its mission doc, its in-flight work — is the product of real operating experience, and
most of it is right. You are here to close specific gaps, not to normalise a filesystem.

Two hard constraints, both learned the expensive way:

- **Never overwrite a script a running shell is executing.** Bash re-reads a file progressively as
  it runs. Wait for the loop to be idle, keep a dated backup, `bash -n` the candidate, then
  atomic-`mv`. (`continuity.md` §9.)
- **Adoption is harness work, so it ranks below live delivery.** If the deployment has an open
  incident or finished-but-unlanded work, that comes first — every time. A team that stops shipping
  to reorganise its harness has reproduced the exact failure this kit's ranking rule exists to
  prevent. Say so out loud rather than quietly starting.

## 1. Gap analysis, read-only, before any proposal

Produce this table and nothing else on the first pass. Cite a real path or a real command output for
every row — an assumed gap is worse than an unknown one.

| Mechanism | Kit reference | Present here? | Evidence | Gap costs what? |
|---|---|---|---|---|
| One ranked queue file, re-ranked on material change | `[deployment].queue_file`, `routines.roadmap-pass` | | | |
| Full enumeration ignoring "updated", disposition per item, **asserted count** | `continuity.md` §3 | | | |
| Delivery ranked above harness, harness capped | `dispatch.md`, `[routines.retro]` | | | |
| Heartbeat written **even on failure** | `tick.sh.template` | | | |
| Off-box dead-man, strict parse, fail-closed | `deadman.yml.template` | | | |
| Fallback ladder crossing scarcity axes | `fallback.sh.template`, `[continuity].legs` | | | |
| Routines: cadence + non-author reviewer + miss-page + **artifact gates the cycle** | `routine.sh.template`, `self-improvement.md` | | | |
| Liveness probes require non-empty content | `continuity.md` §4 | | | |
| Escalation file holding only currently-open, human-only asks | mission template | | | |
| Budget vantage on the pool that stops the loop | `continuity.md` §7 | | | |

Then two questions, answered from the deployment's own recent history rather than from this list:

1. **What has actually gone wrong here in the last month?** Rank the gaps by which of *those*
   incidents they would have prevented. A checklist-led migration fixes the gaps the kit happens to
   name; an evidence-led one fixes the gaps that are costing this deployment money.
2. **What does this deployment do better than the kit?** There will be something. It goes upstream
   as a PR before you change anything here — otherwise adoption quietly destroys the local
   improvement that experience paid for.

## 2. Migration order

Cheapest and most load-bearing first. Stop after each and let a real cycle run before the next.

1. **Conventions before code.** A ranked queue file and the enumeration/disposition/count rule are
   pure convention — no install, no restart, immediate effect on what the loop chooses to do next.
   This is almost always the highest-value step and it is free.
2. **The artifact-gated routine runner**, if the deployment's periodic reviews are self-reported. A
   stamp that advances on "I ran" rather than "I produced the output" is a success detector, and it
   is how a review quietly stops doing its job while still reporting done.
3. **Liveness and the dead-man**, if the existing check watches the wrong layer or cannot reach a
   human when the box is gone.
4. **The fallback ladder**, if outages are currently handled ad hoc.
5. **Everything else** goes on the deployment's retro, not into this migration.

## 3. What must never be unified

Sharing a blueprint is not sharing a runtime. Keep separate, always:

- tenants and OS users · cron · secrets and **one key per project** (a shared key is one pool, one
  blast radius, and no per-project attribution) · repos and issue channels · ledgers, queues and
  state files.

Two deployments should be able to fail independently. If adopting the kit creates a path where an
outage in one takes the other down, the adoption is wrong regardless of how tidy it looks.

## 4. Definition of done

Adoption is complete when the deployment **renders from the same templates and follows the same
playbooks**, not when its files look identical to another deployment's. Divergence that is
documented and justified is a healthy outcome; the kit is the shared mechanism, not a uniform.
