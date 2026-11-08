#!/usr/bin/env python3
"""Source-bound regression probe for generator 83ca9df09514.

The probe is intentionally independent of the battery wrapper.  Future agents
can import ``run_probe`` from focused tests or execute this file directly after
staging the repository runtime.  It checks canonical ownership, exact profile
coverage, public override round-trips, shortcut truthfulness, and all query
rotations of representative four-pair lessons.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "83ca9df09514"
HOME = Path(__file__).resolve().parents[1]


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _load_generator(path: Path | None = None):
    source = path or HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    try:
        from reviewer_support import canonical_pairs, find_root
    except ImportError as exc:  # direct CLI should fail loudly, not guess paths
        raise RuntimeError(
            "reviewer_support is required for standalone canonical loading"
        ) from exc
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def run_probe(gen, canonical_pairs: list[dict[str, Any]], *, seeds_per_band: int = 5) -> dict[str, Any]:
    if type(seeds_per_band) is not int or seeds_per_band < 5:
        raise ValueError("seeds_per_band must be an integer >= 5")

    canonical_failures: list[dict[str, Any]] = []
    canonical_profiles = set()
    for index, pair in enumerate(canonical_pairs):
        canonical_profiles.add(_profile(pair["input"]))
        findings = gen.self_check(pair["input"])
        mirrored = gen.rule_mirror(pair["input"])
        if findings or mirrored != pair["output"]:
            canonical_failures.append(
                {
                    "index": index,
                    "self_check": findings,
                    "mirror_matches": mirrored == pair["output"],
                }
            )

    generated_profiles = set()
    generation_failures: list[dict[str, Any]] = []
    shortcut_failures: list[dict[str, Any]] = []
    ambiguous_rotations = 0
    bands = (None, "easy", "medium", "hard")
    for band in bands:
        pairs = []
        for index in range(max(seeds_per_band, 8)):
            grid = gen.generate(4000 + index, index, difficulty=band)
            output = gen.rule_mirror(grid)
            if index < seeds_per_band:
                generated_profiles.add(_profile(grid))
            findings = gen.self_check(grid)
            if findings:
                generation_failures.append(
                    {"band": band, "index": index, "findings": findings}
                )
            for name, rival in gen.CANONICAL_SHORTCUTS.items():
                if rival(grid) == output:
                    shortcut_failures.append(
                        {"where": "generated", "band": band, "index": index, "rival": name}
                    )
            pairs.append({"input": grid, "output": output})

        for start in range(len(pairs) - 3):
            window = pairs[start : start + 4]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                if gen.lesson_identifiable(demos, window[query_index]):
                    ambiguous_rotations += 1

    for index, pair in enumerate(canonical_pairs):
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            if rival(pair["input"]) != pair["output"]:
                shortcut_failures.append(
                    {"where": "canonical", "index": index, "rival": name}
                )

    override_failures: list[dict[str, Any]] = []
    override_cases = (
        {
            "grid_h": 6,
            "grid_w": 8,
            "n_keys": 4,
            "n_groups": 4,
            "template_position": "top",
            "key_layout": "prefix",
        },
        {
            "grid_h": 16,
            "grid_w": 18,
            "n_keys": 1,
            "n_groups": 2,
            "template_position": "bottom",
            "key_layout": "shifted",
        },
        {
            "grid_h": 11,
            "grid_w": 13,
            "n_keys": 3,
            "n_groups": 3,
            "template_position": "random",
            "key_layout": "scattered",
        },
    )
    for band in bands:
        for case_index, requested in enumerate(override_cases):
            try:
                grid = gen.generate(9000 + case_index, 17, difficulty=band, **requested)
                observed = gen.observe_overrides(grid)
                findings = gen.self_check(grid)
            except Exception as exc:
                override_failures.append(
                    {"band": band, "case": case_index, "exception": repr(exc)}
                )
                continue
            if observed != requested or findings:
                override_failures.append(
                    {
                        "band": band,
                        "case": case_index,
                        "requested": requested,
                        "observed": observed,
                        "self_check": findings,
                    }
                )

    profile_gap = sorted(canonical_profiles - generated_profiles)
    status = "pass" if not any(
        (
            canonical_failures,
            generation_failures,
            override_failures,
            shortcut_failures,
            profile_gap,
            ambiguous_rotations,
        )
    ) else "fail"
    return {
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "status": status,
        "canonical_pairs_checked": len(canonical_pairs),
        "canonical_failures": canonical_failures,
        "canonical_profiles_seen": len(generated_profiles & canonical_profiles),
        "missing_canonical_profiles": profile_gap,
        "generation_failures": generation_failures,
        "override_failures": override_failures,
        "shortcut_failures": shortcut_failures,
        "ambiguous_rotations": ambiguous_rotations,
    }


def main() -> int:
    report = run_probe(_load_generator(), _canonical_pairs())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
