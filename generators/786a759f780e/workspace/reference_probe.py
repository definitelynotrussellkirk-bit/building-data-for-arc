#!/usr/bin/env python3
"""Independent oracle and curriculum probe for ARC task 786a759f780e.

The selected Racket program remains authoritative.  This module deliberately
reimplements the public transformation without importing private helpers from
``generator.py`` so tests and future reviewers can detect correlated mistakes.
It is also executable: run it through ``run_with_racket.py`` to emit a compact
JSON census of profile coverage, rival disagreement, and deterministic replay.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import argparse
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
from typing import Any, Iterable

TASK_ID = "786a759f780e"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

Grid = list[list[int]]
Cell = tuple[int, int]
_NEIGHBORS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}_generator", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def normalize_grid(grid: Iterable[Iterable[int]]) -> Grid:
    if isinstance(grid, (str, bytes)):
        raise ValueError("grid must be a sequence of rows")
    try:
        out = [list(row) for row in grid]
    except TypeError as exc:
        raise ValueError("grid must be iterable") from exc
    if not out or not out[0] or any(len(row) != len(out[0]) for row in out):
        raise ValueError("grid must be nonempty and rectangular")
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for row in out for v in row):
        raise ValueError("ARC cells must be integer colors 0..9")
    return out


def _hole_count(crop: Grid) -> int:
    height, width = len(crop), len(crop[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if crop[r][c] == 0}
    holes = 0
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        border = False
        while queue:
            r, c = queue.popleft()
            border |= r in (0, height - 1) or c in (0, width - 1)
            for dr, dc in _NEIGHBORS_4:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    queue.append(nxt)
        holes += not border
    return holes


def components(grid: Iterable[Iterable[int]]) -> list[dict[str, Any]]:
    """Extract 4-connected components of *all* nonzero cells, across colors."""
    source = normalize_grid(grid)
    height, width = len(source), len(source[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if source[row][col] == 0 or (row, col) in seen:
                continue
            key_color = source[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[Cell] = []
            while queue:
                cell = queue.popleft()
                cells.append(cell)
                for dr, dc in _NEIGHBORS_4:
                    nr, nc = cell[0] + dr, cell[1] + dc
                    nxt = (nr, nc)
                    if 0 <= nr < height and 0 <= nc < width and nxt not in seen and source[nr][nc] != 0:
                        seen.add(nxt)
                        queue.append(nxt)
            cells.sort()
            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [source[r][left:right + 1] for r in range(top, bottom + 1)]
            result.append({
                "key_color": key_color,
                "cells": tuple(cells),
                "colors": tuple(sorted({source[r][c] for r, c in cells})),
                "area": len(cells),
                "top": top,
                "left": left,
                "height": bottom - top + 1,
                "width": right - left + 1,
                "crop": crop,
                "holes": _hole_count(crop),
            })
    result.sort(key=lambda obj: (obj["top"], obj["left"]))
    for rank, obj in enumerate(result):
        obj["reading_rank"] = rank
    return result


def _pack(items: list[dict[str, Any]]) -> Grid:
    if not items:
        raise ValueError("cannot pack an empty object list")
    height = max(item["height"] for item in items)
    width = sum(item["width"] for item in items) + len(items) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for item in items:
        for row, values in enumerate(item["crop"]):
            for col, value in enumerate(values):
                if value != 0:
                    out[row][left + col] = value
        left += item["width"] + 1
    return out


def oracle(grid: Iterable[Iterable[int]]) -> Grid:
    items = components(grid)
    if not items:
        raise ValueError("grid contains no nonzero objects")
    return _pack(sorted(items, key=lambda obj: (obj["holes"], obj["area"], obj["key_color"])))


def facts(grid: Iterable[Iterable[int]]) -> dict[str, Any]:
    source = normalize_grid(grid)
    items = components(source)
    sorted_items = sorted(items, key=lambda obj: (obj["holes"], obj["area"], obj["key_color"]))
    return {
        "height": len(source),
        "width": len(source[0]),
        "palette": tuple(sorted({v for row in source for v in row})),
        "objects": tuple(
            (item["holes"], item["area"], item["height"], item["width"], item["key_color"], item["colors"])
            for item in items
        ),
        "reading_order": tuple(item["reading_rank"] for item in items),
        "packed_order": tuple(item["reading_rank"] for item in sorted_items),
        "mixed_components": sum(len(item["colors"]) > 1 for item in items),
    }


def run_census(*, per_band: int = 36) -> dict[str, Any]:
    gen = load_generator()
    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "examples_needed": getattr(gen, "EXAMPLES_NEEDED", None),
        "bands": {},
    }
    for band in ("easy", "medium", "hard"):
        profiles: Counter[str] = Counter()
        canvases: Counter[str] = Counter()
        strict = 0
        mixed = 0
        rival_disagreements: Counter[str] = Counter()
        unique: set[str] = set()
        replay_ok = True
        for index in range(per_band):
            seed = 1009 + index * 7919
            grid = gen.generate(seed, index, difficulty=band)
            replay_ok &= grid == gen.generate(seed, index, difficulty=band)
            observed = gen.observe_overrides(grid)
            profiles[observed["scene_profile"]] += 1
            canvases[observed["canvas_profile"]] += 1
            strict += not gen.strict_canonical_like(grid)
            mixed += facts(grid)["mixed_components"] > 0
            expected = oracle(grid)
            if getattr(gen, "rule_mirror", lambda _g: None)(deepcopy(grid)) != expected:
                raise AssertionError(f"Python mirror diverged at band={band} index={index}")
            for name, rival in getattr(gen, "LESSON_COMPETITORS", {}).items():
                rival_disagreements[name] += rival(deepcopy(grid)) != expected
            unique.add(json.dumps(grid, separators=(",", ":")))
        report["bands"][band] = {
            "profiles": dict(sorted(profiles.items())),
            "canvases": dict(sorted(canvases.items())),
            "strict_count": strict,
            "mixed_component_count": mixed,
            "unique_inputs": len(unique),
            "deterministic_replay": replay_ok,
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=36)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_census(per_band=args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
