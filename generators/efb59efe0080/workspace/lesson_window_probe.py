#!/usr/bin/env python3
"""Cyclic lesson-window ambiguity probe for efb59efe0080.

For each four-example window, rotate every example into the query position and
ask whether a plausible wrong rule fits the other three demonstrations but
changes that query.  This complements the shared lesson census, which does not
rotate every materialized pair into the query position.

The probe uses the independent geometry functions in ``reference_probe.py``;
the selected Racket rule remains training-label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import (
    absolute_position_xor,
    filled_bbox_xor,
    load_generator,
    normalized_union,
    normalized_xor,
    red_mask_only,
    uncropped_xor,
)

RIVALS = {
    "normalized_union": normalized_union,
    "uncropped_xor": uncropped_xor,
    "filled_bbox_xor": filled_bbox_xor,
    "red_mask_only": red_mask_only,
    "absolute_position_xor": absolute_position_xor,
}
BANDS = ("easy", "medium", "hard")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(source: Path, *, seeds: int, windows: int, max_examples: int = 12) -> dict:
    gen = load_generator(source)
    counts: Counter[str] = Counter()
    by_band: dict[str, Counter[str]] = {band: Counter() for band in BANDS}
    examples: list[dict] = []

    for band in BANDS:
        for seed in range(seeds):
            grids = [
                gen.generate(seed, index, difficulty=band)
                for index in range(windows + 3)
            ]
            answers = [normalized_xor(grid) for grid in grids]
            for start in range(windows):
                window_grids = grids[start : start + 4]
                window_answers = answers[start : start + 4]
                for query_offset in range(4):
                    demo_offsets = [i for i in range(4) if i != query_offset]
                    counts["rotations"] += 1
                    by_band[band]["rotations"] += 1
                    for name, rival in RIVALS.items():
                        fits_demos = all(
                            rival(window_grids[i]) == window_answers[i]
                            for i in demo_offsets
                        )
                        changes_query = (
                            rival(window_grids[query_offset])
                            != window_answers[query_offset]
                        )
                        if fits_demos:
                            counts[f"{name}:survived_demos"] += 1
                            by_band[band][f"{name}:survived_demos"] += 1
                        if fits_demos and changes_query:
                            counts["ambiguities"] += 1
                            counts[f"{name}:ambiguous"] += 1
                            by_band[band]["ambiguities"] += 1
                            by_band[band][f"{name}:ambiguous"] += 1
                            if len(examples) < max_examples:
                                examples.append(
                                    {
                                        "band": band,
                                        "seed": seed,
                                        "start": start,
                                        "query_offset": query_offset,
                                        "query_sample_index": start + query_offset,
                                        "demo_sample_indices": [start + i for i in demo_offsets],
                                        "rival": name,
                                        "inputs": window_grids,
                                        "intended_outputs": window_answers,
                                        "rival_outputs": [rival(grid) for grid in window_grids],
                                    }
                                )

    return {
        "schema": "efb59efe0080-cyclic-lesson-probe-v1",
        "generator": str(source),
        "generator_sha256": sha(source),
        "seeds": seeds,
        "windows_per_seed_band": windows,
        "bands": list(BANDS),
        "lesson_shape": "3 demonstrations + 1 query; all four cyclic query rotations",
        "authority_note": (
            "Independent Python geometry is diagnostic evidence; selected Racket "
            "authority is verified separately by the review battery and lesson census."
        ),
        "rivals": sorted(RIVALS),
        "counts": dict(sorted(counts.items())),
        "by_band": {band: dict(sorted(count.items())) for band, count in by_band.items()},
        "ambiguity_examples": examples,
        "status": "ambiguous" if counts["ambiguities"] else "no_declared_ambiguity",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--windows", type=int, default=10)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.windows < 1:
        parser.error("--seeds and --windows must be positive")
    report = probe(args.generator.resolve(), seeds=args.seeds, windows=args.windows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": report["generator_sha256"],
        "rotations": report["counts"].get("rotations", 0),
        "ambiguities": report["counts"].get("ambiguities", 0),
        "out": str(args.out),
    }, indent=2))
    return 1 if report["status"] == "ambiguous" else 0


if __name__ == "__main__":
    raise SystemExit(main())
