#!/usr/bin/env python3
"""One-command source-bound qualification for generator 35368341e72e.

The tool replays canonical labels with an independent Python oracle, exercises
exact override boundaries, sweeps all difficulty bands, checks the retained
shortcut counterexample, and reproduces the profile-floor census seeds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from reference_probe import (
    TASK_ID,
    canonical_pairs,
    deduplicate_query_output,
    intended_output,
    load_generator,
    observed,
    profile,
    repeated_query,
    witness_input,
)

BANDS = ("easy", "medium", "hard")
CANONICAL_PROFILES = {(6, 11, 5), (6, 11, 6)}


def _profile_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def qualify() -> dict:
    generator_path = Path(
        os.environ.get("GENERATOR_UNDER_TEST", Path(__file__).resolve().parents[1] / "generator.py")
    )
    gen = load_generator(generator_path)
    errors: list[str] = []
    pairs = canonical_pairs()

    for index, pair in enumerate(pairs):
        if gen.self_check(pair["input"]):
            errors.append(f"canonical pair {index} rejected by self_check")
        if intended_output(pair["input"]) != pair["output"]:
            errors.append(f"independent oracle disagrees with canonical pair {index}")
        if gen.rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"production mirror disagrees with canonical pair {index}")
        if deduplicate_query_output(pair["input"]) != pair["output"]:
            errors.append(f"declared shortcut does not fit canonical pair {index}")

    override_cases = (
        {"grid_h": 5, "grid_w": 11, "n_keys": 3, "query_len": 3},
        {"grid_h": 12, "grid_w": 20, "n_keys": 1, "query_len": 2},
    )
    for band in (None, *BANDS):
        for case_index, requested in enumerate(override_cases):
            grid = gen.generate(17 + case_index, 9 + case_index, difficulty=band, **requested)
            if gen.self_check(grid, difficulty=band):
                errors.append(f"override case {case_index} rejected in band {band!r}")
            if observed(grid) != requested or gen.observe_overrides(grid) != requested:
                errors.append(f"override case {case_index} not realized in band {band!r}")

    generated_draws = 0
    shortcut_counterexamples = 0
    unique_inputs: set[str] = set()
    for band in BANDS:
        for index in range(64):
            seed = 7000 + index
            sample_index = index * 11
            grid = gen.generate(seed, sample_index, difficulty=band)
            generated_draws += 1
            signature = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            unique_inputs.add(signature)
            if gen.self_check(grid, difficulty=band):
                errors.append(f"generated grid rejected: band={band} index={index}")
                continue
            if grid != gen.generate(seed, sample_index, difficulty=band):
                errors.append(f"nondeterministic draw: band={band} index={index}")
            intended = intended_output(grid)
            if gen.rule_mirror(grid) != intended:
                errors.append(f"production mirror mismatch: band={band} index={index}")
            rival = deduplicate_query_output(grid)
            if repeated_query(grid) and rival != intended:
                shortcut_counterexamples += 1
            else:
                errors.append(f"missing deduplication counterexample: band={band} index={index}")
            if len(intended) > len(grid) or len(intended[0]) > len(grid[0]):
                errors.append(f"non-shrink transformation: band={band} index={index}")

    profile_hits: dict[str, int] = {}
    for band in BANDS:
        hits = 0
        for index in range(20):
            seed = _profile_seed(band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            hits += profile(grid) in CANONICAL_PROFILES
        profile_hits[band] = hits
    if any(hits < 1 for hits in profile_hits.values()):
        errors.append(f"profile floor has a zero-support band: {profile_hits}")
    if sum(profile_hits.values()) / 60 < 0.25:
        errors.append(f"pooled canonical-profile rate below 25%: {profile_hits}")

    witness = witness_input()
    if gen.self_check(witness):
        errors.append("retained repeated-query witness is outside self_check domain")
    if intended_output(witness) == deduplicate_query_output(witness):
        errors.append("retained witness does not refute deduplication")

    report = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "status": "pass" if not errors else "fail",
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "authority": "independent_python_translation_of_selected_rule",
        "canonical_pairs": len(pairs),
        "generated_draws": generated_draws,
        "unique_inputs": len(unique_inputs),
        "shortcut_counterexamples": shortcut_counterexamples,
        "profile_hits": profile_hits,
        "errors": errors,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit compact JSON only")
    parser.add_argument("--out", type=Path, help="also write the report to this path")
    args = parser.parse_args()
    report = qualify()
    text = json.dumps(report, sort_keys=True) if args.json else json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(text)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
