#!/usr/bin/env python3
"""Source-bound curriculum probe for the H118 generator.

This is intentionally independent of private runner internals.  It loads the
selected generator file, exercises its public semantic declarations, and emits
one JSON report suitable for retaining under ``checks/``.  It checks the exact
override domain, finite output codomain, difficulty ordering, all cyclic lesson
windows, and whether every declared rival is visibly refuted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"

# Work both in the source checkout (repo/shared/runtime) and in the portable
# task-test snapshot (runtime_root/puzzle_generators).  The test harness does
# not export its temporary import path to child processes.
for _candidate in (
    TASK_HOME.parents[1] / "shared" / "runtime",
    TASK_HOME.parents[1],
):
    if (_candidate / "puzzle_generators").is_dir():
        sys.path.insert(0, str(_candidate))
        break


def _load_generator():
    spec = importlib.util.spec_from_file_location("h118_probe_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _matrix_key(matrix) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in matrix)


def build_report(samples: int) -> dict[str, Any]:
    if samples < 10:
        raise ValueError("--samples must be at least 10")
    gen = _load_generator()
    failures: list[str] = []

    override_observations: dict[str, dict[str, int]] = {}
    for band in ("easy", "medium", "hard"):
        override_observations[band] = {}
        for n_panels in (2, 3, 4):
            grid = gen.generate(17, 9, difficulty=band, n_panels=n_panels)
            errors = gen.self_check(grid)
            observed = gen.observe_overrides(grid).get("n_panels")
            override_observations[band][str(n_panels)] = observed
            if errors:
                failures.append(f"override {band}/{n_panels} invalid: {errors}")
            if observed != n_panels:
                failures.append(
                    f"override {band}/{n_panels} observed {observed!r}"
                )

    outputs = set()
    for episode in range(24):
        seed = episode * 101
        for sample_index in range(6):
            grid = gen.generate(seed, sample_index)
            outputs.add(_matrix_key(gen.equivalence_output(grid)))
    expected_codomain = int(gen.EXPECTED_OUTPUT_CODOMAIN)
    if len(outputs) != expected_codomain:
        failures.append(
            f"output codomain observed {len(outputs)}, expected {expected_codomain}"
        )

    counts: dict[str, list[int]] = {band: [] for band in ("easy", "medium", "hard")}
    for sample_index in range(samples):
        for band in counts:
            grid = gen.generate(9000 + sample_index, sample_index, difficulty=band)
            counts[band].append(int(gen.observe_overrides(grid)["n_panels"]))
    means = {band: sum(values) / len(values) for band, values in counts.items()}
    if not means["easy"] < means["medium"] < means["hard"]:
        failures.append(f"difficulty panel means are not ordered: {means}")

    lesson_failures: list[dict[str, Any]] = []
    witness_windows: dict[str, int] = {
        name: 0 for name in gen.SEMANTIC_WITNESSES
    }
    # The generator schedules semantic cases modulo EXAMPLES_NEEDED.  Checking
    # every cyclic start in every band verifies the lesson assembler cannot
    # accidentally select a witness-free window.
    for band in ("easy", "medium", "hard"):
        for start in range(int(gen.EXAMPLES_NEEDED)):
            demos = []
            visible = set()
            for sample_index in range(start, start + int(gen.EXAMPLES_NEEDED)):
                grid = gen.generate(77, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.equivalence_output(grid)})
                visible.update(
                    name
                    for name, predicate in gen.SEMANTIC_WITNESSES.items()
                    if predicate(grid)
                )
            query = {
                "input": gen.generate(
                    78, start + int(gen.EXAMPLES_NEEDED), difficulty=band
                )
            }
            reasons = gen.lesson_identifiable(demos, query)
            for name in visible:
                witness_windows[name] += 1
            if reasons:
                lesson_failures.append(
                    {"band": band, "start": start, "reasons": list(reasons)}
                )
    if lesson_failures:
        failures.append(f"{len(lesson_failures)} cyclic lesson windows failed")

    rival_disagreements = {name: 0 for name in gen.SEMANTIC_RIVALS}
    rival_usable_inputs = {name: 0 for name in gen.SEMANTIC_RIVALS}
    witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    shape_sizes = set()
    for sample_index in range(samples):
        grid = gen.generate(12000 + sample_index, sample_index, difficulty="hard")
        truth = gen.equivalence_output(grid)
        shape_sizes.update(len(shape) for shape in gen.panel_shapes(grid))
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                witness_counts[name] += 1
        for name, rival in gen.SEMANTIC_RIVALS.items():
            rival_usable_inputs[name] += 1
            if rival(grid) != truth:
                rival_disagreements[name] += 1
    for name, count in rival_disagreements.items():
        if count == 0:
            failures.append(f"declared rival {name!r} never disagreed with truth")

    source_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    report = {
        "schema": "h118-curriculum-probe-v1",
        "status": "pass" if not failures else "fail",
        "task_id": str(gen.TASK_ID),
        "generator_version": str(gen.VERSION),
        "generator_sha256": source_sha,
        "rule_hash": str(gen.RULE_HASH),
        "samples_per_distribution_probe": samples,
        "override_observations": override_observations,
        "output_codomain": {
            "expected": expected_codomain,
            "observed": len(outputs),
        },
        "difficulty_panel_count_means": means,
        "lesson_windows": {
            "policy": (
                "EXAMPLES_NEEDED consecutive samples; every cyclic start 0.."
                f"{int(gen.EXAMPLES_NEEDED) - 1}; all three difficulty bands"
            ),
            "checked": 3 * int(gen.EXAMPLES_NEEDED),
            "witness_window_counts": witness_windows,
            "failures": lesson_failures,
        },
        "semantic_probe": {
            "witness_counts": witness_counts,
            "rival_disagreements": rival_disagreements,
            "rival_usable_inputs": rival_usable_inputs,
        },
        "observed_shape_sizes": sorted(shape_sizes),
        "failures": failures,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples",
        type=int,
        default=60,
        help="draws per difficulty/semantic distribution probe (minimum 10)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="also write the report to this path; refuses to overwrite",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(args.samples)
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out is not None:
        if args.json_out.exists():
            print(f"refusing to overwrite {args.json_out}", file=sys.stderr)
            return 2
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
