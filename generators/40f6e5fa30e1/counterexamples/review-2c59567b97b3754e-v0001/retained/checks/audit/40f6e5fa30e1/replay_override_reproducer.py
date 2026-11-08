#!/usr/bin/env python3
"""Replay the ignored-exact-axis audit finding for task 40f6e5fa30e1."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_generator(packet_root: Path):
    path = packet_root / "repo/generators/40f6e5fa30e1/generator.py"
    spec = importlib.util.spec_from_file_location("audit_40f6e5fa30e1_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    packet_root = Path(__file__).resolve().parents[3]
    expected = json.loads(args.expected.read_text())
    gen, source = load_generator(packet_root)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()

    rows = []
    failures = []
    for case in expected["cases"]:
        axis = case["axis"]
        requested = case["requested"]
        grid = gen.generate(
            expected["seed"],
            expected["sample_index"],
            difficulty=expected["difficulty"],
            **{axis: requested},
        )
        actual = {
            "axis": axis,
            "requested": requested,
            "grid_sha256": canonical_sha(grid),
            "observed_dual_touch_zero_count": gen._dual_touch_zero_count(grid),
            "observed_single_touch_zero_count": gen._single_touch_zero_count(grid),
            "observed_decor_cells": sum(
                value not in (0, 1, 2) for row in grid for value in row
            ),
            "self_check_errors": gen.self_check(grid),
        }
        rows.append(actual)
        for key, value in actual.items():
            if key in case and case[key] != value:
                failures.append(
                    {"axis": axis, "requested": requested, "field": key,
                     "expected": case[key], "actual": value}
                )

    unique_hashes = sorted({row["grid_sha256"] for row in rows})
    report = {
        "schema": "arcpuzzles-audit-override-replay-v1",
        "task_id": expected["task_id"],
        "generator_sha256": source_sha,
        "expected_generator_sha256": expected["generator_sha256"],
        "seed": expected["seed"],
        "sample_index": expected["sample_index"],
        "difficulty": expected["difficulty"],
        "cases_checked": len(rows),
        "unique_grid_hashes": unique_hashes,
        "rows": rows,
        "failures": failures,
        "status": "pass" if not failures and source_sha == expected["generator_sha256"] else "fail",
        "command": [
            "python3", "checks/audit/40f6e5fa30e1/replay_override_reproducer.py",
            "--expected", "checks/audit/40f6e5fa30e1/override-reproducer.json",
            "--out", "checks/audit/40f6e5fa30e1/replay-result.json",
        ],
        "cwd": "packet_root",
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "cases_checked", "unique_grid_hashes", "failures")}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
