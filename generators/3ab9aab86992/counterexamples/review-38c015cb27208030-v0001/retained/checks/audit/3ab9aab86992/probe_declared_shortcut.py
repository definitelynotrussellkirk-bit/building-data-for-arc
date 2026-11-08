#!/usr/bin/env python3
"""Replay 3ab9aab86992's declared complete-all-corners rival witness."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "3ab9aab86992"
REPO = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(grid):
    raw = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--input-out", required=True)
    args = parser.parse_args()
    gen = load_generator()
    request = {
        "seed": 0,
        "sample_index": 0,
        "difficulty": None,
        "overrides": {"canvas_size": 7, "bg_color": 8, "n_corners": 1, "palette_size": 1},
    }
    grid = gen.generate(request["seed"], request["sample_index"], **request["overrides"])
    actual = gen.rule_mirror(grid)
    rival = gen.CANONICAL_SHORTCUTS["complete_all_corners"](grid)
    validator = gen.self_check(grid)
    observed = gen.observe_overrides(grid)
    witness_results = {name: bool(fn(grid)) for name, fn in gen.SEMANTIC_WITNESSES.items()}
    result = {
        "schema": "audit-declared-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "rule_hash_pin": getattr(gen, "RULE_HASH", None),
        "request": request,
        "input": grid,
        "input_sha256": digest(grid),
        "self_check": validator,
        "observed_overrides": observed,
        "declared_shortcut": "complete_all_corners",
        "semantic_witness_results": witness_results,
        "intended_output": actual,
        "intended_output_sha256": digest(actual),
        "rival_output": rival,
        "rival_output_sha256": digest(rival),
        "rival_disagrees": rival != actual,
        "ordinary_generator_domain": validator == [],
        "command": {
            "cwd": "packet_root",
            "argv": [
                "python3", "review.py", "run", "python3",
                "../checks/audit/3ab9aab86992/probe_declared_shortcut.py",
                "--input-out", "../checks/audit/3ab9aab86992/input.json",
                "--out", "../checks/audit/3ab9aab86992/shortcut-probe.json",
            ],
        },
    }
    input_out = Path(args.input_out)
    input_out.parent.mkdir(parents=True, exist_ok=True)
    input_out.write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(out),
        "input_out": str(input_out),
        "generator_sha256": result["generator_sha256"],
        "self_check": validator,
        "witness_results": witness_results,
        "rival_disagrees": result["rival_disagrees"],
    }, indent=2, sort_keys=True))
    return 0 if validator == [] and result["rival_disagrees"] and all(witness_results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
