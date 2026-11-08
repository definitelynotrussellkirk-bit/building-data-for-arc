#!/usr/bin/env python3
"""Fast, Racket-free stress probe for the 7f31c4f794b2 teaching contract.

This is reviewer tooling, not the selected generator.  It independently
reconstructs same-color 4-connected components, checks the component-local
border rule, exercises every declared rival, and scans every cyclic lesson
start in a deterministic schedule.  The official battery/lesson census remains
the authority; this probe is intended for rapid iteration before those checks.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

BANDS = ("easy", "medium", "hard")


def component_census(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return an independent census of nonzero same-color 4-components."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")

    height = len(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sides: set[str] = set()
            if any(rr == 0 for rr, _ in cells):
                sides.add("top")
            if any(rr == height - 1 for rr, _ in cells):
                sides.add("bottom")
            if any(cc == 0 for _, cc in cells):
                sides.add("left")
            if any(cc == width - 1 for _, cc in cells):
                sides.add("right")
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "sides": frozenset(sides),
                }
            )
    return result


def independent_output(grid: list[list[int]]) -> list[list[int]]:
    """Apply the intended rule without calling generator implementation hooks."""
    output = [row[:] for row in grid]
    for component in component_census(grid):
        if component["sides"]:
            for row, col in component["cells"]:
                output[row][col] = 7
    return output


def independent_witnesses(grid: list[list[int]]) -> dict[str, bool]:
    """Measure the four task-specific shortcut-breaking facts independently."""
    components = component_census(grid)
    border = [component for component in components if component["sides"]]
    interior = [component for component in components if not component["sides"]]
    border_colors = {component["color"] for component in border}
    interior_colors = {component["color"] for component in interior}
    return {
        "shared_color_split": bool(border_colors & interior_colors),
        "horizontal_only_contact": any(
            component["sides"] <= {"top", "bottom"} for component in border
        ),
        "vertical_only_contact": any(
            component["sides"] <= {"left", "right"} for component in border
        ),
        "mixed_border_and_interior": bool(border and interior),
    }


def _generator_hash(generator: Any) -> str | None:
    source = getattr(generator, "__file__", None)
    if not source:
        return None
    path = Path(source)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def run_probe(
    generator: Any,
    *,
    draws_per_band: int = 64,
    schedule_period: int = 64,
    seed: int = 20261005,
) -> dict[str, Any]:
    """Stress draws and every cyclic lesson start; return a JSON-safe report."""
    if type(draws_per_band) is not int or draws_per_band < 1:
        raise ValueError("draws_per_band must be a positive integer")
    if type(schedule_period) is not int or schedule_period < 2:
        raise ValueError("schedule_period must be at least 2")

    rivals = getattr(generator, "LESSON_COMPETITORS", None)
    if not isinstance(rivals, dict) or not rivals or any(
        not isinstance(name, str) or not callable(function)
        for name, function in rivals.items()
    ):
        raise ValueError("generator must declare nonempty LESSON_COMPETITORS")
    examples_needed = getattr(generator, "EXAMPLES_NEEDED", 3)
    if type(examples_needed) is not int or not 1 <= examples_needed < schedule_period:
        raise ValueError("EXAMPLES_NEEDED must be positive and smaller than schedule_period")

    errors: list[dict[str, Any]] = []
    witness_counts = {
        "shared_color_split": 0,
        "horizontal_only_contact": 0,
        "vertical_only_contact": 0,
        "mixed_border_and_interior": 0,
    }
    rival_refutations = {name: 0 for name in rivals}
    draws = 0

    for band_index, band in enumerate(BANDS):
        for sample_index in range(draws_per_band):
            draw_seed = seed + band_index * 1_000_003 + sample_index * 97
            grid = generator.generate(draw_seed, sample_index, difficulty=band)
            draws += 1
            validation = list(generator.self_check(deepcopy(grid)))
            if validation:
                errors.append(
                    {
                        "kind": "self_check",
                        "band": band,
                        "sample_index": sample_index,
                        "messages": validation,
                    }
                )
                continue
            expected = independent_output(grid)
            mirrored = generator.rule_mirror(deepcopy(grid))
            if mirrored != expected:
                errors.append(
                    {
                        "kind": "rule_mirror_mismatch",
                        "band": band,
                        "sample_index": sample_index,
                    }
                )
            witnesses = independent_witnesses(grid)
            for name, fired in witnesses.items():
                witness_counts[name] += int(fired)
                if not fired:
                    errors.append(
                        {
                            "kind": "missing_witness",
                            "witness": name,
                            "band": band,
                            "sample_index": sample_index,
                        }
                    )
            for name, rival in rivals.items():
                try:
                    rival_output = rival(deepcopy(grid))
                except Exception as exc:  # evidence, not a hidden pass
                    errors.append(
                        {
                            "kind": "rival_error",
                            "rival": name,
                            "band": band,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                if rival_output != expected:
                    rival_refutations[name] += 1
                else:
                    errors.append(
                        {
                            "kind": "rival_survived_draw",
                            "rival": name,
                            "band": band,
                            "sample_index": sample_index,
                        }
                    )

    ambiguous_lessons: list[dict[str, Any]] = []
    cyclic_lessons = 0
    for band_index, band in enumerate(BANDS):
        schedule: list[dict[str, Any]] = []
        schedule_seed = seed + 50_000_000 + band_index * 1_000_003
        for sample_index in range(schedule_period):
            grid = generator.generate(schedule_seed, sample_index, difficulty=band)
            schedule.append({"input": grid, "output": independent_output(grid)})
        for start in range(schedule_period):
            cyclic_lessons += 1
            demo_indices = [
                (start + offset) % schedule_period for offset in range(examples_needed)
            ]
            query_index = (start + examples_needed) % schedule_period
            demos = [schedule[index] for index in demo_indices]
            query = schedule[query_index]
            for name, rival in rivals.items():
                fits_demos = all(
                    rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
                )
                changes_query = (
                    rival(deepcopy(query["input"])) != query["output"]
                )
                if fits_demos and changes_query:
                    ambiguous_lessons.append(
                        {
                            "band": band,
                            "start": start,
                            "demo_indices": demo_indices,
                            "query_index": query_index,
                            "rival": name,
                        }
                    )

    report = {
        "schema": "7f31c4f794b2-component-contract-probe-v1",
        "task_id": getattr(generator, "TASK_ID", None),
        "generator_sha256": _generator_hash(generator),
        "settings": {
            "bands": list(BANDS),
            "draws_per_band": draws_per_band,
            "schedule_period": schedule_period,
            "seed": seed,
            "examples_needed": examples_needed,
        },
        "rivals": sorted(rivals),
        "witness_counts": witness_counts,
        "rival_refutations": rival_refutations,
        "ambiguous_lessons": ambiguous_lessons,
        "errors": errors,
        "summary": {
            "draws": draws,
            "cyclic_lessons": cyclic_lessons,
            "ambiguous_lessons": len(ambiguous_lessons),
            "errors": len(errors),
        },
    }
    report["status"] = "pass" if not errors and not ambiguous_lessons else "fail"
    return report


def write_report(report: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def _load_selected_generator() -> Any:
    source = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("probe_7f31c4f794b2", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=64)
    parser.add_argument("--schedule-period", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261005)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(
        _load_selected_generator(),
        draws_per_band=args.draws_per_band,
        schedule_period=args.schedule_period,
        seed=args.seed,
    )
    if args.out:
        write_report(report, args.out)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
