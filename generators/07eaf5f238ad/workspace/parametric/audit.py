"""Finite learnability audit for the 07eaf5f238ad object-choice family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "object_choice_audit_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling object-choice prototype")
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)

Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def _conditional(grid: Grid, condition: bool) -> Grid:
    return P.apply_choice(grid, "last" if condition else "first")


def _duplicate_at(grid: Grid, position: int) -> bool:
    facts = P.input_facts(grid)
    normalized = position if position >= 0 else facts["header_count"] + position
    return normalized in facts["duplicate_header_positions"]


def rivals() -> dict[str, Rule]:
    return {
        "always first": lambda grid: P.apply_choice(grid, "first"),
        "always last": lambda grid: P.apply_choice(grid, "last"),
        "last only odd width": lambda grid: _conditional(grid, len(grid[0]) % 2 == 1),
        "last only even width": lambda grid: _conditional(grid, len(grid[0]) % 2 == 0),
        "last only square": lambda grid: _conditional(grid, len(grid) == len(grid[0])),
        "last only rectangular": lambda grid: _conditional(grid, len(grid) != len(grid[0])),
        "last only three headers": lambda grid: _conditional(
            grid, P.input_facts(grid)["header_count"] == 3
        ),
        "last only four headers": lambda grid: _conditional(
            grid, P.input_facts(grid)["header_count"] == 4
        ),
        "last only duplicate first header": lambda grid: _conditional(
            grid, _duplicate_at(grid, 0)
        ),
        "last only duplicate last header": lambda grid: _conditional(
            grid, _duplicate_at(grid, -1)
        ),
        "choose largest matching component": lambda grid: P.apply_size_choice(
            grid, "largest"
        ),
        "choose smallest matching component": lambda grid: P.apply_size_choice(
            grid, "smallest"
        ),
        "first selection packed in body order": lambda grid: P.apply_body_order(
            grid, "first"
        ),
        "last selection packed in body order": lambda grid: P.apply_body_order(
            grid, "last"
        ),
    }


def run_audit(*, seeds=(0, 17), demo_counts=(2, 3, 6), queries=4) -> dict[str, Any]:
    named = rivals()
    harmful: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    survivor_counts = {name: 0 for name in named}
    episodes = 0
    queries_checked = 0

    for selected in P.OBJECT_CHOICES:
        for seed in seeds:
            for demos in demo_counts:
                episode = P.generate_episode(seed, selected, demos, queries)
                episodes += 1
                queries_checked += len(episode["test"])
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        try:
                            P.input_facts(pair["input"])
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
        "schema": "arcpuzzles-parametric-object-choice-audit-v1",
        "task_id": P.TASK_ID,
        "settings_checked": list(P.OBJECT_CHOICES),
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
