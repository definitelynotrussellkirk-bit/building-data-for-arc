#!/usr/bin/env python3
"""Source-bound census for semantic-profile retention under exact overrides.

Run from the review packet with:
  python3 run_with_racket.py python3 generators/b1e8f6552b5f/workspace/profile_override_probe.py \
      --seeds 200 --out ../checks/profile-override-probe.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]
DEFAULT_GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator(generator_path: Path):
    spec = importlib.util.spec_from_file_location("reviewed_generator", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR_PATH)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")

    generator_path = args.generator.resolve()
    gen = _load_generator(generator_path)
    profile_cases = (
        (0, "aligned_same_pair", 8, 10),
        (1, "canonical_distinct_pair", 10, 11),
        (2, "mixed_triple", 12, 13),
        (3, "distinct_quad", 12, 12),
    )
    bands = ("easy", "medium", "hard")
    modes = ("height_only", "width_only", "both")
    failures: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    total = 0

    for sample_index, profile, requested_h, requested_w in profile_cases:
        for band in bands:
            for mode in modes:
                overrides: dict[str, int] = {}
                if mode in ("height_only", "both"):
                    overrides["grid_h"] = requested_h
                if mode in ("width_only", "both"):
                    overrides["grid_w"] = requested_w
                row_failures = 0
                unique_inputs: set[str] = set()
                for seed in range(args.seeds):
                    grid = gen.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        **overrides,
                    )
                    total += 1
                    unique_inputs.add(json.dumps(grid, separators=(",", ":")))
                    observed = gen.observe_overrides(grid)
                    centers = tuple((r, c) for r, c, _ in gen._marker_cells(grid))
                    override_ok = all(
                        observed[name] == value for name, value in overrides.items()
                    )
                    profile_ok = gen._layout_ok(
                        centers,
                        profile=profile,
                        h=len(grid),
                        w=len(grid[0]),
                        strict_profile=True,
                    )
                    if not (override_ok and profile_ok):
                        row_failures += 1
                        if len(failures) < 25:
                            failures.append(
                                {
                                    "seed": seed,
                                    "sample_index": sample_index,
                                    "profile": profile,
                                    "difficulty": band,
                                    "mode": mode,
                                    "overrides": overrides,
                                    "observed": observed,
                                    "centers": centers,
                                    "override_ok": override_ok,
                                    "profile_ok": profile_ok,
                                }
                            )
                rows.append(
                    {
                        "profile": profile,
                        "difficulty": band,
                        "mode": mode,
                        "overrides": overrides,
                        "draws": args.seeds,
                        "unique_inputs": len(unique_inputs),
                        "failures": row_failures,
                    }
                )

    result = {
        "schema": "b1e8f6552b5f-profile-override-probe-v1",
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256(generator_path),
        "seed_range": [0, args.seeds - 1],
        "total_draws": total,
        "failure_count": sum(row["failures"] for row in rows),
        "rows": rows,
        "failure_examples": failures,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
