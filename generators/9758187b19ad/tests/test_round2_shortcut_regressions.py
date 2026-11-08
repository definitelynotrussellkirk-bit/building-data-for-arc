"""Second-pass regressions for canonical-feature lesson shortcuts."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest


TASK_ID = "9758187b19ad"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent


def _prepare_import_path() -> None:
    for parent in HERE.parents:
        source_runtime = parent / "shared" / "runtime"
        if (source_runtime / "puzzle_generators").is_dir():
            sys.path.insert(0, str(source_runtime))
            return
        if (parent / "puzzle_generators").is_dir():
            sys.path.insert(0, str(parent))
            return
    raise RuntimeError("could not locate puzzle_generators runtime")


def _load_generator():
    _prepare_import_path()
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"review_generator_round2_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_path() -> Path:
    for parent in HERE.parents:
        for path in (
            parent / "shared" / "data" / "canonical" / "puzzles.jsonl",
            parent / "data" / "canonical" / "puzzles.jsonl",
        ):
            if path.is_file():
                return path
    raise RuntimeError("could not locate canonical puzzles.jsonl")


def _canonical_pairs():
    for line in _canonical_path().read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        yield from row["train"]
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        yield from test


def _blank(grid):
    return [[0 for _ in row] for row in grid]


def _absolute_template_entries(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in GEN._TEMPLATE_COLORS
    ]


def _solve_from_entries(grid, entries):
    out = _blank(grid)
    if not entries:
        return out
    entries = GEN._normalize_entries(entries)
    markers = GEN._markers_from_grid(grid)
    for color in GEN._MARKER_COLORS:
        transformed = GEN._transform_entries(
            entries, {3: 0, 4: 1, 5: 2, 6: 3}[color]
        )
        for anchor in markers[color]:
            GEN._paint_entries(out, transformed, anchor)
    return out


def _first_five_template_cells(grid):
    return _solve_from_entries(grid, _absolute_template_entries(grid)[:5])


def _ignore_color_one(grid):
    return _solve_from_entries(
        grid, [entry for entry in _absolute_template_entries(grid) if entry[2] != 1]
    )


def _canonical_template_boxes_only(grid):
    entries = _absolute_template_entries(grid)
    r0, c0, r1, c1 = GEN._bbox((r, c) for r, c, _ in entries)
    if (r1 - r0 + 1, c1 - c0 + 1) not in {(3, 2), (3, 3)}:
        return _blank(grid)
    return GEN._solve_candidate(grid)


def _canonical_grid_sizes_only(grid):
    if (len(grid), len(grid[0])) not in {(12, 19), (13, 19), (13, 20)}:
        return _blank(grid)
    return GEN._solve_candidate(grid)


LOCAL_RIVALS = {
    "first_five_template_cells": _first_five_template_cells,
    "ignore_color_one": _ignore_color_one,
    "canonical_template_boxes_only": _canonical_template_boxes_only,
    "canonical_grid_sizes_only": _canonical_grid_sizes_only,
}


@pytest.mark.parametrize(
    ("name", "start"),
    [
        ("canonical_template_boxes_only", 0),
        ("canonical_grid_sizes_only", 0),
        ("first_five_template_cells", 60),
        ("ignore_color_one", 193),
    ],
)
def test_known_ambiguous_windows_now_show_the_missing_feature(name, start):
    rival = LOCAL_RIVALS[name]
    pairs = list(_canonical_pairs())
    assert pairs and all(rival(pair["input"]) == pair["output"] for pair in pairs)

    demos = [
        GEN.generate(707, start + offset, difficulty="easy")
        for offset in range(GEN.EXAMPLES_NEEDED)
    ]
    assert any(rival(grid) != GEN._solve_candidate(grid) for grid in demos), name


def test_all_new_canonical_shortcuts_are_declared_and_refuted_by_every_window():
    expected = set(LOCAL_RIVALS)
    assert expected <= set(GEN.CANONICAL_SHORTCUTS)
    assert expected <= set(GEN.SEMANTIC_RIVALS)
    assert expected <= set(GEN.LESSON_COMPETITORS)

    period = math.lcm(
        len(GEN.SCHEDULE_PROFILES),
        len(GEN._SOURCE_SIDE_SCHEDULE),
        len(GEN._MARKER_COUNT_SCHEDULE),
        3,
    )
    for difficulty in ("easy", "medium", "hard"):
        for start in range(period):
            demos = [
                GEN.generate(1707, start + offset, difficulty=difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            for name in expected:
                rival = GEN.CANONICAL_SHORTCUTS[name]
                assert any(
                    rival(grid) != GEN._solve_candidate(grid) for grid in demos
                ), (difficulty, start, name)


def test_canonical_shortcut_registry_contains_only_canonical_fitting_rivals():
    canonical_pairs = list(_canonical_pairs())
    expected = {
        "first_marker_per_code",
        "template_only_in_left_strip",
        "first_five_template_cells",
        "ignore_color_one",
        "canonical_template_boxes_only",
        "canonical_grid_sizes_only",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == expected
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(
            rival(pair["input"]) == pair["output"] for pair in canonical_pairs
        ), name
