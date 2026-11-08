#!/usr/bin/env python3
"""Reusable source-bound lesson and rival probe for task 46580cfcca75.

The repository battery is authoritative for Racket execution.  This probe adds a
cheap, independent Python transcription for exhaustive query rotations across
many consecutive four-pair windows.  It discovers the generator's live rival
and witness declarations instead of copying a stale name list.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

import reference_oracle

TASK_ID = "46580cfcca75"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _source_hash() -> str:
    return hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()


def _failure(kind: str, **details: Any) -> dict[str, Any]:
    return {"kind": kind, **details}


def run_probe(*, per_band: int = 100, seed_base: int = 91000) -> dict[str, Any]:
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    if type(seed_base) is not int:
        raise ValueError("seed_base must be an integer")

    gen = _load_generator()
    rivals = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    failures: list[dict[str, Any]] = []

    root = find_root(__file__)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_mismatches = []
    canonical_rival_fits = {}
    for pair_index, pair in enumerate(canonical):
        actual = reference_oracle.oracle(pair["input"])
        if actual != pair["output"]:
            canonical_mismatches.append(pair_index)
    for name, rival in sorted(rivals.items()):
        canonical_rival_fits[name] = sum(
            rival(pair["input"]) == pair["output"] for pair in canonical
        )

    bands = (None, "easy", "medium", "hard")
    band_reports = {}
    unique_inputs: set[str] = set()
    witness_counts = {name: 0 for name in witnesses}
    rival_disagreements = {name: 0 for name in rivals}
    windows = 0
    rotations = 0

    for band_index, band in enumerate(bands):
        band_name = "none" if band is None else band
        band_failures_before = len(failures)
        band_unique: set[str] = set()
        band_witnesses = {name: 0 for name in witnesses}
        band_rivals = {name: 0 for name in rivals}

        for lesson_index in range(per_band):
            # Advancing the start by one enumerates every residue of the
            # generator's four-slot semantic schedule.  A distinct seed per
            # window keeps the geometry/palette probe broad.
            seed = seed_base + band_index * 100_000 + lesson_index
            start = lesson_index
            pairs = []
            for offset in range(4):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                truth = reference_oracle.oracle(grid)
                pair = {"input": grid, "output": truth}
                pairs.append(pair)

                key = _grid_key(grid)
                unique_inputs.add(key)
                band_unique.add(key)

                check_errors = gen.self_check(grid, difficulty=band)
                strict_errors = gen.strict_canonical_like(grid)
                if check_errors or strict_errors:
                    failures.append(
                        _failure(
                            "validation",
                            band=band_name,
                            lesson_index=lesson_index,
                            seed=seed,
                            sample_index=sample_index,
                            self_check=check_errors,
                            strict=strict_errors,
                            input=grid,
                        )
                    )
                mirror = getattr(gen, "rule_mirror", reference_oracle.oracle)(grid)
                if mirror != truth:
                    failures.append(
                        _failure(
                            "python_oracle_mismatch",
                            band=band_name,
                            lesson_index=lesson_index,
                            seed=seed,
                            sample_index=sample_index,
                            input=grid,
                            independent_output=truth,
                            generator_mirror_output=mirror,
                        )
                    )

                for name, witness in witnesses.items():
                    if witness(grid):
                        witness_counts[name] += 1
                        band_witnesses[name] += 1
                for name, rival in rivals.items():
                    if rival(grid) != truth:
                        rival_disagreements[name] += 1
                        band_rivals[name] += 1

            windows += 1
            for query_index in range(4):
                rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                reported = list(gen.lesson_identifiable(demos, query))
                manual = []
                for name, rival in sorted(rivals.items()):
                    if (
                        all(rival(demo["input"]) == demo["output"] for demo in demos)
                        and rival(query["input"]) != query["output"]
                    ):
                        manual.append(name)
                if reported or manual:
                    failures.append(
                        _failure(
                            "unidentifiable_rotation",
                            band=band_name,
                            lesson_index=lesson_index,
                            seed=seed,
                            start_sample_index=start,
                            query_index=query_index,
                            reported_reasons=reported,
                            fitting_rivals=manual,
                            pairs=pairs,
                        )
                    )

        band_reports[band_name] = {
            "windows": per_band,
            "rotations": per_band * 4,
            "unique_inputs": len(band_unique),
            "witness_counts": band_witnesses,
            "rival_disagreements": band_rivals,
            "failures": len(failures) - band_failures_before,
        }

    return {
        "schema": "46580cfcca75-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _source_hash(),
        "version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "examples_needed": getattr(gen, "EXAMPLES_NEEDED", None),
        "schedule_profiles": list(getattr(gen, "SCHEDULE_PROFILES", ())),
        "assembly": {
            "pairs_per_window": 4,
            "demonstrations": 3,
            "query_rotations": "all four",
            "start_policy": "every consecutive start index in 0..per_band-1",
            "seed_policy": "one deterministic distinct seed per window and band",
        },
        "per_band_requested": per_band,
        "seed_base": seed_base,
        "declared_rivals": sorted(rivals),
        "declared_witnesses": sorted(witnesses),
        "canonical": {
            "pairs": len(canonical),
            "oracle_mismatches": len(canonical_mismatches),
            "mismatch_pair_indices": canonical_mismatches,
            "rival_fit_counts": canonical_rival_fits,
        },
        "windows": windows,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "witness_counts": witness_counts,
        "rival_disagreements": rival_disagreements,
        "bands": band_reports,
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "limitations": [
            "The independent Python oracle is a transcription; the repository Racket gate remains authoritative.",
            "Only declared rivals are tested; this is not a proof of unique induction against every program.",
            "Finite seeds and starts do not exhaust all geometries or palettes.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=91000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(per_band=args.per_band, seed_base=args.seed_base)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    print(
        f"verdict={report['verdict']} windows={report['windows']} "
        f"rotations={report['rotations']} unique_inputs={report['unique_inputs']} "
        f"failures={len(report['failures'])}",
    )
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
