#!/usr/bin/env python3
"""Source-bound qualification probe for generator 6a289c5b0897.

This is deliberately task-local and dependency-light.  It verifies the exact
canonical shortcut claim, exhausts requested cyclic lesson starts against the
production schedule, and saves one generated UDLR-vs-LDRU counterexample with
source hashes.  It never supplies labels to either solve episode.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "6a289c5b0897"
HERE = Path(__file__).resolve()
TASK_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator():
    path = TASK_ROOT / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "qualification_subject_6a289c5b0897", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frozen(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def run_probe(*, seeds_per_band: int = 12, cyclic_starts: int = 6) -> dict[str, Any]:
    if seeds_per_band < 1 or cyclic_starts < 1:
        raise ValueError("seeds_per_band and cyclic_starts must be positive")
    gen = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=find_root(HERE))

    shortcut_rows: dict[str, dict[str, Any]] = {}
    fitting: list[str] = []
    for name, shortcut in sorted(gen.CANONICAL_SHORTCUTS.items()):
        agreements = [shortcut(pair["input"]) == pair["output"] for pair in pairs]
        shortcut_rows[name] = {
            "agreements": sum(agreements),
            "pairs": len(agreements),
            "fits_all": bool(agreements) and all(agreements),
        }
        if shortcut_rows[name]["fits_all"]:
            fitting.append(name)

    bands: dict[str, Any] = {}
    failed_cycles = 0
    total_rotations = 0
    failed_rotations = 0
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    counterexample: dict[str, Any] | None = None
    total_cycles = 0

    for band_index, band in enumerate(("easy", "medium", "hard")):
        band_cycles: list[dict[str, Any]] = []
        for seed_offset in range(seeds_per_band):
            seed = 910_000 + band_index * 10_000 + seed_offset
            for start in range(cyclic_starts):
                total_cycles += 1
                demos: list[dict[str, Any]] = []
                profiles: list[str] = []
                rejected: list[str] = []
                refuted = {name: False for name in gen.LESSON_COMPETITORS}
                accepted_indices: list[int] = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    errors = gen.self_check(grid)
                    if errors:
                        rejected.extend(errors)
                    truth = gen.rule_mirror(grid)
                    demos.append({"input": grid, "output": truth})
                    profiles.append(gen.schedule_profile(seed, sample_index, band))
                    accepted_indices.append(sample_index)
                    unique_inputs.add(_frozen(grid))
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        if rival(grid) != truth:
                            refuted[name] = True
                            if counterexample is None:
                                counterexample = {
                                    "band": band,
                                    "seed": seed,
                                    "sample_index": sample_index,
                                    "profile": profiles[-1],
                                    "rival": name,
                                    "input": grid,
                                    "intended_output": truth,
                                    "rival_output": rival(grid),
                                    "self_check": errors,
                                }
                query_index = start + gen.EXAMPLES_NEEDED
                query = gen.generate(seed, query_index, difficulty=band)
                query_errors = gen.self_check(query)
                rejected.extend(query_errors)
                query_truth = gen.rule_mirror(query)
                unique_inputs.add(_frozen(query))
                reasons = gen.lesson_identifiable(demos, {"input": query})
                profile_complete = set(profiles) == set(gen.SCHEDULE_PROFILES)
                rivals_complete = all(refuted.values())

                all_pairs = demos + [{"input": query, "output": query_truth}]
                rotations: list[dict[str, Any]] = []
                for query_offset, held_out in enumerate(all_pairs):
                    total_rotations += 1
                    rotated_demos = [
                        pair for offset, pair in enumerate(all_pairs)
                        if offset != query_offset
                    ]
                    rotation_reasons = gen.lesson_identifiable(
                        rotated_demos, {"input": held_out["input"]}
                    )
                    rotation_passed = not rotation_reasons
                    if not rotation_passed:
                        failed_rotations += 1
                    rotations.append(
                        {
                            "query_offset": query_offset,
                            "query_sample_index": start + query_offset,
                            "demo_sample_indices": [
                                start + offset
                                for offset in range(len(all_pairs))
                                if offset != query_offset
                            ],
                            "lesson_reasons": rotation_reasons,
                            "passed": rotation_passed,
                        }
                    )

                passed = (
                    not rejected
                    and not reasons
                    and profile_complete
                    and rivals_complete
                    and all(row["passed"] for row in rotations)
                )
                if not passed:
                    failed_cycles += 1
                band_cycles.append(
                    {
                        "seed": seed,
                        "start": start,
                        "accepted_indices": accepted_indices,
                        "query_index": query_index,
                        "profiles": profiles,
                        "profile_complete": profile_complete,
                        "rivals_refuted": refuted,
                        "self_check_errors": rejected,
                        "lesson_reasons": reasons,
                        "rotations": rotations,
                        "passed": passed,
                    }
                )
        bands[band] = {
            "cycles": len(band_cycles),
            "passed_cycles": sum(row["passed"] for row in band_cycles),
            "failed_cycles": sum(not row["passed"] for row in band_cycles),
            "details": band_cycles,
        }

    if counterexample is None:
        raise AssertionError("no declared rival counterexample was generated")

    generator_path = TASK_ROOT / "generator.py"
    return {
        "schema": "arc-generator-qualification-probe-v1",
        "task_id": TASK_ID,
        "generator": {
            "path": str(generator_path.relative_to(REPO_ROOT)),
            "sha256": _sha256(generator_path),
            "version": gen.VERSION,
            "rule_hash": gen.RULE_HASH,
            "examples_needed": gen.EXAMPLES_NEEDED,
            "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        },
        "canonical": {
            "pairs": len(pairs),
            "shortcuts": shortcut_rows,
            "shortcuts_fitting_all": fitting,
        },
        "parameters": {
            "seeds_per_band": seeds_per_band,
            "cyclic_starts": cyclic_starts,
        },
        "bands": bands,
        "counterexample": counterexample,
        "summary": {
            "cycles": total_cycles,
            "failed_cycles": failed_cycles,
            "rotations": total_rotations,
            "failed_rotations": failed_rotations,
            "unique_inputs": len(unique_inputs),
            "all_cycles_passed": failed_cycles == 0 and failed_rotations == 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-per-band", type=int, default=12)
    parser.add_argument("--cyclic-starts", type=int, default=6)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(
        seeds_per_band=args.seeds_per_band,
        cyclic_starts=args.cyclic_starts,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["summary"]["all_cycles_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
