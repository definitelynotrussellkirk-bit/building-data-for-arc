#!/usr/bin/env python3
"""Source-bound contract probe for task 9bde2c3e0346.

Checks exact-axis support, canonical-profile coverage, finite semantic rivals,
all four held-out rotations of short generated lessons, and actual Racket parity.
The independent oracle below does not call generator transformation helpers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "9bde2c3e0346"
BANDS = ("easy", "medium", "hard")


def load_subject(path: Path):
    spec = importlib.util.spec_from_file_location("bbox_frame_probe_subject", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def components(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    groups = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        stack, cells = [start], {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    stack.append(point)
                    cells.add(point)
        groups.append((color, cells))
    return groups


def oracle(grid):
    output = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        frame = (
            {(top, c) for c in range(left, right + 1)}
            | {(bottom, c) for c in range(left, right + 1)}
            | {(r, left) for r in range(top, bottom + 1)}
            | {(r, right) for r in range(top, bottom + 1)}
        )
        for r, c in frame:
            output[r][c] = color
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--defaults-per-band", type=int, default=100)
    args = parser.parse_args()

    root = find_root(__file__)
    source = Path(__file__).resolve().parents[1] / "generator.py"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    gen = load_subject(source)
    canonical = canonical_pairs(TASK_ID, root=root)
    failures = []

    exact_cases = 0
    for band in BANDS:
        for h in range(8, 13):
            for w in range(8, 13):
                for count in (2, 3):
                    requested = {"grid_h": h, "grid_w": w, "n_objects": count}
                    grid = gen.generate(8675309, exact_cases, difficulty=band, **requested)
                    exact_cases += 1
                    if gen.observe_overrides(grid) != requested:
                        failures.append({"kind": "override", "band": band, "requested": requested})
                    if gen.self_check(grid, difficulty=band):
                        failures.append({"kind": "self_check", "band": band, "requested": requested})

    defaults = {}
    generated_for_racket = []
    rotations_checked = 0
    for band_index, band in enumerate(BANDS):
        grids = [gen.generate(12001 + band_index, i, difficulty=band)
                 for i in range(args.defaults_per_band)]
        profiles = {(len(g), len(g[0]), len({v for row in g for v in row if v})) for g in grids}
        defaults[band] = {
            "draws": len(grids),
            "unique_inputs": len({json.dumps(g, separators=(",", ":")) for g in grids}),
            "profiles": sorted(map(list, profiles)),
            "canonical_profile_hits": sum(
                (len(g), len(g[0]), len({v for row in g for v in row if v}))
                in {(8, 8, 2), (9, 9, 2)} for g in grids
            ),
        }
        if defaults[band]["canonical_profile_hits"] == 0:
            failures.append({"kind": "profile_floor", "band": band})
        for index, grid in enumerate(grids):
            expected = oracle(grid)
            if gen.rule_mirror(grid) != expected:
                failures.append({"kind": "mirror", "band": band, "index": index})
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    failures.append({"kind": "witness", "name": name, "band": band, "index": index})
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if rival(grid) == expected:
                    failures.append({"kind": "rival_survived", "name": name, "band": band, "index": index})
        generated_for_racket.extend(grids[:10])

        # Exhaust every query position in 25 consecutive four-pair lessons.
        for start in range(25):
            lesson_grids = [gen.generate(44000 + band_index, start * 4 + offset, difficulty=band)
                            for offset in range(4)]
            pairs = [{"input": grid, "output": oracle(grid)} for grid in lesson_grids]
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = {"input": pairs[query_index]["input"]}
                rotations_checked += 1
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    failures.append({"kind": "rotation", "band": band,
                                     "start": start, "query_index": query_index,
                                     "reasons": reasons})

    canonical_shortcut_fit = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fit = sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        canonical_shortcut_fit[name] = {"fit": fit, "total": len(canonical)}
        if fit != len(canonical):
            failures.append({"kind": "shortcut_not_canonical_fitting", "name": name})

    racket_inputs = [pair["input"] for pair in canonical] + generated_for_racket
    receipt = Catalog(root).apply(TASK_ID, racket_inputs, reference="canonical", timeout=180)
    racket_outputs = [row["output"] for row in receipt["results"]]
    parity_mismatches = [i for i, (grid, output) in enumerate(zip(racket_inputs, racket_outputs))
                         if oracle(grid) != output]
    if parity_mismatches:
        failures.append({"kind": "racket_parity", "indices": parity_mismatches})

    report = {
        "schema": "bbox_frame_contract_probe/1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "declared_rule_hash": gen.RULE_HASH,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "exact_override_cases": exact_cases,
        "default_population": defaults,
        "canonical_shortcut_fit": canonical_shortcut_fit,
        "lesson_rotations_checked": rotations_checked,
        "racket_parity_cases": len(racket_inputs),
        "racket_parity_mismatches": parity_mismatches,
        "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
