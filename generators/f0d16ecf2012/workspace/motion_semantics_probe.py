#!/usr/bin/env python3
"""Probe static-source-footprint motion and movable-color support.

The canonical Racket rule moves each object on a board that still contains the
object's original cells.  A gapped connected shape can therefore stop before a
wall when its next translation would re-enter a vacated source cell.  This tool
checks that the canonical examples expose that behavior and that generated
scenes teach both source-footprint stopping and ordinary wall docking.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "f0d16ecf2012"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
for path in (REPO_ROOT, REPO_ROOT / "shared/runtime"):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

gen = importlib.import_module(f"generators.{TASK_ID}.generator")


def _translation_distance(
    original: list[tuple[int, int]],
    moved: list[tuple[int, int]],
) -> int:
    """Return a rigid east-translation distance, failing on distortion."""
    if len(original) != len(moved):
        raise ValueError("motion changed component cell count")
    original_set = set(original)
    moved_set = set(moved)
    candidates = {
        moved_col - original_col
        for original_row, original_col in original_set
        for moved_row, moved_col in moved_set
        if moved_row == original_row
    }
    for distance in sorted(candidates):
        if distance >= 0 and {
            (row, col + distance) for row, col in original_set
        } == moved_set:
            return distance
    raise ValueError("motion was not a rigid east translation")


def _distances(
    grid: list[list[int]],
    obj: dict[str, Any],
) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    walls = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    }
    original = list(obj["cells"])
    authority_moved = gen._move_component(
        original,
        h=h,
        w=w,
        walls=walls,
        steps=None,
    )
    wall_only_moved = gen._move_component_wall_only(
        original,
        h=h,
        w=w,
        walls=walls,
    )
    return (
        _translation_distance(original, authority_moved),
        _translation_distance(original, wall_only_moved),
    )


def _canonical_inputs() -> list[list[list[int]]]:
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") != TASK_ID:
                continue
            pairs = list(record["train"]) + [record["test"]]
            return [
                [[int(value) for value in row] for row in pair["input"]]
                for pair in pairs
            ]
    raise ValueError(f"canonical task {TASK_ID} not found")


def collect(*, seed: int, draws: int, difficulty: str) -> dict[str, Any]:
    if draws < 1:
        raise ValueError("draws must be positive")
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard")

    canonical_pairs: Counter[str] = Counter()
    canonical_source_blocked: list[dict[str, Any]] = []
    for pair_index, grid in enumerate(_canonical_inputs()):
        for object_index, obj in enumerate(gen._components(grid)):
            authority_distance, wall_only_distance = _distances(grid, obj)
            canonical_pairs[f"{authority_distance}/{wall_only_distance}"] += 1
            if authority_distance < wall_only_distance:
                canonical_source_blocked.append(
                    {
                        "pair_index": pair_index,
                        "object_index": object_index,
                        "color": obj["color"],
                        "cells": obj["cells"],
                        "authority_distance": authority_distance,
                        "wall_only_distance": wall_only_distance,
                    }
                )

    generated_distance_pairs: Counter[str] = Counter()
    generated_colors: Counter[str] = Counter()
    scenes_with_source_blocking = 0
    scenes_with_wall_docking = 0
    scenes_with_both = 0
    scenes_diverging_from_wall_only = 0

    for sample_index in range(draws):
        grid = gen.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            grid_w=13,
            n_compartments=2,
            comp_h=3,
        )
        source_blocked = False
        wall_docked = False
        for obj in gen._components(grid):
            authority_distance, wall_only_distance = _distances(grid, obj)
            generated_distance_pairs[
                f"{authority_distance}/{wall_only_distance}"
            ] += 1
            generated_colors[str(obj["color"])] += 1
            source_blocked |= authority_distance < wall_only_distance
            wall_docked |= (
                authority_distance == wall_only_distance
                and authority_distance >= 2
            )
        scenes_with_source_blocking += int(source_blocked)
        scenes_with_wall_docking += int(wall_docked)
        scenes_with_both += int(source_blocked and wall_docked)
        scenes_diverging_from_wall_only += int(
            gen.rule_mirror(grid) != gen._rival_ignore_source_footprint(grid)
        )

    generator_path = Path(gen.__file__).resolve()
    return {
        "schema": "f0d16ecf2012-motion-semantics-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seed": seed,
        "draws": draws,
        "difficulty": difficulty,
        "canonical_distance_pairs": dict(sorted(canonical_pairs.items())),
        "canonical_source_blocked": canonical_source_blocked,
        "generated_distance_pairs": dict(sorted(generated_distance_pairs.items())),
        "generated_colors": dict(sorted(generated_colors.items())),
        "scenes_with_source_blocking": scenes_with_source_blocking,
        "scenes_with_wall_docking": scenes_with_wall_docking,
        "scenes_with_both_motion_regimes": scenes_with_both,
        "scenes_diverging_from_wall_only": scenes_diverging_from_wall_only,
    }


def coverage_findings(report: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    draws = int(report.get("draws", 0))
    if not report.get("canonical_source_blocked"):
        findings.append("canonical examples did not expose source-footprint blocking")
    if report.get("scenes_with_source_blocking") != draws:
        findings.append("not every generated scene contained a source-blocked component")
    if report.get("scenes_with_wall_docking") != draws:
        findings.append("not every generated scene contained an ordinary wall-docking component")
    if report.get("scenes_with_both_motion_regimes") != draws:
        findings.append("generated scenes did not pair both motion regimes")
    if report.get("scenes_diverging_from_wall_only") != draws:
        findings.append("wall-only docking remained answer-equivalent on some scenes")
    source_stop_distances = {
        int(label.split("/", 1)[0])
        for label in report.get("generated_distance_pairs", {})
        if int(label.split("/", 1)[0]) < int(label.split("/", 1)[1])
    }
    if source_stop_distances != {1, 2}:
        findings.append("source-footprint witnesses did not cover stop distances 1 and 2")
    if set(report.get("generated_colors", {})) != {str(value) for value in range(1, 9)}:
        findings.append("generated support did not cover every movable ARC color 1..8")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--draws", type=int, default=240)
    parser.add_argument(
        "--difficulty",
        choices=("easy", "medium", "hard"),
        default="hard",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = collect(seed=args.seed, draws=args.draws, difficulty=args.difficulty)
    report["coverage_findings"] = coverage_findings(report)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 1 if report["coverage_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
