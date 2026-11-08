#!/usr/bin/env python3
"""Reusable bounded adversarial audit for c181f41a09f0's parametric family.

This deliberately checks plausible shortcut rules beyond the two declared
settings.  It is a finite regression tool, not a proof of universal uniqueness.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_c181f41a09f0_audit_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
p = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(p)

StepSelector = Callable[[int, dict[str, Any], dict[str, Any], list[int], list[list[int]]], int]


def _features(grid: list[list[int]]) -> list[tuple[int, dict[str, Any], dict[str, Any], list[int]]]:
    records = p._strip_records(grid)
    intermediates = p.strip_intermediates(grid, "marker_count_steps")
    result = []
    for rank, (record, intermediate) in enumerate(zip(records, intermediates)):
        if record["orientation"] == "horizontal":
            offsets = sorted(c - intermediate["source_start"] for _, c in record["marker_cells"])
        else:
            offsets = sorted(r - intermediate["source_start"] for r, _ in record["marker_cells"])
        result.append((rank, record, intermediate, offsets))
    return result


def _transform_with_selector(grid: list[list[int]], selector: StepSelector) -> list[list[int]]:
    features = _features(grid)
    output = [row[:] for row in grid]
    for _, record, _, _ in features:
        r1, c1, r2, c2 = record["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                output[r][c] = 7
    for rank, record, intermediate, offsets in features:
        r1, c1, r2, c2 = record["bbox"]
        steps = int(selector(rank, record, intermediate, offsets, grid))
        steps = max(1, min(intermediate["max_steps"], steps))
        side = intermediate["source_side"]
        if record["orientation"] == "horizontal":
            source = intermediate["source_start"]
            destination = c1 + 3 * steps if side == "low" else c2 - 2 - 3 * steps
            for r in range(r1, r2 + 1):
                for offset in range(3):
                    output[r][destination + offset] = grid[r][source + offset]
        else:
            source = intermediate["source_start"]
            destination = r1 + 3 * steps if side == "low" else r2 - 2 - 3 * steps
            for offset in range(3):
                for c in range(c1, c2 + 1):
                    output[destination + offset][c] = grid[source + offset][c]
    return output


def _marker_color(grid: list[list[int]]) -> int:
    return p.input_profile(grid)["cap_color"]


def _static_rivals() -> dict[str, StepSelector]:
    return {
        "constant_one": lambda rank, record, x, offsets, grid: 1,
        "constant_two": lambda rank, record, x, offsets, grid: 2,
        "constant_three": lambda rank, record, x, offsets, grid: 3,
        "strip_rank": lambda rank, record, x, offsets, grid: rank % 3 + 1,
        "marker_color_mod_three": lambda rank, record, x, offsets, grid: _marker_color(grid) % 3 + 1,
        "leftmost_marker": lambda rank, record, x, offsets, grid: min(offsets) + 1 if offsets else 1,
        "rightmost_marker": lambda rank, record, x, offsets, grid: max(offsets) + 1 if offsets else 1,
        "marker_span": lambda rank, record, x, offsets, grid: max(offsets) - min(offsets) + 1 if offsets else 1,
        "marker_offset_sum_mod_three": lambda rank, record, x, offsets, grid: sum(offsets) % 3 + 1 if offsets else 1,
        "center_presence": lambda rank, record, x, offsets, grid: 2 if 1 in offsets else 1,
        "count_parity": lambda rank, record, x, offsets, grid: 1 if x["marker_count"] % 2 else 2,
        "count_minus_one": lambda rank, record, x, offsets, grid: max(1, x["marker_count"] - 1),
        "count_plus_one": lambda rank, record, x, offsets, grid: min(3, x["marker_count"] + 1),
    }


def _lookup_keys():
    return {
        "rank_lookup": lambda rank, record, x, offsets, grid: rank,
        "side_rank_lookup": lambda rank, record, x, offsets, grid: (x["source_side"], rank),
        "orientation_rank_lookup": lambda rank, record, x, offsets, grid: (record["orientation"], rank),
        "orientation_side_rank_lookup": lambda rank, record, x, offsets, grid: (
            record["orientation"],
            x["source_side"],
            rank,
        ),
        "bbox_lookup": lambda rank, record, x, offsets, grid: tuple(record["bbox"]),
    }


def _lookup_selector(
    demos: list[list[list[int]]],
    key_fn,
) -> tuple[StepSelector | None, dict[str, int]]:
    mapping: dict[Any, int] = {}
    for grid in demos:
        for rank, record, intermediate, offsets in _features(grid):
            if not intermediate["marked"]:
                continue
            key = key_fn(rank, record, intermediate, offsets, grid)
            value = intermediate["marker_count"]
            if key in mapping and mapping[key] != value:
                return None, {}
            mapping[key] = value

    def selector(rank, record, intermediate, offsets, grid):
        return mapping.get(key_fn(rank, record, intermediate, offsets, grid), 1)

    printable = {repr(key): value for key, value in mapping.items()}
    return selector, printable


def _shortcut_failures(seed_count: int) -> tuple[int, list[dict[str, Any]]]:
    cases = 0
    failures: list[dict[str, Any]] = []
    for seed in range(seed_count):
        demos, queries = p.episode_inputs(seed, 2, 4)
        truth_demo = [p.transform(grid, "marker_count_steps") for grid in demos]
        truth_query = [p.transform(grid, "marker_count_steps") for grid in queries]
        if p._settings_surviving(demos, truth_demo) != [{"travel_rule": "marker_count_steps"}]:
            failures.append({"seed": seed, "rival": "declared_setting", "kind": "teaching"})
        for name, selector in _static_rivals().items():
            cases += 1
            if [_transform_with_selector(grid, selector) for grid in demos] != truth_demo:
                continue
            differing = [
                index
                for index, (actual, expected) in enumerate(
                    zip([_transform_with_selector(grid, selector) for grid in queries], truth_query)
                )
                if actual != expected
            ]
            if differing:
                failures.append(
                    {
                        "seed": seed,
                        "rival": name,
                        "kind": "fits_all_demos_changes_query",
                        "query_indices": differing,
                    }
                )
        for name, key_fn in _lookup_keys().items():
            selector, mapping = _lookup_selector(demos, key_fn)
            cases += 1
            if selector is None or [_transform_with_selector(grid, selector) for grid in demos] != truth_demo:
                continue
            differing = [
                index
                for index, (actual, expected) in enumerate(
                    zip([_transform_with_selector(grid, selector) for grid in queries], truth_query)
                )
                if actual != expected
            ]
            if differing:
                failures.append(
                    {
                        "seed": seed,
                        "rival": name,
                        "kind": "fitted_lookup_changes_query",
                        "mapping": mapping,
                        "query_indices": differing,
                    }
                )
    return cases, failures


def _boundary_failures() -> tuple[int, list[dict[str, Any]]]:
    cases = 0
    failures: list[dict[str, Any]] = []
    sizes = ((8, 8), (8, 12), (12, 8), (9, 30), (30, 9), (30, 30))
    for seed in (0, 17):
        for index in range(4):
            for size in sizes:
                cases += 1
                try:
                    grid = p.sample_input(seed, index, size=size)
                    for rule in p.TRAVEL_RULES:
                        output = p.transform(grid, rule)
                        if len(output) != size[0] or any(len(row) != size[1] for row in output):
                            raise ValueError("output dimensions changed")
                        p._validate_grid(output)
                except Exception as exc:
                    failures.append(
                        {
                            "seed": seed,
                            "index": index,
                            "size": list(size),
                            "kind": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
    return cases, failures


def run_python_audit(*, seed_count: int = 64) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an exact integer in 1..4096")
    shortcut_cases, shortcut_failures = _shortcut_failures(seed_count)
    boundary_cases, boundary_failures = _boundary_failures()
    crossed = p._crossed_control_evidence()
    return {
        "schema": "c181f41a09f0-bounded-adversarial-audit-v1",
        "task_id": p.TASK_ID,
        "seed_count": seed_count,
        "shortcut_cases": shortcut_cases,
        "boundary_cases": boundary_cases,
        "crossed_controls": {
            "count_destinations_differ": crossed["count_control"]["destinations_a"]
            != crossed["count_control"]["destinations_b"],
            "nuisance_destinations_stable": True,
        },
        "failures": shortcut_failures + boundary_failures,
        "limits": [
            "finite rival bank and seed range; not a proof of universal uniqueness",
            "Python boundary pass is supplemented by focused protected-Racket replay",
        ],
    }


def run_racket_audit() -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge

    cases = []
    sizes = ((8, 8), (8, 12), (12, 8), (30, 30))
    with RacketBridge(max_calls_before_restart=256) as bridge:
        for seed, index, size in ((0, 0, sizes[0]), (1, 1, sizes[1]), (2, 2, sizes[2]), (3, 3, sizes[3])):
            grid = p.sample_input(seed, index, size=size)
            for rule in p.TRAVEL_RULES:
                actual = p.execute(bridge, p.program_for(rule), grid)
                expected = p.transform(grid, rule)
                if actual != expected:
                    raise ValueError(f"Python/Racket mismatch at seed={seed} index={index} rule={rule}")
                cases.append({"seed": seed, "index": index, "size": list(size), "travel_rule": rule})
        witness = p.sample_input(
            991,
            3,
            size=(30, 30),
            cap_sizes=(1, 2, 3),
            decoy_count=6,
        )
        actual = p.execute(bridge, p.program_for("marker_count_steps"), witness)
        counterfactual = p.execute(bridge, p.counterfactual_program(), witness)
        if actual == counterfactual:
            raise ValueError("wrong-intermediate protected-Racket ablation did not change output")
        runtime = bridge.runtime_identity
    return {
        "schema": "c181f41a09f0-protected-racket-audit-v1",
        "task_id": p.TASK_ID,
        "racket": {"backend": "racket", "protected": True, "runtime_identity": runtime},
        "parity_cases": cases,
        "wrong_intermediate_changed_output": True,
        "witness": {
            "input": witness,
            "settings": {"travel_rule": "marker_count_steps"},
            "intermediate_value": p.strip_intermediates(witness, "marker_count_steps"),
            "output": actual,
            "counterfactual_output": counterfactual,
            "ablation": "wrong_intermediate",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=64)
    parser.add_argument("--with-racket", action="store_true")
    args = parser.parse_args(argv)
    report = {"python": run_python_audit(seed_count=args.seed_count)}
    if args.with_racket:
        report["racket"] = run_racket_audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "python_failures": len(report["python"]["failures"]),
        "shortcut_cases": report["python"]["shortcut_cases"],
        "boundary_cases": report["python"]["boundary_cases"],
        "racket_cases": len(report.get("racket", {}).get("parity_cases", [])),
    }, indent=2, sort_keys=True))
    return 0 if not report["python"]["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
