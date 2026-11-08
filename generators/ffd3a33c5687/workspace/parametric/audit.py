"""Finite teaching and public-projection audit for ffd3a33c5687.

This tool is deliberately independent of the Racket programs.  It evaluates a
small, declared family of plausible shortcut rules against every demonstration
and each of the four query positions, then verifies that the public projection
contains demonstrations and only the currently released query input.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable, Iterable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
_RUNTIME = REPO / "shared" / "runtime"
if str(_RUNTIME) not in sys.path:
    sys.path.insert(0, str(_RUNTIME))
from reviewer_support import public_challenge_bytes  # noqa: E402


def _load_adapter():
    spec = importlib.util.spec_from_file_location("_ffd3_parametric_adapter_for_audit", HERE / "adapter.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load parametric adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load_adapter()
Grid = list[list[int]]
Rule = Callable[[Grid], Grid]
POLICIES = ("left_priority", "guide_priority")


def _priority(grid: Grid, side: str) -> Grid:
    """Independent orbit completion with one globally selected side."""
    if side not in {"left", "right"}:
        raise ValueError("side must be left or right")
    output = deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            preferred, fallback = (left, right) if side == "left" else (right, left)
            color = preferred if preferred != 0 else fallback
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


def _guide_side(grid: Grid) -> str:
    """Infer the guide without calling the adapter's implementation."""
    width = len(grid[0])
    center_left, center_right = (width - 1) // 2, width // 2
    guide_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if row[center_left] == 8 and row[center_right] == 8
    ]
    if len(guide_rows) != 1:
        raise ValueError("expected exactly one center-marked guide row")
    row = grid[guide_rows[0]]
    left_count = sum(value != 0 for value in row[:center_left])
    right_count = sum(value != 0 for value in row[center_right + 1 :])
    if (left_count, right_count) == (1, 0):
        return "left"
    if (left_count, right_count) == (0, 1):
        return "right"
    raise ValueError("guide must have one off-center one-sided signal")


def _guide_priority(grid: Grid) -> Grid:
    return _priority(grid, _guide_side(grid))


def _opposite_guide(grid: Grid) -> Grid:
    return _priority(grid, "right" if _guide_side(grid) == "left" else "left")


def _preserve_conflicts(grid: Grid) -> Grid:
    """Mirror singletons but leave already occupied conflicts untouched."""
    output = deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if left == 0 and right != 0:
                output[row_index][left_col] = right
            elif right == 0 and left != 0:
                output[row_index][right_col] = left
    return output


def _numeric_priority(grid: Grid, mode: str) -> Grid:
    """Use numeric min/max as a plausible color-order conflict shortcut."""
    if mode not in {"min", "max"}:
        raise ValueError("mode must be min or max")
    output = deepcopy(grid)
    width = len(grid[0])
    choose = min if mode == "min" else max
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            nonzero = [value for value in (row[left_col], row[right_col]) if value != 0]
            color = choose(nonzero) if nonzero else 0
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


def _majority_singleton_side(grid: Grid) -> Grid:
    """Infer priority from the majority side of all one-sided mirror orbits."""
    width = len(grid[0])
    left_votes = 0
    right_votes = 0
    for row in grid:
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if left != 0 and right == 0:
                left_votes += 1
            elif right != 0 and left == 0:
                right_votes += 1
    return _priority(grid, "left" if left_votes >= right_votes else "right")


def _top_conflict_side(grid: Grid) -> Grid:
    """Use the side of the smaller color in the first occupied conflict."""
    width = len(grid[0])
    for row in grid:
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if left != 0 and right != 0 and left != right:
                return _priority(grid, "left" if left < right else "right")
    return _priority(grid, "left")


RIVALS: dict[str, Rule] = {
    "fixed_left": lambda grid: _priority(grid, "left"),
    "fixed_right": lambda grid: _priority(grid, "right"),
    "guide_priority": _guide_priority,
    "opposite_guide": _opposite_guide,
    "preserve_occupied_conflicts": _preserve_conflicts,
    "numeric_minimum": lambda grid: _numeric_priority(grid, "min"),
    "numeric_maximum": lambda grid: _numeric_priority(grid, "max"),
    "majority_singleton_side": _majority_singleton_side,
    "first_conflict_smaller_side": _top_conflict_side,
}


def _validated_distinct_ints(name: str, values: Iterable[int], low: int, high: int) -> tuple[int, ...]:
    result = tuple(values)
    if not result or len(result) != len(set(result)):
        raise ValueError(f"{name} must contain distinct values")
    if any(type(value) is not int or not low <= value <= high for value in result):
        raise ValueError(f"{name} values must be exact integers in {low}..{high}")
    return result


def _visible_projection(episode: dict) -> dict[str, bool]:
    """Return leakage predicates for controller and first-turn public bytes."""
    controller = json.loads(public_challenge_bytes(episode))
    first_turn_private = {
        "train": episode["train"],
        "test": [episode["test"][0]],
        # These deliberately hostile private fields must still be stripped.
        "settings": {"conflict_policy": "private"},
        "program_solution": "private",
    }
    first_turn = json.loads(public_challenge_bytes(first_turn_private))
    return {
        "settings_visible": "settings" in controller or "settings" in first_turn,
        "program_visible": "program_solution" in controller or "program_solution" in first_turn,
        "query_outputs_visible": any("output" in pair for pair in controller["test"])
        or any("output" in pair for pair in first_turn["test"]),
        "future_queries_visible_on_first_turn": len(first_turn["test"]) != 1
        or first_turn["test"][0]["input"] != controller["test"][0]["input"],
    }


def run_audit(*, seeds=(0, 17), demo_counts=(2, 3, 6)) -> dict:
    """Audit declared rivals over both settings and all four query rotations."""
    seeds = _validated_distinct_ints("seeds", seeds, 0, 2**63 - 1)
    demo_counts = _validated_distinct_ints("demo_counts", demo_counts, 2, 6)

    ambiguous_cases: list[dict] = []
    episodes: list[dict] = []
    projection = {
        "settings_visible": False,
        "program_visible": False,
        "query_outputs_visible": False,
        "future_queries_visible_on_first_turn": False,
    }
    rotations = 0

    for policy in POLICIES:
        settings = {"conflict_policy": policy}
        for seed in seeds:
            for demos in demo_counts:
                episode = adapter.generate(seed, settings, demos, 4)
                visible = _visible_projection(episode)
                for key, value in visible.items():
                    projection[key] = projection[key] or value

                fitted = []
                rejected = []
                for rival_name, rival in RIVALS.items():
                    matches = [rival(pair["input"]) == pair["output"] for pair in episode["train"]]
                    (fitted if all(matches) else rejected).append(rival_name)

                rotation_rows = []
                for query_index, query in enumerate(episode["test"]):
                    rotations += 1
                    disagreeing_fit = [
                        rival_name
                        for rival_name in fitted
                        if RIVALS[rival_name](query["input"]) != query["output"]
                    ]
                    if disagreeing_fit:
                        ambiguous_cases.append(
                            {
                                "policy": policy,
                                "seed": seed,
                                "demos": demos,
                                "query_index": query_index,
                                "rivals": disagreeing_fit,
                            }
                        )
                    rotation_rows.append(
                        {
                            "query_index": query_index,
                            "fitted_rivals_that_disagree": disagreeing_fit,
                        }
                    )

                episodes.append(
                    {
                        "policy": policy,
                        "seed": seed,
                        "demos": demos,
                        "guide_sides": [_guide_side(pair["input"]) for pair in episode["train"]],
                        "fitted_rivals": fitted,
                        "rejected_rivals": rejected,
                        "rotations": rotation_rows,
                    }
                )

    leaked = any(projection.values())
    return {
        "schema": "arcpuzzles-parametric-teaching-audit-v1",
        "task_id": "ffd3a33c5687",
        "status": "passed" if not ambiguous_cases and not leaked else "failed",
        "scope": {
            "seeds": list(seeds),
            "demo_counts": list(demo_counts),
            "settings": list(POLICIES),
            "rivals": list(RIVALS),
        },
        "episodes_checked": len(episodes),
        "query_rotations_checked": rotations,
        "ambiguous_cases": ambiguous_cases,
        "projection": projection,
        "episodes": episodes,
        "limits": (
            "Finite audit over declared plausible rivals; it is not a proof against every "
            "possible induction rule. Public first-turn projection is constructed from the "
            "same episode with only the current query retained."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the JSON report to this path")
    args = parser.parse_args(argv)
    report = run_audit()
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(payload, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(args.out)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
