#!/usr/bin/env python3
"""Replay df74e338b4f5's declared rivals and witnesses against bound sources.

This task-local probe deliberately discovers ``CANONICAL_SHORTCUTS``,
``LESSON_COMPETITORS`` and ``SEMANTIC_WITNESSES`` from the selected generator
instead of carrying a stale hard-coded rival list.  It is useful for quick
reviewer triage; the shared lesson census remains the authoritative curriculum
check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "df74e338b4f5"


def _grid_digest(grid: Any) -> str:
    body = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(body).hexdigest()


def run_probe(*, per_band: int = 20, seed_base: int = 73000) -> dict[str, Any]:
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    if type(seed_base) is not int:
        raise TypeError("seed_base must be an integer")

    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    shortcut_rows = []
    all_shortcuts_fit = True
    for name, rival in getattr(gen, "CANONICAL_SHORTCUTS", {}).items():
        mismatches = []
        for pair in pairs:
            try:
                predicted = rival(pair["input"])
            except Exception as exc:  # retain exact failure for reviewers
                mismatches.append(
                    {
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            if predicted != pair["output"]:
                mismatches.append(
                    {
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "predicted_sha256": _grid_digest(predicted),
                        "expected_sha256": _grid_digest(pair["output"]),
                    }
                )
        fits = not mismatches
        all_shortcuts_fit &= fits
        shortcut_rows.append(
            {
                "name": name,
                "fits_all_canonical_pairs": fits,
                "canonical_pairs": len(pairs),
                "mismatches": mismatches,
            }
        )

    bands = ("easy", "medium", "hard")
    competitors = getattr(gen, "LESSON_COMPETITORS", {})
    witnesses = getattr(gen, "SEMANTIC_WITNESSES", {})
    witness_counts = {
        name: {band: 0 for band in bands}
        for name in witnesses
    }
    generation_errors = []
    rival_survivals = []
    unique_inputs = set()
    lawful = 0

    for band_index, band in enumerate(bands):
        for index in range(per_band):
            seed = seed_base + band_index * 100000 + index
            sample_index = band_index * per_band + index
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    generation_errors.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": list(errors),
                        }
                    )
                    continue
                intended = gen.rule_mirror(grid)
            except Exception as exc:
                generation_errors.append(
                    {
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue

            lawful += 1
            unique_inputs.add(_grid_digest(grid))
            for name, witness in witnesses.items():
                try:
                    if witness(grid):
                        witness_counts[name][band] += 1
                except Exception as exc:
                    generation_errors.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "witness": name,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
            for name, rival in competitors.items():
                try:
                    survived = rival(grid) == intended
                except Exception as exc:
                    generation_errors.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "rival": name,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                if survived:
                    rival_survivals.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "rival": name,
                            "input_sha256": _grid_digest(grid),
                        }
                    )

    status = (
        "pass"
        if all_shortcuts_fit and not generation_errors and not rival_survivals
        else "fail"
    )
    return {
        "schema": "df74e338b4f5-semantic-probe/1",
        "task_id": TASK_ID,
        "status": status,
        "generator_path": str(source.relative_to(root)),
        "generator_source_sha256": source_sha256,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "settings": {"per_band": per_band, "seed_base": seed_base, "bands": list(bands)},
        "canonical_shortcuts": {
            "all_fit": all_shortcuts_fit,
            "pair_count": len(pairs),
            "rows": shortcut_rows,
        },
        "generated": {
            "requested": per_band * len(bands),
            "lawful": lawful,
            "unique_inputs": len(unique_inputs),
            "generation_errors": generation_errors,
            "rival_names": sorted(competitors),
            "rival_survivals": rival_survivals,
            "witness_counts": witness_counts,
        },
        "scope_note": (
            "Finite declared-rival replay only; this does not prove universal "
            "identifiability or replace the shared source-bound lesson census."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=20)
    parser.add_argument("--seed-base", type=int, default=73000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(per_band=args.per_band, seed_base=args.seed_base)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
