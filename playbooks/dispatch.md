# Dispatch — spending cost, skill and quota well, and re-deriving when the market moves

Two failures are near-universal in agent setups, and they are opposite:

1. **Everything runs on the best model.** Bulk file edits, log summarising, formatting — all on the
   frontier seat. It works, and it burns the subscription's *rate* cap, so the judgment call you
   needed on Thursday hits a wall you spent on boilerplate on Tuesday.
2. **Everything runs on the cheapest model.** Then a taste-critical API design ships at the quality
   of a $0.09/M seat and nobody notices until review, or later.

The fix is not a better default. It is treating dispatch as **three axes that must be spent
separately** — and accepting that the right answer changes every month, so what you maintain is the
*method*, not the table.

---

## 1. The three axes

**Cost** is not one number. Three different scarcities stop a seat, and they behave nothing alike:

| Scarcity | Behaves like | Failure shape | Instrument it with |
|---|---|---|---|
| `rate` (subscription) | free until it isn't | hard stop, days long, no warning | consumption vs. reset cycle |
| `tokens` (prepaid plan) | a tank | hard stop, own clock | plan balance |
| `dollars` (metered) | a meter | gradual, predictable | spend/day vs. balance |

The rule that follows: **a fallback must cross the axis.** Two rate-capped subscription seats are
not redundant with each other — they are two seats that will be dry in the same window sooner or
later, and eventually in the same hour. Read a candidate ladder by its *scarcity* column, not its
vendor column.

**Skill** is not one number either. Separate `intel` (can it solve the problem unsupervised) from
`taste` (is the output something you would ship). Bulk execution needs intel and barely any taste.
API design needs taste above all. Arbitration needs both. A single "quality" score collapses these
and produces the two failures at the top of this page.

**Quota state** is the axis everyone forgets, because it is the only one that is *dynamic at
dispatch time*. A seat that was perfect this morning is a 429 this afternoon.

## 2. Spend flat before metered — but protect the caps

Subscription seconds are free at the margin, so the naive rule is "use them for everything." Wrong,
and this is the single most valuable inversion in this document:

> **Cheap metered seats exist to protect subscription rate caps.**
> Pushing a day of file-editing onto a $0.09/M seat is not mainly about the dollars saved. It is
> about the weekly allowance still being there when something needs judgment.

So the order is: **flat first for work that needs the good model, cheap-metered first for volume.**
Not "flat first" flatly.

## 3. Never probe — fall through

Quota state is dynamic, so the instinct is a health check before dispatch. Resist it:

- A probe goes stale between check and use.
- A probe against a **thinking model** actively lies: cap it small and you get empty content, which
  is exactly what a broken provider returns, so it certifies dead seats as healthy
  (`continuity.md` §4).
- **Trying the seat is free when it works.** The attempt *is* the check. Fall through on failure,
  never mark a seat down, and it self-heals the moment quota resets.

The one legitimate exception is when you must know *before* committing to an expensive multi-step
plan. Then require **non-empty content** from the probe, and drill it against a known-broken seat.

Config: `[dispatch].on_seat_unavailable = "fall_through"`, `never_probe_seats = true`, and
`failover = "<model>"` on any seat whose pool can go dry.

## 4. Committee dispatch is a special case

For review, cheapness and even raw capability matter less than **independence**:

- **Distinct lineages.** Two seats from the same family share blind spots, so a second opinion from
  a sibling model is closer to one opinion at double the price.
- **Count seats that answered**, not seats that are listed. A committee whose second challenger is
  quota-dead has one challenger, and one challenger plus a proposer is a rubber stamp that still
  reports quorum.
- Therefore every subscription committee seat wants a `failover` to a *metered* seat: when the
  allowance dies, the committee survives at lower cost rather than silently shrinking.
- Give one seat a **conformance** lens — *does this match the directive it claims to execute?* —
  rather than pointing every seat at the artifact. Artifact-level reviewers reliably miss
  plan-level inversions.

## 5. Re-derivation is a coded routine, not a habit

Catalogs move monthly: new models, price cuts, a provider you now want to route around. A static
role table silently becomes wrong, and the symptom is subtle — nothing breaks, you just quietly
overpay and under-perform for months.

**So this is not a procedure you remember to follow.** It ships as the `catalog-refresh` routine
(`[routines.catalog-refresh]`, monthly, run by `remote/routine.sh`), with a cadence, a non-author
reviewer, a fail-closed page when it does not run, and a PR as its output. Its agenda is the
derivation:

1. **Refresh prices, context limits and availability** for every `[models]` row, from the provider —
   not from memory, and not from this file. Flag anything that moved >2× or vanished.
2. **Find what shipped since last time** that clears a `[dispatch.classes.*]` floor more cheaply than
   the incumbent.
3. **Re-sort each class's candidates**: cheapest model clearing the floor, first.
4. **Check the scarcity spread.** Every fallback chain must cross axes; no class entirely on one
   pool; recheck each pool's `blast_radius` against what it now funds.
5. **Open a PR** moving the role table to match, with a stated reason per change — and do not merge
   it. The table is the derived artifact; this policy is the source; a human plus the committee is
   the gate (`playbooks/self-improvement.md` §3).

Re-score `intel`/`taste`/`cost` only where evidence changed — a score moved without a reason you can
state is noise. Trigger an off-cycle run when a seat disappoints twice on the same class of work.

The reason this is coded rather than written down is the rule in `continuity.md` §6: a re-derivation
that happens "when someone notices" happens never. That applies to this page as much as anything.

## 6. Cost traps worth checking once

- **Reasoning models bill for thinking.** An uncapped call to a thinking model can spend heavily and
  return null content. Always set a token cap with headroom; the cap bounds thinking *and* answer
  together.
- **Effort levels are not free.** Running every seat at max effort is the same mistake as running
  everything on the best model. Match effort to class: bulk at low/high, judgment at xhigh/max.
- **Never route a vendor's models through a reseller when you hold a first-party subscription.** You
  pay a markup to get the same weights off the plan you already bought. Where a reseller *is* the
  route, pin every model slot — a compat proxy serves whatever id you send it, so a leaked default
  buys the expensive model through the expensive path.
- **One key across two projects is one pool.** You lose per-project attribution and couple the blast
  radius. Split keys, and set per-key limits that *sum within the balance* — a key ceiling above the
  account balance isolates nothing.
- **Distil before escalating.** Judgment seats should read a briefing packet built by a cheap
  long-context seat, never a raw dump. This is what makes the expensive seat affordable, and it
  usually improves the answer too.
- **Instrument the pool that stops the loop, first.** It is easy to track metered spend to the cent
  because the API makes it easy, and to track the subscription allowance — the thing everything
  actually depends on — not at all.
