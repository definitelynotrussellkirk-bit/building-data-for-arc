#!/usr/bin/env python3
"""Source-bound cyclic lesson audit for e0650802a8fb.

This is an authoring aid, not an intake gate. It checks every start in the
five-slot schedule, reports unique inputs separately from overlapping windows,
and reads rival names from the selected generator instead of duplicating them.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "e0650802a8fb"
BANDS = ("easy", "medium", "hard")
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"


def _load_generator():
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        spec = importlib.util.spec_from_file_location(
            f"workspace_generator_{TASK_ID}", GENERATOR_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _pair(generator, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def _axis_cases() -> list[dict[str, Any]]:
    return [
        {"grid_h": 8, "grid_w": 8, "pair_count": 2, "scene_profile": "disjoint"},
        {"grid_h": 8, "grid_w": 14, "pair_count": 4, "scene_profile": "interior_cross"},
        {"grid_h": 14, "grid_w": 8, "pair_count": 3, "scene_profile": "endpoint_overwrite"},
        {"grid_h": 14, "grid_w": 14, "pair_count": 4, "scene_profile": "endpoint_survive"},
        {"grid_h": 10, "grid_w": 12, "pair_count": 2, "scene_profile": "controls"},
    ]


def run_probe(
    *, seed_count: int = 4, bands: Iterable[str] = BANDS
) -> dict[str, Any]:
    """Return a JSON-safe schedule, rival, canonical, and exact-axis report."""
    if isinstance(seed_count, bool) or not isinstance(seed_count, int) or seed_count < 1:
        raise ValueError("seed_count must be a positive integer")
    selected_bands = tuple(bands)
    unknown = sorted(set(selected_bands) - set(BANDS))
    if unknown:
        raise ValueError(f"unknown bands: {unknown}")

    generator = _load_generator()
    source_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical_accepted = 0
    canonical_parity = 0
    canonical_failures: list[dict[str, Any]] = []
    for pair in canonical:
        findings = generator.self_check(pair["input"])
        mirrored = generator.rule_mirror(pair["input"])
        canonical_accepted += not findings
        canonical_parity += mirrored == pair["output"]
        if findings or mirrored != pair["output"]:
            canonical_failures.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "self_check": findings,
                    "mirror_matches": mirrored == pair["output"],
                }
            )

    axis_results: list[dict[str, Any]] = []
    for index, overrides in enumerate(_axis_cases()):
        try:
            grid = generator.generate(9001, index, difficulty="hard", **overrides)
            observed = generator.observe_overrides(grid)
            findings = generator.self_check(grid, meta={"overrides": overrides})
            axis_results.append(
                {
                    "requested": overrides,
                    "observed": observed,
                    "self_check": findings,
                    "passed": observed == overrides and not findings,
                }
            )
        except Exception as exc:
            axis_results.append(
                {
                    "requested": overrides,
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    per_band: dict[str, Any] = {}
    all_band_pass = True
    expected_profiles = set(generator.SCHEDULE_PROFILES)
    rivals = dict(generator.LESSON_COMPETITORS)
    for band in selected_bands:
        windows = 0
        profile_complete = 0
        rival_complete = 0
        identifiable = 0
        profile_counts: Counter[str] = Counter()
        rival_refutations: Counter[str] = Counter()
        unique_inputs: set[str] = set()
        failures: list[dict[str, Any]] = []

        for seed in range(seed_count):
            for start in range(len(generator.SCHEDULE_PROFILES)):
                demos = []
                profiles: set[str] = set()
                for offset in range(generator.EXAMPLES_NEEDED):
                    grid = generator.generate(
                        seed, start + offset, difficulty=band
                    )
                    unique_inputs.add(_grid_digest(grid))
                    observed = generator.observe_overrides(grid)
                    profile = observed.get("scene_profile")
                    profiles.add(profile)
                    profile_counts[profile] += 1
                    demos.append(_pair(generator, grid))

                query_grid = generator.generate(
                    seed,
                    start + generator.EXAMPLES_NEEDED,
                    difficulty=band,
                )
                unique_inputs.add(_grid_digest(query_grid))
                query = _pair(generator, query_grid)
                windows += 1

                profiles_ok = profiles == expected_profiles
                profile_complete += profiles_ok
                killed = {
                    name
                    for name, competitor in rivals.items()
                    if any(
                        competitor(pair["input"]) != pair["output"]
                        for pair in demos
                    )
                }
                for name in killed:
                    rival_refutations[name] += 1
                rivals_ok = killed == set(rivals)
                rival_complete += rivals_ok
                reasons = generator.lesson_identifiable(demos, query)
                identifiable += not reasons

                if not profiles_ok or not rivals_ok or reasons:
                    failures.append(
                        {
                            "seed": seed,
                            "start": start,
                            "profiles": sorted(profiles),
                            "missing_rivals": sorted(set(rivals) - killed),
                            "lesson_reasons": reasons,
                        }
                    )

        band_pass = (
            profile_complete == windows
            and rival_complete == windows
            and identifiable == windows
        )
        all_band_pass &= band_pass
        per_band[band] = {
            "windows": windows,
            "overlapping_demo_instances": windows * generator.EXAMPLES_NEEDED,
            "unique_inputs": len(unique_inputs),
            "profile_complete_windows": profile_complete,
            "rival_complete_windows": rival_complete,
            "identifiable_windows": identifiable,
            "profile_counts": dict(sorted(profile_counts.items())),
            "rival_refutation_windows": dict(sorted(rival_refutations.items())),
            "failures": failures[:20],
            "passed": band_pass,
        }

    canonical_pass = (
        canonical_accepted == len(canonical)
        and canonical_parity == len(canonical)
    )
    axes_pass = all(row["passed"] for row in axis_results)
    status = "pass" if canonical_pass and axes_pass and all_band_pass else "fail"
    return {
        "schema": "e0650802a8fb-lesson-probe-v1",
        "status": status,
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "lesson_policy": {
            "examples_needed": generator.EXAMPLES_NEEDED,
            "cyclic_starts": list(range(len(generator.SCHEDULE_PROFILES))),
            "profiles": list(generator.SCHEDULE_PROFILES),
            "seed_count": seed_count,
            "bands": list(selected_bands),
        },
        "canonical": {
            "pairs": len(canonical),
            "accepted": canonical_accepted,
            "mirror_matches": canonical_parity,
            "failures": canonical_failures,
        },
        "exact_axis_cases": axis_results,
        "per_band": per_band,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=4, help="seeds per band")
    parser.add_argument(
        "--bands",
        nargs="+",
        choices=BANDS,
        default=list(BANDS),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(seed_count=args.seeds, bands=args.bands)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
