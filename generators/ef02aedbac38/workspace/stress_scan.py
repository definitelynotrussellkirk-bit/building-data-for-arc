#!/usr/bin/env python3
"""Source-bound construction and four-sample density-window stress scan."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import time
from typing import Any

TASK_ID = "ef02aedbac38"
BANDS = ("easy", "medium", "hard")


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"stress_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _role(grid: list[list[int]]) -> str:
    five = sum(value == 5 for row in grid for value in row)
    other = sum(value != 5 for row in grid for value in row)
    if five > other:
        return "dense"
    if five < other:
        return "sparse"
    return "tie"


def audit(generator_path: Path, seeds: int, indices: int) -> dict[str, Any]:
    gen = _load_generator(generator_path)
    failures: list[dict[str, Any]] = []
    role_failures: list[dict[str, Any]] = []
    generated = 0
    started = time.monotonic()

    for band in BANDS:
        for seed in range(seeds):
            grids: list[list[list[int]] | None] = []
            for sample_index in range(indices):
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    generated += 1
                    errors = gen.self_check(grid)
                    if errors:
                        failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "sample_index": sample_index,
                                "errors": errors,
                            }
                        )
                    grids.append(grid)
                except Exception as exc:  # retain exact long-tail coordinates
                    failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "exception": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
                    grids.append(None)

            for start in range(max(0, indices - 3)):
                roles = {
                    _role(grid)
                    for grid in grids[start : start + 4]
                    if grid is not None and gen.strict_canonical_like(grid)
                }
                if not {"dense", "sparse"} <= roles:
                    role_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "roles": sorted(roles),
                        }
                    )

    return {
        "schema": "ef02aedbac38-stress-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": __import__("hashlib").sha256(
            generator_path.read_bytes()
        ).hexdigest(),
        "seeds_per_band": seeds,
        "indices_per_seed": indices,
        "generated": generated,
        "failures": failures,
        "role_failures": role_failures,
        "seconds": round(time.monotonic() - started, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--indices", type=int, default=20)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.indices < 4:
        parser.error("--seeds must be positive and --indices must be at least 4")

    task_dir = Path(__file__).resolve().parent.parent
    generator_path = (args.generator or task_dir / "generator.py").resolve()
    result = audit(generator_path, args.seeds, args.indices)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "generated": result["generated"],
                "failures": len(result["failures"]),
                "role_failures": len(result["role_failures"]),
                "seconds": result["seconds"],
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 1 if result["failures"] or result["role_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
