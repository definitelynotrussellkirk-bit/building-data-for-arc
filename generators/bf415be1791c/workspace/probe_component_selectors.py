#!/usr/bin/env python3
"""Enumerate component-selection shortcut families for bf415be1791c.

Unlike ``probe_shortcuts.py``, this probe does not depend on a hand-written
rival registry.  It constructs a bounded family of plausible wrong rules from
visible magenta components, keeps every candidate that matches all labeled
canonical pairs, and checks every query holdout in the finite production
schedule.  The candidate transforms are implemented independently of the
generator's semantic-rival helpers.

This is a finite falsification tool, not a proof over all possible rules.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "bf415be1791c"
TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"
Cell = tuple[int, int]
Component = set[Cell]
Rule = Callable[[list[list[int]]], list[list[int]]]


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"component_selector_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _divider(grid: list[list[int]]) -> int:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    columns = [
        col
        for col in range(len(grid[0]))
        if all(row[col] == 5 for row in grid)
    ]
    if len(columns) != 1:
        raise ValueError(f"expected one full-height gray divider, got {columns}")
    return columns[0]


def _components(grid: list[list[int]]) -> list[Component]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    }
    result: list[Component] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = row + drow, col + dcol
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return sorted(result, key=lambda part: (min(part), len(part)))


def _mirror_selected(
    grid: list[list[int]], selector: Callable[[list[Component]], list[Component]]
) -> list[list[int]]:
    divider = _divider(grid)
    output = deepcopy(grid)
    components = _components(grid)
    for component in selector(components):
        for row, col in component:
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < len(output[0]) and output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output


def _predicate_rule(predicate: Callable[[Component], bool]) -> Rule:
    def transform(grid: list[list[int]]) -> list[list[int]]:
        return _mirror_selected(
            grid, lambda components: [part for part in components if predicate(part)]
        )

    return transform


def _rank_rule(
    key: Callable[[Component], Any], *, count: int, reverse: bool = False
) -> Rule:
    def transform(grid: list[list[int]]) -> list[list[int]]:
        def select(components: list[Component]) -> list[Component]:
            return sorted(components, key=key, reverse=reverse)[:count]

        return _mirror_selected(grid, select)

    return transform


def _conditional_all(predicate: Callable[[list[Component]], bool]) -> Rule:
    def transform(grid: list[list[int]]) -> list[list[int]]:
        return _mirror_selected(
            grid, lambda components: components if predicate(components) else []
        )

    return transform


def candidate_rules() -> dict[str, Rule]:
    """Return a deterministic bounded search family of wrong hypotheses."""
    rules: dict[str, Rule] = {}

    for minimum in range(2, 11):
        rules[f"size_at_least_{minimum}"] = _predicate_rule(
            lambda component, minimum=minimum: len(component) >= minimum
        )
    for maximum in range(1, 11):
        rules[f"size_at_most_{maximum}"] = _predicate_rule(
            lambda component, maximum=maximum: len(component) <= maximum
        )
    for minimum in range(1, 11):
        for maximum in range(minimum, 11):
            rules[f"size_between_{minimum}_{maximum}"] = _predicate_rule(
                lambda component, minimum=minimum, maximum=maximum: (
                    minimum <= len(component) <= maximum
                )
            )

    top_key = lambda part: (min(row for row, _ in part), min(part))
    bottom_key = lambda part: (max(row for row, _ in part), max(part))
    left_key = lambda part: (min(col for _, col in part), min(part))
    right_key = lambda part: (max(col for _, col in part), max(part))
    largest_key = lambda part: (len(part), tuple(sorted(part)))
    smallest_key = lambda part: (len(part), tuple(sorted(part)))

    rank_specs = {
        "largest": (largest_key, True),
        "smallest": (smallest_key, False),
        "topmost": (top_key, False),
        "bottommost": (bottom_key, True),
        "leftmost": (left_key, False),
        "rightmost": (right_key, True),
    }
    for label, (key, reverse) in rank_specs.items():
        rules[f"{label}_only"] = _rank_rule(key, count=1, reverse=reverse)
        rules[f"{label}_two"] = _rank_rule(key, count=2, reverse=reverse)

    rules["mirror_only_when_single_component"] = _conditional_all(
        lambda components: len(components) == 1
    )
    for maximum in range(4, 11):
        rules[f"mirror_only_when_total_at_most_{maximum}"] = _conditional_all(
            lambda components, maximum=maximum: (
                sum(map(len, components)) <= maximum
            )
        )
    for minimum in range(1, 11):
        rules[f"mirror_only_when_total_at_least_{minimum}"] = _conditional_all(
            lambda components, minimum=minimum: (
                sum(map(len, components)) >= minimum
            )
        )

    return dict(sorted(rules.items()))


def _rotation_probe(
    gen: Any,
    candidates: dict[str, Rule],
    *,
    schedule_seed: int,
) -> dict[str, Any]:
    by_candidate = {
        name: {
            "ambiguity_count": 0,
            "ambiguities": [],
            "schedule_disagreement_count": 0,
        }
        for name in candidates
    }
    rotations = 0
    seen_schedule_inputs: dict[tuple[str, int], dict[str, Any]] = {}

    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(
            gen.LESSON_SCHEDULE_PERIOD + gen.EXAMPLES_NEEDED
        ):
            grid = gen.generate(schedule_seed, sample_index, difficulty=difficulty)
            expected = gen.rule_mirror(grid)
            seen_schedule_inputs[(difficulty, sample_index)] = {
                "sample_index": sample_index,
                "input": grid,
                "output": expected,
                "observed": gen.semantic_observables(grid),
                "component_sizes": sorted(map(len, _components(grid))),
            }
            for name, rival in candidates.items():
                if rival(grid) != expected:
                    by_candidate[name]["schedule_disagreement_count"] += 1

        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = [
                seen_schedule_inputs[(difficulty, start + offset)]
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query in enumerate(pairs):
                rotations += 1
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                for name, rival in candidates.items():
                    survives = all(
                        rival(pair["input"]) == pair["output"] for pair in demos
                    )
                    changes_query = rival(query["input"]) != query["output"]
                    if survives and changes_query:
                        by_candidate[name]["ambiguity_count"] += 1
                        by_candidate[name]["ambiguities"].append(
                            {
                                "difficulty": difficulty,
                                "start": start,
                                "query_index": query_index,
                                "query_sample_index": query["sample_index"],
                                "query_component_sizes": query["component_sizes"],
                                "demo_sample_indices": [
                                    pair["sample_index"] for pair in demos
                                ],
                            }
                        )

    return {
        "schedule_seed": schedule_seed,
        "period": gen.LESSON_SCHEDULE_PERIOD,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "bands": ["easy", "medium", "hard"],
        "rotation_count": rotations,
        "ambiguity_count": sum(
            item["ambiguity_count"] for item in by_candidate.values()
        ),
        "by_candidate": by_candidate,
    }


def build_record(*, schedule_seed: int = 2609) -> dict[str, Any]:
    root = find_root(__file__)
    gen = _load_generator()
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    all_candidates = candidate_rules()

    canonical_results: dict[str, dict[str, Any]] = {}
    fitting: dict[str, Rule] = {}
    for name, rival in all_candidates.items():
        matches = [
            rival(pair["input"]) == pair["output"] for pair in canonical
        ]
        canonical_results[name] = {
            "matches": matches,
            "fits_all": all(matches),
        }
        if all(matches):
            fitting[name] = rival

    rotation_probe = _rotation_probe(
        gen,
        fitting,
        schedule_seed=schedule_seed,
    )
    return {
        "schema": "bf415be1791c-component-selector-family-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "schedule_seed": schedule_seed,
        "all_candidate_count": len(all_candidates),
        "canonical_fitting_candidate_count": len(fitting),
        "canonical_fitting_candidates": sorted(fitting),
        "canonical_results": canonical_results,
        "rotation_probe": rotation_probe,
        "limitations": (
            "Finite search over size thresholds, contiguous size ranges, rank "
            "selectors, and total/count gates. It does not prove uniqueness "
            "against arbitrary programs; schedule outputs use the Python mirror "
            "that is separately checked against the selected Racket authority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--schedule-seed", type=int, default=2609)
    args = parser.parse_args()

    record = build_record(schedule_seed=args.schedule_seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    summary = {
        "out": str(args.out),
        "generator_sha256": record["generator_sha256"],
        "all_candidate_count": record["all_candidate_count"],
        "canonical_fitting_candidate_count": record[
            "canonical_fitting_candidate_count"
        ],
        "rotation_count": record["rotation_probe"]["rotation_count"],
        "ambiguity_count": record["rotation_probe"]["ambiguity_count"],
    }
    print(json.dumps(summary, indent=2))
    return 1 if summary["ambiguity_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
