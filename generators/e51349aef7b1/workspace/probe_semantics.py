#!/usr/bin/env python3
"""Exhaust the declared four-profile lesson schedule against independent rivals.

This tool is deliberately independent of generator.rule_mirror and the generator's
rival callables.  It re-parses the panels, implements the six-transform authority,
and checks every query rotation for every start residue and difficulty band.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("e51349aef7b1_probe", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def transform(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [list(reversed(row)) for row in grid]
    if code == 6:
        return [row[:] for row in reversed(grid)]
    raise ValueError(code)


def crop(grid: list[list[int]]) -> list[list[int]]:
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not points:
        raise ValueError("empty panel")
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def binary(grid: list[list[int]]) -> list[list[int]]:
    return [[int(value != 0) for value in row] for row in grid]


def split(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    h = len(grid)
    dividers = [c for c in range(len(grid[0])) if all(grid[r][c] == 5 for r in range(h))]
    if len(dividers) != 2:
        raise ValueError(f"expected two dividers, got {dividers}")
    d1, d2 = dividers
    return (
        [row[:d1] for row in grid],
        [row[d1 + 1 : d2] for row in grid],
        [row[d2 + 1 :] for row in grid],
    )


def foreground(panel: list[list[int]]) -> int:
    colors = {value for row in panel for value in row if value not in (0, 5)}
    if len(colors) != 1:
        raise ValueError(f"bad foreground set {sorted(colors)}")
    return next(iter(colors))


def match_codes(a: list[list[int]], b: list[list[int]], *, cropped: bool) -> list[int]:
    aa = binary(crop(a) if cropped else a)
    bb = binary(crop(b) if cropped else b)
    return [code for code in range(1, 7) if transform(aa, code) == bb]


def output_for(grid: list[list[int]], code: int) -> list[list[int]]:
    _, b, c = split(grid)
    color = foreground(b)
    return [[color if value else 0 for value in row] for row in transform(crop(c), code)]


def intended(grid: list[list[int]]) -> list[list[int]]:
    a, b, _ = split(grid)
    matches = match_codes(a, b, cropped=True)
    return output_for(grid, matches[0] if matches else 1)


def uncropped_rival(grid: list[list[int]]) -> list[list[int]]:
    a, b, _ = split(grid)
    matches = match_codes(a, b, cropped=False)
    return output_for(grid, matches[0] if matches else 1)


def last_match_rival(grid: list[list[int]]) -> list[list[int]]:
    a, b, _ = split(grid)
    matches = match_codes(a, b, cropped=True)
    return output_for(grid, matches[-1] if matches else 1)


RIVALS = {
    "uncropped_full_panels": uncropped_rival,
    "last_matching_transform": last_match_rival,
}


def run(seed: int) -> dict[str, Any]:
    bands = ("easy", "medium", "hard")
    period = GEN.LESSON_SCHEDULE_PERIOD
    failures: list[dict[str, Any]] = []
    pair_records: list[dict[str, Any]] = []
    rotation_records: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()

    for band in bands:
        for start in range(period):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(seed, sample_index, difficulty=band)
                a, b, _ = split(grid)
                truth = intended(grid)
                digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
                unique_inputs.add(digest)
                record = {
                    "band": band,
                    "start": start,
                    "offset": offset,
                    "sample_index": sample_index,
                    "profile": sample_index % period,
                    "input_sha256": digest,
                    "cropped_matches": match_codes(a, b, cropped=True),
                    "full_panel_matches": match_codes(a, b, cropped=False),
                    "rival_disagrees": {
                        name: rival(grid) != truth for name, rival in RIVALS.items()
                    },
                }
                pair_records.append(record)
                pairs.append({"input": grid, "output": truth, "record": record})

            for query_index in range(len(pairs)):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                rival_fits = {
                    name: all(rival(pair["input"]) == pair["output"] for pair in demos)
                    for name, rival in RIVALS.items()
                }
                query_disagrees = {
                    name: rival(query["input"]) != query["output"]
                    for name, rival in RIVALS.items()
                }
                rotation = {
                    "band": band,
                    "start": start,
                    "query_index": query_index,
                    "query_profile": query["record"]["profile"],
                    "rival_fits_all_demos": rival_fits,
                    "rival_disagrees_on_query": query_disagrees,
                }
                rotation_records.append(rotation)
                for name, fits in rival_fits.items():
                    if fits:
                        failures.append({**rotation, "failure": f"{name} fits every demonstration"})

    expected_rotations = len(bands) * period * (GEN.EXAMPLES_NEEDED + 1)
    return {
        "schema": "e51349aef7b1-semantic-probe-v1",
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "seed": seed,
        "bands": list(bands),
        "period": period,
        "pairs_checked": len(pair_records),
        "rotations_checked": len(rotation_records),
        "expected_rotations": expected_rotations,
        "unique_inputs": len(unique_inputs),
        "ambiguous_pair_count": sum(len(item["cropped_matches"]) > 1 for item in pair_records),
        "uncropped_match_count": sum(bool(item["full_panel_matches"]) for item in pair_records),
        "failures": failures,
        "passed": not failures and len(rotation_records) == expected_rotations,
        "pairs": pair_records,
        "rotations": rotation_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(json.dumps({k: report[k] for k in (
        "passed", "pairs_checked", "rotations_checked", "unique_inputs",
        "ambiguous_pair_count", "uncropped_match_count", "failures"
    )}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
