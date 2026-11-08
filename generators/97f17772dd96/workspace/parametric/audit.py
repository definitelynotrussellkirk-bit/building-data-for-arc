"""Finite learnability audit for the 97f17772dd96 depth-order family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "depth_order_audit_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling depth-order prototype")
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)

Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def _conditional(grid: Grid, condition: bool) -> Grid:
    return P.apply_order(grid, "inner_to_outer" if condition else "outer_to_inner")


def _fixed_max(grid: Grid, maximum: int) -> Grid:
    return P.apply_inner_to_outer_with_max_depth(grid, maximum)


def rivals() -> dict[str, Rule]:
    return {
        "always outer-to-inner": lambda grid: P.apply_order(grid, "outer_to_inner"),
        "always inner-to-outer": lambda grid: P.apply_order(grid, "inner_to_outer"),
        "reverse only three frames": lambda grid: _conditional(grid, P.depth_facts(grid)["max_depth"] == 3),
        "reverse only two frames": lambda grid: _conditional(grid, P.depth_facts(grid)["max_depth"] == 2),
        "reverse only offset": lambda grid: _conditional(grid, P.depth_facts(grid)["offset"]),
        "reverse only concentric": lambda grid: _conditional(grid, not P.depth_facts(grid)["offset"]),
        "reverse only rectangular": lambda grid: _conditional(grid, len(grid) != len(grid[0])),
        "reverse only square": lambda grid: _conditional(grid, len(grid) == len(grid[0])),
        "reverse with fixed maximum two": lambda grid: _fixed_max(grid, 2),
        "reverse with fixed maximum three": lambda grid: _fixed_max(grid, 3),
    }


def run_audit(*, seeds=(0, 17), demo_counts=(2, 3, 6), queries=4) -> dict[str, Any]:
    named = rivals()
    harmful: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    survivor_counts = {name: 0 for name in named}
    episodes = 0
    queries_checked = 0

    for selected in P.DEPTH_ORDERS:
        for seed in seeds:
            for demos in demo_counts:
                episode = P.generate_episode(seed, selected, demos, queries)
                episodes += 1
                queries_checked += len(episode["test"])
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        try:
                            P.depth_facts(pair["input"])
                        except Exception as exc:
                            failures.append({
                                "setting": selected,
                                "seed": seed,
                                "demos": demos,
                                "split": split,
                                "index": index,
                                "error": f"{type(exc).__name__}: {exc}",
                            })
                for name, rule in named.items():
                    try:
                        survives = all(
                            rule(pair["input"]) == pair["output"]
                            for pair in episode["train"]
                        )
                    except Exception as exc:
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
                        rival_output = rule(pair["input"])
                        if rival_output != pair["output"]:
                            harmful.append({
                                "setting": selected,
                                "seed": seed,
                                "demos": demos,
                                "query_index": query_index,
                                "rival": name,
                                "input": pair["input"],
                                "intended_output": pair["output"],
                                "rival_output": rival_output,
                            })
                            break

    return {
        "schema": "arcpuzzles-parametric-depth-order-audit-v1",
        "task_id": P.TASK_ID,
        "settings_checked": list(P.DEPTH_ORDERS),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries_per_episode": queries,
        "episodes": episodes,
        "queries_checked": queries_checked,
        "rival_names": list(named),
        "survivor_counts": survivor_counts,
        "harmful_survivors": harmful,
        "input_failures": failures,
        "scope": "Finite source-bound Python rival audit; intended labels are separately protected-Racket qualified.",
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
