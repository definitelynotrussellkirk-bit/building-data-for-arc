#!/usr/bin/env python3
"""Read-only exact-control audit for generator 446c18f3b7f4."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PACKET_ROOT = HERE.parents[4]
REPO = PACKET_ROOT / "WORK" / "repo"
for path in (REPO / "shared" / "runtime", REPO / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

TASK = "446c18f3b7f4"
SOURCE = REPO / "generators" / TASK / "generator.py"
OUT = HERE.parent / "evidence.json"


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    gen = load_module()
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

    pair_checks = {}
    for axis, left, right in (
        ("palette_kind", "warm", "cool"),
        ("texture", "warm", "cool"),
        ("palette_kind", "default", "varied"),
    ):
        identical = 0
        examples = []
        for seed in range(100):
            kwargs_left = {axis: left, "grid_h": 13, "grid_w": 13, "n_frames": 2}
            kwargs_right = {axis: right, "grid_h": 13, "grid_w": 13, "n_frames": 2}
            a = gen.generate(seed, 0, difficulty="medium", **kwargs_left)
            b = gen.generate(seed, 0, difficulty="medium", **kwargs_right)
            if a == b:
                identical += 1
                if len(examples) < 1:
                    examples.append({
                        "seed": seed,
                        "left_overrides": kwargs_left,
                        "right_overrides": kwargs_right,
                        "grid": a,
                        "self_check": gen.self_check(a),
                    })
        pair_checks[f"{axis}:{left}_vs_{right}"] = {
            "trials": 100,
            "identical": identical,
            "first_identical": examples,
        }

    frame_count = {"trials": 200, "mismatches": [], "histogram": {}}
    for seed in range(frame_count["trials"]):
        requested = 3
        grid = gen.generate(seed, 0, difficulty="medium", grid_h=11, grid_w=11, n_frames=requested)
        actual = len(gen._green_components(grid))
        frame_count["histogram"][str(actual)] = frame_count["histogram"].get(str(actual), 0) + 1
        if actual != requested and len(frame_count["mismatches"]) < 10:
            frame_count["mismatches"].append({
                "seed": seed,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": {"grid_h": 11, "grid_w": 11, "n_frames": requested},
                "actual_frames": actual,
                "self_check": gen.self_check(grid),
                "grid": grid,
            })

    rejection_probes = []
    for difficulty, overrides in (
        ("medium", {"n_frames": 6}),
        ("easy", {"n_frames": 2}),
        ("medium", {"grid_h": 5}),
        ("hard", {"n_frames": 6}),
    ):
        try:
            grid = gen.generate(0, 0, difficulty=difficulty, **overrides)
            rejection_probes.append({
                "difficulty": difficulty,
                "overrides": overrides,
                "accepted": True,
                "shape": [len(grid), len(grid[0])],
            })
        except Exception as exc:
            rejection_probes.append({
                "difficulty": difficulty,
                "overrides": overrides,
                "accepted": False,
                "exception": f"{type(exc).__name__}: {exc}",
            })

    issue_count = sum(row["identical"] == row["trials"] for row in pair_checks.values())
    issue_count += int(bool(frame_count["mismatches"]))
    issue_count += sum(not row["accepted"] for row in rejection_probes)
    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK,
        "generator_sha256": source_hash,
        "paired_exact_control_checks": pair_checks,
        "requested_frame_count_check": frame_count,
        "declared_range_rejection_probes": rejection_probes,
        "verdict": "reproduced_contract_defects" if issue_count else "no_issue_found",
        "scope": "Generator exact-control behavior only; no incorrect Racket label is claimed.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "generator_sha256": source_hash,
        "paired_checks": {key: value["identical"] for key, value in pair_checks.items()},
        "frame_count_histogram": frame_count["histogram"],
        "saved_frame_mismatches": len(frame_count["mismatches"]),
        "rejection_probes": rejection_probes,
        "verdict": report["verdict"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
