"""Replay the semantic blind spots found in this packet's immutable audits.

The target generators are read-only. This probe checks protected Racket output,
executable canonical-fitting rivals, ordinary generated support, and one exact
self_check-accepted counterexample per target.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from review_probe import REPO, RacketBridge, load_generator, read_task, rule_application

IDS = ("4a3ababcaceb", "cf60523d1603")

TILE_ADVERSARY = [
    [2, 2, 0, 9, 0, 0, 0, 9, 1, 1, 0],
    [2, 0, 0, 9, 0, 3, 0, 9, 1, 1, 0],
    [0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0],
]
TILE_EXPECTED = [
    [2, 2, 0, 9, 8, 8, 0, 9, 1, 1, 0],
    [2, 0, 0, 9, 8, 0, 0, 9, 1, 1, 0],
    [0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0],
]

COLUMN_ADVERSARY = [
    [2, 0, 3, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [2, 0, 4, 0, 0],
]
COLUMN_EXPECTED = [
    [2, 0, 3, 0, 0],
    [2, 0, 0, 0, 0],
    [2, 0, 0, 0, 0],
    [2, 0, 0, 0, 0],
    [2, 0, 0, 0, 0],
    [2, 0, 4, 0, 0],
]


def _segments(length: int, dividers: list[int]) -> list[tuple[int, int]]:
    bounds = [-1, *dividers, length]
    return [(a + 1, b) for a, b in zip(bounds, bounds[1:]) if b - a > 1]


def _tile_layout(grid):
    h, w = len(grid), len(grid[0])
    divider_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    divider_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    row_spans = _segments(h, divider_rows)
    col_spans = _segments(w, divider_cols)
    tiles = []
    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            tiles.append({
                "span": (r0, r1, c0, c1),
                "cells": [row[c0:c1] for row in grid[r0:r1]],
            })
    return tiles


def largest_motif_rival(grid):
    """Canonical-fitting rival: copy the densest non-target tile, any color.

    Ties use row-major order. This agrees with all public examples and ordinary
    draws because their red source is first-on-tie or strictly denser than every
    decoy, but it does not encode the rule's color-2 authority.
    """
    out = [row[:] for row in grid]
    tiles = _tile_layout(grid)
    target_index = next(i for i, tile in enumerate(tiles)
                        if any(3 in row for row in tile["cells"]))
    candidates = [(sum(value != 0 for row in tile["cells"] for value in row), -i, i)
                  for i, tile in enumerate(tiles) if i != target_index]
    source_index = max(candidates)[2]
    source = tiles[source_index]["cells"]
    r0, r1, c0, c1 = tiles[target_index]["span"]
    for rr, r in enumerate(range(r0, r1)):
        for cc, c in enumerate(range(c0, c1)):
            out[r][c] = 8 if source[rr][cc] != 0 else 0
    return out


def endpoint_presence_rival(grid):
    """Canonical-fitting rival: bridge any two nonzero column endpoints.

    It ignores whether the endpoint colors match. All canonical and ordinary
    generated columns make that distinction invisible.
    """
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] != 0]
        if len(rows) != 2:
            continue
        r0, r1 = rows
        if all(grid[r][c] == 0 for r in range(r0 + 1, r1)):
            color = grid[r0][c]
            for r in range(r0, r1 + 1):
                out[r][c] = color
    return out


def _tile_stats(grid):
    tiles = _tile_layout(grid)
    target = next(i for i, tile in enumerate(tiles)
                  if any(3 in row for row in tile["cells"]))
    source = max(range(len(tiles)),
                 key=lambda i: sum(value == 2 for row in tiles[i]["cells"] for value in row))
    decoys = [sum(value != 0 for row in tile["cells"] for value in row)
              for i, tile in enumerate(tiles) if i not in (source, target)]
    return {
        "tile_rows": len({tile["span"][0] for tile in tiles}),
        "tile_cols": len({tile["span"][2] for tile in tiles}),
        "source_twos": sum(value == 2 for row in tiles[source]["cells"] for value in row),
        "max_decoy_nonzero": max(decoys, default=0),
    }


def _column_stats(grid):
    h, w = len(grid), len(grid[0])
    populated = 0
    mixed_endpoint = 0
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] != 0]
        if not rows:
            continue
        populated += 1
        if len(rows) == 2 and grid[rows[0]][c] != grid[rows[1]][c]:
            mixed_endpoint += 1
    return {"populated_columns": populated, "mixed_endpoint_columns": mixed_endpoint}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=80)
    args = parser.parse_args()
    if args.draws < 1:
        parser.error("--draws must be positive")
    args.out.mkdir(parents=True, exist_ok=False)

    rivals = {IDS[0]: largest_motif_rival, IDS[1]: endpoint_presence_rival}
    adversaries = {IDS[0]: (TILE_ADVERSARY, TILE_EXPECTED),
                   IDS[1]: (COLUMN_ADVERSARY, COLUMN_EXPECTED)}
    reports = {}
    cases = []

    with RacketBridge() as bridge:
        for task_id in IDS:
            source = REPO / f"generators/{task_id}/generator.py"
            module = load_generator(source)
            task = read_task(task_id)
            canonical = task["train"] + task["test"]
            rival = rivals[task_id]
            report = {
                "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "version": module.VERSION,
                "canonical_pairs": len(canonical),
                "canonical_rival_matches": 0,
                "canonical_racket_matches": 0,
                "ordinary_draws": args.draws,
                "ordinary_rival_matches": 0,
                "ordinary_racket_checks": 0,
                "ordinary_self_check_rejections": 0,
            }
            for pair in canonical:
                actual = bridge.eval_text(rule_application(task["program_solution"], pair["input"]))
                assert actual == pair["output"]
                report["canonical_racket_matches"] += 1
                report["canonical_rival_matches"] += rival(pair["input"]) == pair["output"]

            profile_counts = Counter()
            detail_counts = Counter()
            for seed in range(args.draws):
                grid = module.generate(seed, seed, difficulty="medium")
                report["ordinary_self_check_rejections"] += bool(module.self_check(grid))
                if task_id == IDS[0]:
                    stats = _tile_stats(grid)
                    profile_counts[f"{stats['tile_rows']}x{stats['tile_cols']}"] += 1
                    detail_counts[f"source_twos={stats['source_twos']}"] += 1
                    detail_counts[f"max_decoy_nonzero={stats['max_decoy_nonzero']}"] += 1
                else:
                    stats = _column_stats(grid)
                    profile_counts[str(stats["populated_columns"])] += 1
                    detail_counts[f"mixed_endpoint_columns={stats['mixed_endpoint_columns']}"] += 1
                rival_output = rival(grid)
                if seed < min(args.draws, 40):
                    actual = bridge.eval_text(rule_application(task["program_solution"], grid))
                    report["ordinary_racket_checks"] += 1
                    report["ordinary_rival_matches"] += actual == rival_output

            report["ordinary_profile_histogram"] = dict(sorted(profile_counts.items()))
            report["ordinary_detail_histogram"] = dict(sorted(detail_counts.items()))

            adversary, expected = adversaries[task_id]
            actual = bridge.eval_text(rule_application(task["program_solution"], adversary))
            rival_output = rival(adversary)
            assert actual == expected
            assert rival_output != actual
            report["adversary_self_check"] = module.self_check(adversary)
            report["adversary_racket_exact"] = True
            report["adversary_rival_disagrees"] = True
            if task_id == IDS[0]:
                override_grid = module.generate(991, 17, difficulty="medium", src_size=9)
                report["src_size_9_override_observed_twos"] = _tile_stats(override_grid)["source_twos"]
                report["canonical_dimension_histogram"] = dict(Counter(
                    f"{len(pair['input'])}x{len(pair['input'][0])}" for pair in canonical
                ))
            else:
                override_grid = module.generate(991, 17, difficulty="medium", n_columns=1)
                report["n_columns_1_override_observed"] = _column_stats(override_grid)["populated_columns"]
            cases.append({
                "task_id": task_id,
                "input": adversary,
                "racket_output": actual,
                "rival_output": rival_output,
                "self_check": report["adversary_self_check"],
            })
            reports[task_id] = report
        reports["runtime_identity"] = bridge.runtime_identity

    (args.out / "audit_report.json").write_text(json.dumps(reports, indent=2) + "\n")
    (args.out / "audit_cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    print(json.dumps({key: value for key, value in reports.items()
                      if key != "runtime_identity"}, indent=2))


if __name__ == "__main__":
    main()
