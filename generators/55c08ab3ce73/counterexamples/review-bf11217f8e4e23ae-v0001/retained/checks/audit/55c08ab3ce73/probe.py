#!/usr/bin/env python3
"""Reproduce the column-zero teaching shortcut in 55c08ab3ce73."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "55c08ab3ce73"
BANDS = ("easy", "medium", "hard")


def intended_mirror(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(dividers) != 1:
        raise ValueError(f"expected one divider, got {dividers}")
    div = dividers[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5) and c < div:
                out[r][2 * div - c] = value
    return out


def skip_column_zero_rival(grid: list[list[int]]) -> list[list[int]]:
    """Mirror left-source cells except cells in column zero."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(dividers) != 1:
        raise ValueError(f"expected one divider, got {dividers}")
    div = dividers[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5) and 0 < c < div:
                out[r][2 * div - c] = value
    return out


def has_source_in_column_zero(grid: list[list[int]]) -> bool:
    return any(row[0] not in (0, 5) for row in grid)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    if type(args.per_band) is not int or args.per_band < 1:
        raise ValueError("--per-band must be a positive integer")

    root = find_root(__file__)
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not canonical:
        raise RuntimeError("no labeled canonical pairs")

    canonical_rows: list[dict[str, Any]] = []
    witness = None
    for index, pair in enumerate(canonical):
        inp = pair["input"]
        expected = pair["output"]
        intended = intended_mirror(inp)
        rival = skip_column_zero_rival(inp)
        row = {
            "pair_index": index,
            "source_in_column_zero": has_source_in_column_zero(inp),
            "intended_matches_label": intended == expected,
            "rival_matches_label": rival == expected,
            "self_check_errors": gen.self_check(inp),
        }
        canonical_rows.append(row)
        if row["source_in_column_zero"] and not row["rival_matches_label"] and witness is None:
            witness = {
                "pair_index": index,
                "input": inp,
                "expected": expected,
                "rival": rival,
                "self_check_errors": row["self_check_errors"],
            }
    if witness is None:
        raise RuntimeError("no canonical column-zero witness found")
    if not all(row["intended_matches_label"] for row in canonical_rows):
        raise RuntimeError("local intended mirror disagrees with canonical data")

    sampled_rows = []
    emitted = 0
    edge_hits = 0
    rival_fits = 0
    for band_index, band in enumerate(BANDS):
        band_edge = 0
        band_fit = 0
        for sample_index in range(args.per_band):
            grid = gen.generate(550000 + band_index * 10000 + sample_index, sample_index, difficulty=band)
            emitted += 1
            edge = has_source_in_column_zero(grid)
            fit = skip_column_zero_rival(grid) == intended_mirror(grid)
            edge_hits += int(edge)
            rival_fits += int(fit)
            band_edge += int(edge)
            band_fit += int(fit)
        sampled_rows.append({
            "difficulty": band,
            "samples": args.per_band,
            "column_zero_source_hits": band_edge,
            "rival_fits": band_fit,
        })

    easy_override = {"accepted": False, "error": None}
    try:
        gen.generate(7, 0, difficulty="easy", grid_h=16)
        easy_override["accepted"] = True
    except Exception as exc:  # evidence, not a library boundary
        easy_override["error"] = f"{type(exc).__name__}: {exc}"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input.json").write_text(json.dumps(witness["input"], indent=2) + "\n")
    (out_dir / "canonical_expected.json").write_text(json.dumps(witness["expected"], indent=2) + "\n")
    (out_dir / "rival_output.json").write_text(json.dumps(witness["rival"], indent=2) + "\n")

    report = {
        "schema": "arcpuzzles-audit-column-zero-shortcut-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash_declared": getattr(gen, "RULE_HASH", None),
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "sampling": {
            "seed_formula": "550000 + band_index*10000 + sample_index",
            "sample_index": "0..per_band-1",
            "bands": sampled_rows,
            "total_samples": emitted,
            "column_zero_source_hits": edge_hits,
            "rival_fits": rival_fits,
        },
        "canonical_pairs": canonical_rows,
        "counterexample": {
            "pair_index": witness["pair_index"],
            "input_path": "input.json",
            "canonical_expected_path": "canonical_expected.json",
            "rival_output_path": "rival_output.json",
            "self_check_errors": witness["self_check_errors"],
            "rival_description": "mirror every eligible left-source cell except those in column 0",
        },
        "declared_axis_probe": {
            "request": {"difficulty": "easy", "grid_h": 16},
            **easy_override,
            "note": "AXES declares grid_h valid through 16, while the easy draw interval is 5..6.",
        },
        "finding": (
            "The production sampler never emits a column-zero motif cell in this finite run, "
            "so a rival that ignores column zero fits all sampled inputs. A canonical input passes "
            "self_check and contains a column-zero source cell, where that rival diverges."
        ),
        "limits": [
            "Finite sampling does not prove column-zero support is impossible, but source enumeration uses range(1, divider).",
            "The local mirror implementation was checked against every labeled canonical pair; the separate apply receipt binds the retained input to Racket.",
        ],
    }
    (out_dir / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(out_dir / "probe.json"),
        "generator_sha256": source_sha256,
        "samples": emitted,
        "column_zero_source_hits": edge_hits,
        "rival_fits": rival_fits,
        "canonical_witness_pair": witness["pair_index"],
        "easy_grid_h_16_accepted": easy_override["accepted"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
