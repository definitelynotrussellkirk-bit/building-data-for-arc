#!/usr/bin/env python3
"""Source-bound curriculum audit for ARC task 00ed2544a15e.

This is a fast Python-side authoring probe.  It discovers shortcuts and lesson
competitors from the live generator declarations, verifies canonical fit,
exhausts the small cyclic profile schedule (including every query rotation),
checks the full legal joint override domain, and records exact shortcut
counterexamples.  The battery and lesson census remain the authority checks.

Run from the packet root through the supplied runtime wrapper::

    python3 run_with_racket.py python3 \
      generators/00ed2544a15e/workspace/curriculum_probe.py \
      --sampled-draws-per-band 25 --out ../checks/curriculum-probe.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "00ed2544a15e"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
DIFFICULTIES: tuple[str | None, ...] = (None, "easy", "medium", "hard")
HEIGHTS = range(8, 13)
WIDTHS = range(9, 14)


def _load_generator(path: Path = GENERATOR_PATH):
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _label(difficulty: str | None) -> str:
    return "default" if difficulty is None else difficulty


def _pair(generator, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        "input": copy.deepcopy(grid),
        "output": generator.rule_mirror(grid),
    }


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _different_cells(
    left: list[list[int]], right: list[list[int]]
) -> list[dict[str, int]]:
    return [
        {"row": row, "col": col, "intended": left[row][col], "rival": right[row][col]}
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def _component_count(grid: list[list[int]]) -> int:
    """Count 4-connected nonzero same-color objects (the defect-lint metric)."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    count = 0
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            count += 1
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def build_report(
    *,
    generator,
    canonical_root: str | Path,
    seed: int = 20261004,
    sampled_draws_per_band: int = 25,
) -> dict[str, Any]:
    """Return a compact JSON-serializable report over the live contracts."""
    if type(sampled_draws_per_band) is not int or sampled_draws_per_band < 1:
        raise ValueError("sampled_draws_per_band must be a positive integer")

    canonical = canonical_pairs(TASK_ID, root=Path(canonical_root))
    canonical_mirror_failures: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical):
        actual = generator.rule_mirror(pair["input"])
        if actual != pair["output"]:
            canonical_mirror_failures.append(
                {
                    "pair_index": index,
                    "different_cells": _different_cells(pair["output"], actual),
                }
            )

    canonical_shortcuts: dict[str, Any] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_shortcuts[name] = {
            "matched_canonical_pairs": sum(matches),
            "canonical_pair_count": len(matches),
            "fits_all_canonical_pairs": all(matches),
        }

    schedule_len = len(generator.SCHEDULE_PROFILES)
    failed_windows: list[dict[str, Any]] = []
    rotation_failures: list[dict[str, Any]] = []
    surviving_competitor_windows: list[dict[str, Any]] = []
    cyclic_windows: list[dict[str, Any]] = []
    competitor_stats = {
        name: {"windows": 0, "refuted_windows": 0, "surviving_windows": 0}
        for name in generator.LESSON_COMPETITORS
    }

    for difficulty in DIFFICULTIES:
        band = _label(difficulty)
        for start in range(schedule_len):
            pairs = [
                _pair(
                    generator,
                    generator.generate(seed, start + offset, difficulty=difficulty),
                )
                for offset in range(generator.EXAMPLES_NEEDED + 1)
            ]
            demos = pairs[: generator.EXAMPLES_NEEDED]
            query = pairs[generator.EXAMPLES_NEEDED]
            reasons = generator.lesson_identifiable(demos, query)
            if reasons:
                failed_windows.append(
                    {"difficulty": band, "cyclic_start": start, "reasons": reasons}
                )

            surviving: list[str] = []
            refuted: list[str] = []
            for name, rival in generator.LESSON_COMPETITORS.items():
                stats = competitor_stats[name]
                stats["windows"] += 1
                survives = all(
                    rival(pair["input"]) == pair["output"] for pair in demos
                )
                if survives:
                    stats["surviving_windows"] += 1
                    surviving.append(name)
                    if rival(query["input"]) != query["output"]:
                        surviving_competitor_windows.append(
                            {
                                "difficulty": band,
                                "cyclic_start": start,
                                "competitor": name,
                            }
                        )
                else:
                    stats["refuted_windows"] += 1
                    refuted.append(name)

            for query_index, held_out in enumerate(pairs):
                rotated = [pair for index, pair in enumerate(pairs) if index != query_index]
                rotation_reasons = generator.lesson_identifiable(rotated, held_out)
                if rotation_reasons:
                    rotation_failures.append(
                        {
                            "difficulty": band,
                            "cyclic_start": start,
                            "query_index": query_index,
                            "reasons": rotation_reasons,
                        }
                    )

            cyclic_windows.append(
                {
                    "difficulty": band,
                    "cyclic_start": start,
                    "profiles": [
                        generator.schedule_profile(seed, start + offset, difficulty)
                        for offset in range(generator.EXAMPLES_NEEDED)
                    ],
                    "identifiable": not reasons,
                    "refuted_competitors": sorted(refuted),
                    "surviving_competitors": sorted(surviving),
                }
            )

    exact_axis_failures: list[dict[str, Any]] = []
    exact_axis_case_count = 0
    for difficulty in DIFFICULTIES:
        for height in HEIGHTS:
            for width in WIDTHS:
                for profile in generator.SCHEDULE_PROFILES:
                    exact_axis_case_count += 1
                    expected = {"grid_h": height, "grid_w": width, "profile": profile}
                    try:
                        grid = generator.generate(
                            seed,
                            exact_axis_case_count,
                            difficulty=difficulty,
                            **expected,
                        )
                        observed = generator.observe_overrides(grid)
                        errors = generator.self_check(
                            grid,
                            difficulty=difficulty,
                            meta={"overrides": expected},
                        )
                    except Exception as exc:  # report a complete domain audit
                        exact_axis_failures.append(
                            {
                                "difficulty": _label(difficulty),
                                "expected": expected,
                                "exception": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        continue
                    if observed != expected or errors:
                        exact_axis_failures.append(
                            {
                                "difficulty": _label(difficulty),
                                "expected": expected,
                                "observed": observed,
                                "self_check_errors": errors,
                            }
                        )

    sampled_hashes: set[str] = set()
    sampled_component_counts: list[int] = []
    sampled_profile_counts = {name: 0 for name in generator.SCHEDULE_PROFILES}
    replay_failures: list[dict[str, Any]] = []
    for difficulty in DIFFICULTIES:
        for index in range(sampled_draws_per_band):
            sample_seed = seed + 1000 * DIFFICULTIES.index(difficulty) + index
            grid = generator.generate(sample_seed, index, difficulty=difficulty)
            replay = generator.generate(sample_seed, index, difficulty=difficulty)
            if grid != replay or grid is replay:
                replay_failures.append(
                    {"difficulty": _label(difficulty), "sample_index": index}
                )
            sampled_hashes.add(_grid_hash(grid))
            sampled_component_counts.append(_component_count(grid))
            sampled_profile_counts[generator.observe_overrides(grid)["profile"]] += 1

    shortcut_witnesses: dict[str, Any] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        witness = None
        for profile_index, profile in enumerate(generator.SCHEDULE_PROFILES):
            grid = generator.generate(
                seed,
                profile_index,
                difficulty="easy",
                grid_h=8,
                grid_w=9,
                profile=profile,
            )
            intended = generator.rule_mirror(grid)
            rival_output = rival(grid)
            if intended != rival_output:
                witness = {
                    "seed": seed,
                    "sample_index": profile_index,
                    "difficulty": "easy",
                    "overrides": {"grid_h": 8, "grid_w": 9, "profile": profile},
                    "input_sha256": _grid_hash(grid),
                    "input": grid,
                    "intended_output": intended,
                    "rival_output": rival_output,
                    "different_cells": _different_cells(intended, rival_output),
                    "rival_differs": True,
                }
                break
        shortcut_witnesses[name] = witness or {
            "rival_differs": False,
            "error": "no ordinary profile witness found",
        }

    source_path = Path(generator.__file__).resolve()
    counts = sampled_component_counts
    return {
        "schema": "arcpuzzles-00ed2544a15e-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "rule_hash": generator.RULE_HASH,
        "seed": seed,
        "canonical_pair_count": len(canonical),
        "canonical_mirror_failures": canonical_mirror_failures,
        "canonical_shortcuts": canonical_shortcuts,
        "schedule_profiles": list(generator.SCHEDULE_PROFILES),
        "cyclic_start_count_per_band": schedule_len,
        "cyclic_windows": cyclic_windows,
        "failed_windows": failed_windows,
        "rotation_failures": rotation_failures,
        "lesson_competitors": competitor_stats,
        "surviving_competitor_windows": surviving_competitor_windows,
        "exact_axis_case_count": exact_axis_case_count,
        "exact_axis_failures": exact_axis_failures,
        "sampled_draws_per_band": sampled_draws_per_band,
        "sampled_unique_inputs": len(sampled_hashes),
        "sampled_profile_counts": sampled_profile_counts,
        "sampled_component_counts": {
            "minimum": min(counts),
            "maximum": max(counts),
            "values": sorted(set(counts)),
            "denominator": len(counts),
        },
        "deterministic_replay_failures": replay_failures,
        "shortcut_witnesses": shortcut_witnesses,
        "limitations": [
            "Finite checks cover declared rivals, not every conceivable learner hypothesis.",
            "The probe uses the Python rule_mirror; Racket authority is checked by the battery and apply receipts.",
        ],
    }


def _blocking_findings(report: dict[str, Any]) -> list[str]:
    findings = []
    for key in (
        "canonical_mirror_failures",
        "failed_windows",
        "rotation_failures",
        "surviving_competitor_windows",
        "exact_axis_failures",
        "deterministic_replay_failures",
    ):
        if report[key]:
            findings.append(key)
    for name, item in report["canonical_shortcuts"].items():
        if not item["fits_all_canonical_pairs"]:
            findings.append(f"canonical_shortcut_not_canonical:{name}")
    for name, item in report["shortcut_witnesses"].items():
        if not item["rival_differs"]:
            findings.append(f"missing_shortcut_witness:{name}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261004)
    parser.add_argument("--sampled-draws-per-band", type=int, default=25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    generator = _load_generator()
    report = build_report(
        generator=generator,
        canonical_root=find_root(__file__),
        seed=args.seed,
        sampled_draws_per_band=args.sampled_draws_per_band,
    )
    report["blocking_findings"] = _blocking_findings(report)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if report["blocking_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
