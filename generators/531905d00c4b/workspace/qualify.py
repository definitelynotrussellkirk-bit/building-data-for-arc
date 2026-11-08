"""Source-bound qualification driver for ARC task 531905d00c4b.

The driver uses the selected generator's actual sampler and declared semantic
contracts.  It checks every declared canonical shortcut on every usable
canonical pair, assembles five-pair lessons across every cyclic schedule start,
and records lesson-level competitor refutation rather than extrapolating from
marginal witness frequency.  Its Python oracle is independent supplementary
evidence; ``--racket`` is required for authority parity and never falls back.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

WORKSPACE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
TASK = "531905d00c4b"
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from reference_probe import (  # noqa: E402
    absolute_row_rival,
    canonical,
    canonical_pairs,
    intended_output,
    load_generator,
    parse,
    racket_outputs,
)

BANDS = ("easy", "medium", "hard")
CYCLIC_STARTS = (0, 1, 2, 3)
PAIRS_PER_LESSON = len(canonical()["train"]) + 1


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _manifest_hash(items: set[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(items)) + "\n").encode()).hexdigest()


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> tuple[int, list[list[int]]]:
    h = max(len(left), len(right))
    w = max(max((len(row) for row in left), default=0), max((len(row) for row in right), default=0))
    coordinates: list[list[int]] = []
    for r in range(h):
        for c in range(w):
            a = left[r][c] if r < len(left) and c < len(left[r]) else None
            b = right[r][c] if r < len(right) and c < len(right[r]) else None
            if a != b:
                coordinates.append([r, c])
    return len(coordinates), coordinates


def shortcut_witness(module) -> dict[str, Any]:
    """Return an exact independent counterexample to the strongest canonical shortcut."""
    seed = 918
    sample_index = 1  # shifted_prototype in the four-cycle schedule
    difficulty = "hard"
    grid = module.generate(seed, sample_index, difficulty=difficulty)
    intended = intended_output(grid)
    independent_rival = absolute_row_rival(grid)
    declared_rival = module.CANONICAL_SHORTCUTS["absolute_row_padding"](deepcopy(grid))
    differing_cells, first_differences = _diff_cells(intended, independent_rival)
    return {
        "task_id": TASK,
        "shortcut": "absolute_row_padding",
        "description": (
            "Crop no prototype vertically; instead preserve each object's absolute row "
            "within the library before tiling. This fits every canonical demonstration "
            "because every canonical prototype begins in library row zero."
        ),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": {},
        "profile": module.schedule_profile(seed, sample_index, difficulty),
        "observed_axes": module.observe_overrides(grid),
        "self_check": module.self_check(grid),
        "input": grid,
        "intended_python": intended,
        "rival_output": independent_rival,
        "declared_rival_matches_independent": declared_rival == independent_rival,
        "differing_cells": differing_cells,
        "first_64_difference_coordinates": first_differences[:64],
        "input_sha256": _grid_hash(grid),
        "intended_sha256": _grid_hash(intended),
        "rival_sha256": _grid_hash(independent_rival),
    }


def _canonical_contract(module, declaration_name: str) -> dict[str, Any]:
    declared = getattr(module, declaration_name)
    rows: dict[str, Any] = {}
    for name, rival in declared.items():
        mismatches = []
        exceptions = []
        for index, pair in enumerate(canonical_pairs()):
            try:
                actual = rival(deepcopy(pair["input"]))
            except Exception as exc:  # evidence must retain contract crashes
                exceptions.append({"pair_index": index, "error": f"{type(exc).__name__}: {exc}"})
                continue
            if actual != pair["output"]:
                mismatches.append(index)
        rows[name] = {
            "pairs_checked": len(canonical_pairs()),
            "mismatch_pair_indices": mismatches,
            "exceptions": exceptions,
            "fits_all_canonical_pairs": not mismatches and not exceptions,
        }
    return rows


def audit(module, *, lessons_per_band: int = 100, parity_per_band: int = 16):
    """Audit actual sampled lessons and return ``(report, grids_for_racket)``.

    Lessons are five consecutive generated pair slots, matching the four visible
    demonstrations plus one query in the canonical episode.  The requested count
    is split equally among schedule phases 0..3.  Large phase-separated index
    ranges avoid overlap while preserving each cyclic start.
    """
    if lessons_per_band < 4 or lessons_per_band % len(CYCLIC_STARTS):
        raise ValueError("lessons_per_band must be a positive multiple of four")
    if parity_per_band < 0:
        raise ValueError("parity_per_band must be nonnegative")

    canonical_rows = canonical_pairs()
    canonical_self_check = [module.self_check(pair["input"]) for pair in canonical_rows]
    canonical_python_mismatches = [
        index for index, pair in enumerate(canonical_rows)
        if intended_output(pair["input"]) != pair["output"]
    ]
    canonical_shortcuts = _canonical_contract(module, "CANONICAL_SHORTCUTS")
    lesson_competitors = _canonical_contract(module, "LESSON_COMPETITORS")

    per_phase = lessons_per_band // len(CYCLIC_STARTS)
    bands: dict[str, Any] = {}
    all_input_hashes: set[str] = set()
    parity_grids = [deepcopy(pair["input"]) for pair in canonical_rows]
    any_generated_failure = False

    for band_index, band in enumerate(BANDS):
        profile_counts: Counter[str] = Counter()
        witness_counts: Counter[str] = Counter()
        input_disagreements: Counter[str] = Counter()
        lessons_refuting: Counter[str] = Counter()
        cyclic_counts: Counter[str] = Counter()
        dimension_counts: Counter[str] = Counter()
        input_hashes: set[str] = set()
        self_check_failures = []
        nondeterministic = []
        unrefuted_lessons = []
        parity_candidates: list[list[list[int]]] = []
        exact_canonical_profiles = 0
        input_slots = 0

        for phase in CYCLIC_STARTS:
            for ordinal in range(per_phase):
                # Every term except phase is divisible by four, so base % 4 == phase.
                base_index = band_index * 1_000_000 + phase * 100_000 + ordinal * 20 + phase
                seed = 531_905_000 + band_index * 10_000 + phase * 1_000 + ordinal
                lesson_disagrees = {name: False for name in module.LESSON_COMPETITORS}
                cyclic_counts[str(phase)] += 1

                for slot in range(PAIRS_PER_LESSON):
                    sample_index = base_index + slot
                    grid = module.generate(seed, sample_index, difficulty=band)
                    replay = module.generate(seed, sample_index, difficulty=band)
                    input_slots += 1
                    if grid != replay:
                        nondeterministic.append({
                            "seed": seed, "sample_index": sample_index, "slot": slot,
                        })
                    issues = module.self_check(grid)
                    if issues:
                        self_check_failures.append({
                            "seed": seed, "sample_index": sample_index,
                            "slot": slot, "issues": issues,
                        })

                    digest = _grid_hash(grid)
                    input_hashes.add(digest)
                    all_input_hashes.add(digest)
                    profile = module.schedule_profile(seed, sample_index, band)
                    profile_counts[profile] += 1
                    for name, predicate in module.SEMANTIC_WITNESSES.items():
                        if predicate(deepcopy(grid)):
                            witness_counts[name] += 1

                    height, width = len(grid), len(grid[0])
                    palette = len({value for row in grid for value in row})
                    dimension_counts[f"{height}x{width}/palette-{palette}"] += 1
                    if (height, width, palette) in {(6, 11, 4), (7, 11, 4)}:
                        exact_canonical_profiles += 1

                    intended = intended_output(grid)
                    for name, rival in module.LESSON_COMPETITORS.items():
                        disagrees = rival(deepcopy(grid)) != intended
                        input_disagreements[name] += int(disagrees)
                        lesson_disagrees[name] |= disagrees

                    if len(parity_candidates) < parity_per_band:
                        parity_candidates.append(deepcopy(grid))

                for name, disagrees in lesson_disagrees.items():
                    lessons_refuting[name] += int(disagrees)
                    if not disagrees:
                        unrefuted_lessons.append({
                            "competitor": name,
                            "seed": seed,
                            "base_sample_index": base_index,
                            "cyclic_start": phase,
                        })

        parity_grids.extend(parity_candidates)
        band_failure = bool(self_check_failures or nondeterministic or unrefuted_lessons)
        any_generated_failure |= band_failure
        bands[band] = {
            "lessons": lessons_per_band,
            "input_slots": input_slots,
            "distinct_inputs": len(input_hashes),
            "input_hash_manifest_sha256": _manifest_hash(input_hashes),
            "cyclic_start_counts": dict(sorted(cyclic_counts.items())),
            "profile_counts": dict(sorted(profile_counts.items())),
            "semantic_witness_input_counts": dict(sorted(witness_counts.items())),
            "input_disagreements_by_competitor": dict(sorted(input_disagreements.items())),
            "lessons_refuting_competitor": dict(sorted(lessons_refuting.items())),
            "exact_canonical_size_palette_profiles": exact_canonical_profiles,
            "dimension_palette_counts": dict(sorted(dimension_counts.items())),
            "self_check_failures": len(self_check_failures),
            "self_check_failure_examples": self_check_failures[:10],
            "nondeterministic_replays": len(nondeterministic),
            "nondeterministic_examples": nondeterministic[:10],
            "unrefuted_lessons": unrefuted_lessons,
            "passed": not band_failure,
        }

    witness = shortcut_witness(module)
    contract_failure = (
        any(canonical_self_check)
        or bool(canonical_python_mismatches)
        or any(not row["fits_all_canonical_pairs"] for row in canonical_shortcuts.values())
        or any(not row["fits_all_canonical_pairs"] for row in lesson_competitors.values())
    )
    witness_failure = (
        witness["self_check"] != []
        or witness["differing_cells"] <= 0
        or not witness["declared_rival_matches_independent"]
    )
    report = {
        "schema": "531905d00c4b-source-bound-qualification-v1",
        "task_id": TASK,
        "generator_version": module.VERSION,
        "declared_rule_hash": module.RULE_HASH,
        "actual_sampler": "generator.generate(seed, sample_index, difficulty=band) from selected generator bytes",
        "domain_limits": {
            "difficulty_bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "pairs_per_lesson": PAIRS_PER_LESSON,
            "generated_input_slots_per_band": lessons_per_band * PAIRS_PER_LESSON,
            "claim_limit": (
                "Finite deterministic qualification over the recorded schedule; it does not prove "
                "universal induction or cover every seed/override combination."
            ),
        },
        "lesson_policy": {
            "pairs_per_lesson": PAIRS_PER_LESSON,
            "meaning": "four consecutive visible demonstrations plus one consecutive query slot",
            "cyclic_starts": list(CYCLIC_STARTS),
            "lessons_per_cyclic_start_per_band": per_phase,
            "index_formula": (
                "band_index*1_000_000 + cyclic_start*100_000 + ordinal*20 + "
                "cyclic_start + slot"
            ),
            "seed_formula": (
                "531_905_000 + band_index*10_000 + cyclic_start*1_000 + ordinal"
            ),
            "overlap": "none among generated pair slots within a band",
        },
        "canonical": {
            "pairs_checked": len(canonical_rows),
            "self_check_errors": canonical_self_check,
            "independent_python_oracle_mismatch_pair_indices": canonical_python_mismatches,
        },
        "canonical_shortcuts": canonical_shortcuts,
        "lesson_competitors": lesson_competitors,
        "bands": bands,
        "global_distinct_inputs": len(all_input_hashes),
        "global_input_hash_manifest_sha256": _manifest_hash(all_input_hashes),
        "shortcut_witness": witness,
        "racket": {"status": "not_requested", "checked": 0, "mismatch_indices": []},
        "passed_without_racket": not (contract_failure or any_generated_failure or witness_failure),
    }
    return report, parity_grids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, help="alternate generator.py for comparison")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-out", type=Path)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--parity-per-band", type=int, default=16)
    parser.add_argument("--racket", action="store_true", help="require canonical Racket parity; no fallback")
    args = parser.parse_args()

    generator_path = (args.generator or ROOT / f"generators/{TASK}/generator.py").resolve()
    module = load_generator(generator_path)
    report, parity_grids = audit(
        module,
        lessons_per_band=args.lessons_per_band,
        parity_per_band=args.parity_per_band,
    )
    report["generator_path"] = str(generator_path)
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_path"] = str(Path(__file__).resolve())
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    normalized_program = " ".join(canonical()["program_solution"].split())
    report["canonical_rule_sha256"] = hashlib.sha256(normalized_program.encode()).hexdigest()
    report["canonical_rule_hash12"] = report["canonical_rule_sha256"][:12]

    exit_code = 0 if report["passed_without_racket"] else 1
    if args.racket:
        try:
            outputs = racket_outputs(parity_grids)
            expected = [intended_output(grid) for grid in parity_grids]
            mismatches = [i for i, (actual, want) in enumerate(zip(outputs, expected)) if actual != want]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "canonical_pairs": len(canonical_pairs()),
                "generated_per_band": args.parity_per_band,
                "mismatch_indices": mismatches,
            }
            witness_grid = report["shortcut_witness"]["input"]
            witness_racket = racket_outputs([witness_grid])[0]
            report["shortcut_witness"]["intended_racket"] = witness_racket
            report["shortcut_witness"]["racket_matches_independent_python"] = (
                witness_racket == report["shortcut_witness"]["intended_python"]
            )
            if mismatches or not report["shortcut_witness"]["racket_matches_independent_python"]:
                exit_code = 1
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "mismatch_indices": [],
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2

    report["passed"] = bool(report["passed_without_racket"] and (
        report["racket"]["status"] == "passed" if args.racket else True
    ))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.witness_out:
        witness = dict(report["shortcut_witness"])
        witness.update({
            "generator_sha256": report["generator_sha256"],
            "probe_sha256": report["probe_sha256"],
            "canonical_rule_sha256": report["canonical_rule_sha256"],
            "command": [
                sys.executable, "-B", str(Path(__file__).resolve()),
                "--lessons-per-band", str(args.lessons_per_band),
                "--parity-per-band", str(args.parity_per_band),
                "--racket", "--out", str(args.out.resolve()),
                "--witness-out", str(args.witness_out.resolve()),
            ],
            "working_directory": str(ROOT),
        })
        args.witness_out.parent.mkdir(parents=True, exist_ok=True)
        args.witness_out.write_text(json.dumps(witness, indent=2) + "\n", encoding="utf-8")

    concise = {
        "passed": report["passed"],
        "generator_sha256": report["generator_sha256"],
        "lessons_per_band": args.lessons_per_band,
        "global_distinct_inputs": report["global_distinct_inputs"],
        "bands": {
            band: {
                "distinct_inputs": row["distinct_inputs"],
                "lessons_refuting_competitor": row["lessons_refuting_competitor"],
                "self_check_failures": row["self_check_failures"],
            }
            for band, row in report["bands"].items()
        },
        "racket": report["racket"],
    }
    print(json.dumps(concise, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
