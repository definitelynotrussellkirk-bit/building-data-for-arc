"""Finite learnability audit for the 9a1459fe40d0 mark-policy family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("mark_policy_audit_prototype", _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling mark-policy prototype")
P = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(P)

Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def _blank(grid: Grid) -> Grid:
    return [[0 for _ in row] for row in grid]


def _mismatch_rows(grid: Grid):
    return P.pair_facts(grid)["mismatches"]


def _mark_both(grid: Grid) -> Grid:
    out = _blank(grid)
    for row in _mismatch_rows(grid):
        out[row["row"]][row["left_col"]] = 7
        out[row["row"]][row["right_col"]] = 7
    return out


def _mark_empty_side(grid: Grid) -> Grid:
    out = _blank(grid)
    for row in _mismatch_rows(grid):
        target = row["right_col"] if row["state"] == "left_only" else row["left_col"]
        out[row["row"]][target] = 7
    return out


def _one_direction(grid: Grid, state: str) -> Grid:
    out = _blank(grid)
    for row in _mismatch_rows(grid):
        if row["state"] == state:
            out[row["row"]][row["right_col"]] = 7
    return out


def _raw_value_inequality(grid: Grid) -> Grid:
    facts = P.pair_facts(grid)
    out = _blank(grid)
    for row in facts["pairs"]:
        if row["left_value"] != row["right_value"]:
            out[row["row"]][row["right_col"]] = 7
    return out


def _right_union(grid: Grid) -> Grid:
    facts = P.pair_facts(grid)
    out = _blank(grid)
    for row in facts["pairs"]:
        if row["left_value"] or row["right_value"]:
            out[row["row"]][row["right_col"]] = 7
    return out


def _right_intersection(grid: Grid) -> Grid:
    facts = P.pair_facts(grid)
    out = _blank(grid)
    for row in facts["pairs"]:
        if row["left_value"] and row["right_value"]:
            out[row["row"]][row["right_col"]] = 7
    return out


def _first_mismatch(grid: Grid) -> Grid:
    out = _blank(grid)
    rows = _mismatch_rows(grid)
    if rows:
        row = rows[0]
        out[row["row"]][row["right_col"]] = 7
    return out


def _preserve_and_mark(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    mask = P.apply_policy(grid, "project_right")
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if mask[row][col] == 7:
                out[row][col] = 7
    return out


def rivals() -> dict[str, Rule]:
    return {
        "always project right": lambda grid: P.apply_policy(grid, "project_right"),
        "always mark occupied side": lambda grid: P.apply_policy(grid, "occupied_side"),
        "identity": lambda grid: [row[:] for row in grid],
        "mark both sides of every mismatch": _mark_both,
        "mark empty side of every mismatch": _mark_empty_side,
        "left-only mismatches only": lambda grid: _one_direction(grid, "left_only"),
        "right-only mismatches only": lambda grid: _one_direction(grid, "right_only"),
        "raw value inequality on right": _raw_value_inequality,
        "right-half occupancy union": _right_union,
        "right-half occupancy intersection": _right_intersection,
        "first mismatch only": _first_mismatch,
        "preserve scene and add marks": _preserve_and_mark,
    }


def _scene_errors(grid: Grid) -> list[str]:
    try:
        facts = P.pair_facts(grid)
    except Exception as exc:
        return [f"{type(exc).__name__}: {exc}"]
    counts = facts["state_counts"]
    errors = []
    for state in ("left_only", "right_only", "both_same", "both_different"):
        if counts[state] < 2:
            errors.append(f"insufficient {state}: {counts[state]}")
    return errors


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
                        errors = _scene_errors(pair["input"])
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
        "schema": "arcpuzzles-parametric-mark-policy-audit-v1",
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
