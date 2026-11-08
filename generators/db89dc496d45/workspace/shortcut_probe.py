#!/usr/bin/env python3
"""Source-bound shortcut and lesson-rotation probe for db89dc496d45.

The probe intentionally discovers rivals from the selected generator's public
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations.  It verifies
that every claimed canonical shortcut really fits every usable canonical pair,
then samples complete lessons across all public schedule starts and holds out
each pair in turn.  This is a finite regression probe, not a proof that no
undeclared rival exists.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "db89dc496d45"
BANDS = ("easy", "medium", "hard")


def _bootstrap() -> tuple[Any, Path, Path]:
    here = Path(__file__).resolve()
    runtime = next(
        (
            ancestor / "shared" / "runtime"
            for ancestor in here.parents
            if (ancestor / "shared" / "runtime" / "reviewer_support.py").is_file()
        ),
        None,
    )
    if runtime is None:
        runtime = next(
            (
                ancestor
                for ancestor in here.parents
                if (ancestor / "reviewer_support.py").is_file()
            ),
            None,
        )
    if runtime is None:
        raise FileNotFoundError("reviewer_support.py not found")
    sys.path.insert(0, str(runtime))
    from reviewer_support import canonical_pairs, find_root  # type: ignore

    root = find_root(__file__)
    source = root / "generators" / TASK_ID / "generator.py"
    if not source.is_file():
        source = root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    if not source.is_file():
        raise FileNotFoundError(f"selected generator not found under {root}")

    # Packet layout uses repo/src; staged task-test layout may already expose the
    # package. Adding an existing src directory is harmless in both cases.
    src = root / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))
    spec = importlib.util.spec_from_file_location(f"shortcut_probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return (module, root, source, canonical_pairs)


def _grid_key(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run_probe(*, starts: int, seed_base: int) -> dict[str, Any]:
    gen, root, source, canonical_pairs = _bootstrap()
    if starts < 1:
        raise ValueError("starts must be positive")
    examples_needed = int(gen.EXAMPLES_NEEDED)
    if examples_needed < 1:
        raise ValueError("EXAMPLES_NEEDED must be positive")

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    if not shortcuts:
        raise AssertionError("generator declares no CANONICAL_SHORTCUTS")
    if not competitors:
        raise AssertionError("generator declares no LESSON_COMPETITORS")

    canonical_results: dict[str, Any] = {}
    for name, rival in shortcuts.items():
        fits = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_results[name] = {
            "pairs": len(fits),
            "fits": sum(fits),
            "fits_every_pair": all(fits),
        }
        if not all(fits):
            raise AssertionError(f"declared shortcut {name!r} misses a canonical pair")

    generated_mismatches = {name: 0 for name in competitors}
    witness_hits = {name: 0 for name in witnesses}
    ambiguous_rotations = {name: 0 for name in competitors}
    profile_witness_hits = {
        profile: {name: 0 for name in witnesses}
        for profile in gen.SCHEDULE_PROFILES
    }
    rotations = 0
    materialized_pairs = 0
    unique_inputs: set[str] = set()
    per_band: dict[str, Any] = {}

    for band_index, band in enumerate(BANDS):
        band_pairs = 0
        band_rotations = 0
        band_starts = []
        for start in range(starts):
            seed = seed_base + 10_000 * band_index + start
            lesson = []
            profiles = []
            for offset in range(examples_needed + 1):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    raise AssertionError(
                        f"self_check failed for {band} start={start} offset={offset}: {errors}"
                    )
                expected = gen.rule_mirror(grid)
                lesson.append({"input": grid, "output": expected})
                profiles.append(gen.schedule_profile(seed, sample_index, band))
                profile = profiles[-1]
                unique_inputs.add(_grid_key(grid))
                for name, rival in competitors.items():
                    generated_mismatches[name] += rival(grid) != expected
                for name, predicate in witnesses.items():
                    fired = bool(predicate(grid))
                    witness_hits[name] += fired
                    profile_witness_hits[profile][name] += fired
                materialized_pairs += 1
                band_pairs += 1

            start_record = {"start": start, "profiles": profiles, "query_results": []}
            for query_index in range(len(lesson)):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                result = {}
                for name, rival in competitors.items():
                    distinguished = any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    )
                    result[name] = distinguished
                    if not distinguished:
                        ambiguous_rotations[name] += 1
                start_record["query_results"].append(
                    {"query_index": query_index, "distinguished": result}
                )
                rotations += 1
                band_rotations += 1
            band_starts.append(start_record)
        per_band[band] = {
            "starts": starts,
            "materialized_pairs": band_pairs,
            "rotations": band_rotations,
            "schedule": band_starts,
        }

    expected_pairs = len(BANDS) * starts * (examples_needed + 1)
    if materialized_pairs != expected_pairs:
        raise AssertionError((materialized_pairs, expected_pairs))
    if any(count == 0 for count in generated_mismatches.values()):
        raise AssertionError(
            f"some lesson competitor never disagreed: {generated_mismatches}"
        )
    if any(ambiguous_rotations.values()):
        raise AssertionError(
            f"ambiguous held-out query rotations: {ambiguous_rotations}"
        )
    missing_profile_witnesses = {
        profile: [name for name, count in counts.items() if count == 0]
        for profile, counts in profile_witness_hits.items()
        if any(count == 0 for count in counts.values())
    }
    if missing_profile_witnesses:
        raise AssertionError(
            f"dimension/profile reveals witness type: {missing_profile_witnesses}"
        )

    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    return {
        "schema": "db89dc496d45-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "generator_version": str(gen.VERSION),
        "rule_hash": str(gen.RULE_HASH),
        "limitations": (
            "Finite declared-rival probe; it does not establish universal "
            "identifiability against undeclared hypotheses."
        ),
        "sample_policy": {
            "bands": list(BANDS),
            "starts_per_band": starts,
            "start_range": [0, starts - 1],
            "seed_base": seed_base,
            "pairs_per_lesson_window": examples_needed + 1,
            "demonstrations_per_rotation": examples_needed,
            "query_policy": "hold out each materialized pair once",
        },
        "canonical_shortcuts": canonical_results,
        "generated": {
            "materialized_pairs": materialized_pairs,
            "unique_inputs": len(unique_inputs),
            "competitor_mismatch_counts": generated_mismatches,
            "witness_hit_counts": witness_hits,
            "profile_witness_hit_counts": profile_witness_hits,
            "rotations": rotations,
            "ambiguous_rotation_counts": ambiguous_rotations,
        },
        "per_band": per_band,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--seed-base", type=int, default=730_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(starts=args.starts, seed_base=args.seed_base)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
