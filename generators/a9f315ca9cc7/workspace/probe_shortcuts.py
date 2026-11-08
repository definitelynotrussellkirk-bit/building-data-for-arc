"""Reusable probe for declared canonical-fitting shortcuts.

The probe reads ``CANONICAL_SHORTCUTS`` from the selected generator, checks
those exact declarations against every labelled canonical pair, then searches
actual generalized generator draws for a lawful disagreement with the intended
Python mirror.  Racket remains the authority; pass the retained witness input
to ``python3 -m arcpuzzles apply`` for the source-bound execution receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a9f315ca9cc7"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _validate_int(name: str, value: int, *, minimum: int | None = None) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")


def _generated_candidates(seed: int, max_samples: int):
    difficulties = ("easy", "medium", "hard", None)
    for sample_index in range(max_samples):
        difficulty = difficulties[sample_index % len(difficulties)]
        overrides = {"scene_profile": "generalized", "fg_color": 4}
        grid = GEN.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **overrides,
        )
        yield sample_index, difficulty, overrides, grid


def build_report(*, seed: int = 19, max_samples: int = 100) -> dict[str, Any]:
    """Check actual shortcut declarations and retain first generated witnesses."""
    _validate_int("seed", seed)
    _validate_int("max_samples", max_samples, minimum=1)

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    declared = dict(GEN.CANONICAL_SHORTCUTS)
    shortcuts: dict[str, Any] = {}

    for name, shortcut in declared.items():
        canonical_checks = [
            {
                "pair_index": index,
                "matches": shortcut(pair["input"]) == pair["output"],
            }
            for index, pair in enumerate(pairs)
        ]
        witness = None
        for sample_index, difficulty, overrides, grid in _generated_candidates(
            seed, max_samples
        ):
            intended = GEN.rule_mirror(grid)
            rival = shortcut(grid)
            if intended == rival:
                continue
            witness = {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": difficulty,
                "overrides": overrides,
                "observed_overrides": GEN.observe_overrides(grid),
                "self_check_errors": GEN.self_check(
                    grid, difficulty=difficulty, meta={"overrides": overrides}
                ),
                "input": grid,
                "intended_python_output": intended,
                "shortcut_output": rival,
            }
            break

        shortcuts[name] = {
            "canonical_checks": canonical_checks,
            "fits_all_canonical_pairs": all(
                check["matches"] for check in canonical_checks
            ),
            "first_generated_disagreement": witness,
        }

    return {
        "schema": "a9f315ca9cc7-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(Path(GENERATOR_PATH).relative_to(ROOT)),
        "generator_sha256": GENERATOR_SHA256,
        "rule_hash": GEN.RULE_HASH,
        "canonical_pair_count": len(pairs),
        "declared_shortcuts": list(declared),
        "search": {
            "seed": seed,
            "sample_indices": [0, max_samples - 1],
            "forced_scene_profile": "generalized",
            "forced_fg_color": 4,
        },
        "shortcuts": shortcuts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--max-samples", type=int, default=100)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--input-out", type=Path)
    args = parser.parse_args()

    report = build_report(seed=args.seed, max_samples=args.max_samples)
    if args.input_out is not None:
        witnesses = [
            item["first_generated_disagreement"]
            for item in report["shortcuts"].values()
            if item["first_generated_disagreement"] is not None
        ]
        if not witnesses:
            raise RuntimeError("no generated disagreement found")
        args.input_out.parent.mkdir(parents=True, exist_ok=True)
        args.input_out.write_text(
            json.dumps(witnesses[0]["input"], indent=2) + "\n",
            encoding="utf-8",
        )

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(payload, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
