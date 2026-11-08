#!/usr/bin/env python3
"""Bounded protected-Racket self-audit for the native turn-preference family."""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Callable

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "f8d1d470d522"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
CARDINAL = ((0, 1), (1, 0), (0, -1), (-1, 0))


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_f8d1d470d522_self_audit"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _changed(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def _unchanged(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _paint_all_eights(grid: list[list[int]]) -> list[list[int]]:
    return [[9 if value == 8 else value for value in row] for row in grid]


def _paint_all_legal_network(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 8:
                continue
            adjacent_seven = any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == 7
                for dr, dc in CARDINAL
            )
            if not adjacent_seven:
                out[row][col] = 9
    return out


def _lexicographic_shortest(grid: list[list[int]]) -> list[list[int]]:
    """Paint the lexicographically first shortest route, ignoring turn count."""
    height, width = len(grid), len(grid[0])
    markers = sorted(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    )
    if len(markers) != 2:
        raise ValueError("expected two markers")
    start, goal = markers

    def legal(point: tuple[int, int]) -> bool:
        row, col = point
        if not (0 <= row < height and 0 <= col < width):
            return False
        if grid[row][col] == 9:
            return True
        if grid[row][col] != 8:
            return False
        return not any(
            0 <= row + dr < height
            and 0 <= col + dc < width
            and grid[row + dr][col + dc] == 7
            for dr, dc in CARDINAL
        )

    def distances(origin: tuple[int, int]) -> dict[tuple[int, int], int]:
        result = {origin: 0}
        queue = deque([origin])
        while queue:
            row, col = queue.popleft()
            for dr, dc in CARDINAL:
                nxt = row + dr, col + dc
                if legal(nxt) and nxt not in result:
                    result[nxt] = result[(row, col)] + 1
                    queue.append(nxt)
        return result

    forward = distances(start)
    reverse = distances(goal)
    shortest = forward[goal]
    path = [start]
    current = start
    while current != goal:
        candidates = sorted(
            (current[0] + dr, current[1] + dc)
            for dr, dc in CARDINAL
            if (current[0] + dr, current[1] + dc) in forward
            and forward[(current[0] + dr, current[1] + dc)] == forward[current] + 1
            and reverse.get((current[0] + dr, current[1] + dc), shortest + 1)
            + forward[(current[0] + dr, current[1] + dc)]
            == shortest
        )
        if not candidates:
            raise AssertionError("shortest-path reconstruction failed")
        current = candidates[0]
        path.append(current)
    out = [row[:] for row in grid]
    for row, col in path:
        out[row][col] = 9
    return out


def _fixed_manhattan_l(grid: list[list[int]]) -> list[list[int]]:
    """Cheap fixed-order bypass: horizontal first, then vertical."""
    markers = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    )
    start, goal = markers
    out = [row[:] for row in grid]
    row, col = start
    step = 1 if goal[1] >= col else -1
    while col != goal[1]:
        col += step
        out[row][col] = 9
    step = 1 if goal[0] >= row else -1
    while row != goal[0]:
        row += step
        out[row][col] = 9
    return out


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "unchanged": _unchanged,
    "paint_all_eights": _paint_all_eights,
    "paint_all_legal_network": _paint_all_legal_network,
    "lexicographic_shortest": _lexicographic_shortest,
    "fixed_horizontal_then_vertical": _fixed_manhattan_l,
}


def run(out_path: Path) -> dict:
    started = time.monotonic()
    prototype = _load_prototype()
    preferences = tuple(prototype.ALLOWED_TURN_PREFERENCES)
    programs = {value: prototype.program_for(value) for value in preferences}
    canonical = prototype.program_for(prototype.DEFAULT_TURN_PREFERENCE)
    if programs["fewest"] != canonical:
        raise AssertionError("default source identity failed")

    jobs: list[dict] = []
    racket_evaluations = 0
    stress_nonbackground = 0
    stress_changed = 10**9
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for seed in (0, 17):
                for demos in (2, 6):
                    episodes = {
                        preference: prototype.generate_episode(
                            seed, preference, demos, 4
                        )
                        for preference in preferences
                    }
                    baseline_inputs = [
                        pair["input"]
                        for pair in episodes[preferences[0]]["train"]
                        + episodes[preferences[0]]["test"]
                    ]
                    for preference in preferences[1:]:
                        compared = [
                            pair["input"]
                            for pair in episodes[preference]["train"]
                            + episodes[preference]["test"]
                        ]
                        if compared != baseline_inputs:
                            raise AssertionError("settings changed sampled inputs")

                    for preference, episode in episodes.items():
                        replay = prototype.generate_episode(seed, preference, demos, 4)
                        if replay != episode:
                            raise AssertionError("episode replay is not deterministic")
                        survivors: list[str] = []
                        for candidate in preferences:
                            labels = [
                                apply(programs[candidate], pair["input"])
                                for pair in episode["train"]
                            ]
                            racket_evaluations += len(labels)
                            if all(
                                actual == pair["output"]
                                for actual, pair in zip(
                                    labels, episode["train"], strict=True
                                )
                            ):
                                survivors.append(candidate)
                        if survivors != [preference]:
                            raise AssertionError(
                                f"finite setting survivors {preference=} {seed=} "
                                f"{demos=}: {survivors}"
                            )

                        rival_survivors = [
                            name
                            for name, rival in RIVALS.items()
                            if all(
                                rival(pair["input"]) == pair["output"]
                                for pair in episode["train"]
                            )
                        ]
                        if rival_survivors:
                            raise AssertionError(
                                f"plausible rivals survive {preference=} {seed=} "
                                f"{demos=}: {rival_survivors}"
                            )

                        for pair in episode["train"] + episode["test"]:
                            actual = apply(programs[preference], pair["input"])
                            racket_evaluations += 1
                            if actual != pair["output"]:
                                raise AssertionError(
                                    f"Racket/Python mismatch {preference=} {seed=}"
                                )
                        public = prototype.public_challenge(episode)
                        if any(key in repr(public) for key in ("program_solution", "parameter")):
                            raise AssertionError("public projection leaked private metadata")
                        if any("output" in pair for pair in public["test"]):
                            raise AssertionError("public projection leaked query labels")
                        if len({json.dumps(pair["input"], separators=(",", ":"))
                                for pair in episode["train"] + episode["test"]}) != demos + 4:
                            raise AssertionError("episode inputs are not distinct")

                        stress = episode["test"][-1]
                        if (len(stress["input"]), len(stress["input"][0])) != (30, 30):
                            raise AssertionError("last query is not 30x30")
                        stress_nonbackground = max(
                            stress_nonbackground,
                            sum(value != 0 for row in stress["input"] for value in row),
                        )
                        stress_changed = min(
                            stress_changed,
                            _changed(stress["input"], stress["output"]),
                        )
                        jobs.append(
                            {
                                "turn_preference": preference,
                                "seed": seed,
                                "demos": demos,
                                "queries": 4,
                                "finite_setting_survivors": survivors,
                                "plausible_rival_survivors": rival_survivors,
                                "query_shapes": [
                                    [len(pair["input"]), len(pair["input"][0])]
                                    for pair in episode["test"]
                                ],
                            }
                        )

            witness = prototype.generate_episode(17, "most", 2, 4)["train"][0]
            correct_output = apply(programs["most"], witness["input"])
            wrong_output = apply(programs["fewest"], witness["input"])
            racket_evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("self-audit requires protected Racket")
    if correct_output == wrong_output:
        raise AssertionError("causal counterfactual did not change output")

    generated_requests = 0
    dimensions: set[tuple[int, int]] = set()
    for seed in range(24):
        for preference in preferences:
            episode = prototype.generate_episode(seed, preference, 2, 4)
            generated_requests += 1
            for pair in episode["train"] + episode["test"]:
                dimensions.add((len(pair["input"]), len(pair["input"][0])))

    intermediate_path = sorted(
        [
            [row, col]
            for row, values in enumerate(correct_output)
            for col, value in enumerate(values)
            if value == 9
        ]
    )
    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "racket": identity,
        "racket_evaluations": racket_evaluations,
        "jobs": jobs,
        "plausible_rivals": sorted(RIVALS),
        "bounded_generation_requests": generated_requests,
        "observed_dimensions": [list(shape) for shape in sorted(dimensions)],
        "substantive_30x30": {
            "shape": [30, 30],
            "maximum_nonbackground_input_cells": stress_nonbackground,
            "minimum_changed_cells_from_input": stress_changed,
        },
        "causal_counterfactual": {
            "setting": {"turn_preference": "most"},
            "intermediate": "ordered legal shortest path selected by maximum turn count",
            "intermediate_path_cells": intermediate_path,
            "changed_cells": _changed(correct_output, wrong_output),
            "program_sha256": _sha_text(programs["most"]),
            "counterfactual_program_sha256": _sha_text(programs["fewest"]),
        },
        "source_sha256": {
            "prototype.py": hashlib.sha256((HERE / "prototype.py").read_bytes()).hexdigest(),
            "adapter.py": hashlib.sha256((HERE / "adapter.py").read_bytes()).hexdigest(),
            "turn_fewest.rkt": _sha_text(programs["fewest"]),
            "turn_most.rkt": _sha_text(programs["most"]),
        },
        "limits": [
            "Finite settings, two qualification seeds, demo boundaries 2/6, and 24 additional generation seeds; not universal proof.",
            "Plausible-rival checks are bounded to the retained cheap bypasses.",
            "Owner qualification and acceptance remain separate gates.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(
        json.dumps(
            {
                "status": result["status"],
                "racket": result["racket"],
                "jobs": len(result["jobs"]),
                "racket_evaluations": result["racket_evaluations"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
