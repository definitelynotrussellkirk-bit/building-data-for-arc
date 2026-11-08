#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK_ID = "cd818a9d92d1"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SEED_HEX = "f59f3aa37122ea0303aab4ddf510ec4175ce993e11940e34b6d8d29c0699578f"
SEED = int(SEED_HEX[:16], 16)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    gen = load(SOURCE, "ticket_647f_generator")
    common = {
        "seed": SEED,
        "sample_index": 0,
        "difficulty": "easy",
        "grid_h": 5,
        "branch_profile": "compact_one_bend_one_distractor",
    }
    valid = gen.generate(grid_w=6, **common)
    valid_observed = gen.observe_overrides(valid)
    invalid = {"raised": False, "exception_type": None, "message": None}
    try:
        gen.generate(grid_w=5, **common)
    except Exception as exc:  # record actual public API behavior
        invalid = {
            "raised": True,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    result = {
        "schema": "arcpuzzles-supplementary-api-boundary-v1",
        "ticket_id": "ticket-647f5dfe13c25ecd",
        "task_id": TASK_ID,
        "probe_seed_hex": SEED_HEX,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "axis": "grid_w",
        "advertised_domain": "6..18",
        "valid_call": {**common, "grid_w": 6},
        "valid_shape": [len(valid), len(valid[0])],
        "valid_self_check_errors": gen.self_check(valid),
        "valid_observed_overrides": valid_observed,
        "invalid_call": {**common, "grid_w": 5},
        "invalid_behavior": invalid,
        "boundary_exact": (
            len(valid) == 5
            and len(valid[0]) == 6
            and gen.self_check(valid) == []
            and valid_observed
            == {
                "grid_h": 5,
                "grid_w": 6,
                "branch_profile": "compact_one_bend_one_distractor",
            }
            and invalid["raised"]
            and invalid["exception_type"] == "ValueError"
        ),
        "valid_input": valid,
    }
    if not result["boundary_exact"]:
        raise SystemExit(json.dumps(result, indent=2))
    path = Path(__file__).with_name("result.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"boundary_exact": True, "invalid_behavior": invalid}, indent=2))


if __name__ == "__main__":
    main()
