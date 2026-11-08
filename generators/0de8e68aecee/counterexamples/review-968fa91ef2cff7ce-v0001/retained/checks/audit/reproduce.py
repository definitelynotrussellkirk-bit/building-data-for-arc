#!/usr/bin/env python3
"""Reproduce the two assigned audit findings without editing either target."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "repo/shared/runtime"), str(ROOT / "repo/src")]


def load(task_id: str):
    path = ROOT / "repo/generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_hash(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def write(task_id: str, report: dict) -> None:
    out = ROOT / "checks/audit" / task_id / "case.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def probe_0de8e68aecee() -> None:
    task_id = "0de8e68aecee"
    gen, path = load(task_id)
    low = gen.generate(123, 7, difficulty="medium", palette_size=3)
    high = gen.generate(123, 7, difficulty="medium", palette_size=5)
    unknown = gen.generate(123, 7, difficulty="medium", __unknown_typo__="accepted")
    dimensions = []
    for seed in range(20):
        grid = gen.generate(seed, 0, difficulty="hard")
        dimensions.append({"seed": seed, "h": len(grid), "w": len(grid[0])})
    write(
        task_id,
        {
            "task_id": task_id,
            "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "rule_hash": "a3e81b1ce61f",
            "cwd": "packet_root",
            "command": ["python3", "checks/audit/reproduce.py"],
            "probe": "advertised exact controls and ordinary dimension domain",
            "requests": [
                {"seed": 123, "sample_index": 7, "difficulty": "medium", "overrides": {"palette_size": 3}},
                {"seed": 123, "sample_index": 7, "difficulty": "medium", "overrides": {"palette_size": 5}},
                {"seed": 123, "sample_index": 7, "difficulty": "medium", "overrides": {"__unknown_typo__": "accepted"}},
            ],
            "palette_size_3_hash": grid_hash(low),
            "palette_size_5_hash": grid_hash(high),
            "palette_size_outputs_identical": low == high,
            "unknown_override_accepted": True,
            "unknown_override_hash": grid_hash(unknown),
            "hard_dimensions": dimensions,
            "ordinary_outside_declared_12_22": [
                row for row in dimensions
                if not (12 <= row["h"] <= 22 and 12 <= row["w"] <= 22)
            ],
            "validator_domain_note": (
                "Generated hard-band outputs are ordinary generator outputs; "
                "they contradict the AXES-declared 12..22 dimension range."
            ),
        },
    )


def probe_f813212d1e20() -> None:
    task_id = "f813212d1e20"
    gen, path = load(task_id)
    low = gen.generate(
        321, 4, difficulty="medium", ring_count=1, n_decoys=0, grid_h=5, grid_w=5
    )
    high = gen.generate(
        321, 4, difficulty="medium", ring_count=7, n_decoys=3, grid_h=22, grid_w=24
    )
    unknown = gen.generate(321, 4, difficulty="medium", __unknown_typo__=1)
    one_pixel = [[0] * 5 for _ in range(5)]
    one_pixel[2][2] = 3
    write(
        task_id,
        {
            "task_id": task_id,
            "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "rule_hash": "36651b0c48c1",
            "cwd": "packet_root",
            "command": ["python3", "checks/audit/reproduce.py"],
            "probe": "advertised controls and self-check semantic minimum",
            "requests": [
                {"seed": 321, "sample_index": 4, "difficulty": "medium", "overrides": {"ring_count": 1, "n_decoys": 0, "grid_h": 5, "grid_w": 5}},
                {"seed": 321, "sample_index": 4, "difficulty": "medium", "overrides": {"ring_count": 7, "n_decoys": 3, "grid_h": 22, "grid_w": 24}},
                {"seed": 321, "sample_index": 4, "difficulty": "medium", "overrides": {"__unknown_typo__": 1}},
            ],
            "low_request": {"hash": grid_hash(low), "h": len(low), "w": len(low[0]), "fires": len(gen._fires(low))},
            "high_request": {"hash": grid_hash(high), "h": len(high), "w": len(high[0]), "fires": len(gen._fires(high))},
            "contradictory_override_outputs_identical": low == high,
            "unknown_override_accepted": True,
            "unknown_override_hash": grid_hash(unknown),
            "one_pixel_grid": one_pixel,
            "one_pixel_self_check": gen.self_check(one_pixel),
            "validator_domain_note": (
                "The one-pixel input is intentionally outside the documented task grammar "
                "but is accepted by self_check, demonstrating that the validator does not "
                "enforce its own invariant."
            ),
        },
    )


if __name__ == "__main__":
    probe_0de8e68aecee()
    probe_f813212d1e20()
    print("wrote checks/audit/{0de8e68aecee,f813212d1e20}/case.json")
