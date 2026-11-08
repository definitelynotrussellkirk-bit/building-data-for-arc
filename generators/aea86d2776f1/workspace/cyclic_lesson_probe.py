#!/usr/bin/env python3
"""Exhaustive cyclic lesson probe for aea86d2776f1's four-slot schedule.

The shared lesson census exercises production assembly and real Racket labels.
This complementary probe focuses on the generator's small deterministic schedule:
it covers every cyclic start, rotates each of four pairs into the query position,
iterates the generator's actual rival registries, verifies claimed canonical
shortcuts against every canonical pair, and records exact replay seeds/hashes.

The probe uses the independent Python oracle in ``reference_probe.py``. It is
finite evidence against declared rivals, not a proof of unique induction.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from reference_probe import canonical_pairs, intended_output, load_generator

TASK = "aea86d2776f1"
BANDS = ("easy", "medium", "hard")
PERIOD = 4


def _seed(band: str, phase: int, ordinal: int) -> int:
    payload = f"cyclic-lesson-probe:v1:{TASK}:{band}:{phase}:{ordinal}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _registries(module) -> dict[str, dict[str, Callable]]:
    result: dict[str, dict[str, Callable]] = {}
    for registry_name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        raw = getattr(module, registry_name, None)
        if not isinstance(raw, dict):
            result[registry_name] = {}
            continue
        result[registry_name] = {
            str(name): function
            for name, function in raw.items()
            if callable(function)
        }
    return result


def _canonical_contract(module, rivals: dict[str, Callable]) -> dict[str, Any]:
    rows = {}
    pairs = canonical_pairs()
    for name, rival in sorted(rivals.items()):
        mismatches = []
        exceptions = []
        for index, pair in enumerate(pairs):
            try:
                actual = rival(deepcopy(pair["input"]))
            except Exception as exc:  # retain contract crashes as evidence
                exceptions.append({"pair_index": index, "error": f"{type(exc).__name__}: {exc}"})
                continue
            if actual != pair["output"]:
                mismatches.append(index)
        rows[name] = {
            "pairs_checked": len(pairs),
            "mismatch_pair_indices": mismatches,
            "exceptions": exceptions,
            "fits_all_canonical_pairs": not mismatches and not exceptions,
        }
    return rows


def run(per_band: int) -> dict[str, Any]:
    if per_band <= 0 or per_band % PERIOD:
        raise ValueError(f"per_band must be a positive multiple of {PERIOD}")

    module = load_generator()
    registries = _registries(module)
    canonical_contract = _canonical_contract(
        module, registries.get("CANONICAL_SHORTCUTS", {})
    )
    failures: list[dict[str, Any]] = []
    all_hashes: set[str] = set()
    total_rotations = 0
    total_pairs = 0
    bands: dict[str, Any] = {}
    witness_totals = {name: 0 for name in module.SEMANTIC_WITNESSES}
    rival_disagreement_totals = {name: 0 for name in module.LESSON_COMPETITORS}

    per_phase = per_band // PERIOD
    for band_index, band in enumerate(BANDS):
        band_hashes: set[str] = set()
        band_failures = 0
        phase_counts = {str(phase): 0 for phase in range(PERIOD)}
        profile_counts = {str(profile): 0 for profile in module.SCHEDULE_PROFILES}
        band_witnesses = {name: 0 for name in module.SEMANTIC_WITNESSES}
        band_rival_disagreements = {name: 0 for name in module.LESSON_COMPETITORS}

        for phase in range(PERIOD):
            for ordinal in range(per_phase):
                # Large separated ranges make the exact cyclic phase explicit.
                start = band_index * 1_000_000 + phase * 100_000 + ordinal * 20 + phase
                seed = _seed(band, phase, ordinal)
                phase_counts[str(phase)] += 1
                pairs = []

                for slot in range(PERIOD):
                    sample_index = start + slot
                    grid = module.generate(seed, sample_index, difficulty=band)
                    replay = module.generate(seed, sample_index, difficulty=band)
                    issues = module.self_check(grid)
                    profile = module.schedule_profile(seed, sample_index, band)
                    profile_counts[str(profile)] = profile_counts.get(str(profile), 0) + 1
                    digest = _grid_hash(grid)
                    band_hashes.add(digest)
                    all_hashes.add(digest)
                    total_pairs += 1

                    if grid != replay or issues:
                        band_failures += 1
                        if len(failures) < 40:
                            failures.append(
                                {
                                    "kind": "pair_contract",
                                    "band": band,
                                    "phase": phase,
                                    "ordinal": ordinal,
                                    "seed": seed,
                                    "sample_index": sample_index,
                                    "deterministic": grid == replay,
                                    "self_check": issues,
                                }
                            )

                    truth = intended_output(grid)
                    for name, predicate in module.SEMANTIC_WITNESSES.items():
                        if predicate(deepcopy(grid)):
                            band_witnesses[name] += 1
                            witness_totals[name] += 1
                    for name, rival in module.LESSON_COMPETITORS.items():
                        if rival(deepcopy(grid)) != truth:
                            band_rival_disagreements[name] += 1
                            rival_disagreement_totals[name] += 1
                    pairs.append(
                        {
                            "input": grid,
                            "output": truth,
                            "input_sha256": digest,
                            "sample_index": sample_index,
                            "profile": profile,
                        }
                    )

                for query_index in range(PERIOD):
                    total_rotations += 1
                    query = pairs[query_index]
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    hook_errors = module.lesson_identifiable(demos, query)
                    ambiguous = []
                    for name, rival in module.LESSON_COMPETITORS.items():
                        survives_demos = all(
                            rival(deepcopy(demo["input"])) == demo["output"]
                            for demo in demos
                        )
                        changes_query = (
                            rival(deepcopy(query["input"])) != query["output"]
                        )
                        if survives_demos and changes_query:
                            ambiguous.append(name)
                    if hook_errors or ambiguous:
                        band_failures += 1
                        if len(failures) < 40:
                            failures.append(
                                {
                                    "kind": "rotation_ambiguity",
                                    "band": band,
                                    "phase": phase,
                                    "ordinal": ordinal,
                                    "seed": seed,
                                    "start": start,
                                    "query_index": query_index,
                                    "hook_errors": hook_errors,
                                    "surviving_query_changing_rivals": ambiguous,
                                    "pair_hashes": [pair["input_sha256"] for pair in pairs],
                                }
                            )

        bands[band] = {
            "lessons": per_band,
            "pairs": per_band * PERIOD,
            "query_rotations": per_band * PERIOD,
            "failures": band_failures,
            "unique_inputs": len(band_hashes),
            "phase_counts": phase_counts,
            "profile_counts": profile_counts,
            "witness_counts": band_witnesses,
            "rival_disagreement_counts": band_rival_disagreements,
        }

    bad_shortcuts = [
        name
        for name, row in canonical_contract.items()
        if not row["fits_all_canonical_pairs"]
    ]
    status = "pass" if not failures and not bad_shortcuts else "fail"
    source = Path(module.__file__).resolve()
    probe = Path(__file__).resolve()
    return {
        "schema": "aea86d2776f1-cyclic-lesson-probe-v1",
        "status": status,
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(probe.read_bytes()).hexdigest(),
        "per_band": per_band,
        "pairs_per_lesson": PERIOD,
        "query_rotations_per_lesson": PERIOD,
        "lesson_policy": (
            "100 four-pair lessons per band, equally split across starts modulo 4; "
            "each pair is held out once with the other three as demonstrations"
        ),
        "seed_recipe": "sha256('cyclic-lesson-probe:v1:TASK:BAND:PHASE:ORDINAL')[:8]",
        "start_recipe": "band*1_000_000 + phase*100_000 + ordinal*20 + phase",
        "registries": {name: sorted(rows) for name, rows in registries.items()},
        "canonical_shortcut_contract": canonical_contract,
        "canonical_shortcuts_not_fitting_all_pairs": bad_shortcuts,
        "bands": bands,
        "summary": {
            "lessons": per_band * len(BANDS),
            "materialized_pairs": total_pairs,
            "query_rotations": total_rotations,
            "unique_inputs": len(all_hashes),
            "failures": len(failures),
            "witness_counts": witness_totals,
            "rival_disagreement_counts": rival_disagreement_totals,
        },
        "failures": failures,
        "limits": [
            "Finite evidence against declared rivals, not proof of universal induction.",
            "Uses an independent Python mirror; real Racket labels are covered by the shared census and task tests.",
            "Checks consecutive four-pair windows because EXAMPLES_NEEDED=3 and the schedule period is four.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(f"status={report['status']} out={args.out}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
