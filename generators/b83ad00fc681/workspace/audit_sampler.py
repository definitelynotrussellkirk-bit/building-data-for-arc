#!/usr/bin/env python3
"""Standalone distribution/rival/parity audit for b83ad00fc681.

The report includes replay seeds, exact axis coverage, one concrete
fixed-dictionary counterexample, canonical checks, and optional real-Racket
parity.  It imports only the public generator and the independent
``reference_probe`` oracle in this workspace.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from reference_probe import (
    canonical_pairs,
    fixed_dictionary_output,
    load_generator,
    observed,
    profile,
    racket_outputs,
    stamp_output,
)

BANDS = ("easy", "medium", "hard")


def _digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def audit(module, count: int, *, use_racket: bool) -> dict:
    canonical = canonical_pairs()
    report = {
        "schema": "b83ad00fc681-sampler-audit-v1",
        "task_id": module.TASK_ID,
        "version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "sample_schedule": {
            "bands": list(BANDS),
            "count_per_band": count,
            "seed": "91000 + band_index*10000 + index",
            "sample_index": "17*index + 3",
        },
        "canonical": {
            "pairs": len(canonical),
            "accepted": 0,
            "python_oracle_matches": 0,
            "fixed_dictionary_matches": 0,
            "profiles": sorted({profile(pair["input"]) for pair in canonical}),
        },
        "bands": {},
        "totals": {},
        "first_counterexample": None,
        "racket": {"status": "not_requested", "checked": 0},
    }

    for pair in canonical:
        report["canonical"]["accepted"] += not module.self_check(pair["input"])
        report["canonical"]["python_oracle_matches"] += stamp_output(pair["input"]) == pair["output"]
        report["canonical"]["fixed_dictionary_matches"] += fixed_dictionary_output(pair["input"]) == pair["output"]

    total = Counter()
    all_inputs = set()
    parity_grids = [pair["input"] for pair in canonical]
    for band_index, band in enumerate(BANDS):
        stats = Counter()
        axis_values = defaultdict(set)
        profiles = Counter()
        inputs = set()
        for index in range(count):
            seed = 91000 + band_index * 10000 + index
            sample_index = 17 * index + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            replay = {
                "band": band,
                "seed": seed,
                "sample_index": sample_index,
            }
            stats["draws"] += 1
            stats["self_check_failures"] += bool(module.self_check(grid))
            stats["strict_failures"] += bool(module.strict_canonical_like(grid))
            stats["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            actual = observed(grid)
            stats["observer_mismatches"] += actual != module.observe_overrides(grid)
            for name, value in actual.items():
                axis_values[name].add(value)
            profiles[str(profile(grid))] += 1
            digest = _digest(grid)
            inputs.add(digest)
            all_inputs.add(digest)
            intended = stamp_output(grid)
            rival = fixed_dictionary_output(grid)
            disagrees = intended != rival
            stats["fixed_dictionary_disagreements"] += disagrees
            stats["witness_fires"] += module.SEMANTIC_WITNESSES[
                "fixed_dictionary_counterexample"
            ](grid)
            if disagrees and report["first_counterexample"] is None:
                differing = [
                    [r, c, intended[r][c], rival[r][c]]
                    for r in range(len(intended))
                    for c in range(len(intended[0]))
                    if intended[r][c] != rival[r][c]
                ]
                report["first_counterexample"] = {
                    "replay": replay,
                    "observed_axes": actual,
                    "input": grid,
                    "intended_python": intended,
                    "fixed_dictionary_rival": rival,
                    "differing_cells": differing,
                }
            if index < 12:
                parity_grids.append(grid)
        stats["distinct_inputs"] = len(inputs)
        report["bands"][band] = {
            **dict(stats),
            "axis_values": {name: sorted(values) for name, values in axis_values.items()},
            "profiles": dict(sorted(profiles.items())),
        }
        total.update(stats)
    total["distinct_inputs"] = len(all_inputs)
    report["totals"] = dict(total)

    if use_racket:
        try:
            outputs = racket_outputs(parity_grids)
            expected = [stamp_output(grid) for grid in parity_grids]
            mismatches = [index for index, pair in enumerate(zip(outputs, expected)) if pair[0] != pair[1]]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatch_indices": mismatches,
            }
        except Exception as exc:  # retained as explicit evidence, never fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }

    report["generator_sha256"] = hashlib.sha256(
        Path(module.__file__).read_bytes()
    ).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    failures = (
        report["canonical"]["accepted"] != len(canonical)
        or report["canonical"]["python_oracle_matches"] != len(canonical)
        or report["canonical"]["fixed_dictionary_matches"] != len(canonical)
        or any(report["totals"].get(name, 0) for name in (
            "self_check_failures", "strict_failures", "nondeterministic", "observer_mismatches"
        ))
        or report["totals"].get("fixed_dictionary_disagreements") != count * len(BANDS)
        or report["totals"].get("witness_fires") != count * len(BANDS)
        or (use_racket and report["racket"]["status"] != "passed")
    )
    report["status"] = "failed" if failures else "passed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count, use_racket=args.racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "canonical": report["canonical"],
        "totals": report["totals"],
        "racket": report["racket"],
        "counterexample_replay": report["first_counterexample"]["replay"],
    }, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
