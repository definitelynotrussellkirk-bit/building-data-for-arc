#!/usr/bin/env python3
"""Source-bound contract probe for ``aa0b08801e61``.

This is an authoring/maintenance tool, not label authority.  It reads the
selected generator through ``reviewer_support``, enumerates every legal joint
axis tuple in every production difficulty band, verifies the declared lesson
schedule under every held-out query position, checks every declared canonical
shortcut against the canonical pairs, and retains an exact generated witness.
Racket remains the authoritative source for labels; use ``arcpuzzles apply``
for a retained authority receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "aa0b08801e61"
BANDS = ("easy", "medium", "hard")


def _pair(module, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": module.rule_mirror(grid)}


def _canonical_shortcut_report(module, pairs):
    report: dict[str, dict[str, int]] = {}
    for name, shortcut in module.CANONICAL_SHORTCUTS.items():
        fits = sum(shortcut(pair["input"]) == pair["output"] for pair in pairs)
        report[name] = {"fits": fits, "pairs": len(pairs)}
    return report


def _shape_bank_report(module):
    failures: list[str] = []
    classes: dict[str, dict[str, int]] = {}
    owners: dict[object, tuple[str, int]] = {}
    declared_masks = canonical_masks = novel_masks = 0

    for class_name in sorted(module.SHAPE_BANKS):
        bank = tuple(module.SHAPE_BANKS[class_name])
        unique = len(set(bank))
        canonical = sum(shape in module._CANONICAL_MASKS for shape in bank)
        novel = len(bank) - canonical
        class_matches = sum(module._symmetry_class(shape) == class_name for shape in bank)
        connected = sum(module._is_4_connected(shape) for shape in bank)
        classes[class_name] = {
            "declared": len(bank),
            "unique": unique,
            "canonical": canonical,
            "novel": novel,
            "class_matches": class_matches,
            "connected": connected,
        }
        declared_masks += len(bank)
        canonical_masks += canonical
        novel_masks += novel

        if len(bank) != 3:
            failures.append(f"{class_name} bank declares {len(bank)} masks; expected 3")
        if unique != len(bank):
            failures.append(f"{class_name} bank contains duplicate masks")
        if not bank or bank[0] not in module._CANONICAL_MASKS:
            failures.append(f"{class_name} bank does not start with a canonical mask")
        if any(shape in module._CANONICAL_MASKS for shape in bank[1:]):
            failures.append(f"{class_name} bank leaks a canonical mask into teaching slots")
        if class_matches != len(bank):
            failures.append(f"{class_name} bank contains a mask from another symmetry class")
        if connected != len(bank):
            failures.append(f"{class_name} bank contains a disconnected mask")

        for index, shape in enumerate(bank):
            previous = owners.get(shape)
            if previous is not None:
                failures.append(
                    "mask reused by "
                    f"{previous[0]}[{previous[1]}] and {class_name}[{index}]"
                )
            else:
                owners[shape] = (class_name, index)

    return {
        "declared_masks": declared_masks,
        "unique_masks": len(owners),
        "canonical_masks": canonical_masks,
        "novel_masks": novel_masks,
        "classes": classes,
        "failures": failures,
    }


def _joint_override_report(module, seed: int):
    failures: list[dict[str, Any]] = []
    attempted = accepted = exact = self_check_passed = 0
    axis_triples: set[tuple[int, int, int]] = set()
    for band_index, band in enumerate(BANDS):
        for height in range(9, 16):
            for width in range(12, 19):
                for count in (3, 4):
                    attempted += 1
                    overrides = {
                        "grid_h": height,
                        "grid_w": width,
                        "n_objects": count,
                    }
                    sample_index = (
                        band_index * 10_000 + height * 100 + width * 3 + count
                    )
                    try:
                        grid = module.generate(
                            seed + band_index,
                            sample_index,
                            difficulty=band,
                            **overrides,
                        )
                    except Exception as exc:  # evidence should retain exact failures
                        failures.append(
                            {
                                "band": band,
                                "overrides": overrides,
                                "kind": "generation_error",
                                "detail": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        continue
                    accepted += 1
                    observed = module.observe_overrides(grid)
                    if observed == overrides:
                        exact += 1
                    else:
                        failures.append(
                            {
                                "band": band,
                                "overrides": overrides,
                                "kind": "inexact_override",
                                "observed": observed,
                            }
                        )
                    errors = module.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": overrides},
                    )
                    if not errors:
                        self_check_passed += 1
                    else:
                        failures.append(
                            {
                                "band": band,
                                "overrides": overrides,
                                "kind": "self_check",
                                "errors": errors,
                            }
                        )
                    axis_triples.add(
                        (observed["grid_h"], observed["grid_w"], observed["n_objects"])
                    )
    return {
        "attempted": attempted,
        "accepted": accepted,
        "exact": exact,
        "self_check_passed": self_check_passed,
        "unique_axis_triples": len(axis_triples),
        "failures": failures,
    }


def _schedule_report(module, seed: int):
    period = module.LESSON_SCHEDULE_PERIOD
    lessons = rotations = ambiguous_lessons = ambiguous_rotations = 0
    failures: list[dict[str, Any]] = []
    for band_index, band in enumerate(BANDS):
        for start in range(period):
            pairs = [
                _pair(
                    module,
                    module.generate(
                        seed + band_index * 1009 + start,
                        start + offset,
                        difficulty=band,
                    ),
                )
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            lessons += 1
            production_reasons = module.lesson_identifiable(
                pairs[: module.EXAMPLES_NEEDED],
                pairs[module.EXAMPLES_NEEDED],
            )
            if production_reasons:
                ambiguous_lessons += 1
                failures.append(
                    {
                        "band": band,
                        "start": start,
                        "query_index": module.EXAMPLES_NEEDED,
                        "scope": "ordered_production",
                        "reasons": production_reasons,
                    }
                )
            for query_index, query in enumerate(pairs):
                rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = module.lesson_identifiable(demos, query)
                if reasons:
                    ambiguous_rotations += 1
                    failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "scope": "query_rotation",
                            "reasons": reasons,
                        }
                    )
    return {
        "period": period,
        "bands": list(BANDS),
        "demonstrations_per_lesson": module.EXAMPLES_NEEDED,
        "lessons": lessons,
        "rotations": rotations,
        "ambiguous_lessons": ambiguous_lessons,
        "ambiguous_rotations": ambiguous_rotations,
        "failures": failures,
    }


def _default_support_report(module, seed: int):
    exact_by_band: dict[str, int] = {}
    envelope_by_band: dict[str, int] = {}
    unique_inputs_by_band: dict[str, int] = {}
    canonical_profiles = {(9, 12, 3), (9, 13, 3), (10, 13, 4), (10, 14, 4)}
    for band_index, band in enumerate(BANDS):
        exact = envelope = 0
        signatures = set()
        for index in range(20):
            grid = module.generate(seed + band_index * 100_003, index, difficulty=band)
            observed = module.observe_overrides(grid)
            profile = (
                observed["grid_h"],
                observed["grid_w"],
                observed["n_objects"],
            )
            exact += profile in canonical_profiles and module.strict_canonical_like(grid) == []
            envelope += (
                9 <= profile[0] <= 10
                and 12 <= profile[1] <= 14
                and 3 <= profile[2] <= 4
            )
            signatures.add(json.dumps(grid, separators=(",", ":")))
        exact_by_band[band] = exact
        envelope_by_band[band] = envelope
        unique_inputs_by_band[band] = len(signatures)
    return {
        "draws_per_band": 20,
        "exact_canonical_like_by_band": exact_by_band,
        "canonical_envelope_by_band": envelope_by_band,
        "unique_inputs_by_band": unique_inputs_by_band,
    }


def _counterexample(module, seed: int):
    shortcut_name, shortcut = next(iter(module.CANONICAL_SHORTCUTS.items()))
    for sample_index in range(module.LESSON_SCHEDULE_PERIOD * 3):
        grid = module.generate(seed, sample_index, difficulty="medium")
        intended = module.rule_mirror(grid)
        rival = shortcut(grid)
        if intended != rival:
            differing = [
                [row, col]
                for row in range(len(grid))
                for col in range(len(grid[0]))
                if intended[row][col] != rival[row][col]
            ]
            return {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": "medium",
                "profile": module.schedule_profile(seed, sample_index, "medium"),
                "shortcut": shortcut_name,
                "self_check": module.self_check(grid),
                "shortcut_disagrees": True,
                "differing_cells": differing,
                "input": grid,
                "intended_output": intended,
                "shortcut_output": rival,
            }
    return {
        "seed": seed,
        "shortcut": shortcut_name,
        "self_check": ["no shortcut-breaking generated witness found"],
        "shortcut_disagrees": False,
    }


def analyze(seed: int = 20261012) -> dict[str, Any]:
    root = find_root(__file__)
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    pairs = canonical_pairs(TASK_ID, root=root)
    canonical_shortcuts = _canonical_shortcut_report(module, pairs)
    shape_banks = _shape_bank_report(module)
    joint_overrides = _joint_override_report(module, seed)
    schedule = _schedule_report(module, seed)
    default_support = _default_support_report(module, seed)
    counterexample = _counterexample(module, seed)

    failures: list[str] = []
    for name, row in canonical_shortcuts.items():
        if row["fits"] != row["pairs"]:
            failures.append(f"declared canonical shortcut {name!r} does not fit all pairs")
    if shape_banks["failures"]:
        failures.append("shape-bank declaration contract failed")
    if joint_overrides["failures"]:
        failures.append("joint override enumeration produced failures")
    if schedule["failures"]:
        failures.append("declared schedule has ambiguous production/rotation cases")
    if not counterexample["shortcut_disagrees"] or counterexample["self_check"]:
        failures.append("no lawful generated shortcut counterexample found")

    return {
        "schema": "aa0b08801e61-semantic-probe-v2",
        "task_id": TASK_ID,
        "generator": {
            "path": source_path.relative_to(root).as_posix(),
            "sha256": source_sha256,
            "version": module.VERSION,
            "rule_hash": module.RULE_HASH,
        },
        "seed": seed,
        "canonical_pairs": len(pairs),
        "canonical_shortcuts": canonical_shortcuts,
        "shape_banks": shape_banks,
        "joint_overrides": joint_overrides,
        "schedule": schedule,
        "default_support": default_support,
        "counterexample": counterexample,
        "limitations": [
            "Python rule_mirror is diagnostic; retained labels must be checked with Racket.",
            "Finite declared-rival checks do not prove universal lesson identifiability.",
            "Schedule enumeration covers the declared period at one deterministic seed per start/band.",
        ],
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261012)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = analyze(seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "generator_sha256": report["generator"]["sha256"],
                "joint_overrides": report["joint_overrides"]["attempted"],
                "rotations": report["schedule"]["rotations"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
