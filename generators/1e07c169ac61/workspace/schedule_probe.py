#!/usr/bin/env python3
"""Exhaust the short teaching schedule and every one-pair query rotation.

This is a fast, source-bound complement to the Racket-backed lesson census.  It
uses the independent geometry oracle in ``reference_probe.py`` and the selected
generator's own declared competitor set.  Passing is evidence only for the
requested cyclic starts, seeds, bands, and declared competitors.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
from typing import Sequence

from reference_probe import ambiguity_records, load_generator, rotation_output

DEFAULT_BANDS = ("easy", "medium", "hard")
DEFAULT_SEEDS = (61_001, 61_002)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(*, bands: Sequence[str], seeds: Sequence[int], cycles: int) -> dict[str, object]:
    if cycles < 1:
        raise ValueError("cycles must be positive")
    gen = load_generator()
    source = Path(inspect.getsourcefile(gen) or "")
    period = len(gen.SCHEDULE_PROFILES)
    pairs_per_lesson = gen.EXAMPLES_NEEDED + 1
    checked_lessons = 0
    checked_rotations = 0
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    profile_windows: set[tuple[str, ...]] = set()
    ambiguities: list[dict[str, object]] = []
    witness_minima = {name: pairs_per_lesson for name in gen.SEMANTIC_WITNESSES}

    for band in bands:
        for seed in seeds:
            for start in range(period * cycles):
                grids = [
                    gen.generate(seed, start + offset, difficulty=band)
                    for offset in range(pairs_per_lesson)
                ]
                pairs = [
                    {"input": grid, "output": rotation_output(grid)} for grid in grids
                ]
                profiles = tuple(
                    gen.schedule_profile(seed, start + offset, band)
                    for offset in range(pairs_per_lesson)
                )
                profile_windows.add(profiles)
                for grid in grids:
                    unique_inputs.add(tuple(tuple(row) for row in grid))
                for name, predicate in gen.SEMANTIC_WITNESSES.items():
                    count = sum(bool(predicate(grid)) for grid in grids)
                    witness_minima[name] = min(witness_minima[name], count)

                found = ambiguity_records(pairs, gen.LESSON_COMPETITORS)
                checked_lessons += 1
                checked_rotations += pairs_per_lesson
                for row in found:
                    ambiguities.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "profiles": list(profiles),
                            **row,
                        }
                    )

    return {
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(source),
        "schedule_period": period,
        "cycles": cycles,
        "bands": list(bands),
        "seeds": list(seeds),
        "declared_competitors": sorted(gen.LESSON_COMPETITORS),
        "checked_lessons": checked_lessons,
        "checked_rotations": checked_rotations,
        "unique_inputs": len(unique_inputs),
        "unique_profile_windows": len(profile_windows),
        "minimum_witnesses_per_five_pair_window": witness_minima,
        "ambiguity_count": len(ambiguities),
        "ambiguities": ambiguities,
        "status": "pass" if not ambiguities else "ambiguous",
        "scope_note": (
            "Exhaustive only over the requested cyclic starts/seeds/bands and "
            "the selected generator's declared competitors; labels use the "
            "independent Python geometry oracle, while the retained production "
            "lesson census supplies Racket-backed evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--bands", nargs="+", choices=DEFAULT_BANDS, default=list(DEFAULT_BANDS))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = probe(bands=tuple(args.bands), seeds=tuple(args.seeds), cycles=args.cycles)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
