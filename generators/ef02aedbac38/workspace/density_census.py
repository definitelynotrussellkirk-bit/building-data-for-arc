#!/usr/bin/env python3
"""Source-bound density-role and canonical-shortcut census for ef02aedbac38."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "ef02aedbac38"
BANDS = ("easy", "medium", "hard")


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"density_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _role(grid: list[list[int]]) -> str:
    five = sum(value == 5 for row in grid for value in row)
    other = sum(value != 5 for row in grid for value in row)
    if five > other:
        return "dense"
    if five < other:
        return "sparse"
    return "tie"


def audit(generator_path: Path, seeds: int, samples: int) -> dict[str, Any]:
    gen = _load_generator(generator_path)
    declared_rival = getattr(gen, "CANONICAL_SHORTCUTS", {}).get(
        "sparse_or_canonical_lookup"
    )

    def density_rival(grid):
        if declared_rival is not None:
            return declared_rival(grid)
        facts = gen._grid_facts(grid)
        sparse_or_tied = len(facts["five_cells"]) <= len(facts["other_cells"])
        official = not gen.strict_canonical_like(grid)
        if sparse_or_tied or official:
            return gen._rule_mirror(grid)
        return [[0 for _ in row] for row in grid]

    result: dict[str, Any] = {
        "schema": "ef02aedbac38-density-census-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seeds": seeds,
        "samples_per_seed": samples,
        "bands": {},
    }
    for band in BANDS:
        counts: Counter[str] = Counter()
        unique: set[str] = set()
        errors: list[dict[str, Any]] = []
        windows = balanced = shortcut_killed = 0
        for seed in range(seeds):
            grids = []
            for sample_index in range(samples):
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                except Exception as exc:
                    errors.append(
                        {
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": repr(exc),
                        }
                    )
                    continue
                grids.append(grid)
                unique.add(_grid_hash(grid))
                kind = "canonical" if not gen.strict_canonical_like(grid) else "novel"
                counts[f"{kind}_{_role(grid)}"] += 1
                counts["self_check_errors"] += bool(gen.self_check(grid))
            if len(grids) != samples:
                continue
            for start in range(samples - 3):
                window = grids[start : start + 4]
                roles = {
                    _role(grid)
                    for grid in window
                    if gen.strict_canonical_like(grid)
                }
                windows += 1
                balanced += {"sparse", "dense"} <= roles
                shortcut_killed += any(
                    density_rival(grid) != gen._rule_mirror(grid) for grid in window
                )
        result["bands"][band] = {
            "counts": dict(sorted(counts.items())),
            "distinct_inputs": len(unique),
            "windows": windows,
            "balanced_novel_role_windows": balanced,
            "shortcut_killed_windows": shortcut_killed,
            "errors": errors,
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.samples < 4:
        parser.error("--seeds must be positive and --samples must be at least 4")

    task_dir = Path(__file__).resolve().parent.parent
    generator_path = (args.generator or task_dir / "generator.py").resolve()
    result = audit(generator_path, args.seeds, args.samples)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    failures = sum(
        len(row["errors"]) + row["counts"].get("self_check_errors", 0)
        for row in result["bands"].values()
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
