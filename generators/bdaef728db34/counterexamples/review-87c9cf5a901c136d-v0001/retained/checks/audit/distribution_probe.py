#!/usr/bin/env python3
"""Source-bound audit probe for ordinary generated samples and simple rivals."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Callable

Grid = list[list[int]]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"audit_dist_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_left_rule(grid: Grid) -> Grid:
    return [
        [v if v != 0 and (c == 0 or row[c - 1] != v) else 0 for c, v in enumerate(row)]
        for row in grid
    ]


def component_representative(grid: Grid) -> Grid:
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    seen: set[tuple[int, int]] = set()
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r, c = min(cells)
            out[r][c] = color
    return out


def initial_windows_once(grid: Grid) -> Grid:
    h, w = len(grid), len(grid[0])
    fills: dict[tuple[int, int], int] = {}
    for r in range(h - 1):
        for c in range(w - 1):
            coords = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            vals = [grid[rr][cc] for rr, cc in coords]
            nz = [v for v in vals if v != 0]
            if vals.count(0) == 1 and len(nz) == 3 and len(set(nz)) == 1:
                fills[coords[vals.index(0)]] = nz[0]
    out = [row[:] for row in grid]
    for (r, c), v in fills.items():
        out[r][c] = v
    return out


def iterative_fill(grid: Grid) -> Grid:
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for _ in range(h * w):
        changed = False
        for r in range(h - 1):
            for c in range(w - 1):
                coords = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
                vals = [out[rr][cc] for rr, cc in coords]
                nz = [v for v in vals if v != 0]
                if vals.count(0) == 1 and len(nz) == 3 and len(set(nz)) == 1:
                    rr, cc = coords[vals.index(0)]
                    out[rr][cc] = nz[0]
                    changed = True
        if not changed:
            return out
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True)
    p.add_argument("--generator", type=Path, required=True)
    p.add_argument("--seeds", type=int, default=100)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    module = load_module(args.generator)

    if args.task == "bdaef728db34":
        canonical: Callable[[Grid], Grid] = row_left_rule
        rival: Callable[[Grid], Grid] = component_representative
        rival_name = "one representative per monochrome 4-connected component"
    elif args.task == "8b7d1307ff93":
        canonical = iterative_fill
        rival = initial_windows_once
        rival_name = "fill only initially licensed 2x2 corners once"
    else:
        raise ValueError(args.task)

    per_band = {}
    examples = []
    for difficulty in ("easy", "medium", "hard"):
        row = {
            "requested": args.seeds,
            "generated": 0,
            "generation_errors": 0,
            "validator_failures": 0,
            "rival_disagreements": 0,
        }
        for seed in range(args.seeds):
            try:
                grid = module.generate(seed, 0, difficulty=difficulty)
            except Exception as exc:
                row["generation_errors"] += 1
                if len(examples) < 10:
                    examples.append({"difficulty": difficulty, "seed": seed, "kind": "generation_error", "detail": repr(exc)})
                continue
            row["generated"] += 1
            errs = list(module.self_check(grid, difficulty=difficulty, meta=None))
            if errs:
                row["validator_failures"] += 1
                if len(examples) < 10:
                    examples.append({"difficulty": difficulty, "seed": seed, "kind": "validator_failure", "detail": errs})
            if canonical(grid) != rival(grid):
                row["rival_disagreements"] += 1
                if len(examples) < 10:
                    examples.append({"difficulty": difficulty, "seed": seed, "kind": "rival_disagreement"})
        per_band[difficulty] = row

    total_generated = sum(v["generated"] for v in per_band.values())
    record = {
        "schema": "arcpuzzles-audit-distribution-probe-v1",
        "task_id": args.task,
        "generator_sha256": hashlib.sha256(args.generator.read_bytes()).hexdigest(),
        "sample_schedule": {
            "difficulties": ["easy", "medium", "hard"],
            "seed_range": [0, args.seeds - 1],
            "sample_index": 0,
            "ordinary_overrides": {},
        },
        "rival": rival_name,
        "per_band": per_band,
        "totals": {
            "requested": args.seeds * 3,
            "generated": total_generated,
            "generation_errors": sum(v["generation_errors"] for v in per_band.values()),
            "validator_failures": sum(v["validator_failures"] for v in per_band.values()),
            "rival_disagreements": sum(v["rival_disagreements"] for v in per_band.values()),
            "rival_agreements": total_generated - sum(v["rival_disagreements"] for v in per_band.values()),
        },
        "examples": examples,
        "limits": [
            "Empirical finite-seed probe; source inspection is needed for universal claims.",
            "Canonical behavior is mirrored in this independent Python probe; concrete disagreements are separately verified with public Racket apply evidence.",
        ],
    }
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record["totals"], indent=2))


if __name__ == "__main__":
    main()
