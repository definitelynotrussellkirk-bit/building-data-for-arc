"""Exhaust every start residue of the deterministic teaching schedule.

The production census samples many source-bound lessons.  This smaller probe is
complementary: it enumerates each residue of the generator's short cyclic
schedule, holds out every one of five labelled pairs, and scores the generator's
currently declared lesson competitors.  Labels are reconstructed independently
from returned pixels through ``review_probe.vote_profile`` rather than by calling
the production rule mirror.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from review_probe import load_generator, vote_profile


def _label(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    observed = vote_profile(grid)
    return {"input": deepcopy(grid), "output": deepcopy(observed["output"])}


def audit_windows(
    *,
    generator=None,
    seed: int = 223,
    bands: Iterable[str] = ("easy", "medium", "hard"),
    period: int = 6,
    window: int = 5,
) -> dict[str, Any]:
    """Return a JSON-safe exhaustive cyclic-start and hold-one-out report."""
    if period < 1 or window < 2:
        raise ValueError("period must be positive and window must be at least two")
    gen = generator or load_generator()
    rivals = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    if not rivals:
        raise ValueError("generator declares no LESSON_COMPETITORS")

    rows: list[dict[str, Any]] = []
    ambiguous_rotations = 0
    hook_failures = 0
    band_values = tuple(bands)
    for band in band_values:
        for start in range(period):
            pairs = [
                _label(gen.generate(seed, start + offset, difficulty=band))
                for offset in range(window)
            ]
            textures = [vote_profile(pair["input"])["texture"] for pair in pairs]
            rotations = []
            for held_out in range(window):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                query = pairs[held_out]
                survivors = []
                for name, rival in sorted(rivals.items()):
                    fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                    if fits:
                        survivors.append({
                            "name": name,
                            "query_relation": (
                                "agrees" if rival(query["input"]) == query["output"]
                                else "disagrees"
                            ),
                        })
                hook_reasons = list(gen.lesson_identifiable(demos, query) or [])
                ambiguous_rotations += int(bool(survivors))
                hook_failures += int(bool(hook_reasons))
                rotations.append({
                    "held_out": held_out,
                    "survivors": survivors,
                    "hook_reasons": hook_reasons,
                })
            rows.append({
                "band": band,
                "start": start,
                "sample_indices": list(range(start, start + window)),
                "textures": textures,
                "rotations": rotations,
            })

    return {
        "schema": "0701a2c36d45-cyclic-lesson-probe-v1",
        "task_id": getattr(gen, "TASK_ID", "0701a2c36d45"),
        "seed": seed,
        "period": period,
        "window": window,
        "rivals": sorted(rivals),
        "summary": {
            "bands": len(band_values),
            "starts": len(rows),
            "rotations": len(rows) * window,
            "ambiguous_rotations": ambiguous_rotations,
            "hook_failures": hook_failures,
        },
        "windows": rows,
        "limits": [
            "This is a finite mirror-labelled authoring probe, not a universal identifiability proof.",
            "The source-bound Racket lesson census remains the authority-labelled population check.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=223)
    parser.add_argument("--period", type=int, default=6)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    gen = load_generator()
    report = audit_windows(
        generator=gen,
        seed=args.seed,
        period=args.period,
        window=args.window,
    )
    source = Path(gen.__file__)
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(json.dumps(report["summary"], sort_keys=True))
    return int(
        report["summary"]["ambiguous_rotations"] > 0
        or report["summary"]["hook_failures"] > 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
