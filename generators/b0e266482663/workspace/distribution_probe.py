#!/usr/bin/env python3
"""Measure whether b0e266482663-style ray data teaches the actual rule.

The probe is intentionally rule-structural rather than task-implementation
specific: it reads only the generated input grid.  It can therefore compare an
older generator snapshot with a candidate generator using identical seeds.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence

BANDS = ("easy", "medium", "hard")
CANONICAL_SHAPES = {(7, 8), (8, 9), (9, 10)}
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and non-empty")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid contains a non-ARC color")
    return len(grid), width


def analyze_grid(grid: list[list[int]]) -> dict[str, int | bool]:
    """Return observable curriculum features for a ray/blocker input grid."""
    height, width = _validate_grid(grid)
    row_shooters = {row for row in range(1, height) if grid[row][0] == 2}
    col_shooters = {col for col in range(1, width) if grid[0][col] == 3}
    blockers = {
        (row, col)
        for row in range(1, height)
        for col in range(1, width)
        if grid[row][col] == 9
    }

    horizontal_cells: set[tuple[int, int]] = set()
    horizontal_stops: set[tuple[int, int]] = set()
    for row in row_shooters:
        for col in range(1, width):
            if grid[row][col] == 9:
                if col < width - 1 and any(
                    grid[row][later] != 9 for later in range(col + 1, width)
                ):
                    horizontal_stops.add((row, col))
                break
            horizontal_cells.add((row, col))

    vertical_cells: set[tuple[int, int]] = set()
    vertical_stops: set[tuple[int, int]] = set()
    for col in col_shooters:
        for row in range(1, height):
            if grid[row][col] == 9:
                if row < height - 1 and any(
                    grid[later][col] != 9 for later in range(row + 1, height)
                ):
                    vertical_stops.add((row, col))
                break
            vertical_cells.add((row, col))

    nonlowest_shooter_crossings = 0
    sorted_rows = sorted(row_shooters)
    sorted_cols = sorted(col_shooters)
    if len(sorted_rows) >= 2 and len(sorted_cols) >= 2:
        nonlowest_shooter_crossings = sum(
            (row, col) in horizontal_cells and (row, col) in vertical_cells
            for row in sorted_rows[1:]
            for col in sorted_cols[1:]
        )
    stopped_rows = {row for row, _ in horizontal_stops}
    stopped_cols = {col for _, col in vertical_stops}
    extreme_row_stops = (
        len(sorted_rows) >= 4
        and {sorted_rows[0], sorted_rows[-1]} <= stopped_rows
    )
    extreme_col_stops = (
        len(sorted_cols) >= 4
        and {sorted_cols[0], sorted_cols[-1]} <= stopped_cols
    )

    return {
        "height": height,
        "width": width,
        "row_shooters": len(row_shooters),
        "col_shooters": len(col_shooters),
        "productive_row_shooters": sum(grid[row][1] != 9 for row in row_shooters),
        "productive_col_shooters": sum(grid[1][col] != 9 for col in col_shooters),
        "blockers": len(blockers),
        "active_horizontal_stop": bool(horizontal_stops),
        "active_vertical_stop": bool(vertical_stops),
        "adjacent_row_shooter": 1 in row_shooters,
        "adjacent_col_shooter": 1 in col_shooters,
        "first_step_horizontal_stop": any(col == 1 for _, col in horizontal_stops),
        "first_step_vertical_stop": any(row == 1 for row, _ in vertical_stops),
        "horizontal_only_cells": len(horizontal_cells - vertical_cells),
        "vertical_only_cells": len(vertical_cells - horizontal_cells),
        "crossing_cells": len(horizontal_cells & vertical_cells),
        "nonlowest_shooter_crossings": nonlowest_shooter_crossings,
        "lowest_and_highest_row_stops": extreme_row_stops,
        "lowest_and_highest_col_stops": extreme_col_stops,
    }


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _load_generator(path: Path) -> ModuleType:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    name = "distribution_probe_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "generate", None)):
        raise TypeError(f"{path} does not expose generate()")
    return module


def _counter_json(counter: Counter[Any]) -> dict[str, int]:
    return {
        str(key): int(value)
        for key, value in sorted(counter.items(), key=lambda item: str(item[0]))
    }


def _safe_profile(module: ModuleType, seed: int, sample_index: int, band: str) -> str | None:
    profile = getattr(module, "schedule_profile", None)
    if not callable(profile):
        return None
    try:
        value = profile(seed, sample_index, band)
    except TypeError:
        value = profile(seed, sample_index)
    return value if isinstance(value, str) else repr(value)


def _render_with_shooter_subset(
    grid: list[list[int]],
    keep_rows,
    keep_cols,
) -> list[list[int]]:
    """Independent ray renderer with a selectable subset of edge markers."""
    height, width = _validate_grid(grid)
    rows = sorted(row for row in range(1, height) if grid[row][0] == 2)
    cols = sorted(col for col in range(1, width) if grid[0][col] == 3)
    active_rows = set(keep_rows(rows))
    active_cols = set(keep_cols(cols))
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 9:
                continue
            horizontal = (
                col >= 1
                and row in active_rows
                and all(grid[row][cc] != 9 for cc in range(1, col + 1))
            )
            vertical = (
                row >= 1
                and col in active_cols
                and all(grid[rr][col] != 9 for rr in range(1, row + 1))
            )
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output


_SHOOTER_SHORTCUTS = {
    "lowest_row_only": (lambda rows: rows[:1], lambda cols: cols),
    "highest_row_only": (lambda rows: rows[-1:], lambda cols: cols),
    "lowest_col_only": (lambda rows: rows, lambda cols: cols[:1]),
    "highest_col_only": (lambda rows: rows, lambda cols: cols[-1:]),
    "first_two_rows_only": (lambda rows: rows[:2], lambda cols: cols),
    "last_two_rows_only": (lambda rows: rows[-2:], lambda cols: cols),
    "first_two_cols_only": (lambda rows: rows, lambda cols: cols[:2]),
    "last_two_cols_only": (lambda rows: rows, lambda cols: cols[-2:]),
    "first_three_rows_only": (lambda rows: rows[:3], lambda cols: cols),
    "last_three_rows_only": (lambda rows: rows[-3:], lambda cols: cols),
    "first_three_cols_only": (lambda rows: rows, lambda cols: cols[:3]),
    "last_three_cols_only": (lambda rows: rows, lambda cols: cols[-3:]),
}


def _render_cyan_only_on_lowest_axes(
    grid: list[list[int]],
    fallback: int,
) -> list[list[int]]:
    """Render the rival where secondary-by-secondary crossings are not cyan."""
    height, width = _validate_grid(grid)
    rows = sorted(row for row in range(1, height) if grid[row][0] == 2)
    cols = sorted(col for col in range(1, width) if grid[0][col] == 3)
    output = _render_with_shooter_subset(
        grid, lambda candidates: candidates, lambda candidates: candidates
    )
    for row in rows[1:]:
        for col in cols[1:]:
            if grid[row][col] == 9:
                continue
            horizontal = all(
                grid[row][cc] != 9 for cc in range(1, col + 1)
            )
            vertical = all(
                grid[rr][col] != 9 for rr in range(1, row + 1)
            )
            if horizontal and vertical:
                output[row][col] = fallback
    return output


_CROSSING_SHORTCUTS = {
    "cyan_only_lowest_axes_horizontal": lambda grid: (
        _render_cyan_only_on_lowest_axes(grid, 2)
    ),
    "cyan_only_lowest_axes_vertical": lambda grid: (
        _render_cyan_only_on_lowest_axes(grid, 3)
    ),
}


def _render_with_blocker_scope(
    grid: list[list[int]],
    respect_rows,
    respect_cols,
) -> list[list[int]]:
    """Render a rival where only selected shooters stop at blockers."""
    height, width = _validate_grid(grid)
    rows = sorted(row for row in range(1, height) if grid[row][0] == 2)
    cols = sorted(col for col in range(1, width) if grid[0][col] == 3)
    blocked_rows = set(respect_rows(rows))
    blocked_cols = set(respect_cols(cols))
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 9:
                continue
            horizontal = (
                col >= 1
                and row in rows
                and (
                    row not in blocked_rows
                    or all(grid[row][cc] != 9 for cc in range(1, col + 1))
                )
            )
            vertical = (
                row >= 1
                and col in cols
                and (
                    col not in blocked_cols
                    or all(grid[rr][col] != 9 for rr in range(1, row + 1))
                )
            )
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output


_BLOCKER_SCOPE_SHORTCUTS = {
    "first_three_rows_respect_blockers": (
        lambda rows: rows[:3],
        lambda cols: cols,
    ),
    "last_three_rows_respect_blockers": (
        lambda rows: rows[-3:],
        lambda cols: cols,
    ),
    "first_three_cols_respect_blockers": (
        lambda rows: rows,
        lambda cols: cols[:3],
    ),
    "last_three_cols_respect_blockers": (
        lambda rows: rows,
        lambda cols: cols[-3:],
    ),
}


def shooter_shortcut_window_census(
    module: ModuleType,
    band: str,
    *,
    seed: int,
    starts: int = 12,
) -> dict[str, Any]:
    """Independently test fixed-cardinality shooter shortcuts over 3-demo windows."""
    if starts < 1:
        raise ValueError("starts must be positive")
    refuted: Counter[str] = Counter()
    failures: dict[str, list[dict[str, Any]]] = {}
    for start in range(starts):
        grids = [
            module.generate(seed, start + offset, difficulty=band)
            for offset in range(3)
        ]
        truths = [
            _render_with_shooter_subset(grid, lambda rows: rows, lambda cols: cols)
            for grid in grids
        ]
        for name, (keep_rows, keep_cols) in _SHOOTER_SHORTCUTS.items():
            differs = any(
                _render_with_shooter_subset(grid, keep_rows, keep_cols) != truth
                for grid, truth in zip(grids, truths)
            )
            if differs:
                refuted[name] += 1
                continue
            examples = failures.setdefault(name, [])
            if len(examples) < 4:
                examples.append(
                    {
                        "start": start,
                        "profiles": [
                            _safe_profile(module, seed, start + offset, band)
                            for offset in range(3)
                        ],
                        "features": [analyze_grid(grid) for grid in grids],
                    }
                )
        for name, render in _CROSSING_SHORTCUTS.items():
            differs = any(
                render(grid) != truth
                for grid, truth in zip(grids, truths)
            )
            if differs:
                refuted[name] += 1
                continue
            examples = failures.setdefault(name, [])
            if len(examples) < 4:
                examples.append(
                    {
                        "start": start,
                        "profiles": [
                            _safe_profile(module, seed, start + offset, band)
                            for offset in range(3)
                        ],
                        "features": [analyze_grid(grid) for grid in grids],
                    }
                )
        for name, (respect_rows, respect_cols) in _BLOCKER_SCOPE_SHORTCUTS.items():
            differs = any(
                _render_with_blocker_scope(grid, respect_rows, respect_cols)
                != truth
                for grid, truth in zip(grids, truths)
            )
            if differs:
                refuted[name] += 1
                continue
            examples = failures.setdefault(name, [])
            if len(examples) < 4:
                examples.append(
                    {
                        "start": start,
                        "profiles": [
                            _safe_profile(module, seed, start + offset, band)
                            for offset in range(3)
                        ],
                        "features": [analyze_grid(grid) for grid in grids],
                    }
                )
    shortcut_names = (
        tuple(_SHOOTER_SHORTCUTS)
        + tuple(_CROSSING_SHORTCUTS)
        + tuple(_BLOCKER_SCOPE_SHORTCUTS)
    )
    return {
        "checked": starts,
        "refuted": {name: int(refuted[name]) for name in shortcut_names},
        "failures": failures,
    }


def _lesson_window_census(module: ModuleType, band: str, seed: int) -> dict[str, Any] | None:
    identifiable = getattr(module, "lesson_identifiable", None)
    mirror = getattr(module, "rule_mirror", None)
    if not callable(identifiable) or not callable(mirror):
        return None
    checked = passed = 0
    failures: list[dict[str, Any]] = []
    for start in range(12):
        grids = [
            module.generate(seed, start + offset, difficulty=band)
            for offset in range(4)
        ]
        pairs = [{"input": grid, "output": mirror(grid)} for grid in grids]
        reasons = identifiable(pairs[:3], pairs[3])
        checked += 1
        if not reasons:
            passed += 1
        elif len(failures) < 4:
            failures.append({"start": start, "reasons": list(reasons)})
    return {"checked": checked, "passed": passed, "failures": failures}


def census(module: ModuleType, *, draws: int, seed_base: int) -> dict[str, Any]:
    if draws < 1:
        raise ValueError("draws must be positive")
    report: dict[str, Any] = {"draws_per_band": draws, "bands": {}}
    for band_index, band in enumerate(BANDS):
        unique: set[tuple[tuple[int, ...], ...]] = set()
        shapes: Counter[str] = Counter()
        rows: Counter[int] = Counter()
        cols: Counter[int] = Counter()
        productive_rows: Counter[int] = Counter()
        productive_cols: Counter[int] = Counter()
        blockers: Counter[int] = Counter()
        profiles: Counter[str] = Counter()
        hits: Counter[str] = Counter()
        errors: list[str] = []
        self_check_failures: Counter[str] = Counter()
        deterministic_mismatches = 0

        for index in range(draws):
            seed = seed_base + band_index * 1_000_000 + index
            sample_index = index
            try:
                grid = module.generate(seed, sample_index, difficulty=band)
                features = analyze_grid(grid)
            except Exception as exc:  # evidence probe: retain, do not abort census
                if len(errors) < 8:
                    errors.append(
                        f"index={index} seed={seed}: {type(exc).__name__}: {exc}"
                    )
                continue

            unique.add(_freeze(grid))
            shape = (int(features["height"]), int(features["width"]))
            shapes[f"{shape[0]}x{shape[1]}"] += 1
            rows[int(features["row_shooters"])] += 1
            cols[int(features["col_shooters"])] += 1
            productive_rows[int(features["productive_row_shooters"])] += 1
            productive_cols[int(features["productive_col_shooters"])] += 1
            blockers[int(features["blockers"])] += 1
            profile = _safe_profile(module, seed, sample_index, band)
            if profile is not None:
                profiles[profile] += 1

            if shape in CANONICAL_SHAPES:
                hits["canonical_shape"] += 1
            for key in (
                "active_horizontal_stop",
                "active_vertical_stop",
                "adjacent_row_shooter",
                "adjacent_col_shooter",
                "first_step_horizontal_stop",
                "first_step_vertical_stop",
            ):
                if bool(features[key]):
                    hits[key] += 1
            if bool(features["active_horizontal_stop"]) and bool(
                features["active_vertical_stop"]
            ):
                hits["both_stop_directions"] += 1
            if bool(features["adjacent_row_shooter"]) and bool(
                features["adjacent_col_shooter"]
            ):
                hits["adjacent_shooters_both_edges"] += 1
            if bool(features["first_step_horizontal_stop"]) and bool(
                features["first_step_vertical_stop"]
            ):
                hits["first_step_stops_both_axes"] += 1
            if int(features["productive_row_shooters"]) >= 2:
                hits["multiple_productive_row_shooters"] += 1
            if int(features["productive_col_shooters"]) >= 2:
                hits["multiple_productive_col_shooters"] += 1
            if (
                int(features["productive_row_shooters"]) >= 2
                and int(features["productive_col_shooters"]) >= 2
            ):
                hits["multiple_productive_shooters_both_axes"] += 1
            if int(features["productive_row_shooters"]) >= 3:
                hits["three_productive_row_shooters"] += 1
            if int(features["productive_col_shooters"]) >= 3:
                hits["three_productive_col_shooters"] += 1
            if (
                int(features["productive_row_shooters"]) >= 3
                and int(features["productive_col_shooters"]) >= 3
            ):
                hits["three_productive_shooters_both_axes"] += 1
            if int(features["productive_row_shooters"]) >= 4:
                hits["four_productive_row_shooters"] += 1
            if int(features["productive_col_shooters"]) >= 4:
                hits["four_productive_col_shooters"] += 1
            if (
                int(features["productive_row_shooters"]) >= 4
                and int(features["productive_col_shooters"]) >= 4
            ):
                hits["four_productive_shooters_both_axes"] += 1
            if int(features["nonlowest_shooter_crossings"]) > 0:
                hits["nonlowest_shooter_crossing"] += 1
            if bool(features["lowest_and_highest_row_stops"]):
                hits["lowest_and_highest_row_stops"] += 1
            if bool(features["lowest_and_highest_col_stops"]):
                hits["lowest_and_highest_col_stops"] += 1
            if (
                int(features["horizontal_only_cells"]) > 0
                and int(features["vertical_only_cells"]) > 0
                and int(features["crossing_cells"]) > 0
            ):
                hits["all_output_branches_visible"] += 1

            self_check = getattr(module, "self_check", None)
            if callable(self_check):
                try:
                    reasons = self_check(grid, difficulty=band)
                except TypeError:
                    reasons = self_check(grid)
                except Exception as exc:
                    self_check_failures[f"raised {type(exc).__name__}: {exc}"] += 1
                else:
                    for reason in reasons or ():
                        self_check_failures[str(reason)] += 1

            if index < min(draws, 50):
                replay = module.generate(seed, sample_index, difficulty=band)
                deterministic_mismatches += replay != grid

        successful = draws - len(errors)
        rates = {
            key: (value / successful if successful else 0.0)
            for key, value in sorted(hits.items())
        }
        lesson_seed = seed_base + 9_000_000 + band_index
        lesson = _lesson_window_census(module, band, lesson_seed)
        shooter_shortcuts = shooter_shortcut_window_census(
            module, band, seed=lesson_seed, starts=12
        )
        report["bands"][band] = {
            "planned": draws,
            "successful": successful,
            "generation_error_examples": errors,
            "unique_grids": len(unique),
            "unique_rate": len(unique) / successful if successful else 0.0,
            "feature_hits": dict(sorted(hits.items())),
            "feature_rates": rates,
            "shape_histogram": _counter_json(shapes),
            "row_shooter_histogram": _counter_json(rows),
            "col_shooter_histogram": _counter_json(cols),
            "productive_row_shooter_histogram": _counter_json(productive_rows),
            "productive_col_shooter_histogram": _counter_json(productive_cols),
            "blocker_histogram": _counter_json(blockers),
            "schedule_profiles": _counter_json(profiles),
            "self_check_failures": _counter_json(self_check_failures),
            "deterministic_mismatches_first_50": deterministic_mismatches,
            "three_demo_lesson_windows": lesson,
            "independent_shooter_shortcut_windows": shooter_shortcuts,
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument("--seed-base", type=int, default=20261002)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    module = _load_generator(args.generator)
    payload = {
        "schema": "b0e266482663-distribution-probe-v6",
        "generator_path": str(args.generator),
        "generator_sha256": hashlib.sha256(args.generator.read_bytes()).hexdigest(),
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "census": census(module, draws=args.draws, seed_base=args.seed_base),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
