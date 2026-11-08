#!/usr/bin/env python3
"""Exhaustive finite probe of the declared two-profile lesson schedule.

This is intentionally task-local and declaration-driven: future edits to the
rival/witness mappings are included automatically instead of being hidden behind
copied name lists.  It verifies canonical-shortcut fit, every cyclic schedule
start in every difficulty band, exact grammar, witness presence, and rival
refutation in demonstrations.  Labels use the pure reference mirror; run the
shared lesson-census for live-Racket evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2f7883fbd26f"


def _load_generator():
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError as exc:
        # The task-test snapshot exposes per_puzzle; the source checkout keeps
        # generators under generators/TASK_ID. Support both layouts so future
        # reviewers can run this tool directly from an extracted packet.
        if exc.name != f"puzzle_generators.per_puzzle.{TASK_ID}":
            raise
        from importlib import util as importlib_util

        root = find_root(__file__)
        source = root / "generators" / TASK_ID / "generator.py"
        spec = importlib_util.spec_from_file_location(
            f"task_generator_{TASK_ID}", source
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load generator source: {source}")
        module = importlib_util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-per-start", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds_per_start < 1:
        parser.error("--seeds-per-start must be positive")

    failures: list[dict] = []
    shortcut_fits: dict[str, bool] = {}
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        fits = all(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs)
        shortcut_fits[name] = fits
        if not fits:
            failures.append({"kind": "canonical_shortcut_mismatch", "name": name})

    rival_refuted = {name: 0 for name in GEN.LESSON_COMPETITORS}
    witness_present = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    rotation_rival_refuted = {name: 0 for name in GEN.LESSON_COMPETITORS}
    windows_total = 0
    rotations_total = 0
    examples_total = 0
    source_path = Path(GEN.__file__).resolve()

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(GEN.SCHEDULE_PERIOD):
            for seed_offset in range(args.seeds_per_start):
                seed = 80_000 + band_index * 10_000 + start * 1_000 + seed_offset
                labelled: list[dict] = []
                for offset in range(GEN.EXAMPLES_NEEDED + 1):
                    sample_index = start + offset
                    try:
                        grid = GEN.generate(seed, sample_index, difficulty=band)
                    except Exception as exc:
                        failures.append({
                            "kind": "generation_error",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                        labelled = []
                        break
                    grammar_errors = GEN.self_check(grid)
                    strict_errors = GEN.strict_canonical_like(grid)
                    if grammar_errors or strict_errors:
                        failures.append({
                            "kind": "grammar_error",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "sample_index": sample_index,
                            "self_check": grammar_errors,
                            "strict": strict_errors,
                        })
                    labelled.append({"input": grid, "output": GEN._reference_output(grid)})
                    examples_total += 1
                if not labelled:
                    continue
                demos, query = labelled[:-1], labelled[-1]
                windows_total += 1
                reasons = GEN.lesson_identifiable(demos, query)
                if reasons:
                    failures.append({
                        "kind": "unidentifiable",
                        "band": band,
                        "start": start,
                        "seed": seed,
                        "reasons": reasons,
                    })
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    if any(rival(copy.deepcopy(demo["input"])) != demo["output"] for demo in demos):
                        rival_refuted[name] += 1
                    else:
                        failures.append({
                            "kind": "rival_survived_demos",
                            "name": name,
                            "band": band,
                            "start": start,
                            "seed": seed,
                        })
                for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    if any(predicate(demo["input"]) for demo in demos):
                        witness_present[name] += 1
                    else:
                        failures.append({
                            "kind": "witness_missing_from_demos",
                            "name": name,
                            "band": band,
                            "start": start,
                            "seed": seed,
                        })

                for query_index in range(len(labelled)):
                    rotations_total += 1
                    rotated_query = labelled[query_index]
                    rotated_demos = [
                        pair for index, pair in enumerate(labelled)
                        if index != query_index
                    ]
                    rotation_reasons = GEN.lesson_identifiable(
                        rotated_demos, rotated_query
                    )
                    if rotation_reasons:
                        failures.append({
                            "kind": "rotation_unidentifiable",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "query_index": query_index,
                            "reasons": rotation_reasons,
                        })
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        if any(
                            rival(copy.deepcopy(demo["input"])) != demo["output"]
                            for demo in rotated_demos
                        ):
                            rotation_rival_refuted[name] += 1
                        else:
                            failures.append({
                                "kind": "rival_survived_rotated_demos",
                                "name": name,
                                "band": band,
                                "start": start,
                                "seed": seed,
                                "query_index": query_index,
                            })

    report = {
        "schema": "2f7883fbd26f-lesson-window-probe-v1",
        "status": "pass" if not failures else "fail",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "seeds_per_start": args.seeds_per_start,
        "schedule_profiles": list(GEN.SCHEDULE_PROFILES),
        "schedule_roles": list(GEN.SCHEDULE_ROLES),
        "schedule_period": GEN.SCHEDULE_PERIOD,
        "examples_needed": GEN.EXAMPLES_NEEDED,
        "windows_total": windows_total,
        "rotations_total": rotations_total,
        "examples_total": examples_total,
        "canonical_pairs": len(pairs),
        "canonical_shortcut_fits": shortcut_fits,
        "rival_refuted_in_demos": rival_refuted,
        "rotation_rival_refuted_in_demos": rotation_rival_refuted,
        "witness_present_in_demos": witness_present,
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "windows_total": windows_total,
        "failures": len(failures),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
