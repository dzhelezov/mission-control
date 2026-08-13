"""mission-control -> prime-agent continual harness bootstrap.

Run this ONCE inside the resident session's IPython kernel. It translates the kit's
configuration into prime-agent's own native machinery, so nothing about the roster
depends on shelling out to `bin/agent`:

  [roles.*] + agents/<role>.md  ->  harness SUBAGENT specs (global, refinable)
  routing principles            ->  a harness MEMORY
  the Anthropic billing rule    ->  a harness PROMPT note (always in-context policy)

Model ids from the catalog are resolved to exact `rlm.find_models` selectors here, at
bootstrap time, so every spec carries a selector the host will actually accept — and an
unreachable model fails loudly now instead of mid-mission.

Usage, from the resident session:

    %run ~/mission-control/prime/bootstrap.py
    await bootstrap()                      # add force=True to overwrite existing entries
    print(rlm.harness.overview(global_=True))

Re-run it after editing orchestration.toml. It upserts by stable id (`mc-<role>`), so it
never duplicates, and `refine.run()` improvements to a spec survive unless force=True.
"""

import os
import tomllib
from pathlib import Path

REPO = Path(os.environ.get("MC_REPO", Path(__file__).resolve().parent.parent))
CONFIG = Path(os.environ.get("MC_CONFIG", REPO / "orchestration.toml"))
if not CONFIG.exists():
    CONFIG = REPO / "orchestration.example.toml"


def _role_body(role: str) -> str:
    """agents/<role>.md minus its frontmatter — the role's operating instructions."""
    path = REPO / "agents" / f"{role}.md"
    if not path.exists():
        return ""
    text = path.read_text()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text.strip()


def _upsert(kind: str, entry_id: str, title: str, content: str, path: str, force: bool):
    create = getattr(rlm.harness, f"create_{kind}")          # noqa: F821 — kernel global
    update = getattr(rlm.harness, f"update_{kind}")          # noqa: F821
    existing = rlm.harness.get("prompt" if kind == "prompt_note" else kind,  # noqa: F821
                               entry_id, global_=True)
    if existing and not force:
        print(f"  = {entry_id:<22} kept (exists; force=True to overwrite)")
        return existing
    if existing:
        return update(entry_id, title, content, path=path, global_=True)
    return create(title, content, id=entry_id, path=path, global_=True)


async def _selector(model_id: str) -> str:
    """Exact provider/model selector for rlm(..., model=...); raises if unreachable."""
    matches = await rlm.find_models(model_id)                # noqa: F821
    exact = [m for m in matches if m.id == model_id] or matches
    if not exact:
        raise RuntimeError(
            f"no reachable model for '{model_id}' — check auth.json / models.json, then re-run")
    return exact[0].selector


async def bootstrap(force: bool = False):
    cfg = tomllib.loads(CONFIG.read_text())
    models, pools, roles = cfg["models"], cfg["pools"], cfg.get("roles", {})
    guards = cfg.get("guardrails", {})
    print(f"mission-control bootstrap  ({CONFIG})\n")

    # 1) Resolve every catalog model to a live selector. Anthropic models are deliberately
    #    NOT resolved here: they belong on the `claude` harness (plan limits, not per-token).
    selectors, skipped = {}, {}
    for key, m in models.items():
        pool = pools.get(m.get("pool"), {})
        if pool.get("provider") == "anthropic" and guards.get("anthropic_subscription_only", True):
            skipped[key] = "anthropic — runs on the claude harness, not here"
            continue
        try:
            selectors[key] = await _selector(m["id"])
            print(f"  ✓ {key:<7} {m['id']:<32} -> {selectors[key]}")
        except Exception as exc:                                   # noqa: BLE001
            skipped[key] = str(exc)
            print(f"  ✗ {key:<7} {m['id']:<32} {exc}")

    # 2) One subagent spec per role. The spec IS the delegation contract: the child's
    #    operating instructions plus the exact spawn call, so the parent never guesses.
    print("\nsubagent specs:")
    for role, spec in roles.items():
        seats = spec.get("seats") or []
        lines = [f"Role `{role}` ({spec.get('kind', 'work')}) from mission-control orchestration.toml.", ""]
        spawnable = False
        for seat in seats:
            key = seat.get("model")
            lens = seat.get("lens") or seat.get("as") or ""
            if key in selectors:
                effort = seat.get("effort") or ""
                lines.append(
                    f"- {lens or 'seat'}: await rlm(TASK, name='{role}-{key}', "
                    f"model='{selectors[key]}')"
                    + (f"   # thinking: {effort}" if effort else ""))
                spawnable = True
            else:
                lines.append(
                    f"- {lens or 'seat'}: model `{key}` is not spawnable here "
                    f"({skipped.get(key, 'not in catalog')}). Reach it with "
                    f"`agent --model {key} ...` from a %%bash cell instead.")
        esc = spec.get("escalation") or {}
        if esc:
            lines += ["", f"Escalate to `{esc.get('model')}` when: {esc.get('when', 'the seat misses the bar')}."]
        arb = spec.get("arbiter") or {}
        if arb:
            lines += ["", f"Arbiter `{arb.get('model')}` decides when: {arb.get('when', 'seats split')}."]
        body = _role_body(role)
        if body:
            lines += ["", "--- operating instructions for the child ---", body]
        lines += ["", "The child replies with `await agent_message.send(msg, receiver_role='parent')`."]
        _upsert("subagent", f"mc-{role}", f"mission-control: {role}", "\n".join(lines),
                "mission-control", force)
        print(f"  + mc-{role:<18} seats={len(seats)} spawnable={spawnable}")

    # 3) Routing policy as memory, billing rule as an always-on prompt note.
    catalog = "\n".join(
        f"- {k}: {m['id']} · pool {m.get('pool')} ({pools.get(m.get('pool'), {}).get('billing', '?')})"
        f" · cost {m.get('cost')} intel {m.get('intel')} taste {m.get('taste')}"
        for k, m in sorted(models.items()))
    _upsert("memory", "mc-routing", "mission-control: routing policy", "\n".join([
        "Judge the output, not the price tag; escalate on a miss without asking.",
        "When axes conflict for anything that SHIPS: intelligence > taste > cost.",
        "Final authorship of shipping code/API/correctness logic requires taste >= 7.",
        "Volume (bulk, logs, distillation, suites) goes to the cheapest capable seat — that is",
        "what keeps the subscription pools' weekly caps free for judgment work.",
        "Review is a committee of blind seats with distinct lenses AND distinct model lineages,",
        "plus an arbiter for splits. Review must exercise the built artifact, not read the diff.",
        "", "Catalog:", catalog,
    ]), "mission-control", force)
    print("  + mc-routing")

    _upsert("prompt_note", "mc-billing-guard", "mission-control: Anthropic billing guard", "\n".join([
        "Anthropic models (opus/fable/sonnet) run ONLY on the `claude` harness, where they draw on",
        "Claude Pro/Max plan limits. Routing them through this harness's Anthropic provider bills",
        "claude.ai extra usage per token instead. Never spawn an Anthropic child here; shell out",
        "with `agent --model opus ...` from a %%bash cell, which enforces the same rule.",
        f"Metered spend across all metered pools is bounded by ${guards.get('metered_budget_usd', '?')}.",
    ]), "policy", force)
    print("  + mc-billing-guard\n")
    print(rlm.harness.overview(global_=True))                # noqa: F821


print(__doc__.split("Usage,")[0].strip())
print("\nready — now run:  await bootstrap()")
