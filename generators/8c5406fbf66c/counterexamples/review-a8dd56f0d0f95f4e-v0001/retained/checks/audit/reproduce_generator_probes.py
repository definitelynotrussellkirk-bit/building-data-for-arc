#!/usr/bin/env python3
"""Reproduce the two audit-target generator-side observations."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def load_generator(repo: Path, task_id: str):
    path = repo / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def marker_columns(grid):
    return [col for col, value in enumerate(grid[0]) if value != 0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = Path.cwd()
    if not (repo / "generators").is_dir():
        raise SystemExit("run from the repository root (the packet wrapper does this)")

    panel, panel_path = load_generator(repo, "5dbba35ed715")
    degenerate = panel.generate(1, 0, texture="marker_off_panel")
    ordinary = []
    for seed in range(100):
        grid = panel.generate(seed, 0)
        if marker_columns(grid) == [12]:
            ordinary.append(seed)
        if len(ordinary) == 5:
            break
    left = panel.generate(0, 0, marker_panel=0)
    right = panel.generate(0, 0, marker_panel=2)

    blocks, blocks_path = load_generator(repo, "8c5406fbf66c")
    block_input = json.loads((repo.parent / "checks/audit/8c5406fbf66c/input.json").read_text())

    report = {
        "schema": "arcpuzzles-audit-generator-probes/1",
        "command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audit/reproduce_generator_probes.py",
            "--out", "../checks/audit/generator_probe.json",
        ],
        "cwd": "packet_root",
        "5dbba35ed715": {
            "generator_sha256": hashlib.sha256(panel_path.read_bytes()).hexdigest(),
            "degenerate_generation": {
                "seed": 1,
                "sample_index": 0,
                "overrides": {"texture": "marker_off_panel"},
                "marker_columns": marker_columns(degenerate),
                "self_check_errors": panel.self_check(degenerate),
            },
            "ordinary_sample_index": 0,
            "ordinary_seeds_emitting_marker_col_12": ordinary,
            "ignored_override_witness": {
                "seed": 0,
                "sample_index": 0,
                "left": {"marker_panel": 0},
                "right": {"marker_panel": 2},
                "generated_inputs_equal": left == right,
                "marker_columns": marker_columns(left),
            },
        },
        "8c5406fbf66c": {
            "generator_sha256": hashlib.sha256(blocks_path.read_bytes()).hexdigest(),
            "input_path": "checks/audit/8c5406fbf66c/input.json",
            "self_check_errors": blocks.self_check(block_input),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
