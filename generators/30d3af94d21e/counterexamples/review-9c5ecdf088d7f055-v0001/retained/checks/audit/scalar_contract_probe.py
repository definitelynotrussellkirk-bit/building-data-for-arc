#!/usr/bin/env python3
"""Source-bound audit probe for generator scalar argument validation."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

CASES: list[tuple[str, dict[str, Any]]] = [
    ("seed_bool", {"seed": True, "sample_index": 0}),
    ("seed_float", {"seed": 1.5, "sample_index": 0}),
    ("sample_index_bool", {"seed": 1, "sample_index": True}),
    ("sample_index_negative", {"seed": 1, "sample_index": -1}),
    ("sample_index_float", {"seed": 1, "sample_index": 0.5}),
    ("difficulty_unknown", {"seed": 1, "sample_index": 0, "difficulty": "__invalid_difficulty__"}),
    ("difficulty_int", {"seed": 1, "sample_index": 0, "difficulty": 1}),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_generator(path: Path, task_id: str):
    spec = importlib.util.spec_from_file_location(f"audit_scalar_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    repo = Path.cwd()
    path = repo / "generators" / args.task_id / "generator.py"
    source = path.read_bytes()
    gen = load_generator(path, args.task_id)

    cases = list(CASES)
    if args.task_id == "30d3af94d21e":
        cases.append(
            (
                "integer_override_float",
                {
                    "seed": 1,
                    "sample_index": 0,
                    "difficulty": "hard",
                    "marker_row_count": 6.75,
                },
            )
        )

    results = []
    for name, kwargs in cases:
        try:
            grid = gen.generate(**kwargs)
        except Exception as exc:  # evidence includes exact rejection type/message
            results.append(
                {
                    "case": name,
                    "kwargs": kwargs,
                    "status": "rejected",
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                }
            )
        else:
            encoded = json.dumps(grid, separators=(",", ":")).encode()
            results.append(
                {
                    "case": name,
                    "kwargs": kwargs,
                    "status": "accepted",
                    "height": len(grid),
                    "width": len(grid[0]) if grid else 0,
                    "grid_sha256": sha256_bytes(encoded),
                    "self_check": list(gen.self_check(grid)),
                }
            )

    report = {
        "schema": "arc-review-scalar-contract-probe-v1",
        "task_id": args.task_id,
        "generator_path": str(path.relative_to(repo)),
        "generator_sha256": sha256_bytes(source),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "declared_version": getattr(gen, "VERSION", None),
        "working_directory": str(repo),
        "results": results,
        "accepted_cases": [row["case"] for row in results if row["status"] == "accepted"],
        "rejected_cases": [row["case"] for row in results if row["status"] == "rejected"],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
