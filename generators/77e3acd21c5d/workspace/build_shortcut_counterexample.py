#!/usr/bin/env python3
"""Materialize the retained canonical-shortcut counterexample.

Run through the packet wrapper so the selected protected Racket authority is
available:

    python3 review.py run python3 \
      generators/77e3acd21c5d/workspace/build_shortcut_counterexample.py \
      --out generators/77e3acd21c5d/counterexamples/single_nearest_anchor.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_probe import canonical_pairs, geometry_output, load_generator, observed, racket_outputs


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    generator = load_generator()
    seed = 71
    sample_index = 8
    difficulty = "hard"
    overrides = {"profile": "compact4", "marker_mode": "both_tie"}
    grid = generator.generate(seed, sample_index, difficulty=difficulty, **overrides)

    intended = geometry_output(grid)
    rival = geometry_output(grid, mirror_ties=False)
    racket = racket_outputs([grid])[0]
    if intended != racket:
        raise AssertionError("independent geometry oracle disagrees with selected Racket authority")
    if intended == rival:
        raise AssertionError("chosen input does not distinguish tie mirroring")

    canonical = canonical_pairs()
    rival_fit = [
        geometry_output(pair["input"], mirror_ties=False) == pair["output"]
        for pair in canonical
    ]
    if not all(rival_fit):
        raise AssertionError("single-nearest-anchor rival does not fit every canonical pair")

    root = Path(__file__).resolve().parents[3]
    generator_path = root / "generators/77e3acd21c5d/generator.py"
    canonical_path = root / "shared/data/canonical/puzzles.jsonl"
    difference = [
        {"row": r, "column": c, "intended": intended[r][c], "rival": rival[r][c]}
        for r in range(len(intended))
        for c in range(len(intended[0]))
        if intended[r][c] != rival[r][c]
    ]
    return {
        "schema": "arcpuzzles-shortcut-counterexample-v1",
        "task_id": "77e3acd21c5d",
        "generator_version": generator.VERSION,
        "generator_sha256": sha256(generator_path),
        "canonical_data_sha256": sha256(canonical_path),
        "rule_hash": generator.RULE_HASH,
        "shortcut": {
            "name": "single_nearest_anchor",
            "description": (
                "Project a marker only to one nearest vertical and horizontal edge; "
                "on an exact tie choose the top/left anchor instead of mirroring to both sides."
            ),
            "canonical_pairs_fit": sum(rival_fit),
            "canonical_pairs_total": len(rival_fit),
        },
        "generation": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": overrides,
            "call": (
                "generate(71, 8, difficulty='hard', "
                "profile='compact4', marker_mode='both_tie')"
            ),
        },
        "observed": observed(grid),
        "input": grid,
        "selected_racket_output": racket,
        "independent_oracle_output": intended,
        "shortcut_output": rival,
        "differing_cells": difference,
        "checks": {
            "selected_racket_equals_independent_oracle": racket == intended,
            "selected_racket_differs_from_shortcut": racket != rival,
            "input_passes_strict_validator": bool(generator.strict_canonical_like(grid)),
            "generator_emits_case_by_exact_override": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": payload["generator_sha256"],
        "canonical_fit": (
            f"{payload['shortcut']['canonical_pairs_fit']}/"
            f"{payload['shortcut']['canonical_pairs_total']}"
        ),
        "differing_cells": len(payload["differing_cells"]),
        "racket_parity": payload["checks"]["selected_racket_equals_independent_oracle"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
