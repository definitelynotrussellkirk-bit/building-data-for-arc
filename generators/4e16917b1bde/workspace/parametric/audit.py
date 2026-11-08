"""Finite learnability audit for the 4e16917b1bde depth-policy family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "depth_policy_audit_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling depth-policy prototype")
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)

Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def _conditional(grid: Grid, condition: bool) -> Grid:
    return P.apply_policy(grid, "reverse_depth" if condition else "same_depth")


def _reverse_within_source_bbox(grid: Grid) -> Grid:
    """Plausible shortcut: reverse only between occupied min/max depths."""
    facts = P.depth_facts(grid)
    divider = facts["divider_col"]
    result = [list(row) for row in grid]
    for row, col, value in facts["sources"]:
        depth = abs(col - divider)
        target_depth = facts["min_depth"] + facts["max_depth"] - depth
        direction = 1 if col < divider else -1
        target_col = divider + direction * target_depth
        result[row][target_col] = value
    return result


def _fixed_span(grid: Grid, span: int) -> Grid:
    facts = P.depth_facts(grid)
    safe = min(span, min(facts["divider_col"], len(grid[0]) - 1 - facts["divider_col"]))
    try:
        return P.apply_reverse_with_span(grid, safe)
    except ValueError:
        return P.apply_policy(grid, "same_depth")


def rivals() -> dict[str, Rule]:
    return {
        "always same depth": lambda grid: P.apply_policy(grid, "same_depth"),
        "always reverse depth": lambda grid: P.apply_policy(grid, "reverse_depth"),
        "reverse only left sources": lambda grid: _conditional(grid, P.depth_facts(grid)["source_side"] == "left"),
        "reverse only right sources": lambda grid: _conditional(grid, P.depth_facts(grid)["source_side"] == "right"),
        "reverse only even widths": lambda grid: _conditional(grid, len(grid[0]) % 2 == 0),
        "reverse only divider color five": lambda grid: _conditional(grid, P.depth_facts(grid)["divider_color"] == 5),
        "reverse only multicolor sources": lambda grid: _conditional(grid, len(P.depth_facts(grid)["source_colors"]) > 1),
        "reverse only when nearest depth is one": lambda grid: _conditional(grid, P.depth_facts(grid)["min_depth"] == 1),
        "reverse with fixed span four": lambda grid: _fixed_span(grid, 4),
        "reverse within occupied depth bounds": _reverse_within_source_bbox,
    }


def run_audit(*, seeds=(0, 17), demo_counts=(2, 3, 6), queries=4) -> dict[str, Any]:
    named = rivals()
    harmful: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    survivor_counts = {name: 0 for name in named}
    episodes = 0
    queries_checked = 0

    for selected in P.POLICIES:
        for seed in seeds:
            for demos in demo_counts:
                episode = P.generate_episode(seed, selected, demos, queries)
                episodes += 1
                queries_checked += len(episode["test"])
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        errors = P._generator().self_check(pair["input"])
                        if errors:
                            failures.append({
                                "setting": selected,
                                "seed": seed,
                                "demos": demos,
                                "split": split,
                                "index": index,
                                "errors": errors,
                            })
                for name, rule in named.items():
                    try:
                        survives = all(rule(pair["input"]) == pair["output"] for pair in episode["train"])
                    except Exception as exc:  # A rival error is a failed rival, but retain it.
                        survives = False
                        failures.append({
                            "setting": selected,
                            "seed": seed,
                            "demos": demos,
                            "rival": name,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                    if not survives:
                        continue
                    survivor_counts[name] += 1
                    for query_index, pair in enumerate(episode["test"]):
                        if rule(pair["input"]) != pair["output"]:
                            harmful.append({
                                "setting": selected,
                                "seed": seed,
                                "demos": demos,
                                "query_index": query_index,
                                "rival": name,
                                "input": pair["input"],
                                "intended_output": pair["output"],
                                "rival_output": rule(pair["input"]),
                            })
                            break

    return {
        "schema": "arcpuzzles-parametric-depth-policy-audit-v1",
        "task_id": P.TASK_ID,
        "settings_checked": list(P.POLICIES),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries_per_episode": queries,
        "episodes": episodes,
        "queries_checked": queries_checked,
        "rival_names": list(named),
        "survivor_counts": survivor_counts,
        "harmful_survivors": harmful,
        "input_failures": failures,
        "scope": "Finite source-bound audit against named executable Python rivals; intended labels are separately protected-Racket qualified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_audit()
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
