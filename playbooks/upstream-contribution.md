# Playbook — analyze, verify, and contribute to a repo you do not own

For pointing the kit at a **live GitHub project with active maintainers**. The goal is to be a
useful contributor, not a bot that generates work for other people. Everything here is downstream
of one rule:

> **The maintainer's time is the scarcest resource in the project. Spend your own tokens freely and
> theirs almost never.**

An agent that opens twelve plausible PRs has not helped; it has handed someone twelve reviews. An
agent that opens one PR with a failing test, a fix, and a reproduction has paid for its own review.

Render this per project and append it to the mission doc, or hand it to a session as its goal
preamble.

---

## 0. Before anything: which mode are you in?

| Mode | Write access | What you may do |
|---|---|---|
| **Observer** | none | read, build, test, reproduce, write findings to your own repo |
| **Contributor** | fork only | everything above + PRs from your fork |
| **Committer** | upstream | only if a human has said so, in writing, for this repo |

Default to **Contributor**. Never self-promote between modes. The `gh` PAT should make this
structural, not a matter of good behaviour: scope it to *your fork* plus read on upstream, with no
`workflow` scope, so an over-eager agent physically cannot push to upstream branches.

```bash
gh auth status                                    # confirm which token is live
gh repo view OWNER/REPO --json viewerPermission   # confirm what it can actually do
```

## 1. Orient before you touch anything

The single most common way an agent interferes is by doing work someone is already doing. Look
first, and look at the *last 30 days*, not the README.

```bash
gh repo view OWNER/REPO
gh pr list  -R OWNER/REPO --state open  --limit 50 --json number,title,author,updatedAt,isDraft
gh pr list  -R OWNER/REPO --state merged --limit 30 --json number,title,author,mergedAt
gh issue list -R OWNER/REPO --state open --limit 50 --json number,title,labels,assignees,comments
git -C ./checkout log --since="30 days" --pretty='%an %ad %s' --date=short | head -50
```

Read, in this order: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, the PR template, the last five merged
PRs (this is how you learn the *real* review bar and commit-message style), and the issue labels
that maintainers actually use (`good first issue`, `help wanted`, `needs-repro`).

Build the map before you build anything:

- Who is the main contributor, and what are they working on **right now**? Their open PRs and
  recent commits are a no-go zone: do not refactor, rename, or reformat anything they are touching.
- Which issues are assigned, and which are stale-but-claimed? A claimed issue is claimed.
- What is the project's stated roadmap? Contributions off the roadmap get closed, however good.

## 2. Analyze — produce evidence, not opinions

Work on a clean checkout of your fork. Everything you claim must be reproducible by a stranger.

```bash
gh repo fork OWNER/REPO --clone --remote     # origin = your fork, upstream = theirs
cd REPO && git remote -v
<the project's own build + test commands, from CONTRIBUTING.md>
```

Three passes, cheapest first:

1. **Does it build and pass from cold?** A fresh clone, the documented setup steps, exactly as
   written. Failures here are the most valuable finding a newcomer can report, because maintainers
   stop seeing them.
2. **Does the documented behaviour match the actual behaviour?** Run the quickstart. Click the
   thing. Compare against the docs.
3. **Only then, the code.** Correctness, invariants, error paths, resource handling, concurrency.

Route the passes by cost: the long-context seat reads the whole repo, the cheap seat compresses
logs and diffs, the judgment seat only ever sees the distilled packet.

```bash
agent --role long-context "Map OWNER/REPO: entry points, module boundaries, the invariants that hold
  the design together, and the three places a bug would hurt most. Cite file:line."
agent --role compress -f build.log "Distil to: what failed, the minimal repro, the suspected cause."
agent --role cto -f packet.md "Given this, what is the single most useful contribution we can make
  that the maintainers would actually want? Say what NOT to do."
```

**Do not open an issue yet.**

## 3. Verify — the bar that makes a finding worth someone's attention

A finding is not real until all four hold:

1. It reproduces on a **clean checkout of upstream `main`**, not just your working tree.
2. You have the **minimal** reproduction — smallest input, fewest steps.
3. You can name the **mechanism**, not just the symptom, at `file:line`.
4. You have checked it is **not already reported** (search open *and* closed issues, and open PRs).

```bash
git checkout -B verify upstream/main && <clean build> && <minimal repro>
gh issue list  -R OWNER/REPO --state all --search "<key phrase>" --limit 20
gh pr list     -R OWNER/REPO --state all --search "<key phrase>" --limit 20
```

Run findings through the review committee **before** they leave your machine, on distinct model
lineages, and drop anything that does not survive. This is where an autonomous contributor earns
its place: your false-positive rate is the only thing maintainers will remember.

```bash
for seat in kimi sol qwen; do
  agent --model $seat -f finding.md "Try to REFUTE this finding. Default to 'not a bug' if
    uncertain. Name the specific reason it is wrong, or say CONFIRMED with the mechanism." &
done; wait
```

Majority refutes → discard it. Do not "report it anyway, just in case."

## 4. Contribute — small, single-purpose, complementary

**Claim before you code, in the open.** One comment on the issue: what you intend to do, roughly
how, and an estimate. If nobody objects in a day, proceed. If a maintainer says "I'm on it," you
are done — thank them and move on.

Then, per contribution:

- **One PR, one purpose.** No drive-by refactors, no reformatting, no dependency bumps riding along.
- **Follow the local style**, not your preferred style. Match the surrounding code's naming, comment
  density, and idioms. Do not introduce a new abstraction to fix a two-line bug.
- **Test first**: a test that fails on upstream `main` and passes with your change. If you cannot
  write one, say so explicitly in the PR body and explain why.
- **Never touch** `.github/workflows/`, release configs, or CI credentials. Workflow-file changes
  stay human — the PAT has no `workflow` scope precisely so this is enforced, not remembered.
- **Rebase onto them, never over them.** If a maintainer pushes while your PR is open, rebase your
  branch onto theirs, keep their commits intact, and never force-push a shared branch.
- **Cap concurrency.** At most **two open PRs** at a time on a repo you do not own, and no new one
  until an earlier one gets a response. A queue of unreviewed PRs is interference.
- **Write the PR for the reviewer**: what changed, why, how you verified it, what you did *not*
  verify, and the risk if you are wrong. Candor about limits buys more trust than confidence does.
- **Disclose the tooling** if the project asks for it (many now do — check `CONTRIBUTING.md`).

```bash
git checkout -b fix/short-descriptive-name upstream/main
# ... change + test ...
<project test command>                    # green, from cold
gh pr create -R OWNER/REPO --base main --head YOUR_FORK:fix/short-descriptive-name \
  --title "..." --body-file pr.md
```

Then **stop and wait.** Respond to review comments promptly and without arguing about taste. If a
maintainer says no, the answer is no; close it and record why in your own journal.

## 5. Collaborating, not colliding — the standing rules

- Orient on open PRs and issues **before every work session**, not once at the start. The state
  changed while you were thinking.
- If your change overlaps someone's open PR: **comment on their PR** offering the finding, rather
  than opening a competing one. Credit them.
- Never revert, rewrite, or "clean up" another contributor's work. If you believe it is wrong,
  say so on their PR with evidence and let a maintainer decide.
- Prefer **complementing**: a test for their fix, a repro for their bug, docs for their feature.
  These are welcome almost everywhere and compete with nobody.
- Batch small observations into **one** issue, not five. Ten trivial issues from an unknown account
  reads as spam regardless of correctness.
- Public-surface rule applies with full force: **never** post infra internals — host names, paths,
  tenant names, budgets, the existence of this box — into any public repo. Operational detail goes
  to the private journal.
- Rate-limit yourself socially, not just technically: a few high-value contributions per week beats
  a daily stream.

## 6. Running it

**One-shot analysis, no writes anywhere** (safe first move on any repo):

```bash
prime-agent -p --cwd ~/work/REPO \
  --provider openrouter --model moonshotai/kimi-k3 --thinking max \
  --append-system-prompt "$(cat playbooks/upstream-contribution.md)" \
  "Observer mode. Analyze OWNER/REPO per the playbook sections 1-2. Produce findings.md: the map,
   the cold-build result, and ranked candidate contributions with evidence. Open nothing, push
   nothing."
```

**Verified contribution loop, gated on the project's own tests:**

```bash
prime-agent --cwd ~/work/REPO \
  --provider openai-codex --model gpt-5.6-sol --thinking xhigh \
  --goal "Land one verified, maintainer-welcome contribution to OWNER/REPO, following
          playbooks/upstream-contribution.md. Contributor mode: fork only, at most two open PRs,
          claim before coding, never touch workflows." \
  --goal-token-budget 400000 \
  --autonomous --autonomous-gate "<the project's own test command>" \
  --autonomous-gate "git diff --cached --name-only | grep -qv '^.github/workflows/'" \
  --autonomous-max-turns 40
```

The second gate is the interference guard expressed as a command: the run cannot finish while a
workflow file is staged. Add one gate per rule you actually care about — a gate is worth more than
a paragraph of instruction, because the harness enforces it.

**Resident, contributing continuously:** run `remote/resident.sh` with the goal above, then let the
native schedule re-orient every tick. Steer without ssh:

```bash
prime-agent send mc-resident "Upstream merged #412 — rebase our open PR and re-run the gate."
prime-agent send mc-resident "/goal status"
```

## 7. Definition of done

A contribution is done when it is **merged**, or when a maintainer has declined it and you have
recorded why. Not when the PR is opened. Track both numbers honestly in the journal — the ratio of
opened to merged is the only real measure of whether this is helping.
