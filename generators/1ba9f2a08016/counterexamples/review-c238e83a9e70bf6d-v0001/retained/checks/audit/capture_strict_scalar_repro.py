#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

CHECKS = Path(__file__).resolve().parent
WORK = CHECKS.parents[1]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))

PROBES = {
    "f6b9f647b109": [
        {"name": "bool_seed", "seed": True, "sample_index": 0, "difficulty": "easy", "overrides": {}},
        {"name": "negative_sample_index", "seed": 991, "sample_index": -1, "difficulty": "easy", "overrides": {}},
        {"name": "invalid_difficulty", "seed": 991, "sample_index": 0, "difficulty": "__invalid_difficulty__", "overrides": {}},
        {"name": "string_grid_h", "seed": 991, "sample_index": 0, "difficulty": "easy", "overrides": {"grid_h": "6"}},
    ],
    "1ba9f2a08016": [
        {"name": "bool_seed", "seed": True, "sample_index": 0, "difficulty": "easy", "overrides": {}},
        {"name": "negative_sample_index", "seed": 991, "sample_index": -1, "difficulty": "easy", "overrides": {}},
        {"name": "string_sample_index", "seed": 991, "sample_index": "1", "difficulty": "easy", "overrides": {}},
    ],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid) -> str:
    payload = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return path, module


def main() -> int:
    for task_id, probes in PROBES.items():
        path, module = load(task_id)
        rows = []
        for probe in probes:
            row = dict(probe)
            try:
                grid = module.generate(
                    probe["seed"],
                    probe["sample_index"],
                    difficulty=probe["difficulty"],
                    **probe["overrides"],
                )
                row.update({
                    "status": "accepted_invalid_scalar",
                    "grid": grid,
                    "grid_sha256": grid_hash(grid),
                    "shape": [len(grid), len(grid[0])],
                    "self_check": module.self_check(grid, difficulty=probe["difficulty"]),
                    "observed_overrides": module.observe_overrides(grid),
                })
            except Exception as exc:
                row.update({
                    "status": "raised",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
            rows.append(row)
        result = {
            "schema": "arcpuzzles-audit-strict-scalar-reproducer-v1",
            "task_id": task_id,
            "generator_path": str(path.relative_to(WORK)),
            "generator_sha256": sha256_bytes(path.read_bytes()),
            "rule_hash": getattr(module, "RULE_HASH", None),
            "working_directory": str(REPO),
            "command": "python3 review.py run python3 ../checks/audit/capture_strict_scalar_repro.py",
            "probes": rows,
            "all_invalid_probes_accepted": all(row["status"] == "accepted_invalid_scalar" for row in rows),
        }
        out = CHECKS / task_id / "strict-scalar-reproducer.json"
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(task_id, result["generator_sha256"], [row["status"] for row in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
