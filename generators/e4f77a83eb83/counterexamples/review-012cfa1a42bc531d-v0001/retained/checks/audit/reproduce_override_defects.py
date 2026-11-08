#!/usr/bin/env python3
"""Reproduce two audit-only override-contract defects without editing targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

WORK_ROOT = Path(__file__).resolve().parents[2]
REPO = WORK_ROOT / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def digest_json(value: Any) -> str:
    encoded = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def audit_e4() -> None:
    task_id = "e4f77a83eb83"
    gen, source = load(task_id)
    root = WORK_ROOT / "checks" / "audit" / task_id
    common = {"seed": 17, "sample_index": 3, "difficulty": "medium"}
    low = gen.generate(**common, n_pairs=1)
    high = gen.generate(**common, n_pairs=8)
    observed = len({cell for row in low for cell in row if cell != 0})
    assert low == high
    assert observed == 5
    assert gen.self_check(low) == []
    write_json(root / "input.json", low)
    write_json(root / "repro.json", {
        "schema": "arc-audit-override-repro-v1",
        "task_id": task_id,
        "classification": "reproduced defect: advertised exact override ignored",
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "declared_axis": {"name": "n_pairs", "valid": "1..8"},
        "replay": common,
        "calls": [
            {"overrides": {"n_pairs": 1}, "input_sha256": digest_json(low)},
            {"overrides": {"n_pairs": 8}, "input_sha256": digest_json(high)},
        ],
        "inputs_equal": low == high,
        "observed_distinct_nonzero_colors_as_pairs": observed,
        "self_check": gen.self_check(low),
        "cause": "generate() draws key 'pairs' rather than the advertised 'n_pairs'",
        "command": ["python3", "checks/audit/reproduce_override_defects.py"],
        "cwd": "packet_root/WORK",
    })


def audit_204() -> None:
    task_id = "204eaaff6c24"
    gen, source = load(task_id)
    root = WORK_ROOT / "checks" / "audit" / task_id
    common = {"seed": 17, "sample_index": 3, "difficulty": "medium"}
    int_two = gen.generate(**common, n_cells=2)
    float_two = gen.generate(**common, n_cells=2.7)
    int_one = gen.generate(**common, n_cells=1)
    bool_one = gen.generate(**common, n_cells=True)
    default = gen.generate(**common)
    unknown = gen.generate(**common, unknown_axis=123)
    assert float_two == int_two
    assert bool_one == int_one
    assert unknown == default
    assert gen.self_check(float_two) == []
    write_json(root / "input.json", float_two)
    write_json(root / "repro.json", {
        "schema": "arc-audit-override-repro-v1",
        "task_id": task_id,
        "classification": "reproduced defect: invalid and unknown overrides silently accepted",
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "declared_axis": {"name": "n_cells", "type": "int", "valid": "1..30"},
        "replay": common,
        "invalid_type_equivalences": [
            {
                "invalid": {"n_cells": 2.7},
                "coerced_to": {"n_cells": 2},
                "same_input": float_two == int_two,
                "input_sha256": digest_json(float_two),
                "observed": gen.observe_overrides(float_two),
            },
            {
                "invalid": {"n_cells": True},
                "coerced_to": {"n_cells": 1},
                "same_input": bool_one == int_one,
                "input_sha256": digest_json(bool_one),
                "observed": gen.observe_overrides(bool_one),
            },
        ],
        "unknown_override": {
            "invalid": {"unknown_axis": 123},
            "silently_ignored": unknown == default,
            "input_sha256": digest_json(unknown),
        },
        "self_check": gen.self_check(float_two),
        "cause": "n_cells is coerced with int(...) before strict type validation; unknown keys are not rejected",
        "command": ["python3", "checks/audit/reproduce_override_defects.py"],
        "cwd": "packet_root/WORK",
    })


if __name__ == "__main__":
    audit_e4()
    audit_204()
    print("wrote audit reproductions for e4f77a83eb83 and 204eaaff6c24")
