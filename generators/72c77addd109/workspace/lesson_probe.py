#!/usr/bin/env python3
"""Task-local semantic/axis audit for generator 72c77addd109.

This complements the shared lesson census in two ways it intentionally does not
cover: every cyclic choice of query within a four-pair lesson, and the full
cross-product of the generator's small exact semantic-axis domain at dimension
endpoints.  It uses the generator's declared contract rather than a copied list
of rival names.  Racket authority parity remains the job of rule_smoke and the
source-bound shared lesson census.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
from typing import Any

from reference_probe import canonical_pairs, load_generator, observed

BANDS = ("easy", "medium", "hard")
PERIOD = 6


def _frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run_probe(samples_per_band: int = 100) -> dict[str, Any]:
    gen = load_generator()
    canonical = canonical_pairs()

    shortcut_fit: dict[str, dict[str, Any]] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = [rival(pair["input"]) == pair["output"] for pair in canonical]
        shortcut_fit[name] = {
            "pairs": len(fits),
            "fits": sum(fits),
            "fits_all": all(fits),
        }

    cyclic_failures: list[dict[str, Any]] = []
    cyclic_checks = 0
    for band in BANDS:
        for start in range(PERIOD):
            seed = 88000 + 100 * BANDS.index(band) + start
            pairs = []
            for offset in range(4):
                grid = gen.generate(seed, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                for name, rival in gen.LESSON_COMPETITORS.items():
                    cyclic_checks += 1
                    if all(rival(pair["input"]) == pair["output"] for pair in demos):
                        cyclic_failures.append({
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "rival": name,
                        })

    axis_domains = {
        "grid_h": (11, 16),
        "grid_w": (12, 18),
        "solid_style": tuple(gen.SOLID_STYLES),
        "solid_rank_order": tuple(gen.RANK_ORDERS),
        "frame_rank_order": tuple(gen.RANK_ORDERS),
        "solid_color_order": tuple(gen.COLOR_ORDERS),
        "palette_kind": tuple(gen.PALETTE_KINDS),
    }
    axis_names = tuple(axis_domains)
    axis_failures: list[dict[str, Any]] = []
    axis_draws = 0
    axis_unique: set[tuple[tuple[int, ...], ...]] = set()
    for band_index, band in enumerate(BANDS):
        for case_index, values in enumerate(product(*(axis_domains[name] for name in axis_names))):
            requested = dict(zip(axis_names, values))
            axis_draws += 1
            try:
                grid = gen.generate(910000 + band_index, case_index, difficulty=band, **requested)
                axis_unique.add(_frozen(grid))
                errors = gen.self_check(grid)
                seen = observed(grid)
                declared_seen = gen.observe_overrides(grid)
                output = gen.rule_mirror(grid)
                if errors or seen != requested or declared_seen != requested or output == grid:
                    axis_failures.append({
                        "band": band,
                        "case_index": case_index,
                        "requested": requested,
                        "self_check": errors,
                        "independent_observed": seen,
                        "declared_observed": declared_seen,
                        "identity_output": output == grid,
                    })
            except Exception as exc:  # retained with the exact requested tuple
                axis_failures.append({
                    "band": band,
                    "case_index": case_index,
                    "requested": requested,
                    "exception": f"{type(exc).__name__}: {exc}",
                })

    default: dict[str, Any] = {}
    for band_index, band in enumerate(BANDS):
        witness_counts = Counter({name: 0 for name in gen.SEMANTIC_WITNESSES})
        strict = 0
        valid = 0
        unique: set[tuple[tuple[int, ...], ...]] = set()
        for index in range(samples_per_band):
            grid = gen.generate(920000 + band_index * 10000 + index, index, difficulty=band)
            valid += not gen.self_check(grid)
            strict += not gen.strict_canonical_like(grid)
            unique.add(_frozen(grid))
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(witness(grid))
        default[band] = {
            "draws": samples_per_band,
            "valid": valid,
            "strict": strict,
            "unique_inputs": len(unique),
            "witness_counts": dict(witness_counts),
        }

    return {
        "schema": "72c77addd109-task-probe-v1",
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "canonical_shortcut_fit": shortcut_fit,
        "cyclic_query_rotations": {
            "period": PERIOD,
            "bands": list(BANDS),
            "starts_per_band": PERIOD,
            "query_positions_per_start": 4,
            "rivals": list(gen.LESSON_COMPETITORS),
            "checks": cyclic_checks,
            "failures": cyclic_failures,
        },
        "exact_axis_cross_product": {
            "domains": {key: list(value) for key, value in axis_domains.items()},
            "bands": list(BANDS),
            "draws": axis_draws,
            "unique_inputs": len(axis_unique),
            "failures": axis_failures,
        },
        "default_distribution": default,
        "status": (
            "pass"
            if all(item["fits_all"] for item in shortcut_fit.values())
            and not cyclic_failures
            and not axis_failures
            and all(
                row["valid"] == row["draws"]
                and row["strict"] > 0
                and all(count > 0 for count in row["witness_counts"].values())
                for row in default.values()
            )
            else "fail"
        ),
        "limits": [
            "Finite declared-rival checks do not prove universal identifiability.",
            "Python rule_mirror is corroborated separately by Racket rule_smoke and lesson-census evidence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(args.samples_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "out": str(args.out),
        "axis_draws": report["exact_axis_cross_product"]["draws"],
        "cyclic_checks": report["cyclic_query_rotations"]["checks"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
