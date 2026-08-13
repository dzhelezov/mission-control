# Self-improvement — the harness maintains itself, on a cadence, with a gate

Most agent setups improve exactly once: at install. After that the model catalog moves, prices move,
a seat quietly degrades, the roadmap drifts from the issues, and the retro that was going to catch
all of it never runs. The config becomes an archaeological record of what someone believed in
month one.

The fix is not discipline. It is to make every improvement loop a **coded routine** with the same
four properties, and then to bound what those routines may change on their own.

---

## 1. What "coded" means here

A routine is real when it has all four. Miss one and it is decoration:

| Property | Why | Where it lives |
|---|---|---|
| **Cadence** | in cron, not in a document that says it should happen | `[routines.*].cron` |
| **Non-author reviewer** | the writer of a review cannot be its reviewer | `[routines.*].reviewer` |
| **Fail-closed page on a miss** | a routine that stops running must be louder than one that runs badly | `remote/routine.sh` |
| **Durable artifact** | evidence, dated; and the artifact is what proves the cycle happened | `[routines.*].artifact` |

The fourth is subtler than it looks. `routine.sh` records a cycle as *having happened* only if the
artifact exists and is non-empty. Otherwise a crashing routine is indistinguishable from a healthy
one with nothing to say, and the missed-cycle page never fires — the failure hides inside the very
mechanism meant to expose it.

**A routine is an LLM pass with mechanical scaffolding**, not a shell script pretending to reason.
Shell owns cadence, locking, the artifact path, the page, and reviewer dispatch. The model does the
judgment. And because a governance routine that silently stops when a quota dies is precisely the
decoration this exists to prevent, routines run through the same fallback ladder as the tick.

## 2. The four shipped routines

- **`retro`** — weekly. Incidents, instruments that read green through a real failure, deferred
  residue, cost per pool, a **decoration audit** (standing rules with no cadence, owner, or check —
  code them or drop them), and the count of things the human had to catch that the harness should
  have. That count is the maturity KPI and its target is zero.
- **`catalog-refresh`** — monthly. Re-derives dispatch from *live* prices and availability, hunts
  for models that now clear a capability floor more cheaply, verifies every fallback chain still
  crosses scarcity axes, and opens a PR moving the role table to match. **This is what replaces "a
  human periodically rewrites the model config."**
- **`seat-election`** — monthly. Re-decides who holds which seat on the period's real artifacts:
  findings that survived challenge, defects caught versus missed, whether the seat exercised the
  artifact or only read it, availability. Opens a PR with the evidence. An incumbent may not review
  its own seat.
- **`roadmap-pass`** — daily. Full enumeration, disposition per item, asserted count with its
  denominator stated, re-rank, owning issues updated.

Scheduling note that matters: put the periodic review **after** the subscription reset, never
before. The hours before a reset are when the primary seat is most likely dead, so a retro scheduled
just before it only lands in healthy weeks — and misses exactly the weeks worth reviewing.

## 3. The bound: propose, never self-apply

A harness that can rewrite its own governance has no governance. So:

> **A routine may propose any change to the harness — roster, dispatch policy, cadences, even these
> rules — but it lands as a PR. Never an in-place edit. Merge is committee plus human.**

`[routines.*].proposes` names the single path a routine may open a PR against; empty means
report-only. `roadmap-pass` is deliberately report-only: it re-ranks the queue it owns, and touches
no governance.

This is the same shape as publishing to any public surface: **the loop drafts, a gate publishes.**
It keeps self-improvement auditable — every change to how the system judges itself arrives as a
reviewable diff with a stated reason — and it means a bad routine produces a rejected PR rather than
a silently degraded committee.

Two failure modes the gate is specifically for:

- **Seat capture.** A seat that scores its own performance drifts toward keeping itself. Hence a
  non-incumbent reviewer, evidence from real artifacts rather than self-report, and a human merge.
- **Floor erosion.** Standards drift down one small justified step at a time. Any PR that *lowers* a
  capability floor, drops a challenger, or widens what a routine may self-apply should be treated as
  a governance change and reviewed as one — not as config tidying.

## 4. Re-evaluate on evidence, not on decree or inertia

Both directions are failures: appointing a seat because it is impressive, and keeping a seat because
it is already there.

- Score on **what actually happened** in the period, from artifacts, not impressions.
- Beware the **like-for-like trap**: a seat only ever handed one kind of task has not been compared
  fairly with one handed the full range. Say so rather than ranking through it.
- Give the incumbent the *same* brief as the challenger before concluding anything.
- Re-run a small bake-off on **recorded real tasks** when the evidence is thin. Synthetic prompts
  reward the wrong things.
- Keep the governance floor as a hard check every cycle: at least two live challengers, distinct
  lineages, no seat that is its own challenger or its own fallback. A seat change that breaks the
  floor is rejected regardless of scores.

## 5. Installing them

Render `remote/routine.sh.template` → `~/ops/routine.sh`, add one cron line per routine from
`[routines.*].cron`, and **drill the miss**: move a routine's `.last` stamp back beyond its cadence
and confirm the page fires. A fail-closed page that has never been observed firing is not a page —
it is an assumption, and this kit has a whole section on those (`continuity.md` §8).
