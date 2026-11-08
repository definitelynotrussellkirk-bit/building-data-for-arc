#!/usr/bin/env python3
"""Independent oracle and coverage probe for 4f6f232c17bc.

This file intentionally does not import geometry helpers from the production
sampler.  Reviewers can point ``--generator`` at a candidate patch and replay
canonical ownership, exact observed axes, clipping, and named-rival coverage.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "4f6f232c17bc"
HOME = Path(__file__).resolve().parents[1]
Grid = list[list[int]]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_4f6f232c17bc", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def divider_column(grid: Grid) -> int:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    columns = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(columns) != 1:
        raise ValueError(f"expected one full-height 5 column, found {columns}")
    return columns[0]


def blue_cells(grid: Grid) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}


def connected4(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        r, c = frontier.pop()
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen == cells


def oracle(grid: Grid) -> Grid:
    """Independent transcription of the selected Racket rule."""
    h, w = len(grid), len(grid[0])
    divider = divider_column(grid)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in blue_cells(grid):
        mirror = 2 * divider - c
        if 0 <= mirror < w:
            out[r][mirror] = 8
    return out


def observed(grid: Grid) -> dict[str, Any]:
    divider = divider_column(grid)
    blues = blue_cells(grid)
    if not blues:
        raise ValueError("no blue cells")
    sides = {"left" if c < divider else "right" for _, c in blues}
    source_side = next(iter(sides)) if len(sides) == 1 else "both"
    mirrors = [2 * divider - c for _, c in blues]
    visible = sum(0 <= c < len(grid[0]) for c in mirrors)
    visibility = "full" if visible == len(blues) else ("partial" if visible else "none")
    distractors = sum(
        1
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1) and not (c == divider and value == 5)
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "blue_size": len(blues),
        "source_side": source_side,
        "mirror_visibility": visibility,
        "n_distractors": distractors,
    }


def profile(grid: Grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def run_audit(*, generator_path: str | None = None, count: int = 40) -> dict[str, Any]:
    gen = load_generator(generator_path)
    canonical = canonical_pairs()
    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "generator_version": getattr(gen, "VERSION", None),
        "canonical_pairs": len(canonical),
        "canonical_accepted": 0,
        "canonical_oracle_matches": 0,
        "bands": {},
        "errors": [],
    }
    for index, pair in enumerate(canonical):
        findings = gen.self_check(deepcopy(pair["input"]))
        if not findings:
            report["canonical_accepted"] += 1
        else:
            report["errors"].append(f"canonical[{index}] rejected: {findings}")
        if oracle(pair["input"]) == pair["output"]:
            report["canonical_oracle_matches"] += 1
        else:
            report["errors"].append(f"canonical[{index}] oracle mismatch")

    for band in ("easy", "medium", "hard"):
        rows = []
        witness_hits = {name: 0 for name in getattr(gen, "SEMANTIC_WITNESSES", {})}
        rival_disagreements = {name: 0 for name in getattr(gen, "SEMANTIC_RIVALS", {})}
        for index in range(count):
            grid = gen.generate(90_000 + index, index, difficulty=band)
            findings = gen.self_check(deepcopy(grid))
            obs = observed(grid)
            rows.append({"profile": profile(grid), "observed": obs, "findings": findings})
            if findings:
                report["errors"].append(f"{band}[{index}] self_check: {findings}")
            intended = oracle(grid)
            for name, witness in getattr(gen, "SEMANTIC_WITNESSES", {}).items():
                witness_hits[name] += bool(witness(deepcopy(grid)))
            for name, rival in getattr(gen, "SEMANTIC_RIVALS", {}).items():
                rival_disagreements[name] += rival(deepcopy(grid)) != intended
        report["bands"][band] = {
            "samples": count,
            "profiles": sorted({tuple(row["profile"]) for row in rows}),
            "source_sides": sorted({row["observed"]["source_side"] for row in rows}),
            "mirror_visibility": sorted({row["observed"]["mirror_visibility"] for row in rows}),
            "witness_hits": witness_hits,
            "rival_disagreements": rival_disagreements,
        }
    report["status"] = "pass" if not report["errors"] else "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator")
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = run_audit(generator_path=args.generator, count=args.count)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
