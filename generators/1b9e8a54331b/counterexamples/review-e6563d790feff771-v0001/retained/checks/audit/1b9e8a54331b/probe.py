#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parents[3]
    repo = packet / "repo"
    sys.path.insert(0, str(repo / "shared" / "runtime"))
    task_id = "1b9e8a54331b"
    source = repo / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_1b9", source)
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    seed, sample_index, difficulty = 123, 4, "medium"
    cases = {}
    for label, overrides in {
        "texture_default": {"texture": "default"},
        "texture_warm": {"texture": "warm"},
        "palette_kind_warm": {"palette_kind": "warm"},
    }.items():
        grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
        cases[label] = {
            "overrides": overrides,
            "grid": grid,
            "grid_sha256": hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest(),
            "self_check": gen.self_check(grid),
        }

    try:
        gen.generate(seed, sample_index, difficulty=difficulty, grid_h=14, grid_w=14)
    except Exception as exc:
        boundary = {
            "overrides": {"grid_h": 14, "grid_w": 14},
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    else:
        boundary = {"unexpected": "accepted"}

    report = {
        "schema": "arcpuzzles-audit-control-counterexample-v1",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "cases": cases,
        "identical_output_claim": (
            cases["texture_default"]["grid"]
            == cases["texture_warm"]["grid"]
            == cases["palette_kind_warm"]["grid"]
        ),
        "advertised_boundary_override": boundary,
        "command": [
            "python3",
            "checks/audit/1b9e8a54331b/probe.py",
            "--out",
            "checks/audit/1b9e8a54331b/dead-overrides.json",
        ],
        "cwd": "packet_root",
        "finding": (
            "texture and palette_kind are advertised exact axes but do not affect ordinary "
            "generation; advertised grid_h/grid_w upper boundary 14 is rejected by the "
            "difficulty-local draw range."
        ),
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
