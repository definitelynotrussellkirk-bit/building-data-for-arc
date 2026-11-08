#!/usr/bin/env python3
"""Measure spurious lane-role, orientation, and palette correlations.

Run from any directory.  The probe fixes dimensions so it measures semantic
layout variation rather than dimensional variation, then emits a compact JSON
report suitable for before/after evidence.
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


def _normalize(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _lane_info(grid: list[list[int]]) -> list[dict[str, Any]]:
    analysis = gen._analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"generated invalid probe grid: {analysis['errors']}")
    return analysis["lanes"]


def collect(*, seed: int, draws: int, difficulty: str) -> dict[str, Any]:
    if draws < 1:
        raise ValueError("draws must be positive")
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard")

    split_positions: Counter[str] = Counter()
    split_slopes: Counter[str] = Counter()
    connected_shapes: Counter[str] = Counter()
    palette_modes: Counter[str] = Counter()
    canonical_anchor_slots: Counter[str] = Counter()
    anchor_block_violations = 0

    for block in range(draws // 3):
        flags = [
            gen._is_canonical_anchor(
                seed,
                block * 3 + slot,
                has_overrides=False,
            )
            for slot in range(3)
        ]
        if sum(flags) != 1:
            anchor_block_violations += 1
        elif any(flags):
            canonical_anchor_slots[str(flags.index(True))] += 1

    for sample_index in range(draws):
        grid = gen.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            grid_w=13,
            n_compartments=2,
            comp_h=3,
        )
        lanes = _lane_info(grid)
        split_lane_index = next(
            index for index, lane in enumerate(lanes) if len(lane["components"]) > 1
        )
        split_positions[str(split_lane_index)] += 1
        split_components = lanes[split_lane_index]["components"]
        singleton_points = sorted(
            obj["cells"][0] for obj in split_components if len(obj["cells"]) == 1
        )
        if len(singleton_points) < 2:
            raise ValueError("split witness did not contain at least two singleton components")
        slope = "down_right" if singleton_points[-1][1] > singleton_points[0][1] else "down_left"
        split_slopes[slope] += 1

        connected_lane = next(lane for lane in lanes if len(lane["components"]) == 1)
        shape = _normalize(connected_lane["components"][0]["cells"])
        connected_shapes[repr(shape)] += 1

    for sample_index in range(draws):
        grid = gen.generate(
            seed + 1,
            sample_index,
            difficulty=difficulty,
            grid_w=13,
            n_compartments=3,
            comp_h=3,
        )
        colors = [lane["colors"][0] for lane in _lane_info(grid)]
        mode = "reused" if len(set(colors)) < len(colors) else "distinct"
        palette_modes[mode] += 1

    generator_path = Path(gen.__file__).resolve()
    return {
        "schema": "f0d16ecf2012-correlation-probe-v2",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "seed": seed,
        "draws_per_probe": draws,
        "difficulty": difficulty,
        "split_positions_two_lane": dict(sorted(split_positions.items())),
        "split_slopes": dict(sorted(split_slopes.items())),
        "connected_witness_shapes": dict(sorted(connected_shapes.items())),
        "palette_modes_three_lane": dict(sorted(palette_modes.items())),
        "canonical_anchor_slots": dict(sorted(canonical_anchor_slots.items())),
        "anchor_block_violations": anchor_block_violations,
    }


def coverage_findings(report: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if set(report.get("split_positions_two_lane", {})) != {"0", "1"}:
        findings.append("split witness did not appear in both two-lane positions")
    if set(report.get("split_slopes", {})) != {"down_left", "down_right"}:
        findings.append("split witness did not cover both diagonal slopes")
    if len(report.get("connected_witness_shapes", {})) < 4:
        findings.append("fewer than four connected witness profiles were observed")
    if set(report.get("palette_modes_three_lane", {})) != {"distinct", "reused"}:
        findings.append("both distinct and reused lane-color palettes were not observed")
    if set(report.get("canonical_anchor_slots", {})) != {"0", "1", "2"}:
        findings.append("canonical anchors did not appear in all three block slots")
    if report.get("anchor_block_violations") != 0:
        findings.append("canonical anchor cadence was not exactly one per complete block")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261004)
    parser.add_argument("--draws", type=int, default=240)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="hard")
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
