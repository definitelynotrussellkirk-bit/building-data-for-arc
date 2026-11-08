#!/usr/bin/env python3
"""Reproduce accepted invalid scalar inputs in generator 6d26bc40cbb2."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path

TASK = "6d26bc40cbb2"
ROOT = Path(os.environ["ARCPUZZLES_HOME"]).resolve()
SOURCE = ROOT / "generators" / TASK / "generator.py"
OUT = Path(__file__).with_suffix(".json")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    gen = load_generator()
    cases = [
        ("sample_index_true", 17, True, {}),
        ("sample_index_false", 17, False, {}),
        ("sample_index_float", 17, 1.0, {}),
        ("sample_index_negative", 17, -1, {}),
        ("palette_size_bool", 17, 1, {"palette_size": True}),
        ("palette_size_float", 17, 1, {"palette_size": 1.0}),
        ("palette_size_string", 17, 1, {"palette_size": "1"}),
    ]
    rows = []
    for name, seed, sample_index, overrides in cases:
        row = {
            "name": name,
            "seed": seed,
            "sample_index": sample_index,
            "sample_index_type": type(sample_index).__name__,
            "overrides": overrides,
            "override_types": {key: type(value).__name__ for key, value in overrides.items()},
        }
        try:
            grid = gen.generate(seed, sample_index, **overrides)
            row.update({
                "status": "accepted",
                "shape": [len(grid), len(grid[0])],
                "observed": gen.observe_overrides(grid),
                "self_check": gen.self_check(grid),
            })
        except Exception as exc:  # pragma: no cover - expected only after repair
            row.update({"status": "rejected", "exception": type(exc).__name__, "message": str(exc)})
        rows.append(row)

    result = {
        "schema": "arc-generator-audit-strict-scalars-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "accepted_count": sum(row["status"] == "accepted" for row in rows),
        "case_count": len(rows),
        "cases": rows,
        "finding": "invalid scalar types/ranges are accepted instead of failing closed",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("task_id", "generator_sha256", "accepted_count", "case_count", "finding")}, sort_keys=True))
    return 1 if result["accepted_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
