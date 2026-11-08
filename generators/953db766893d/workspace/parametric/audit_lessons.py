"""Reproduce teaching and protected-Racket checks for the room-extreme family."""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root

HERE = Path(__file__).resolve().parent
TASK_ID = "953db766893d"
SETTINGS = ({"extreme": "minimum"}, {"extreme": "maximum"})


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "_audit_room_extreme_" + hashlib.sha256(str(path).encode()).hexdigest(), path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    result = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def _is_rectangle(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return len(component) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _has_opening(grid):
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            if (
                grid[row][col - 1] == grid[row][col + 1] == 0
                and grid[row - 1][col] != 0
                and grid[row + 1][col] != 0
            ) or (
                grid[row - 1][col] == grid[row + 1][col] == 0
                and grid[row][col - 1] != 0
                and grid[row][col + 1] != 0
            ):
                return True
    return False


def _size_labels(pair):
    labels = defaultdict(set)
    for component in _components(pair["input"]):
        observed = {pair["output"][row][col] for row, col in component}
        if len(observed) != 1:
            raise ValueError("one zero component received multiple output colors")
        labels[len(component)].update(observed)
    return labels


def _racket_receipt(prototype, episodes):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    root = find_root(__file__)
    runtime = root / "shared/runtime"
    evaluations = 0
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for settings, episode in episodes:
                source = prototype.program(settings)
                for pair in episode["train"] + episode["test"]:
                    evaluations += 1
                    if apply(source, pair["input"]) != pair["output"]:
                        raise ValueError(
                            f"protected Racket label mismatch for {settings} at evaluation {evaluations}"
                        )
        finally:
            bridge.close()
    return {
        "executed": True,
        "all_labels_match": True,
        "evaluations": evaluations,
        "identity": identity,
    }


def build_report(seed=0, execute_racket=False):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(execute_racket) is not bool:
        raise ValueError("execute_racket must be bool")

    prototype = _load_prototype()
    episodes = [
        (settings, prototype.generate(seed, settings, demos=2, queries=4))
        for settings in SETTINGS
    ]
    minimum = episodes[0][1]
    maximum = episodes[1][1]
    minimum_inputs = [pair["input"] for split in ("train", "test") for pair in minimum[split]]
    maximum_inputs = [pair["input"] for split in ("train", "test") for pair in maximum[split]]
    if minimum_inputs != maximum_inputs:
        raise ValueError("settings did not receive matched inputs")

    first = minimum["train"][0]
    first_components = _components(first["input"])
    first_sizes = sorted(len(component) for component in first_components)
    opened_wall_rival_mismatched_cells = sum(
        first["input"][row][col] == 0 and first["output"][row][col] != 3
        for row in range(len(first["input"]))
        for col in range(len(first["input"][0]))
    )

    reversals = {}
    for settings, episode in episodes:
        labels = defaultdict(set)
        for pair in episode["train"][:2]:
            for size, observed in _size_labels(pair).items():
                labels[size].update(observed)
        reversals[settings["extreme"]] = sorted(
            size for size, observed in labels.items() if observed == {3, 4}
        )

    large = minimum["test"][-1]
    large_sizes = sorted({len(component) for component in _components(large["input"])})
    report = {
        "schema": "arcpuzzles-room-extreme-lesson-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": list(SETTINGS),
        "matched_inputs": True,
        "first_demo": {
            "shape": [len(first["input"]), len(first["input"][0])],
            "has_opening": _has_opening(first["input"]),
            "component_sizes": first_sizes,
            "all_components_rectangular": all(_is_rectangle(component) for component in first_components),
            "output_component_colors": sorted(
                {next(iter(observed)) for observed in _size_labels(first).values()}
            ),
            "opened_wall_rival_mismatched_cells": opened_wall_rival_mismatched_cells,
        },
        "second_demo": {
            "shape": [len(minimum["train"][1]["input"]), len(minimum["train"][1]["input"][0])],
            "has_opening": _has_opening(minimum["train"][1]["input"]),
            "component_sizes": sorted(
                len(component) for component in _components(minimum["train"][1]["input"])
            ),
        },
        "fixed_absolute_area_role_reversal": reversals,
        "large_query": {
            "shape": [len(large["input"]), len(large["input"][0])],
            "nonzero_cells": sum(value != 0 for row in large["input"] for value in row),
            "has_opening": _has_opening(large["input"]),
            "component_sizes": large_sizes,
        },
        "program_sha256": {
            settings["extreme"]: hashlib.sha256(prototype.program(settings).encode()).hexdigest()
            for settings in SETTINGS
        },
        "racket": _racket_receipt(prototype, episodes) if execute_racket else {"executed": False},
        "limits": (
            "Bounded authored seeds and the two declared programs only; this records concrete "
            "shortcut counterexamples and label parity, not universal rule uniqueness or learning gain."
        ),
    }
    if report["first_demo"]["has_opening"]:
        raise ValueError("first teaching case unexpectedly contains an opening")
    if not report["second_demo"]["has_opening"]:
        raise ValueError("second teaching case unexpectedly lacks an opening")
    if opened_wall_rival_mismatched_cells <= 0:
        raise ValueError("first teaching case did not refute the opened-wall shortcut")
    if not all(reversals.values()):
        raise ValueError("first two demos did not refute fixed absolute-area shortcuts")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(seed=args.seed, execute_racket=args.racket)
    raw = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    else:
        print(raw, end="")


if __name__ == "__main__":
    main()
