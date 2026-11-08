#!/usr/bin/env python3
"""Independent audit probe for 0bd65c18b34c tie-break coverage.

The target generator is imported only to draw its published distribution and
query its public self_check/rule_mirror hooks. Geometry analysis and the rival
solver below are independent implementations.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("audit_target_0bd", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def red_squares(grid: list[list[int]]) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(h - 1)
        for c in range(w - 1)
        if all(grid[rr][cc] == 2 for rr in (r, r + 1) for cc in (c, c + 1))
    ]


def cheby_to_square(r: int, c: int, top: int, left: int) -> int:
    dr = max(0, top - r, r - (top + 1))
    dc = max(0, left - c, c - (left + 1))
    return max(dr, dc)


def target_for(r: int, c: int, square: tuple[int, int]) -> tuple[int, int]:
    top, left = square
    if top <= r <= top + 1:
        return (r, left - 1) if c < left else (r, left + 2)
    if left <= c <= left + 1:
        return (top - 1, c) if r < top else (top + 2, c)
    return r, c


def choose_square(
    grid: list[list[int]], r: int, c: int, *, rival: bool
) -> tuple[tuple[int, int], tuple[int, ...]]:
    squares = red_squares(grid)
    distances = [cheby_to_square(r, c, *square) for square in squares]
    minimum = min(distances)
    tied = tuple(i for i, distance in enumerate(distances) if distance == minimum)
    if rival:
        # Plausible shortcut: nearest, then topmost, then rightmost.
        index = min(tied, key=lambda i: (squares[i][0], -squares[i][1]))
    else:
        # Canonical: squares are scanned in row-major order; first minimum wins.
        index = tied[0]
    return squares[index], tied


def solve(grid: list[list[int]], *, rival: bool) -> list[list[int]]:
    out = [row[:] for row in grid]
    blues = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    for r, c in blues:
        out[r][c] = 0
    for r, c in blues:
        square, _tied = choose_square(grid, r, c, rival=rival)
        tr, tc = target_for(r, c, square)
        out[tr][tc] = 1
    return out


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def analyze_distribution(gen: Any, per_band: int) -> dict[str, Any]:
    bands: dict[str, Any] = {}
    aggregate = Counter()
    examples: list[dict[str, Any]] = []
    for band_i, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        profiles = Counter()
        for i in range(per_band):
            seed = 910_000 + band_i * 10_000 + i
            grid = gen.generate(seed, i, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                raise AssertionError(f"generated {band} sample {i} failed self_check: {errors}")
            profile = gen.observe_overrides(grid)["scene_profile"]
            profiles[profile] += 1
            squares = red_squares(grid)
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value != 1:
                        continue
                    counts["blue_dots"] += 1
                    distances = [cheby_to_square(r, c, *sq) for sq in squares]
                    minimum = min(distances)
                    tied = tuple(j for j, d in enumerate(distances) if d == minimum)
                    if len(tied) <= 1:
                        continue
                    counts["tied_dots"] += 1
                    tied_squares = [squares[j] for j in tied]
                    same_top_row = len({sq[0] for sq in tied_squares}) == 1
                    if same_top_row:
                        counts["same_row_tied_dots"] += 1
                    canonical_square = tied_squares[0]
                    rival_index = min(
                        tied,
                        key=lambda j: (squares[j][0], -squares[j][1]),
                    )
                    rival_square = squares[rival_index]
                    canonical_target = target_for(r, c, canonical_square)
                    rival_target = target_for(r, c, rival_square)
                    if canonical_target != rival_target:
                        counts["behaviorally_distinguishing_ties"] += 1
                        if len(examples) < 5:
                            examples.append({
                                "band": band,
                                "sample_index": i,
                                "seed": seed,
                                "dot": [r, c],
                                "tied_squares": [list(x) for x in tied_squares],
                                "canonical_target": list(canonical_target),
                                "rival_target": list(rival_target),
                            })
        bands[band] = {
            key: counts[key]
            for key in (
                "blue_dots",
                "tied_dots",
                "same_row_tied_dots",
                "behaviorally_distinguishing_ties",
            )
        }
        bands[band].update({
            "profiles": dict(sorted(profiles.items())),
            "samples": per_band,
        })
        aggregate.update(counts)
    return {
        "bands": bands,
        "aggregate": {
            key: aggregate[key]
            for key in (
                "blue_dots",
                "tied_dots",
                "same_row_tied_dots",
                "behaviorally_distinguishing_ties",
            )
        },
        "distinguishing_examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--racket", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=60)
    args = parser.parse_args()

    gen = load_generator(args.generator)
    grid = json.loads(args.input.read_text())
    racket_record = json.loads(args.racket.read_text())
    racket_output = racket_record["results"][0]["output"]
    mirror_output = gen.rule_mirror(grid)
    rival_output = solve(grid, rival=True)
    canonical_independent = solve(grid, rival=False)
    squares = red_squares(grid)
    blue = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    )
    _chosen, tied = choose_square(grid, *blue, rival=False)
    result = {
        "schema": "0bd65c18b34c-audit-probe-v1",
        "generator": {
            "path": str(args.generator),
            "sha256": hashlib.sha256(args.generator.read_bytes()).hexdigest(),
            "rule_hash": getattr(gen, "RULE_HASH", None),
            "version": getattr(gen, "VERSION", None),
        },
        "counterexample": {
            "input_sha256": grid_sha(grid),
            "shape": [len(grid), len(grid[0])],
            "squares_row_major": [list(x) for x in squares],
            "blue_dot": list(blue),
            "tied_square_indices": list(tied),
            "self_check_errors": gen.self_check(grid),
            "racket_generator_domain": racket_record["results"][0]["generator_domain"],
            "racket_output_sha256": grid_sha(racket_output),
            "mirror_output_sha256": grid_sha(mirror_output),
            "independent_canonical_output_sha256": grid_sha(canonical_independent),
            "rival_output_sha256": grid_sha(rival_output),
            "racket_equals_mirror": racket_output == mirror_output,
            "racket_equals_independent_canonical": racket_output == canonical_independent,
            "racket_differs_from_rival": racket_output != rival_output,
            "canonical_blue_cells": [
                [r, c]
                for r, row in enumerate(racket_output)
                for c, value in enumerate(row)
                if value == 1
            ],
            "rival_blue_cells": [
                [r, c]
                for r, row in enumerate(rival_output)
                for c, value in enumerate(row)
                if value == 1
            ],
            "rival_description": "nearest square; ties choose topmost then rightmost",
        },
        "generated_distribution": analyze_distribution(gen, args.per_band),
        "commands": {
            "probe": " ".join(__import__("sys").argv),
            "racket_apply": racket_record.get("command"),
        },
    }
    agg = result["generated_distribution"]["aggregate"]
    result["finding_reproduced"] = bool(
        result["counterexample"]["racket_differs_from_rival"]
        and agg.get("behaviorally_distinguishing_ties", 0) == 0
    )
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["finding_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
