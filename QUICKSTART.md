# Quickstart — pick a tier, not the whole thing

The full kit is a two-tier orchestration with a committee, a fallback ladder and a dead-man. You do
not need all of it on day one, and installing it all at once is the slowest way to find out whether
it suits you. Each tier below works on its own and upgrades cleanly into the next.

**The actual setup command is: clone, open a coding agent in the repo, say "set me up".**
`CLAUDE.md` is the installer and it runs the interview. This page is only about *what to ask for*.

---

## What it costs

Two subscriptions you may already have, plus a few dollars of metered credit, covers everything.

| Pool | What it is | Marginal cost | Runs out by |
|---|---|---|---|
| Anthropic subscription | Pro/Max plan limits | **$0** | rate cap, resets weekly-ish |
| ChatGPT subscription | Plus/Pro via the Codex path | **$0** | rate cap, own clock |
| Prepaid token plan | a vendor's managed endpoint | prepaid | tokens, own clock |
| Metered credit | pay-per-token, any model | cents to dollars | dollars, does not reset |

Indicative per-1M-token metered prices from the shipped catalog: flash-class **$0.09/$0.18** ·
cheap-capable **$0.76/$2.42** · frontier non-US **$3/$15** · frontier US **$5/$25** and up.
**A day of bulk file-editing on the flash seat costs cents.** That is the whole cost story: keep
volume off the subscription pools so their rate caps stay available for judgment.

> The inversion most setups miss: cheap metered seats are not primarily about saving money, they are
> about **protecting the subscription rate caps**. See `playbooks/dispatch.md`.

---

## Tier 0 — laptop only (~10 minutes)

One subscription you already hold, one metered key. You get the role roster and a dispatcher that
knows which route is free.

1. `agents/*.md` → `~/.claude/agents/`
2. `bin/agent` → a PATH dir; metered key into a 600 env file
3. Copy `orchestration.example.toml` → `orchestration.toml`; delete the pools you do not have
4. `agent --list` → every row shows its harness and billing, no `[!!]`

**You now have:** role-based dispatch, the billing guard, and a committee you can call by hand.
**You do not have:** anything running while you sleep.

## Tier 1 — add a resident (~30 minutes)

A remote box, a tenant user, and a loop. Follow *Setup — remote tier* in `CLAUDE.md`.

**You now have:** a 24/7 loop consuming directives and journaling.
**You do not have:** any answer to "what if it dies?" — which it will, the first time the model
quota runs out. Do not leave Tier 1 running unattended for more than a few days.

## Tier 2 — make it survivable (~20 minutes) — **this is the one that matters**

The step most setups skip and then relearn during an outage.

1. **Fallback ladder** — `remote/fallback.sh.template` → `~/ops/fallback.sh`. Fill leg 2 with a seat
   on a **different scarcity axis** than your primary (a token plan or a second subscription, *not*
   a second seat on the same subscription), and leg 3 with a flash-class model at cents per run.
2. **Heartbeat + dead-man** — create the heartbeat and alert issues, install
   `remote/deadman.yml.template` into the control repo **from the laptop** (the resident's token
   deliberately cannot push workflow files).
3. **Drill both.** Force the primary to fail and watch a leg carry a real run. Stale the heartbeat
   and watch the page land. A leg that has never run is decoration, and both drills have caught real
   bugs on their first execution.

**You now have:** a loop that survives a quota wall and tells you when it doesn't.

## Tier 3 — committee and tuned dispatch

Turn on multi-seat review and let `[dispatch]` do the cost/skill/quota allocation. Two rules do most
of the work: **at least two challengers of distinct model lineage**, and **every subscription seat
gets a `failover`** to a metered one, so a dry allowance shrinks the bill instead of the committee.

---

## The five settings people get wrong

1. **Fallback on the same scarcity axis.** Two seats on the same subscription go dry together. Cross
   the axis or you have not built redundancy.
2. **A staleness bound set from the nominal cron.** Hosted sub-hourly schedules coalesce — measured
   51–96 min apart against a nominal 15. A bound below the real cadence false-fires until everyone
   ignores the channel. Measure first.
3. **A liveness probe that accepts HTTP 200.** Against a thinking model this certifies a *dead* seat
   as healthy. Require non-empty content, or better, do not probe at all — just try the seat.
4. **Everything at max effort.** Same mistake as everything on the best model. Match effort to the
   work class.
5. **A ranked queue that lives in two places.** One file, re-ranked in the same pass as any material
   change; every "what's next" is a pointer at it.

## Where to read next

`playbooks/dispatch.md` — cost × skill × quota, and the monthly ritual that keeps assignments
current as models and prices move.
`playbooks/continuity.md` — the operational disciplines, each traced to the failure that produced it.
`NOTES.md` — why the kit is shaped this way.
