"""Reusable qualification probe for the a8a8969ab4f1 generator.

This task-local harness complements the shared battery.  It enumerates every
start phase of the three-sample semantic schedule across overlapping four-pair
lessons, rotates every query position, replays the generator's *declared*
competitors, checks every legal exact-axis combination, and confirms declared
canonical shortcuts really fit all usable canonical pairs.

It deliberately labels generated grids with ``reference_probe.intended_output``
rather than importing implementation helpers from ``generator.py``.  The shared
Racket battery and task tests separately bind that independent mirror to the
selected authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Any

from reference_probe import canonical_pairs, intended_output, load_generator

BANDS = ("easy", "medium", "hard")
WINDOW_SIZE = 4


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _competitors(generator) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        for name, solve in getattr(generator, namespace, {}).items():
            merged.setdefault(name, solve)
    return merged


def _axis_domains(generator) -> dict[str, tuple[str, ...]]:
    domains: dict[str, tuple[str, ...]] = {}
    for name, spec in generator.AXES.items():
        valid = spec.get("valid")
        if not isinstance(valid, str) or not valid:
            raise ValueError(f"axis {name!r} has no literal pipe-delimited domain")
        domains[name] = tuple(valid.split("|"))
    return domains


def run_qualification(generator, *, starts_per_band: int = 100, seed: int = 404) -> dict[str, Any]:
    """Return a JSON-serializable report; no Racket/private runner imports."""
    if starts_per_band < 1:
        raise ValueError("starts_per_band must be positive")

    errors: list[dict[str, Any]] = []
    profile_counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    windows = rotations = ambiguous = invalid = 0
    competitors = _competitors(generator)
    competitor_ambiguities: Counter[str] = Counter()

    # The start index advances by one, so this covers all cyclic phases and a
    # broad set of keyed-draw realizations rather than sampling only disjoint lessons.
    for band_index, band in enumerate(BANDS):
        band_seed = seed + band_index * 100_003
        for start in range(starts_per_band):
            windows += 1
            pairs: list[dict[str, Any]] = []
            for offset in range(WINDOW_SIZE):
                sample_index = start + offset
                grid = generator.generate(band_seed, sample_index, difficulty=band)
                validation = generator.self_check(deepcopy(grid), difficulty=band)
                if validation:
                    invalid += 1
                    errors.append(
                        {
                            "kind": "invalid_generated_input",
                            "band": band,
                            "start": start,
                            "offset": offset,
                            "reasons": list(validation),
                        }
                    )
                unique_inputs.add(_grid_hash(grid))
                profile_counts[str(generator.schedule_profile(band_seed, sample_index, band))] += 1
                pairs.append({"input": grid, "output": intended_output(grid)})

            for held_out in range(WINDOW_SIZE):
                rotations += 1
                query = pairs[held_out]
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                hook_reasons = generator.lesson_identifiable(deepcopy(demos), deepcopy(query))
                if hook_reasons:
                    ambiguous += 1
                    errors.append(
                        {
                            "kind": "lesson_hook_ambiguity",
                            "band": band,
                            "start": start,
                            "query_index": held_out,
                            "reasons": list(hook_reasons),
                        }
                    )
                for name, solve in competitors.items():
                    if all(solve(pair["input"]) == pair["output"] for pair in demos):
                        if solve(query["input"]) != query["output"]:
                            competitor_ambiguities[name] += 1
                            errors.append(
                                {
                                    "kind": "competitor_ambiguity",
                                    "competitor": name,
                                    "band": band,
                                    "start": start,
                                    "query_index": held_out,
                                }
                            )

    canonical_status: dict[str, str] = {}
    canonical = canonical_pairs()
    for name, solve in getattr(generator, "CANONICAL_SHORTCUTS", {}).items():
        if all(solve(pair["input"]) == pair["output"] for pair in canonical):
            canonical_status[name] = "fits_all_canonical_pairs"
        else:
            canonical_status[name] = "does_not_fit_all_canonical_pairs"
            errors.append({"kind": "misdeclared_canonical_shortcut", "shortcut": name})

    # Exhaust every advertised exact control jointly in every difficulty band.
    domains = _axis_domains(generator)
    names = tuple(domains)
    override_cases = 0
    for band_index, band in enumerate(BANDS):
        for case_index, values in enumerate(product(*(domains[name] for name in names))):
            override_cases += 1
            requested = dict(zip(names, values))
            grid = generator.generate(
                seed + 900_001 + band_index * 100_003,
                case_index,
                difficulty=band,
                **requested,
            )
            validation = generator.self_check(deepcopy(grid), difficulty=band)
            observed = generator.observe_overrides(deepcopy(grid))
            if validation or observed != requested:
                errors.append(
                    {
                        "kind": "exact_override_failure",
                        "band": band,
                        "requested": requested,
                        "observed": observed,
                        "validation": list(validation),
                    }
                )

    report = {
        "schema": "a8a8969ab4f1-qualification-v1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "generator_rule_hash": generator.RULE_HASH,
        "status": "passed" if not errors else "failed",
        "parameters": {
            "starts_per_band": starts_per_band,
            "bands": list(BANDS),
            "window_size": WINDOW_SIZE,
            "seed": seed,
            "query_policy": "all four rotations",
        },
        "summary": {
            "windows": windows,
            "rotations": rotations,
            "ambiguous_rotations": ambiguous + sum(competitor_ambiguities.values()),
            "hook_ambiguities": ambiguous,
            "competitor_ambiguities": dict(sorted(competitor_ambiguities.items())),
            "invalid_inputs": invalid,
            "unique_inputs": len(unique_inputs),
            "exact_override_cases": override_cases,
        },
        "schedule_profiles": dict(sorted(profile_counts.items())),
        "canonical_shortcuts": canonical_status,
        "errors": errors,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="alternate generator.py to probe")
    parser.add_argument("--starts-per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=404)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_qualification(
        load_generator(args.source),
        starts_per_band=args.starts_per_band,
        seed=args.seed,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
