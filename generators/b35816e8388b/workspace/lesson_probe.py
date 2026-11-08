#!/usr/bin/env python3
"""Source-bound lesson census for generator b35816e8388b.

The probe intentionally imports the selected generator file, reads its live
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations, and assembles
three-demo/one-query lessons with the same consecutive-index policy used by the
semantic contract.  It is evidence about this finite sampler, not a proof of
universal induction.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "b35816e8388b"
BANDS = ("easy", "medium", "hard")
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row["test"]
            return list(row["train"]) + (
                list(test) if isinstance(test, list) else [test]
            )
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _seed_for(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}|lesson-probe-v1|{band}|{lesson_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda kv: str(kv[0]))}


def run_probe(*, lessons_per_band: int = 120) -> dict[str, Any]:
    if type(lessons_per_band) is not int or lessons_per_band < 3:
        raise ValueError("lessons_per_band must be an integer >= 3")

    generator = _load_generator()
    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(generator, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(generator, "SEMANTIC_WITNESSES", {}))
    profiles = tuple(getattr(generator, "SCHEDULE_PROFILES", ()))
    n_demos = int(getattr(generator, "EXAMPLES_NEEDED", 3))
    if n_demos != 3:
        raise RuntimeError(
            f"this probe is specified for three-demo lessons, got {n_demos}"
        )

    canonical_pairs = _canonical_pairs()
    canonical_shortcuts: dict[str, Any] = {}
    for name, shortcut in sorted(shortcuts.items()):
        matches = [
            shortcut(pair["input"]) == pair["output"]
            for pair in canonical_pairs
        ]
        canonical_shortcuts[name] = {
            "pairs": len(matches),
            "matches": sum(matches),
            "fits_all_pairs": bool(matches) and all(matches),
        }

    report: dict[str, Any] = {
        "schema": "b35816e8388b-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO_ROOT)),
        "generator_sha256": _source_sha256(GENERATOR_PATH),
        "generator_version": getattr(generator, "VERSION", None),
        "rule_hash": getattr(generator, "RULE_HASH", None),
        "domain_limits": {
            "axes": getattr(generator, "AXES", {}),
            "difficulties": list(BANDS),
            "examples_per_lesson": n_demos,
            "queries_per_lesson": 1,
        },
        "sampler": {
            "lessons_per_band": lessons_per_band,
            "seed_rule": "uint64(sha256(task|lesson-probe-v1|band|lesson_index)[:8])",
            "sample_index_rule": "lesson_index * 4 + offset, offsets 0..3",
            "lesson_policy": "three consecutive demonstrations plus the next consecutive query, sharing one lesson seed",
            "cyclic_start_policy": "4 is coprime to the declared 3-profile schedule, so lesson_index 0..N-1 visits every start residue",
            "label_oracle": "generator.rule_mirror; separate battery evidence checks Racket parity",
        },
        "declarations": {
            "schedule_profiles": [str(value) for value in profiles],
            "canonical_shortcuts": sorted(shortcuts),
            "lesson_competitors": sorted(competitors),
            "semantic_witnesses": sorted(witnesses),
        },
        "canonical_shortcuts": canonical_shortcuts,
        "bands": {},
        "limitations": [
            "Finite deterministic census; it does not prove universal rule induction.",
            "Rival outputs use the generator's independent Python mirror here; the full battery separately binds that mirror to the selected Racket authority.",
        ],
    }

    for band in BANDS:
        unique_inputs: set[str] = set()
        unique_lessons: set[str] = set()
        start_counts: Counter = Counter()
        profile_counts: Counter = Counter()
        axis_support = {name: Counter() for name in getattr(generator, "AXES", {})}
        shortcut_disagreements: Counter = Counter()
        witness_hits: Counter = Counter()
        competitor_stats = {
            name: {
                "survives_demos": 0,
                "survives_all": 0,
                "query_disagreements_after_surviving_demos": 0,
            }
            for name in competitors
        }
        identifiable = 0
        unidentifiable_examples: list[dict[str, Any]] = []
        invalid_examples: list[dict[str, Any]] = []
        all_inputs = 0

        for lesson_index in range(lessons_per_band):
            seed = _seed_for(band, lesson_index)
            start = lesson_index * (n_demos + 1)
            start_counts[start % len(profiles) if profiles else 0] += 1

            pairs = []
            lesson_input_keys = []
            for offset in range(n_demos + 1):
                sample_index = start + offset
                grid = generator.generate(
                    seed, sample_index, difficulty=band
                )
                errors = generator.self_check(grid)
                if errors:
                    invalid_examples.append(
                        {
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": list(errors),
                        }
                    )
                    continue
                output = generator.rule_mirror(grid)
                pair = {"input": grid, "output": output}
                pairs.append(pair)

                key = _grid_key(grid)
                unique_inputs.add(key)
                lesson_input_keys.append(key)
                all_inputs += 1

                if hasattr(generator, "schedule_profile"):
                    profile_counts[
                        generator.schedule_profile(seed, sample_index, band)
                    ] += 1
                observed = generator.observe_overrides(grid)
                for axis, value in observed.items():
                    if axis in axis_support:
                        axis_support[axis][value] += 1
                for name, shortcut in shortcuts.items():
                    if shortcut(grid) != output:
                        shortcut_disagreements[name] += 1
                for name, witness in witnesses.items():
                    if witness(grid):
                        witness_hits[name] += 1

            if len(pairs) != n_demos + 1:
                continue
            demos, query = pairs[:n_demos], pairs[n_demos]
            unique_lessons.add("|".join(lesson_input_keys))
            reasons = generator.lesson_identifiable(demos, query)
            if reasons:
                if len(unidentifiable_examples) < 5:
                    unidentifiable_examples.append(
                        {
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start,
                            "reasons": list(reasons),
                        }
                    )
            else:
                identifiable += 1

            for name, competitor in competitors.items():
                survives_demos = all(
                    competitor(pair["input"]) == pair["output"]
                    for pair in demos
                )
                survives_query = (
                    competitor(query["input"]) == query["output"]
                )
                if survives_demos:
                    competitor_stats[name]["survives_demos"] += 1
                    if survives_query:
                        competitor_stats[name]["survives_all"] += 1
                    else:
                        competitor_stats[name][
                            "query_disagreements_after_surviving_demos"
                        ] += 1

        band_row = {
            "lessons": lessons_per_band,
            "examples": all_inputs,
            "identifiable": identifiable,
            "unidentifiable": lessons_per_band - identifiable,
            "unidentifiable_examples": unidentifiable_examples,
            "invalid_examples": invalid_examples,
            "unique_inputs": len(unique_inputs),
            "duplicate_inputs": all_inputs - len(unique_inputs),
            "unique_lessons": len(unique_lessons),
            "cyclic_start_counts": _counter_dict(start_counts),
            "profile_counts": _counter_dict(profile_counts),
            "axis_support": {
                name: _counter_dict(values)
                for name, values in axis_support.items()
            },
            "shortcut_disagreements": {
                name: int(shortcut_disagreements[name])
                for name in sorted(shortcuts)
            },
            "witness_hits": {
                name: int(witness_hits[name])
                for name in sorted(witnesses)
            },
            "competitors": competitor_stats,
        }
        report["bands"][band] = band_row

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=120)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = run_probe(lessons_per_band=args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    summary = {
        band: {
            "identifiable": f"{row['identifiable']}/{row['lessons']}",
            "unique_inputs": f"{row['unique_inputs']}/{row['examples']}",
            "shortcut_disagreements": row["shortcut_disagreements"],
        }
        for band, row in report["bands"].items()
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    problems = []
    for name, row in report["canonical_shortcuts"].items():
        if not row["fits_all_pairs"]:
            problems.append(f"declared canonical shortcut {name} does not fit all canonical pairs")
    for band, row in report["bands"].items():
        if row["invalid_examples"]:
            problems.append(f"{band}: invalid generated examples")
        if row["identifiable"] != row["lessons"]:
            problems.append(f"{band}: unidentifiable lessons")
        for name in report["declarations"]["canonical_shortcuts"]:
            if row["shortcut_disagreements"].get(name, 0) == 0:
                problems.append(f"{band}: no generated disagreement for shortcut {name}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
