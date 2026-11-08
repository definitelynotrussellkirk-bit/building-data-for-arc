#!/usr/bin/env python3
"""Bounded protected-Racket self-audit for the native count-scope family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Callable

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "017f1406edaf"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_017f1406edaf_self_audit"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _blank(grid: list[list[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in grid]


def _paint(grid: list[list[int]], cells: tuple[tuple[int, int], ...]) -> list[list[int]]:
    out = _blank(grid)
    for row, col in cells:
        out[row][col] = 8
    return out


def _include_row0(prototype, grid: list[list[int]], scope: str) -> list[list[int]]:
    target = prototype.target_count(grid, scope)
    component = next(
        (
            item
            for item in prototype.components(grid)
            if item.color != 1 and item.size == target
        ),
        None,
    )
    return _paint(grid, component.cells) if component is not None else _blank(grid)


def _topmost_eligible(prototype, grid: list[list[int]], scope: str) -> list[list[int]]:
    del scope
    component = next(
        (
            item
            for item in prototype.components(grid)
            if item.color != 1 and not item.touches_row0
        ),
        None,
    )
    return _paint(grid, component.cells) if component is not None else _blank(grid)


def _bottommost_eligible(prototype, grid: list[list[int]], scope: str) -> list[list[int]]:
    del scope
    candidates = [
        item
        for item in prototype.components(grid)
        if item.color != 1 and not item.touches_row0
    ]
    component = max(candidates, key=lambda item: item.first) if candidates else None
    return _paint(grid, component.cells) if component is not None else _blank(grid)


def _median_area(prototype, grid: list[list[int]], scope: str) -> list[list[int]]:
    del scope
    candidates = [
        item
        for item in prototype.components(grid)
        if item.color != 1 and not item.touches_row0
    ]
    candidates.sort(key=lambda item: (item.size, item.first))
    component = candidates[(len(candidates) - 1) // 2] if candidates else None
    return _paint(grid, component.cells) if component is not None else _blank(grid)


def _paint_all_eligible(prototype, grid: list[list[int]], scope: str) -> list[list[int]]:
    del scope
    cells = tuple(
        cell
        for item in prototype.components(grid)
        if item.color != 1 and not item.touches_row0
        for cell in item.cells
    )
    return _paint(grid, cells)


def _unchanged(prototype, grid: list[list[int]], scope: str) -> list[list[int]]:
    del prototype, scope
    return [row[:] for row in grid]


RIVALS: dict[str, Callable] = {
    "include_row0_size_match": _include_row0,
    "topmost_eligible_object": _topmost_eligible,
    "bottommost_eligible_object": _bottommost_eligible,
    "lower_median_candidate_area": _median_area,
    "paint_all_eligible_objects": _paint_all_eligible,
    "unchanged": _unchanged,
}


def _changed(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def run(out_path: Path) -> dict:
    started = time.monotonic()
    prototype = _load_prototype()
    scopes = tuple(prototype.COUNT_SCOPES)
    programs = {scope: prototype.program_for(scope) for scope in scopes}
    if programs["row0"] != (HERE / "rules" / "count_row0.rkt").read_text():
        raise AssertionError("canonical source identity failed")

    jobs: list[dict] = []
    racket_evaluations = 0
    stress_nonbackground = 0
    stress_occupied_rows: set[int] = set()
    stress_occupied_cols: set[int] = set()
    stress_changed = 10**9

    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for seed in (0, 17):
                for demos in (2, 6):
                    episodes = {
                        scope: prototype.generate_episode(seed, scope, demos, 4)
                        for scope in scopes
                    }
                    reference_inputs = [
                        pair["input"]
                        for pair in episodes[scopes[0]]["train"]
                        + episodes[scopes[0]]["test"]
                    ]
                    for scope in scopes[1:]:
                        compared = [
                            pair["input"]
                            for pair in episodes[scope]["train"]
                            + episodes[scope]["test"]
                        ]
                        if compared != reference_inputs:
                            raise AssertionError("settings changed sampled inputs")

                    for scope, episode in episodes.items():
                        if prototype.generate_episode(seed, scope, demos, 4) != episode:
                            raise AssertionError("episode replay is not deterministic")

                        survivors: list[str] = []
                        for candidate in scopes:
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
                        if survivors != [scope]:
                            raise AssertionError(
                                f"finite setting survivors {scope=} {seed=} "
                                f"{demos=}: {survivors}"
                            )

                        rival_survivors = [
                            name
                            for name, rival in RIVALS.items()
                            if all(
                                rival(prototype, pair["input"], scope)
                                == pair["output"]
                                for pair in episode["train"]
                            )
                        ]
                        if rival_survivors:
                            raise AssertionError(
                                f"plausible rivals survive {scope=} {seed=} "
                                f"{demos=}: {rival_survivors}"
                            )

                        for pair in episode["train"] + episode["test"]:
                            actual = apply(programs[scope], pair["input"])
                            racket_evaluations += 1
                            if actual != pair["output"]:
                                raise AssertionError(
                                    f"Racket/Python mismatch {scope=} {seed=}"
                                )
                            selected = prototype.selected_cells(pair["input"], scope)
                            if len(selected) != prototype.target_count(pair["input"], scope):
                                raise AssertionError("selected object does not consume target count")

                        public = prototype.public_challenge(episode)
                        if "parameter" in repr(public) or "program_solution" in repr(public):
                            raise AssertionError("public projection leaked private metadata")
                        if any("output" in pair for pair in public["test"]):
                            raise AssertionError("public projection leaked query labels")
                        serialized = {
                            json.dumps(pair["input"], separators=(",", ":"))
                            for pair in episode["train"] + episode["test"]
                        }
                        if len(serialized) != demos + 4:
                            raise AssertionError("episode inputs are not distinct")

                        stress = episode["test"][-1]
                        if (len(stress["input"]), len(stress["input"][0])) != (30, 30):
                            raise AssertionError("last query is not 30x30")
                        stress_nonbackground = max(
                            stress_nonbackground,
                            sum(value != 0 for row in stress["input"] for value in row),
                        )
                        stress_occupied_rows.update(
                            row
                            for row, values in enumerate(stress["input"])
                            if any(value != 0 for value in values)
                        )
                        stress_occupied_cols.update(
                            col
                            for col in range(30)
                            if any(stress["input"][row][col] != 0 for row in range(30))
                        )
                        stress_changed = min(
                            stress_changed,
                            _changed(stress["input"], stress["output"]),
                        )
                        jobs.append(
                            {
                                "count_scope": scope,
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

            witness = prototype.generate_episode(17, "all_blue", 2, 4)["train"][0]
            correct_output = apply(programs["all_blue"], witness["input"])
            wrong_output = apply(programs["row0"], witness["input"])
            racket_evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("self-audit requires protected Racket")
    if correct_output == wrong_output:
        raise AssertionError("causal counterfactual did not change output")

    generated_requests = 0
    ordering_values: set[bool] = set()
    prefix_requests = 0
    dimensions: set[tuple[int, int]] = set()
    for seed in range(64):
        for scope in scopes:
            large = prototype.generate_episode(seed, scope, 6, 4)
            demo_min = prototype.generate_episode(seed, scope, 2, 4)
            query_one = prototype.build_episode(
                seed, count_scope=scope, demos=2, queries=1
            )
            generated_requests += 1
            if demo_min["train"] != large["train"][:2]:
                raise AssertionError("demo count changed the stable training prefix")
            if (
                query_one["train"] != demo_min["train"]
                or query_one["test"] != demo_min["test"][:1]
            ):
                raise AssertionError("query count changed the stable query prefix")
            prefix_requests += 1
            for pair in large["train"] + large["test"]:
                dimensions.add((len(pair["input"]), len(pair["input"][0])))
        for pair_index in range(8):
            grid = prototype.build_input(seed, pair_index)
            ordering_values.add(
                min(prototype.selected_cells(grid, "row0"))
                < min(prototype.selected_cells(grid, "all_blue"))
            )
    if ordering_values != {False, True}:
        raise AssertionError("target position did not vary across count scopes")

    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "racket": identity,
        "racket_evaluations": racket_evaluations,
        "jobs": jobs,
        "plausible_rivals": sorted(RIVALS),
        "bounded_generation_requests": generated_requests,
        "stable_prefix_requests": prefix_requests,
        "observed_dimensions": [list(shape) for shape in sorted(dimensions)],
        "target_orderings_observed": sorted(ordering_values),
        "substantive_30x30": {
            "shape": [30, 30],
            "maximum_nonbackground_input_cells": stress_nonbackground,
            "occupied_row_count": len(stress_occupied_rows),
            "occupied_column_count": len(stress_occupied_cols),
            "minimum_changed_cells_from_input": stress_changed,
        },
        "causal_counterfactual": {
            "setting": {"count_scope": "all_blue"},
            "row0_count": prototype.target_count(witness["input"], "row0"),
            "all_blue_count": prototype.target_count(witness["input"], "all_blue"),
            "selected_cells": [
                list(cell)
                for cell in prototype.selected_cells(witness["input"], "all_blue")
            ],
            "changed_cells": _changed(correct_output, wrong_output),
            "program_sha256": _sha_text(programs["all_blue"]),
            "counterfactual_program_sha256": _sha_text(programs["row0"]),
        },
        "source_sha256": {
            "prototype.py": hashlib.sha256((HERE / "prototype.py").read_bytes()).hexdigest(),
            "adapter.py": hashlib.sha256((HERE / "adapter.py").read_bytes()).hexdigest(),
            "count_row0.rkt": _sha_text(programs["row0"]),
            "count_all_blue.rkt": _sha_text(programs["all_blue"]),
        },
        "limits": [
            "Finite settings, two qualification seeds, demo boundaries 2/6, and 64 additional generation seeds; not universal proof.",
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
