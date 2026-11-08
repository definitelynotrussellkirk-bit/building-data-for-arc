#!/usr/bin/env python3
"""Exhaust cyclic lesson starts and query rotations for e965836d9f92.

This finite authoring probe complements the Racket-backed shared lesson census.
It dynamically reads the generator's complete semantic-rival and witness
registries, checks that every leave-one-out demo set covers all six transform
codes and refutes every declared rival, verifies square noncanonical defaults
that avoid authority clipping collisions, and confirms every declared canonical
shortcut really fits every canonical pair.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
REPO = HERE.parents[2]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root

TASK_ID = "e965836d9f92"
ALL_CODES = set(range(1, 7))


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("e965836d9f92_rotation_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run(*, seeds_per_start: int, starts: int, semantic_grid_limit: int) -> dict[str, Any]:
    gen = _load_generator()
    generator_path = TASK_DIR / "generator.py"
    bands = (None, "easy", "medium", "hard")
    competitors = dict(gen.LESSON_COMPETITORS)
    semantic_rivals = dict(gen.SEMANTIC_RIVALS)
    rotation_rivals = semantic_rivals
    witness_rivals = dict(gen.WITNESS_RIVALS)
    period = len(getattr(gen, "SCHEDULE_CYCLE", gen.SCHEDULE_PROFILES))
    lesson_size = int(gen.EXAMPLES_NEEDED) + 1

    shortcut_failures: list[dict[str, Any]] = []
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        for pair_index, pair in enumerate(canonical):
            if rival(pair["input"]) != pair["output"]:
                shortcut_failures.append(
                    {"rival": name, "canonical_pair_index": pair_index}
                )

    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    profile_counts = {name: 0 for name in gen.SCHEDULE_PROFILES}
    self_check_failures: list[dict[str, Any]] = []
    witness_claim_failures: list[dict[str, Any]] = []
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    semantic_checked: set[tuple[tuple[int, ...], ...]] = set()
    square_failures: list[dict[str, Any]] = []
    coverage_failures: list[dict[str, Any]] = []
    ambiguities: list[dict[str, Any]] = []
    surviving_declared_rivals: list[dict[str, Any]] = []
    rotations = 0
    windows = 0

    for band_index, band in enumerate(bands):
        band_name = "default" if band is None else band
        for start in range(starts):
            for seed_offset in range(seeds_per_start):
                seed = 20261006 + 10_007 * seed_offset + 101 * start + band_index
                pairs: list[dict[str, Any]] = []
                profiles: list[str] = []
                facts_list: list[dict[str, Any]] = []
                for offset in range(lesson_size):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    errors = list(gen.self_check(grid))
                    facts = gen._facts(grid)
                    profile = gen.schedule_profile(seed, sample_index, band)
                    profile_counts[profile] += 1
                    profiles.append(profile)
                    facts_list.append(facts)
                    key = _grid_key(grid)
                    unique_inputs.add(key)
                    output = gen.rule_mirror(grid)
                    if key not in semantic_checked and len(semantic_checked) < semantic_grid_limit:
                        semantic_checked.add(key)
                        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                            if not witness(grid):
                                continue
                            witness_hits[witness_name] += 1
                            rival_names = list(witness_rivals.get(witness_name, ()))
                            unknown = [name for name in rival_names if name not in semantic_rivals]
                            refuted = [
                                name
                                for name in rival_names
                                if name in semantic_rivals
                                and semantic_rivals[name](grid) != output
                            ]
                            if not rival_names or unknown or not refuted:
                                witness_claim_failures.append(
                                    {
                                        "band": band_name,
                                        "start": start,
                                        "seed": seed,
                                        "sample_index": sample_index,
                                        "witness": witness_name,
                                        "declared_rivals": rival_names,
                                        "unknown_rivals": unknown,
                                        "refuted_rivals": refuted,
                                    }
                                )
                    if errors:
                        self_check_failures.append(
                            {
                                "band": band_name,
                                "start": start,
                                "seed": seed,
                                "sample_index": sample_index,
                                "errors": errors,
                            }
                        )
                    if profile != "canonical_anchor" and facts["bbox_h"] != facts["bbox_w"]:
                        square_failures.append(
                            {
                                "band": band_name,
                                "start": start,
                                "seed": seed,
                                "sample_index": sample_index,
                                "profile": profile,
                                "bbox": [facts["bbox_h"], facts["bbox_w"]],
                                "codes": facts["codes"],
                            }
                        )
                    pairs.append({"input": grid, "output": output})
                windows += 1

                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    covered = {
                        code
                        for index, facts in enumerate(facts_list)
                        if index != query_index
                        for code in facts["codes"]
                    }
                    if covered != ALL_CODES:
                        coverage_failures.append(
                            {
                                "band": band_name,
                                "start": start,
                                "seed": seed,
                                "query_index": query_index,
                                "profiles": profiles,
                                "codes": [facts["codes"] for facts in facts_list],
                                "covered": sorted(covered),
                            }
                        )

                    hook_reasons = list(gen.lesson_identifiable(demos, query))
                    survivors = []
                    query_changing_survivors = []
                    for name, rival in rotation_rivals.items():
                        fits_demos = all(
                            rival(pair["input"]) == pair["output"] for pair in demos
                        )
                        if not fits_demos:
                            continue
                        survivors.append(name)
                        if rival(query["input"]) != query["output"]:
                            query_changing_survivors.append(name)
                    rotations += 1
                    record = {
                        "band": band_name,
                        "start": start,
                        "seed": seed,
                        "query_index": query_index,
                        "profiles": profiles,
                        "codes": [facts["codes"] for facts in facts_list],
                    }
                    if survivors:
                        surviving_declared_rivals.append(
                            {**record, "surviving_rivals": survivors}
                        )
                    if hook_reasons or query_changing_survivors:
                        ambiguities.append(
                            {
                                **record,
                                "hook_reasons": hook_reasons,
                                "query_changing_survivors": query_changing_survivors,
                            }
                        )

    failures = {
        "canonical_shortcut_failures": shortcut_failures,
        "self_check_failures": self_check_failures,
        "witness_claim_failures": witness_claim_failures,
        "square_failures": square_failures,
        "coverage_failures": coverage_failures,
        "surviving_declared_rivals": surviving_declared_rivals,
        "ambiguities": ambiguities,
    }
    status = "pass" if not any(failures.values()) else "fail"
    return {
        "schema": "e965836d9f92-lesson-rotation-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(generator_path),
        "rule_hash": gen.RULE_HASH,
        "status": status,
        "bands": ["default", "easy", "medium", "hard"],
        "schedule_period": period,
        "starts": starts,
        "seeds_per_start": seeds_per_start,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "window_size": lesson_size,
        "windows": windows,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "canonical_pairs": len(canonical),
        "competitors": sorted(competitors),
        "rotation_rivals": sorted(rotation_rivals),
        "semantic_rivals": sorted(semantic_rivals),
        "semantic_grids_checked": len(semantic_checked),
        "semantic_grid_limit": semantic_grid_limit,
        "witness_hits": witness_hits,
        "profile_counts": profile_counts,
        "failure_counts": {name: len(items) for name, items in failures.items()},
        "failures": {name: items[:20] for name, items in failures.items()},
        "limits": [
            "Finite declared-rival probe, not a proof of universal identifiability.",
            "Uses the Python rule mirror; retain the Racket-backed battery and lesson census separately.",
            "Default generations are checked; exact-axis overrides are covered by the battery override stage.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-start", type=int, default=25)
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--semantic-grid-limit", type=int, default=600)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds_per_start < 1:
        parser.error("--seeds-per-start must be at least 1")
    if args.starts < 1:
        parser.error("--starts must be at least 1")
    if args.semantic_grid_limit < 1:
        parser.error("--semantic-grid-limit must be at least 1")
    report = run(
        seeds_per_start=args.seeds_per_start,
        starts=args.starts,
        semantic_grid_limit=args.semantic_grid_limit,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
