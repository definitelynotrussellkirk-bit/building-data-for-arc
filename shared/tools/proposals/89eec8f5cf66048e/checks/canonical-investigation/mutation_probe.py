#!/usr/bin/env python3
"""Bounded source-linked diagnostic; does not edit the selected task."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import load_selected_generator

TASK = "fc814cec3976"
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def key(grid):
    return tuple(tuple(row) for row in grid)


def scan(grid, mode="canonical"):
    candidates = []
    for top in range(len(grid) - 2):
        for left in range(len(grid[0]) - 2):
            cells = tuple((r, c) for r in range(top, top + 3) for c in range(left, left + 3))
            reds = tuple((r, c) for r, c in cells if grid[r][c] == 2)
            if reds and grid[top + 1][left + 1] == 5 and all(grid[r][c] in (2, 5) for r, c in cells):
                candidates.append((top, left, cells, reds))
    if mode == "reading_order":
        candidates.sort(key=lambda x: (x[0], x[1]))
    elif mode == "reverse_tie":
        candidates.sort(key=lambda x: (-len(x[3]), -x[0], -x[1]))
    else:
        candidates.sort(key=lambda x: (-len(x[3]), x[0], x[1]))
    covered = set()
    selected = []
    for cand in candidates:
        used = cand[2] if mode == "cell_overlap" else cand[3]
        if mode == "independent_windows" or not covered.intersection(used):
            selected.append(cand)
            covered.update(used)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            hit = next((x for x in selected if (r, c) in x[2]), None)
            if hit and value == 5:
                out[r][c] = 4 if (r, c) == (hit[0] + 1, hit[1] + 1) else 7
    return candidates, selected, out


def summary(grid):
    candidates, selected, output = scan(grid)
    reds = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    covered = {p for x in selected for p in x[3]}
    counts = Counter(v for row in grid for v in row)
    return {
        "shape": [len(grid), len(grid[0])],
        "palette": sorted(counts),
        "counts": dict(counts),
        "candidates": [[x[0], x[1], len(x[3])] for x in candidates],
        "selected": [[x[0], x[1], len(x[3])] for x in selected],
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "red_coverage_complete": covered == reds,
        "yellow_count": sum(v == 4 for row in output for v in row),
    }


def mutations(gen, source, digest):
    baseline_snapshot = OUT / "baseline-generator.py"
    if not baseline_snapshot.exists():
        baseline_snapshot.write_bytes(source.read_bytes())
    rows = []
    counts = Counter()
    for (profile_index, transform), template in gen._TEMPLATES.items():
        base = [list(row) for row in template["grid"]]
        _, base_selected, canonical = scan(base)
        assert canonical == gen.rule_mirror(base)
        mask = {(r, c): canonical[r][c] for r in range(19) for c in range(19) if canonical[r][c] != base[r][c]}
        for r, c in sorted(template["protected"]):
            if base[r][c] not in (0, 5):
                continue
            counts["flips_tested"] += 1
            changed = deepcopy(base)
            changed[r][c] = 5 - changed[r][c]
            candidates, selected, actual = scan(changed)
            reds = set(gen._red_key(changed))
            if len(selected) != 4 or {p for x in selected for p in x[3]} != reds:
                counts["violates_four_winner_or_red_coverage"] += 1
                continue
            if not 4 <= len(candidates) <= 7:
                counts["candidate_count_outside_original_range"] += 1
                continue
            if [(x[0], x[1]) for x in selected] == [(x[0], x[1]) for x in base_selected]:
                counts["unchanged_selected_windows"] += 1
                continue
            lookup = deepcopy(changed)
            for (mr, mc), value in mask.items():
                lookup[mr][mc] = value
            assert key(lookup) != key(actual)
            assert actual == gen.rule_mirror(changed)
            assert gen._red_key(changed) == gen._red_key(base)
            info = summary(changed)
            # All candidate-changing options are retained, with density scope explicit.
            density_in_range = 177 <= info["counts"][5] <= 223 and info["counts"][5] >= info["counts"][0]
            counts["useful_mutations"] += 1
            counts["density_preserved" if density_in_range else "density_needs_safe_cell_compensation"] += 1
            row = {
                "profile_index": profile_index, "profile": template["profile"], "transform": transform,
                "mutation": [r, c, base[r][c], changed[r][c]],
                "baseline": summary(base), "mutated": info,
                "density_in_original_range": density_in_range,
                "same_red_key": True,
                "input": changed, "original_input": base,
                "independent_output": actual, "lookup_output": lookup,
                "lookup_mismatch_cells": [[rr, cc, actual[rr][cc], lookup[rr][cc]] for rr in range(19) for cc in range(19) if actual[rr][cc] != lookup[rr][cc]],
                "old_self_check_errors": gen.self_check(changed),
                "rival_disagreements": {mode: scan(changed, mode)[2] != actual for mode in ("reading_order", "reverse_tie", "cell_overlap", "independent_windows")},
            }
            rows.append(row)
    result = {
        "schema": "fc814cec3976-canonical-investigation-v1",
        "generator_source": str(source), "generator_sha256": digest,
        "rule_hash": gen.RULE_HASH, "counts": dict(counts), "mutations": rows,
        "scope": "Exhaustive one-cell 0/5 flips in the 32 protected template regions; selected windows must change, stay four, cover every red, and retain 4..7 candidates. Density exception marked individually; generator encoding intentionally not yet changed.",
    }
    dump("mutation-census.json", result)
    print(json.dumps({"counts": dict(counts), "first_mutations": [{k: x[k] for k in ("profile", "transform", "mutation", "density_in_original_range", "rival_disagreements")} for x in rows[:12]]}), flush=True)
    return result


def verify_with_racket(gen, result):
    from arcpuzzles import Catalog
    chosen = []
    seen = set()
    for row in result["mutations"]:
        ident = (row["profile_index"], row["transform"])
        if ident not in seen:
            seen.add(ident)
            chosen.append(row)
    inputs = []
    for row in chosen:
        inputs.extend([row["original_input"], row["input"]])
    if not inputs:
        dump("racket-verification.json", {"status": "not_run", "reason": "No useful single-cell mutations found"})
        return
    receipt = Catalog(ROOT).apply(TASK, inputs, check_generator_domain=True, timeout=180)
    dump("racket-raw-receipt.json", receipt)
    verified = []
    for i, row in enumerate(chosen):
        base_result, mutant_result = receipt["results"][2*i:2*i+2]
        oracle = mutant_result["output"]
        verified.append({
            "profile": row["profile"], "transform": row["transform"], "mutation": row["mutation"],
            "canonical_matches_independent": oracle == row["independent_output"],
            "canonical_differs_lookup": oracle != row["lookup_output"],
            "same_red_key": gen._red_key(row["original_input"]) == gen._red_key(row["input"]),
            "recolor_masks_differ": {(r,c): base_result["output"][r][c] for r in range(19) for c in range(19) if base_result["output"][r][c] != row["original_input"][r][c]} != {(r,c): oracle[r][c] for r in range(19) for c in range(19) if oracle[r][c] != row["input"][r][c]},
            "racket_result_index": 2*i+1,
            "density_in_original_range": row["density_in_original_range"],
        })
    dump("racket-verification.json", {"generator_sha256": result["generator_sha256"], "executed_rule_hash": receipt["executed_rule_hash"], "rule_text_sha256": receipt["rule_text_sha256"], "pairs": verified})
    print(json.dumps({"racket_pair_count": len(verified), "all_independent_match": all(x["canonical_matches_independent"] for x in verified), "all_lookup_refuted": all(x["canonical_differs_lookup"] for x in verified), "executed_rule_hash": receipt["executed_rule_hash"]}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    result = mutations(gen, source, digest)
    if args.racket:
        verify_with_racket(gen, result)


if __name__ == "__main__":
    main()
