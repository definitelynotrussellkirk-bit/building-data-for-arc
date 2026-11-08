#!/usr/bin/env python3
"""Detect axis-position shortcuts in generator 4ee97d4d2321.

The probe is intentionally independent of the generator's declared rival.  It
samples the default curriculum, measures joint support for source_mode and
axis_offset, and asks whether a solver that guesses the source side solely from
the axis displacement can survive any full lesson window.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, Sequence

SCRIPT_PATH = Path(__file__).resolve()
GENERATOR_PATH = SCRIPT_PATH.parents[1] / "generator.py"
REPO_ROOT = SCRIPT_PATH.parents[3]
BANDS = ("easy", "medium", "hard")


def load_generator(path: Path = GENERATOR_PATH) -> ModuleType:
    """Load the reviewed generator directly from its source path."""
    repo_root = path.resolve().parents[2]
    runtime_root = repo_root / "shared" / "runtime"
    for import_root in (runtime_root, repo_root):
        import_text = str(import_root)
        if import_text not in sys.path:
            sys.path.insert(0, import_text)
    spec = importlib.util.spec_from_file_location(
        "review_probe_generator_4ee97d4d2321", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def axis_offset_side_shortcut(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Mirror only the side guessed from axis displacement.

    This models the pre-repair shortcut exactly, without importing any rival
    implementation from the generator under review.
    """
    height, width = len(grid), len(grid[0])
    axes = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if not axes:
        raise ValueError("grid has no full-height cyan axis")
    axis = axes[0]
    offset = axis - (width - 1) // 2

    if offset == 0:
        selected_side = "both"
    elif abs(offset) == 1:
        selected_side = "left" if offset < 0 else "right"
    else:
        selected_side = "right" if offset < 0 else "left"

    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value in (0, 8):
                continue
            if selected_side == "left" and col > axis:
                continue
            if selected_side == "right" and col < axis:
                continue
            mirror_col = 2 * axis - col
            if 0 <= mirror_col < width:
                out[row][mirror_col] = value
    return out


def _pair_key(source_mode: str, axis_offset: int) -> str:
    return f"{source_mode}@{axis_offset:+d}"


def analyze(
    *,
    draws_per_band: int = 100,
    seed: int = 8700,
    generator: ModuleType | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable shortcut audit report."""
    if draws_per_band < 20:
        raise ValueError("draws_per_band must be at least 20")
    gen = generator or load_generator()
    expected_pairs = {
        (mode, offset)
        for mode in gen.SOURCE_MODES
        for offset in gen.AXIS_OFFSETS
    }
    window_size = int(gen.EXAMPLES_NEEDED)
    report_bands: dict[str, Any] = {}
    all_passed = True

    for band in BANDS:
        grids = [
            gen.generate(seed, index, difficulty=band)
            for index in range(draws_per_band + window_size - 1)
        ]
        observations = [
            gen.observe_overrides(grid) for grid in grids[:draws_per_band]
        ]
        joint_counts = Counter(
            (row["source_mode"], int(row["axis_offset"]))
            for row in observations
        )
        agreements = [
            axis_offset_side_shortcut(grid) == gen.rule_mirror(grid)
            for grid in grids[:draws_per_band]
        ]
        surviving_windows = [
            start
            for start in range(draws_per_band)
            if all(
                axis_offset_side_shortcut(grid) == gen.rule_mirror(grid)
                for grid in grids[start : start + window_size]
            )
        ]
        observed_pairs = set(joint_counts)
        band_passed = (
            observed_pairs == expected_pairs and not surviving_windows
        )
        all_passed = all_passed and band_passed
        report_bands[band] = {
            "passed": band_passed,
            "draws": draws_per_band,
            "distinct_joint_pairs": len(observed_pairs),
            "expected_joint_pairs": len(expected_pairs),
            "missing_joint_pairs": sorted(
                _pair_key(mode, offset)
                for mode, offset in expected_pairs - observed_pairs
            ),
            "joint_counts": {
                _pair_key(mode, offset): count
                for (mode, offset), count in sorted(joint_counts.items())
            },
            "shortcut_agreements": sum(agreements),
            "shortcut_agreement_fraction": sum(agreements) / len(agreements),
            "lesson_windows_checked": draws_per_band,
            "surviving_lesson_windows": surviving_windows,
        }

    counterexample = gen.generate(
        seed,
        0,
        difficulty="medium",
        source_mode="both",
        axis_offset=1,
    )
    shortcut_refuted = (
        axis_offset_side_shortcut(counterexample)
        != gen.rule_mirror(counterexample)
    )
    all_passed = all_passed and shortcut_refuted

    return {
        "task_id": getattr(gen, "TASK_ID", "4ee97d4d2321"),
        "generator_version": getattr(gen, "VERSION", None),
        "seed": seed,
        "draws_per_band": draws_per_band,
        "window_size": window_size,
        "probe": "axis_offset_side_shortcut",
        "passed": all_passed,
        "bands": report_bands,
        "explicit_counterexample": {
            "overrides": {"source_mode": "both", "axis_offset": 1},
            "shortcut_refuted": shortcut_refuted,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=8700)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = analyze(draws_per_band=args.draws_per_band, seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
