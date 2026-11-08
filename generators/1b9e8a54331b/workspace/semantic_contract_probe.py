#!/usr/bin/env python3
"""Replayable semantic/override probe for generator 1b9e8a54331b.

The probe is intentionally independent of the repository's aggregate battery.
It exercises the repaired teaching contract, all exact semantic-axis boundary
combinations, uniqueness under sequential sampling, and emits a compact batch
that can be handed directly to ``python -m arcpuzzles apply`` for Racket parity.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[3]
TASK_DIR = SCRIPT.parents[1]
for path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _load_generator():
    source = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("probe_generator_1b9e8a54331b", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _case_record(grid: list[list[int]], *, label: str) -> tuple[dict[str, Any], list[str]]:
    errors = list(GEN.self_check(grid))
    output = GEN.rule_mirror(grid)
    competitor_diffs = {
        name: sum(
            a != b
            for expected_row, rival_row in zip(output, rival(grid))
            for a, b in zip(expected_row, rival_row)
        )
        for name, rival in GEN.LESSON_COMPETITORS.items()
    }
    if not any(6 in row for row in output):
        errors.append("missing crossing witness")
    for name, count in competitor_diffs.items():
        if count == 0:
            errors.append(f"competitor {name} survives")
    try:
        observed = GEN.observe_overrides(grid)
    except Exception as exc:  # retained as evidence, not hidden
        observed = None
        errors.append(f"observe_overrides raised {type(exc).__name__}: {exc}")
    return (
        {
            "label": label,
            "input_sha256": _sha256_json(grid),
            "output_sha256": _sha256_json(output),
            "shape": [len(grid), len(grid[0])],
            "observed": observed,
            "crossing_cells": sum(value == 6 for row in output for value in row),
            "competitor_diff_cells": competitor_diffs,
        },
        errors,
    )


def run_probe() -> tuple[dict[str, Any], list[list[list[int]]], list[list[list[int]]]]:
    failures: list[dict[str, Any]] = []
    ordinary_records: list[dict[str, Any]] = []
    uniqueness: dict[str, dict[str, int]] = {}

    for difficulty in ("easy", "medium", "hard"):
        fingerprints: set[str] = set()
        for sample_index in range(12):
            grid = GEN.generate(17_071, sample_index, difficulty=difficulty)
            record, errors = _case_record(
                grid, label=f"ordinary:{difficulty}:{sample_index}"
            )
            ordinary_records.append(record)
            fingerprints.add(record["input_sha256"])
            if errors:
                failures.append({"label": record["label"], "errors": errors})
        twenty_five = [
            GEN.generate(0, sample_index, difficulty=difficulty)
            for sample_index in range(25)
        ]
        unique_twenty_five = len({_sha256_json(grid) for grid in twenty_five})
        uniqueness[difficulty] = {
            "sampled": 25,
            "unique_inputs": unique_twenty_five,
        }
        if unique_twenty_five < 20:
            failures.append(
                {
                    "label": f"uniqueness:{difficulty}",
                    "errors": [f"only {unique_twenty_five}/25 unique inputs"],
                }
            )

    boundary_records: list[dict[str, Any]] = []
    boundary_index = 0
    for block_axis in ("horizontal", "vertical"):
        for horizontal_seed_count in (1, 2):
            for vertical_seed_count in (1, 2):
                requested = {
                    "grid_h": 14,
                    "grid_w": 14,
                    "horizontal_seed_count": horizontal_seed_count,
                    "vertical_seed_count": vertical_seed_count,
                    "block_axis": block_axis,
                }
                grid = GEN.generate(991, boundary_index, difficulty="hard", **requested)
                record, errors = _case_record(
                    grid,
                    label=(
                        f"boundary:{block_axis}:h{horizontal_seed_count}:"
                        f"v{vertical_seed_count}"
                    ),
                )
                record["requested"] = requested
                boundary_records.append(record)
                if record.get("observed") != requested:
                    errors.append(
                        f"observer mismatch: requested {requested}, got {record.get('observed')}"
                    )
                if errors:
                    failures.append({"label": record["label"], "errors": errors})
                boundary_index += 1

    audited_windows: list[dict[str, Any]] = []
    for seed, start, difficulty in ((7, 187, "easy"), (1, 2, "easy")):
        pairs = []
        for offset in range(4):
            grid = GEN.generate(seed, start + offset, difficulty=difficulty)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        lesson_errors = GEN.lesson_identifiable(pairs[:3], pairs[3])
        audited_windows.append(
            {
                "seed": seed,
                "start": start,
                "difficulty": difficulty,
                "lesson_errors": lesson_errors,
                "demo_crossing_cells": [
                    sum(value == 6 for row in pair["output"] for value in row)
                    for pair in pairs[:3]
                ],
                "demo_wall_stop_diff_cells": [
                    sum(
                        a != b
                        for expected_row, rival_row in zip(
                            pair["output"], GEN.LESSON_COMPETITORS["ignore_walls"](pair["input"])
                        )
                        for a, b in zip(expected_row, rival_row)
                    )
                    for pair in pairs[:3]
                ],
            }
        )
        if lesson_errors:
            failures.append(
                {
                    "label": f"audited-window:{seed}:{start}:{difficulty}",
                    "errors": lesson_errors,
                }
            )

    replay_inputs = [
        GEN.generate(
            123,
            4,
            difficulty="medium",
            grid_h=14,
            grid_w=14,
            horizontal_seed_count=2,
            vertical_seed_count=2,
            block_axis="vertical",
        ),
        GEN.generate(
            321,
            5,
            difficulty="easy",
            grid_h=7,
            grid_w=8,
            horizontal_seed_count=2,
            vertical_seed_count=2,
            block_axis="horizontal",
        ),
        GEN.generate(7, 187, difficulty="easy"),
        GEN.generate(1, 2, difficulty="easy"),
        GEN.generate(99, 0, difficulty="medium", texture="no_crossings"),
    ]
    replay_outputs = [GEN.rule_mirror(grid) for grid in replay_inputs]

    source_bytes = (TASK_DIR / "generator.py").read_bytes()
    report = {
        "schema": "arc-generator-semantic-contract-probe-v1",
        "task_id": GEN.TASK_ID,
        "version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "status": "pass" if not failures else "fail",
        "summary": {
            "ordinary_cases": len(ordinary_records),
            "boundary_cases": len(boundary_records),
            "audited_windows": len(audited_windows),
            "racket_replay_cases": len(replay_inputs),
            "failures": len(failures),
        },
        "uniqueness": uniqueness,
        "ordinary_cases": ordinary_records,
        "boundary_cases": boundary_records,
        "audited_windows": audited_windows,
        "failures": failures,
    }
    return report, replay_inputs, replay_outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    args = parser.parse_args()

    report, inputs, outputs = run_probe()
    _write_json(args.report, report)
    _write_json(args.inputs, {"inputs": inputs})
    _write_json(args.expected, {"outputs": outputs})
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
