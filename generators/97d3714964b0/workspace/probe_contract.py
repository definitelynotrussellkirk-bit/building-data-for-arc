#!/usr/bin/env python3
"""Reproducible contract and teaching probe for generator 97d3714964b0.

Run from a review packet with:
    python3 review.py run python3 generators/97d3714964b0/workspace/probe_contract.py \
        --out ../checks/contract-probe.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from copy import deepcopy
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK = "97d3714964b0"


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("contract_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def canonical_recolor(grid: list[list[int]]) -> list[list[int]]:
    """Independent 4-connected color-7 oracle used only by this probe."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in remaining:
                    remaining.remove((rr, cc))
                    cells.add((rr, cc))
                    stack.append((rr, cc))
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        hollow = any(
            grid[r][c] == 0 and (r, c) not in cells
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        )
        color = 4 if hollow else 2
        for r, c in cells:
            out[r][c] = color
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--default-draws", type=int, default=200)
    args = parser.parse_args()

    root = find_root(__file__)
    generator_path = args.generator or root / f"generators/{TASK}/generator.py"
    gen = load_generator(generator_path)
    errors: list[dict[str, Any]] = []
    grids = set()
    cases = 0

    for band in (None, "easy", "medium", "hard"):
        for h in range(7, 15):
            for w in range(9, 15):
                for n_hollow in (1, 2):
                    for n_solid in (1, 2):
                        expected = {
                            "grid_h": h,
                            "grid_w": w,
                            "n_hollow": n_hollow,
                            "n_solid": n_solid,
                        }
                        cases += 1
                        try:
                            grid = gen.generate(19401, cases, difficulty=band, **expected)
                            observed = gen.observe_overrides(grid)
                            validation = gen.self_check(
                                grid, meta={"require_teaching_witness": True}
                            )
                            if observed != expected or validation:
                                errors.append(
                                    {
                                        "band": band,
                                        "expected": expected,
                                        "observed": observed,
                                        "validation": validation,
                                    }
                                )
                            grids.add(freeze(grid))
                        except Exception as exc:  # evidence should retain exact failure
                            errors.append(
                                {
                                    "band": band,
                                    "expected": expected,
                                    "exception": f"{type(exc).__name__}: {exc}",
                                }
                            )

    pairs = canonical_pairs(TASK, root=root)
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in pairs
    }
    per_band_profiles: dict[str, list[list[int]]] = {}
    rival_failures: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        profiles = set()
        for index in range(args.default_draws):
            grid = gen.generate(25000 + index, index * 17 + 3, difficulty=band)
            profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
            intended = canonical_recolor(grid)
            for name, rival in gen.LESSON_COMPETITORS.items():
                if rival(grid) == intended:
                    rival_failures.append({"band": band, "index": index, "rival": name})
        per_band_profiles[band] = [list(profile) for profile in sorted(profiles)]

    canonical_rival_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    profile_hits = {
        band: sorted([p for p in profiles if tuple(p) in canonical_profiles])
        for band, profiles in per_band_profiles.items()
    }

    report = {
        "task_id": TASK,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "override_matrix": {
            "cases": cases,
            "errors": len(errors),
            "unique_grids": len(grids),
            "failure_rows": errors,
        },
        "defaults": {
            "draws_per_band": args.default_draws,
            "profiles": per_band_profiles,
            "canonical_profile_hits": profile_hits,
        },
        "rivals": {
            "canonical_fit": canonical_rival_fit,
            "generated_survivors": rival_failures,
        },
        "status": "pass" if not errors and not rival_failures and all(canonical_rival_fit.values()) else "fail",
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
