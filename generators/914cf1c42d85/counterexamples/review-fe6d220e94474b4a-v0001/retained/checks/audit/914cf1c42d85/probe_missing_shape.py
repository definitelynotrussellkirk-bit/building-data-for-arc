#!/usr/bin/env python3
"""Reproduce ordinary samples that silently omit the advertised size-4 shape.

This is audit evidence only. It imports the public generator module directly,
asks for a deterministic ordinary sample, and independently counts monochrome
4-connected body components below the legend row.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Iterable


def load_module(path: Path):
    repo_root = path.parents[2]
    runtime = repo_root / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("audit_target_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: list[list[int]]) -> list[dict[str, object]]:
    """Return monochrome 4-connected components below row 0."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, object]] = []
    for r in range(1, h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[list[int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append([rr, cc])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"color": color, "size": len(cells), "cells": sorted(cells)})
    return sorted(out, key=lambda item: (int(item["size"]), int(item["color"])))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("none", "easy", "medium", "hard"), default="none")
    args = parser.parse_args()

    generator_path = args.generator.resolve()
    module = load_module(generator_path)
    difficulty = None if args.difficulty == "none" else args.difficulty
    grid = module.generate(args.seed, args.sample_index, difficulty=difficulty)
    comps = components(grid)
    legend = [value for value in grid[0] if value != 0]
    meta = {"texture": "default"}
    self_check_errors = list(module.self_check(grid, difficulty=difficulty, meta=meta))
    sizes = [int(item["size"]) for item in comps]
    expected_sizes = [1, 2, 4]
    report = {
        "schema": "arc-audit-missing-shape-v1",
        "task_id": "914cf1c42d85",
        "generator_sha256": sha256(generator_path.read_bytes()).hexdigest(),
        "replay": {
            "seed": args.seed,
            "sample_index": args.sample_index,
            "difficulty": difficulty,
        },
        "grid": grid,
        "legend_colors": legend,
        "body_components": comps,
        "actual_sizes": sizes,
        "expected_sizes_from_declared_invariants": expected_sizes,
        "missing_sizes": sorted(set(expected_sizes) - set(sizes)),
        "self_check_errors": self_check_errors,
        "finding": (
            "ordinary generation omitted an advertised shape, but self_check accepted it"
            if sizes != expected_sizes and not self_check_errors
            else "not reproduced"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "actual_sizes", "missing_sizes", "self_check_errors", "finding")}, indent=2))
    return 0 if report["finding"] != "not reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
