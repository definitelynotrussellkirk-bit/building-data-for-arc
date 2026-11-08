"""Independent oracle and coverage probe for b7fbb716d189.

This module is reviewer tooling, not label authority.  It deliberately computes
crop/transform behavior without importing helpers from the selected generator.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "b7fbb716d189"
CORNERS = ("top_left", "top_right", "bottom_right", "bottom_left")
CANONICAL_CORNER_CODE = {
    "top_left": 2,
    "top_right": 4,
    "bottom_right": 3,
    "bottom_left": 1,
}


def _root() -> Path:
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "shared" / "runtime" / "reviewer_support.py").is_file():
            return parent
        if (parent / "reviewer_support.py").is_file() and (parent / "puzzle_generators").is_dir():
            return parent
    raise RuntimeError("could not locate staged or source repository root")


ROOT = _root()
for candidate in (ROOT / "shared" / "runtime", ROOT):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def load_generator(path: str | os.PathLike[str] | None = None):
    if path is None:
        path = os.environ.get("GENERATOR_UNDER_TEST")
    if path is None:
        source = ROOT / "generators" / TASK_ID / "generator.py"
        if not source.is_file():
            source = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    else:
        source = Path(path)
    source = source.resolve()
    spec = importlib.util.spec_from_file_location("reviewed_b7fbb716d189", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def token_info(grid: list[list[int]]) -> tuple[int, int, int, str]:
    hits = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (1, 2, 3, 4)
    ]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one token, found {len(hits)}")
    row, col, value = hits[0]
    h, w = len(grid), len(grid[0])
    corner_by_position = {
        (0, 0): "top_left",
        (0, w - 1): "top_right",
        (h - 1, w - 1): "bottom_right",
        (h - 1, 0): "bottom_left",
    }
    if (row, col) not in corner_by_position:
        raise ValueError(f"token {(row, col)} is not in a corner")
    return row, col, value, corner_by_position[(row, col)]


def motif_crop(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 1, 2, 3, 4)
    ]
    if not cells:
        raise ValueError("motif is empty")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def transform(crop: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in crop]
    if code == 2:
        return [list(row) for row in zip(*crop[::-1])]
    if code == 3:
        return [row[::-1] for row in crop[::-1]]
    if code == 4:
        return [list(row) for row in zip(*crop)]
    raise ValueError(f"invalid transform code {code}")


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    _, _, code, _ = token_info(grid)
    return transform(motif_crop(grid), code)


def corner_shortcut_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical-fit rival: corner, not token color, chooses transform."""
    _, _, _, corner = token_info(grid)
    return transform(motif_crop(grid), CANONICAL_CORNER_CODE[corner])


def observe(grid: list[list[int]]) -> dict[str, int | str]:
    _, _, token, corner = token_info(grid)
    motif_values = [
        value
        for row in grid
        for value in row
        if value not in (0, 1, 2, 3, 4)
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "token": token,
        "token_corner": corner,
        "motif_cells": len(motif_values),
        "motif_colors": len(set(motif_values)),
    }


def audit(module, samples_per_band: int = 128) -> dict:
    canonical = canonical_pairs()
    canonical_matches = [intended_output(pair["input"]) == pair["output"] for pair in canonical]
    canonical_rival_matches = [corner_shortcut_output(pair["input"]) == pair["output"] for pair in canonical]
    by_band: dict[str, dict] = {}
    for band in ("easy", "medium", "hard"):
        counter: Counter[str] = Counter()
        corners: set[str] = set()
        pairings: set[tuple[int, str]] = set()
        profiles: set[tuple[int, int, int]] = set()
        hashes: set[str] = set()
        for index in range(samples_per_band):
            grid = module.generate(1701 + index, index * 7 + 3, difficulty=band)
            counter["self_check_failures"] += bool(module.self_check(grid))
            counter["nondeterministic"] += grid != module.generate(1701 + index, index * 7 + 3, difficulty=band)
            stats = observe(grid)
            corners.add(str(stats["token_corner"]))
            pairings.add((int(stats["token"]), str(stats["token_corner"])))
            profiles.add((int(stats["grid_h"]), int(stats["grid_w"]), int(stats["motif_colors"]) + 2))
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            counter["corner_rival_disagreements"] += intended_output(grid) != corner_shortcut_output(grid)
        by_band[band] = {
            **counter,
            "corners": sorted(corners),
            "token_corner_pairs": sorted([list(item) for item in pairings]),
            "profiles": sorted([list(item) for item in profiles]),
            "distinct_inputs": len(hashes),
        }
    return {
        "schema": "b7fbb716d189-independent-audit-v1",
        "generator_version": getattr(module, "VERSION", None),
        "canonical_oracle_matches": canonical_matches,
        "canonical_corner_rival_matches": canonical_rival_matches,
        "by_band": by_band,
        "limitations": [
            "The Python oracle is supplementary; the packet battery owns Racket parity.",
            "Finite sampling does not prove universal coverage or lesson identifiability.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--samples-per-band", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples_per_band < 1:
        parser.error("--samples-per-band must be positive")
    report = audit(load_generator(args.generator), args.samples_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    bad = not all(report["canonical_oracle_matches"])
    bad |= not all(report["canonical_corner_rival_matches"])
    bad |= any(row["self_check_failures"] or row["nondeterministic"] for row in report["by_band"].values())
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())
