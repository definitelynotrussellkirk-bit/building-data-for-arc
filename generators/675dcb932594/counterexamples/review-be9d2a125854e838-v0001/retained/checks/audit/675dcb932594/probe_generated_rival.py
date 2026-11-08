#!/usr/bin/env python3
"""Reproduce the Manhattan-geodesic shortcut audit for task 675dcb932594."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
from collections import Counter
from typing import Any

TASK_ID = "675dcb932594"
BANDS = ("easy", "medium", "hard")


def load_generator(repo: pathlib.Path):
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def endpoints(grid: list[list[int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    starts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    goals = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if len(starts) != 1 or len(goals) != 1:
        raise ValueError(f"expected one start/goal, got {len(starts)}/{len(goals)}")
    return starts[0], goals[0]


def rival(grid: list[list[int]]) -> list[list[int]]:
    """Paint open cells on an obstacle-blind Manhattan geodesic."""
    start, goal = endpoints(grid)
    sr, sc = start
    gr, gc = goal
    direct = abs(sr - gr) + abs(sc - gc)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            if abs(sr - r) + abs(sc - c) + abs(gr - r) + abs(gc - c) == direct:
                out[r][c] = 8
    return out


def classify(grid: list[list[int]]) -> str:
    start, goal = endpoints(grid)
    corridor = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 5}
    if all(r == start[0] for r, _ in corridor):
        return "straight"
    if start[0] == goal[0]:
        return "two_routes"
    rlo, rhi = sorted((start[0], goal[0]))
    clo, chi = sorted((start[1], goal[1]))
    rect = {(r, c) for r in range(rlo, rhi + 1) for c in range(clo, chi + 1)}
    if corridor == rect:
        return "rect"
    if rect < corridor:
        return "rect_with_branch"
    return "L_corridor"


def command_prepare(args: argparse.Namespace) -> None:
    repo = pathlib.Path(args.repo).resolve()
    module, source = load_generator(repo)
    records: list[dict[str, Any]] = []
    grids: list[list[list[int]]] = []
    counts: Counter[str] = Counter()
    for band in BANDS:
        for seed in range(args.per_band):
            grid = module.generate(seed, 0, difficulty=band)
            errors = module.self_check(grid, difficulty=band, meta={})
            if errors:
                raise AssertionError(f"self_check failed band={band} seed={seed}: {errors}")
            kind = classify(grid)
            counts[kind] += 1
            records.append({"index": len(grids), "band": band, "seed": seed, "sample_index": 0, "kind": kind})
            grids.append(grid)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    pathlib.Path(args.inputs).write_text(json.dumps(grids, indent=2) + "\n")
    manifest = {
        "schema": "arcpuzzles-audit-rival-sample-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "per_band": args.per_band,
        "total": len(grids),
        "bands": list(BANDS),
        "kind_counts": dict(sorted(counts.items())),
        "records": records,
        "rival": "paint each open cell on the obstacle-blind Manhattan geodesic between start and goal",
        "working_directory": str(repo),
    }
    pathlib.Path(args.manifest).write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ("task_id", "generator_sha256", "total", "kind_counts")}, indent=2))


def command_compare(args: argparse.Namespace) -> None:
    grids = json.loads(pathlib.Path(args.inputs).read_text())
    racket = json.loads(pathlib.Path(args.racket).read_text())
    results = racket.get("results", [])
    if len(results) != len(grids):
        raise AssertionError(f"result count {len(results)} != input count {len(grids)}")
    mismatches = []
    for i, (grid, result) in enumerate(zip(grids, results)):
        expected = rival(grid)
        if result.get("output") != expected:
            mismatches.append({"index": i, "error": result.get("error")})
    summary = {
        "schema": "arcpuzzles-audit-rival-comparison-v1",
        "task_id": TASK_ID,
        "generator_sha256": racket.get("generator_sha256"),
        "executed_rule_hash": racket.get("executed_rule_hash"),
        "rule_hash_matches_catalog": racket.get("rule_hash_matches_catalog"),
        "sample_count": len(grids),
        "rival_matches": len(grids) - len(mismatches),
        "mismatches": mismatches,
        "verdict": "rival_survives_all_samples" if not mismatches else "rival_refuted",
    }
    pathlib.Path(args.out).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    if mismatches:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--repo", required=True)
    prep.add_argument("--per-band", type=int, default=20)
    prep.add_argument("--inputs", required=True)
    prep.add_argument("--manifest", required=True)
    prep.set_defaults(func=command_prepare)
    comp = sub.add_parser("compare")
    comp.add_argument("--inputs", required=True)
    comp.add_argument("--racket", required=True)
    comp.add_argument("--out", required=True)
    comp.set_defaults(func=command_compare)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
