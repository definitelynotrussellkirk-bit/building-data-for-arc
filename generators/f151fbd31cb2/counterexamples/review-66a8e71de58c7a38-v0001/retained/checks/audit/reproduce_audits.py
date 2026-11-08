#!/usr/bin/env python3
"""Reproduce the two read-only audit findings selected for this packet."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def digest_grid(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def reproduce_f151() -> Path:
    task_id = "f151fbd31cb2"
    gen, source = load(task_id)
    args = {"seed": 1729, "sample_index": 7, "difficulty": "medium"}
    draws = {
        "shape_key=1": gen.generate(**args, shape_key=1),
        "shape_key=4": gen.generate(**args, shape_key=4),
        "color_key=2": gen.generate(**args, color_key=2),
        "color_key=8": gen.generate(**args, color_key=8),
        "grid_h=11": gen.generate(**args, grid_h=11),
        "grid_h=18": gen.generate(**args, grid_h=18),
    }
    hashes = {name: digest_grid(grid) for name, grid in draws.items()}
    payload = {
        "schema": "arcpuzzles-audit-reproduction-v2",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "cwd": "packet_root",
        "argv": ["python3", "checks/audit/reproduce_audits.py"],
        "base_args": args,
        "finding": "declared exact overrides are accepted but ignored",
        "comparisons": {
            "shape_key_1_vs_4": hashes["shape_key=1"] == hashes["shape_key=4"],
            "color_key_2_vs_8": hashes["color_key=2"] == hashes["color_key=8"],
            "grid_h_11_vs_18": hashes["grid_h=11"] == hashes["grid_h=18"],
        },
        "output_sha256": hashes,
        "representative_output": draws["shape_key=1"],
        "observed_height_for_grid_h_11": len(draws["grid_h=11"]),
        "observed_height_for_grid_h_18": len(draws["grid_h=18"]),
        "documented_domain": True,
        "validator_status": "generator has no task-local self_check",
    }
    if not all(payload["comparisons"].values()):
        raise AssertionError(payload["comparisons"])
    out = ROOT / "checks/audit/f151fbd31cb2-evidence/ignored-overrides.json"
    write(out, payload)
    return out


def reproduce_6c40() -> Path:
    task_id = "6c40e60caa4a"
    gen, source = load(task_id)
    zero = [[0] * 13 for _ in range(13)]
    documented = gen.generate(1729, 7, difficulty="medium", texture="no_seed")
    payload = {
        "schema": "arcpuzzles-audit-reproduction-v2",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "cwd": "packet_root",
        "argv": ["python3", "checks/audit/reproduce_audits.py"],
        "finding": "self_check accepts a blank grid outside the documented domain",
        "all_zero_grid": zero,
        "all_zero_self_check": gen.self_check(zero),
        "all_zero_in_documented_domain": False,
        "documented_no_seed_grid": documented,
        "documented_no_seed_self_check": gen.self_check(documented),
        "documented_no_seed_nonzero_cells": sum(
            value != 0 for row in documented for value in row
        ),
    }
    if payload["all_zero_self_check"] != []:
        raise AssertionError(payload["all_zero_self_check"])
    if payload["documented_no_seed_nonzero_cells"] == 0:
        raise AssertionError("documented no_seed unexpectedly blank")
    out = ROOT / "checks/audit/6c40e60caa4a-evidence/validator-accepts-empty-grid.json"
    write(out, payload)
    return out


def main() -> int:
    outputs = [reproduce_f151(), reproduce_6c40()]
    print(json.dumps({"outputs": [str(p.relative_to(ROOT)) for p in outputs]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
