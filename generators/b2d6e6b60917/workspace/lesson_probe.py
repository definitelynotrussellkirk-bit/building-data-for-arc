#!/usr/bin/env python3
"""Source-bound lesson probe for b2d6e6b60917.

The central battery samples a small number of lessons.  This retained probe
uses the selected generator's actual schedule, witnesses, canonical shortcuts,
and lesson competitors to inspect larger disjoint lesson sets.  Labels come
from the task-local Python rule reconstruction, whose canonical parity is
checked first; the central Racket stages remain the execution authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "b2d6e6b60917"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
REPO_ROOT = HERE.parents[2]
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")
LESSON_STRIDE = 11


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_PATH.open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}|lesson-probe-v1|{band}|{lesson_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _signature(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _canonical_report(generator) -> dict[str, Any]:
    pairs = _canonical_pairs()
    mirror_failures = []
    for index, pair in enumerate(pairs):
        if generator.rule_mirror(pair["input"]) != pair["output"]:
            mirror_failures.append(index)
    shortcuts_fitting = []
    shortcut_failures: dict[str, list[int]] = {}
    for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
        failures = [
            index
            for index, pair in enumerate(pairs)
            if shortcut(pair["input"]) != pair["output"]
        ]
        if failures:
            shortcut_failures[name] = failures
        else:
            shortcuts_fitting.append(name)
    return {
        "pairs": len(pairs),
        "mirror_failures": mirror_failures,
        "shortcuts_fitting_all_pairs": sorted(shortcuts_fitting),
        "shortcut_pair_failures": shortcut_failures,
    }


def _band_report(generator, band: str, lessons_per_band: int) -> dict[str, Any]:
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    profiles: Counter[str] = Counter()
    witness_hits = Counter({name: 0 for name in generator.SEMANTIC_WITNESSES})
    rival_disagreements = Counter({name: 0 for name in generator.LESSON_COMPETITORS})
    surviving_competitors: Counter[str] = Counter()
    lesson_failures: list[dict[str, Any]] = []
    invalid_inputs: list[dict[str, Any]] = []
    pair_count = 0

    for lesson_index in range(lessons_per_band):
        seed = _seed(band, lesson_index)
        start = lesson_index * LESSON_STRIDE
        pairs = []
        for offset in range(generator.EXAMPLES_NEEDED + 1):
            sample_index = start + offset
            grid = generator.generate(seed, sample_index, difficulty=band)
            pair_count += 1
            unique_inputs.add(_signature(grid))
            profile = generator.schedule_profile(seed, sample_index, difficulty=band)
            profiles[str(profile)] += 1
            validation = generator.self_check(grid, difficulty=band)
            if validation:
                invalid_inputs.append(
                    {
                        "lesson": lesson_index,
                        "offset": offset,
                        "seed": seed,
                        "sample_index": sample_index,
                        "reasons": validation,
                    }
                )
            output = generator.rule_mirror(grid)
            for name, witness in generator.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_hits[name] += 1
            for name, rival in generator.LESSON_COMPETITORS.items():
                if rival(grid) != output:
                    rival_disagreements[name] += 1
            pairs.append({"input": grid, "output": output})

        demos = pairs[:-1]
        query = pairs[-1]
        reasons = generator.lesson_identifiable(demos, query)
        if reasons:
            lesson_failures.append(
                {
                    "lesson": lesson_index,
                    "seed": seed,
                    "start_sample_index": start,
                    "reasons": reasons,
                }
            )
        for name, rival in generator.LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                surviving_competitors[name] += 1

    return {
        "lessons": lessons_per_band,
        "pairs": pair_count,
        "lesson_stride": LESSON_STRIDE,
        "examples_needed": generator.EXAMPLES_NEEDED,
        "unique_inputs": len(unique_inputs),
        "duplicate_inputs": pair_count - len(unique_inputs),
        "profiles": dict(sorted(profiles.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
        "rival_disagreements": dict(sorted(rival_disagreements.items())),
        "surviving_competitors": {
            name: count for name, count in sorted(surviving_competitors.items()) if count
        },
        "lesson_failures": lesson_failures,
        "invalid_inputs": invalid_inputs,
    }


def build_report(*, lessons_per_band: int = 100) -> dict[str, Any]:
    if type(lessons_per_band) is not int or lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be a positive integer")
    generator = _load_generator()
    generator_bytes = GENERATOR_PATH.read_bytes()
    return {
        "schema_version": 1,
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO_ROOT)),
        "generator_sha256": hashlib.sha256(generator_bytes).hexdigest(),
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "oracle": (
            "generator.rule_mirror; canonical parity checked in this report; "
            "central rule_smoke/semantic_gate remain Racket authority"
        ),
        "sampler": {
            "seed": "sha256(task|lesson-probe-v1|band|lesson_index)[:8]",
            "sample_index_start": "lesson_index * 11",
            "lesson_layout": (
                f"{generator.EXAMPLES_NEEDED} consecutive demos plus one query"
            ),
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "overlap": "none within a band; four-pair blocks are separated by stride 11",
        },
        "domain_limits": [
            "21x21 zero-background inputs only",
            "one unique-largest monochrome 5..8-cell source with bbox dimensions 2..4",
            "two or three monochrome marker fragments",
            "scheduled source bboxes are 3x3, 2x4, and 4x2",
            "this is sampled evidence over declared rivals, not universal induction",
        ],
        "declarations": {
            "profiles": list(generator.SCHEDULE_PROFILES),
            "witnesses": sorted(generator.SEMANTIC_WITNESSES),
            "witness_rivals": {
                name: list(rivals)
                for name, rivals in sorted(generator.WITNESS_RIVALS.items())
            },
            "competitors": sorted(generator.LESSON_COMPETITORS),
            "canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS),
        },
        "canonical": _canonical_report(generator),
        "bands": {
            band: _band_report(generator, band, lessons_per_band) for band in BANDS
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(lessons_per_band=args.lessons_per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    failed = bool(report["canonical"]["mirror_failures"])
    failed = failed or any(
        band["lesson_failures"]
        or band["invalid_inputs"]
        or band["surviving_competitors"]
        for band in report["bands"].values()
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
