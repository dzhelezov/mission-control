# Continuity — keeping an autonomous loop alive, honest, and observable

Everything here was paid for by an outage, a silent failure, or a wrong decision in a real 24/7
deployment. None of it is theoretical, and none of it is expensive to install. Read it before you
tune cadences or add a sensor.

The through-line: **an autonomous loop fails quietly.** It has no user to notice a blank screen.
Every mechanism below exists to convert a quiet failure into a loud one, or to keep the loop running
through a failure that would otherwise stop it.

---

## 1. Continuity — the model path will die, on a schedule you don't control

A resident loop pinned to one model dies when that model's quota dies. This is not an edge case; it
is a weekly event on subscription pools and a monthly one on metered pools.

**Two pools can be dry at the same time.** A two-leg design (primary + one fallback) reads as
redundancy right up until both legs are token-plan seats and both exhaust in the same window. The
durable answer is a leg that is **too cheap to quota out** — a flash-class model at cents per run.
Its job is not quality. Its job is that the loop keeps its heartbeat, keeps journaling, and keeps
refusing to fabricate until the good seat comes back.

Design rules, each one learned the hard way:

- **Legs are per-invocation and never sticky.** Try the primary on *every* run and fall through on
  failure. Do not set a "degraded mode" flag. The primary attempt *is* the availability check: it
  costs nothing when healthy, it needs no probe, it cannot go stale, and the loop self-returns to
  the good seat on the first run after the quota resets.
- **Pin every model slot in an env-swap config.** An OpenAI- or Anthropic-compatible proxy serves
  whatever model ID you send it. If one CLI default leaks through — a "small/fast model" slot, a
  summarizer slot — you will silently buy the expensive model through the expensive route. Set
  every slot the harness reads, then **verify from the run transcript which model IDs actually went
  out.** Do not trust the config; trust the transcript.
- **Use a scratch config directory per leg.** Most CLIs prefer a stored credentials file over the
  environment variable you just set. A leg that inherits the primary's config directory will
  cheerfully authenticate as the primary and report a confusing failure.
- **Failures in the fallback path must not corrupt the primary's result.** If the fallback machinery
  itself errors, leave the primary's exit code untouched. A rescue path that turns a clean failure
  into an ambiguous one is worse than no rescue path.
- **Never route a vendor's models through a reseller when you hold a first-party subscription.**
  It is more expensive and usually less capable than a purpose-picked cheap model. The fallback
  ladder should change *vendors* as it descends, not just endpoints.
- **A leg that has never run is decoration.** Drill it deliberately — force the primary to fail and
  watch the fallback carry a real run end to end. The first drill of one such leg found a bug the
  wiring review had missed. Schedule the drill; do not wait for a natural double failure, which may
  be weeks away and will arrive at the worst time.

`remote/fallback.sh.template` implements this ladder. `remote/tick.sh.template` calls it.

## 2. Liveness — build the pager before you need it

A loop that dies at 22:00 and is noticed at 12:00 has lost the night. The fix is cheap and must
exist **before** the first outage, not after it.

Three legs, deliberately not identical:

1. **The loop reports on itself.** Every run writes a machine-parseable heartbeat record —
   timestamp, exit code, consecutive-failure count, which leg served it. Write it **even when the
   run fails**; a heartbeat that only appears on success is a success detector, not a liveness
   detector.
2. **Something off the box watches the heartbeat.** A scheduled job elsewhere (a CI cron is enough)
   parses the record strictly, **fails closed** on anything it cannot parse, and raises an alert.
   On-box monitoring cannot report that the box is gone.
3. **A box-local sidecar** on its own lock and its own schedule, as the fast path for the case where
   the loop is wedged but the machine is fine.

Then state the residual out loud: if legs 2 and 3 both deliver alerts through the same service, they
are **correlated** — one provider outage silences both. Name that gap in your notes even if you
accept it. An unnamed correlated failure is the one that surprises you.

**Set staleness thresholds from measured delivery, not nominal schedule.** A hosted cron advertised
as every 15 minutes was observed coalescing and delivering 51–96 minutes apart under load. A
45-minute staleness bound sat *below* the real cadence and false-fired almost every gap, which
trained everyone to ignore the channel. Measure the worst case over a real day, then set the bound
above it with margin. Alert fatigue on the dead-man channel is a liveness failure with extra steps.

`remote/deadman.yml.template` is leg 2. The heartbeat writer is in `remote/tick.sh.template`.

## 3. Perception — a queue can go invisible while every sensor reads green

The subtlest failure in this kit's history, and the one most worth internalizing.

A sweep that selects work by "changed since my last cursor" has a fatal property: **an item that is
filed and then ignored leaves perception permanently.** Not working on it is precisely what removes
it. The queue reports zero items, the loop declares itself idle, and the ignored work becomes
*more* invisible the longer it is ignored. Dozens of open items sat at their creation timestamps
while the loop truthfully reported nothing new.

The fix is small and mechanical:

- **Enumerate every open item, ignoring "last updated".** Full enumeration every cycle. It is a
  cheap API call; the delta optimization is what broke.
- **Carry an explicit disposition per item** — `ranked` / `gated` (name the gate) / `deferred` (name
  the reason). "Not mentioned" must not be a reachable state.
- **Assert the count.** The run fails loudly if the enumeration returns a different number than the
  disposition list accounts for.
- **Check the denominator.** A count assertion only certifies the set it *chose* to count. One
  deployment asserted its count correctly and completely over four of seven sources — the assertion
  passed while a release-blocking item sat outside the enumeration by construction. When a sensor
  reports a number, verify its scope against ground truth, not against itself.
- **Keep one ranked queue file** that the loop re-reads every cycle and re-ranks in the same cycle
  as any material change. Each run's "what's next" is a *pointer at that file*, never a competing
  list. A plan that names a source of truth and then ranks something else is worse than no plan: it
  looks governed.
- **Update the owning item, not just the log.** Progress recorded only in a journal means the
  tracker shows an untouched item forever, and the next reviewer — human or model — reads it as
  never started.

## 4. Seats and probes — the instrument can be the failure

**Never probe a thinking model with `max_tokens=1`.** A reasoning model emits its reasoning first
and writes `content` only after it stops thinking. Cap it at 1 and you get empty content — which is
*exactly* the response a broken provider returns. The probe's success test and the seat's failure
mode become the same event, so the probe certifies a dead seat as healthy. This happened, and it
kept a committee seat listed as live for a full day while every call to it returned nothing.

Rules that follow:

- **A liveness probe must require non-empty content**, not HTTP 200 and not a non-error exit.
- **Always set `max_tokens` on a thinking model, with headroom** — it bounds reasoning *and* answer
  together. Unset, some providers bill the reasoning and return null content after a long wait; the
  same call with an explicit cap answers in seconds. One missing parameter looked like three
  different bugs before anyone measured it.
- **Read the `reasoning` / `reasoning_details` fields when content is null** before concluding the
  seat is broken.
- **Prefer no probe at all.** The per-call failover of §1 is strictly better than a probe: try the
  seat, fall through on failure. Zero cost when healthy, no stale state, and nothing to lie to you.
  Add a probe only where you must know *before* dispatching, and then drill it against a
  known-broken seat.
- **Fail-safe direction matters.** Only a positive not-reachable signal should remove a seat. Stale
  state, an unparseable record, or a seat the prober doesn't cover must all mean "try it anyway."
  Skipping a live seat is worse than trying a dead one: the second costs one failed call, the first
  can strand a decision with a healthy seat sitting idle.

## 5. Governance — nothing is decided single-handed

An autonomous loop with one reviewer is a loop with no reviewer.

- **A proposal stands as a proposal** until it has been challenged and every objection is folded in
  or refused with a stated reason.
- **Require at least two live challengers with distinct model lineages.** Same-lineage reviewers
  share blind spots. Count only seats you have *verified* are answering — see §4, because a lying
  probe will happily tell you the quorum is met.
- **A seat cannot challenge itself,** and it cannot be its own fallback. Name a different seat for
  each role, and check that the fallback chain does not loop back.
- **Which model holds a seat is settled by evaluation, not decree** — and re-evaluated on a
  schedule, because the catalog moves monthly.
- **Widen the review brief beyond the artifact.** A reviewer asked "attack this diff" will find real
  defects in the diff and miss that the plan contradicts the directive it claims to follow. Add a
  *conformance* review type: does this work match the thing it says it is executing? One deployment
  ran five sound artifact-level reviews and none of them caught a portfolio-level inversion.
- **Exercise the artifact.** Build it, run it from clean, drive it. A diff read is not a review.

**Rank project work above harness work.** A loop that can improve itself will, forever. Cap the
harness queue explicitly, put the residue on the scheduled retro (§6), and let delivery run. The
counterpart rule for the human/gateway tier: **check whether the loop already perceives an item
before reporting it as undone.** Handing a loop a list of things already ranked in its own queue
inverts the priority you just set, and costs cycles to service the report. The correct output of a
process review that finds the process working is "the process is working."

## 6. Cadence — a routine without a mechanical check is decoration

The rule, stated plainly: **a standing instruction with no cadence, no named owner, and no automated
check that it happened is decoration.** It will be followed once, on the day it is written, and
never again — and nothing will notice. This has been observed more than once, including for the very
review meant to catch it.

So for any recurring obligation:

- **Put it in cron**, not in a document that says it should happen.
- **Name the reviewer, and make it not the author.**
- **Page when it is missing**, fail-closed, and prove the page fires by drilling a skipped cycle.
- **Fix the agenda** so it does not degrade into whatever is on someone's mind.
- **Require an artifact**, and treat *only* a produced artifact as evidence the cycle happened —
  otherwise a crashing routine looks exactly like a healthy quiet one and the miss-page never fires.
- **Place the slot deliberately.** Schedule a periodic review *after* the subscription reset, not
  before it: the hours before a reset are exactly when the primary seat is most likely dead, and a
  review that only lands in healthy weeks systematically misses the weeks worth reviewing.

This is not advice to follow by hand — `remote/routine.sh.template` plus `[routines.*]` implements
all six for the retro, the roadmap pass, seat re-election and catalog re-derivation, so the harness
maintains itself rather than waiting for someone to rewrite its config. The bound that keeps that
safe (**routines propose via PR, never self-apply**) is in `playbooks/self-improvement.md`.

## 7. Budget — measure the currency you actually depend on

A deployment tracked its metered spend to the cent — daily polls, thresholds, a state file — and
tracked the subscription allowance that every single run depended on **not at all**. The word
"allowance" appeared exactly once in the whole ops tree: in the text of the page that fires *after*
it is gone.

- **Instrument the pool that stops the loop**, first. Precision on a side pool is not coverage.
- **One key across two projects is one pool and one blast radius** — and no per-project attribution,
  which you will want the first time spend jumps. Split keys per project.
- **Separate keys give attribution; only per-key limits that sum within the available balance give
  isolation.** A key with a ceiling above the account balance is not isolated from anything.
- **Know what a pool's exhaustion takes down.** If one metered pool funds three committee seats and
  the cheap fallback leg, then emptying it costs the reviewers *and* the continuity floor at once.
  Write that sentence down for each pool; it is usually a surprise.

## 8. The class: instruments that report green through a real failure

Five separate sensors in one deployment reported healthy through a real failure: a memory alert
silent at the threshold it existed to catch, a staleness watcher flapping on cron jitter until it
was ignored, a seat probe certifying a dead seat, a fingerprint reading an abandoned file, and a
count assertion certifying the wrong denominator. That is not five accidents. It is a class.

**Every sensor you add needs a negative control: drive it against a known-bad state and watch it go
red.** A sensor that has only ever been observed green is an untested branch that happens to be
load-bearing. Two related habits:

- **A safeguard that is built but not wired is not a safeguard.** Helpers passing their self-tests
  while the wiring stayed pending is exactly how a silent outage happens anyway.
- **Verify the premise before reasoning on top of it.** Confident chains built on an unchecked
  assumption are the most expensive failure mode here, because they *look* like diligence.

## 9. Operational gotchas worth the one line each

- **Never overwrite a script a running shell is executing.** Bash re-reads the file progressively as
  it runs; editing in place corrupts the live run in ways that look like a logic bug. Write beside
  it and atomic-`mv`, and wait for the current run to finish.
- **Keep a dated backup beside any live operational file you change**, and verify syntax
  (`bash -n`) on the target host before the swap.
- **A run that inherits the wrong working directory** may find nothing readable and conclude the
  world is broken. Set the working directory explicitly in every entry point, including drills and
  one-off launchers — production paths are often immune while the hand-run launcher is not.
- **Prefer expressing a rule as an automated gate over stating it in prose.** The harness enforces a
  gate; it only reads a paragraph.
- **Honest error beats any fabricated response.** A resident that cannot verify state must say so
  and stop, never invent a green. When a cheap fallback model refused to write an unverifiable
  status and journaled the failure instead, that was the system working.
