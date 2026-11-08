#!/usr/bin/env python3
"""Build self-contained audit comparison evidence from public Racket apply output."""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Any

Grid = list[list[int]]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"audit_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def component_representative_rival(grid: Grid) -> Grid:
    """Keep one lexicographically first cell per 4-connected monochrome object."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    seen: set[tuple[int, int]] = set()
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            seen.add((r0, c0))
            queue = deque([(r0, c0)])
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r, c = min(cells)
            out[r][c] = color
    return out


def initial_windows_once_rival(grid: Grid) -> Grid:
    """Fill only corners already licensed by the original grid, simultaneously."""
    h, w = len(grid), len(grid[0])
    fills: dict[tuple[int, int], int] = {}
    for r in range(h - 1):
        for c in range(w - 1):
            coords = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            vals = [grid[rr][cc] for rr, cc in coords]
            nonzero = [v for v in vals if v != 0]
            if vals.count(0) == 1 and len(nonzero) == 3 and len(set(nonzero)) == 1:
                fills[coords[vals.index(0)]] = nonzero[0]
    out = [row[:] for row in grid]
    for (r, c), color in fills.items():
        out[r][c] = color
    return out


def differing_cells(a: Grid, b: Grid) -> list[dict[str, int]]:
    return [
        {"row": r, "col": c, "canonical": a[r][c], "rival": b[r][c]}
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--racket", type=Path, required=True)
    parser.add_argument("--rival", choices=("component-representative", "initial-windows-once"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    grid: Grid = json.loads(args.input.read_text())
    racket: dict[str, Any] = json.loads(args.racket.read_text())
    canonical: Grid = racket["results"][0]["output"]
    rival = (
        component_representative_rival(grid)
        if args.rival == "component-representative"
        else initial_windows_once_rival(grid)
    )

    module = load_module(args.generator)
    validator_errors = list(module.self_check(grid, difficulty=None, meta=None))
    record = {
        "schema": "arcpuzzles-audit-rival-comparison-v1",
        "task_id": args.task,
        "generator_sha256": racket["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "input_sha256": racket["results"][0]["input_sha256"],
        "canonical_output_sha256": racket["results"][0]["output_sha256"],
        "rival": args.rival,
        "validator_errors": validator_errors,
        "validator_passes": not validator_errors,
        "input": grid,
        "canonical_output": canonical,
        "rival_output": rival,
        "outputs_disagree": canonical != rival,
        "differing_cells": differing_cells(canonical, rival),
        "racket_evidence": str(args.racket),
    }
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("task_id", "rival", "validator_passes", "outputs_disagree", "differing_cells")}, indent=2))


if __name__ == "__main__":
    main()
