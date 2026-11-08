#!/usr/bin/env python3
"""Reproduce the first-vs-largest symmetric-component curriculum gap."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs

TASK = "a78185b4bd20"
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ["ARCPUZZLES_HOME"]).resolve()
SOURCE = ROOT / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr, nc = rr+dr, cc+dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr,nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr,nc)); stack.append((nr,nc))
            cells.sort()
            result.append((color, cells))
    return result


def normalized(cells: Iterable[tuple[int, int]]):
    cells = list(cells)
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return {(r-r0, c-c0) for r,c in cells}


def lr_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    norm = normalized(cells)
    width = max(c for _, c in norm)
    return all((r, width-c) in norm for r,c in norm)


def recolored_crop(cells: Iterable[tuple[int, int]]):
    norm = normalized(cells)
    h = max(r for r,_ in norm)+1; w = max(c for _,c in norm)+1
    return [[8 if (r,c) in norm else 0 for c in range(w)] for r in range(h)]


def intended(grid):
    for _color, cells in components(grid):
        if lr_symmetric(cells):
            return recolored_crop(cells)
    return [[0]]


def first_color_largest_symmetric_rival(grid):
    """First qualifying color, but largest symmetric component of that color."""
    comps = components(grid)
    first_seen = []
    by_color = defaultdict(list)
    for color, cells in comps:
        if color not in by_color:
            first_seen.append(color)
        by_color[color].append(cells)
    for color in first_seen:
        symmetric = [cells for cells in by_color[color] if lr_symmetric(cells)]
        if symmetric:
            symmetric.sort(key=lambda cells: -len(cells))
            return recolored_crop(symmetric[0])
    return [[0]]


def main() -> int:
    gen = load_generator()
    canon = canonical_pairs(TASK, root=ROOT)
    canonical_matches = []
    for index, pair in enumerate(canon):
        actual = intended(pair["input"])
        rival = first_color_largest_symmetric_rival(pair["input"])
        canonical_matches.append({
            "pair": index,
            "intended_matches_label": actual == pair["output"],
            "rival_matches_label": rival == pair["output"],
            "component_sizes_by_color": {
                str(color): [len(cells) for c, cells in components(pair["input"]) if c == color]
                for color in sorted({c for c, _ in components(pair["input"])})
            },
        })

    generated = []
    aggregate = {
        "draws": 0,
        "rival_agrees": 0,
        "one_component_per_color": 0,
        "exactly_one_symmetric_component": 0,
        "contains_singleton_component": 0,
        "self_check_errors": 0,
    }
    for band_i, band in enumerate(("easy", "medium", "hard")):
        for index in range(200):
            seed = 781000 + band_i * 1000 + index
            grid = gen.generate(seed, index, difficulty=band)
            comps = components(grid)
            counts = defaultdict(int)
            for color, _cells in comps:
                counts[color] += 1
            symmetric_count = sum(lr_symmetric(cells) for _, cells in comps)
            row = {
                "band": band,
                "seed": seed,
                "sample_index": index,
                "component_count": len(comps),
                "one_component_per_color": all(n == 1 for n in counts.values()),
                "symmetric_component_count": symmetric_count,
                "contains_singleton": any(len(cells) == 1 for _, cells in comps),
                "rival_agrees": first_color_largest_symmetric_rival(grid) == intended(grid),
                "self_check": gen.self_check(grid),
            }
            generated.append(row)
            aggregate["draws"] += 1
            aggregate["rival_agrees"] += int(row["rival_agrees"])
            aggregate["one_component_per_color"] += int(row["one_component_per_color"])
            aggregate["exactly_one_symmetric_component"] += int(symmetric_count == 1)
            aggregate["contains_singleton_component"] += int(row["contains_singleton"])
            aggregate["self_check_errors"] += int(bool(row["self_check"]))

    witness = json.loads((HERE / "witness_input.json").read_text())
    witness_result = {
        "self_check": gen.self_check(witness),
        "intended": intended(witness),
        "rival": first_color_largest_symmetric_rival(witness),
        "disagrees": intended(witness) != first_color_largest_symmetric_rival(witness),
        "components": [
            {"color": color, "cells": cells, "size": len(cells), "lr_symmetric": lr_symmetric(cells)}
            for color, cells in components(witness)
        ],
    }
    result = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "canonical_pairs": canonical_matches,
        "canonical_rival_matches": sum(r["rival_matches_label"] for r in canonical_matches),
        "canonical_pair_count": len(canonical_matches),
        "generated_aggregate": aggregate,
        "witness": witness_result,
        "scope": "600 production draws: 200 per explicit difficulty; finite evidence only",
    }
    (HERE / "probe.json").write_text(json.dumps({"result": result, "draws": generated}, indent=2) + "\n")
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
