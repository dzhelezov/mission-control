#!/usr/bin/env bash
exec 9>/home/claude-ops/ops/.lock; flock -n 9 || exit 0
[ -f ~/.claude/.credentials.json ] || { echo "$(date -u +%FT%TZ) no-auth" >> /home/claude-ops/ops/runs/skipped.log; exit 0; }
OPS=/home/claude-ops/ops
R=$OPS/runs/$(date -u +%Y%m%dT%H%M)
cd $OPS/portal-ponder && git fetch -q origin && git checkout -q main && git pull -q

# ---- zero-token idle gate: skip the LLM invocation when nothing changed ----
# Fingerprint of everything the orchestrator would react to. gh failures inject
# randomness -> fingerprint differs -> we RUN (fail open, never fail silent).
FP=$( {
  git ls-remote -q origin 2>/dev/null | sort
  gh pr list --state open --json number,updatedAt 2>/dev/null || echo "GH_PR_FAIL_$RANDOM"
  gh issue list --state open --json number,updatedAt 2>/dev/null || echo "GH_ISSUE_FAIL_$RANDOM"
  systemctl is-active soak-b euler-bench2a euler-soak euler-probe flagship-clean 2>/dev/null
  stat -c '%Y %s' "$OPS/LEDGER.md" 2>/dev/null
} | sha256sum | cut -d' ' -f1 )
NOW=$(date +%s); LAST=$(cat "$OPS/.tick-lastrun" 2>/dev/null || echo 0)
if [ -f "$OPS/.tick-force" ]; then
  rm -f "$OPS/.tick-force"   # manual override: touch ~/ops/.tick-force to force a run
elif [ "$FP" = "$(cat "$OPS/.tick-fp" 2>/dev/null)" ] && [ $((NOW - LAST)) -lt 21600 ]; then
  # unchanged state + last real run < 6h ago -> zero-token skip
  echo "$(date -u +%FT%TZ) skip-idle fp=${FP:0:12}" >> "$OPS/runs/ticks.log"; exit 0
fi
echo "$FP" > "$OPS/.tick-fp"; echo "$NOW" > "$OPS/.tick-lastrun"
# ---------------------------------------------------------------------------

timeout 3000 claude -p "Ops tick: follow CLAUDE.local.md exactly — ops sweep first, then continue the backlog from where the ledger LEDGER.md (+ your previous run logs in /home/claude-ops/ops/runs/) left off. Be surgical; leave durable state (PR comments, LEDGER.md updates) for the next tick." \
  --model claude-opus-4-8 --effort xhigh --dangerously-skip-permissions > "$R.log" 2>&1
echo "$(date -u +%FT%TZ) exit=$?" >> "$OPS/runs/ticks.log"
