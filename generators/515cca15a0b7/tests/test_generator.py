"""Focused regression tests for the 515cca15a0b7 generator repair."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "515cca15a0b7"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append((color, cells))
    return result


def _roles(grid):
    height, width = len(grid), len(grid[0])
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    counts = {"noncorner_keep": 0, "corner_keep": 0, "edge_drop": 0, "interior_drop": 0}
    for _, cells in _components(grid):
        horizontal = any(r in (0, height - 1) for r, _ in cells)
        vertical = any(c in (0, width - 1) for _, c in cells)
        if horizontal and vertical:
            counts["corner_keep" if cells & corners else "noncorner_keep"] += 1
        elif horizontal or vertical:
            counts["edge_drop"] += 1
        else:
            counts["interior_drop"] += 1
    return counts


def _intended_output(grid):
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for color, cells in _components(grid):
        horizontal = any(r in (0, height - 1) for r, _ in cells)
        vertical = any(c in (0, width - 1) for _, c in cells)
        if horizontal and vertical:
            for row, col in cells:
                out[row][col] = color
    return out


def _has_extended_noncorner_keep(grid):
    height, width = len(grid), len(grid[0])
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    literal = set(corners)
    for _, cells in _components(grid):
        horizontal = any(r in (0, height - 1) for r, _ in cells)
        vertical = any(c in (0, width - 1) for _, c in cells)
        if horizontal and vertical and not (cells & literal):
            if not any(
                all(max(abs(r - cr), abs(c - cc)) <= 2 for r, c in cells)
                for cr, cc in corners
            ):
                return True
    return False




def _global_color_union_output(grid):
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    by_color = {}
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color:
                by_color.setdefault(color, []).append((row, col))
    for color, cells in by_color.items():
        horizontal = any(row in (0, height - 1) for row, _ in cells)
        vertical = any(col in (0, width - 1) for _, col in cells)
        if horizontal and vertical:
            for row, col in cells:
                out[row][col] = color
    return out


def _has_split_same_color_edge_witness(grid):
    height, width = len(grid), len(grid[0])
    by_color = {}
    for color, cells in _components(grid):
        horizontal = any(row in (0, height - 1) for row, _ in cells)
        vertical = any(col in (0, width - 1) for _, col in cells)
        by_color.setdefault(color, []).append((horizontal, vertical))
    return any(
        any(horizontal and not vertical for horizontal, vertical in roles)
        and any(vertical and not horizontal for horizontal, vertical in roles)
        for roles in by_color.values()
    )

def test_contract_surface_is_small_exact_and_rule_pinned():
    assert gen.RULE_HASH == "8a3c35320856"
    assert gen.VERSION == "2.1.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "layout"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)


def test_all_canonical_pairs_are_accepted_and_match_independent_oracle():
    for pair in PAIRS:
        source = deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert _intended_output(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "layout,expected,has_extended,has_split_color",
    [
        ("canonical_mix", {"noncorner_keep": 1, "corner_keep": 1, "edge_drop": 1, "interior_drop": 1}, False, False),
        ("edge_contrast", {"noncorner_keep": 1, "corner_keep": 1, "edge_drop": 2, "interior_drop": 0}, False, True),
        ("kept_variety", {"noncorner_keep": 2, "corner_keep": 1, "edge_drop": 1, "interior_drop": 1}, True, False),
        ("dense", {"noncorner_keep": 2, "corner_keep": 2, "edge_drop": 2, "interior_drop": 1}, True, True),
    ],
)
def test_exact_overrides_are_constructive_observable_and_semantic(
    band, layout, expected, has_extended, has_split_color
):
    options = {"grid_h": 8, "grid_w": 9, "layout": layout}
    grid = gen.generate(319, 17, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert _roles(grid) == expected
    assert _has_extended_noncorner_keep(grid) is has_extended
    assert _has_split_same_color_edge_witness(grid) is has_split_color
    if has_split_color:
        assert _global_color_union_output(grid) != _intended_output(grid)
    if not has_extended:
        assert max(len(cells) for _, cells in _components(grid)) <= 3
    assert gen.rule_mirror(grid) == _intended_output(grid)
    assert gen.generate(319, 17, difficulty=band, **options) == grid


@pytest.mark.parametrize(
    "override",
    [
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_h": 11},
        {"grid_w": 8},
        {"grid_w": 12},
        {"layout": "corner_only"},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"layout": 1},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(override):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **override)


def test_default_schedule_covers_every_layout_and_every_three_demo_window_has_witnesses():
    expected = ("canonical_mix", "dense", "canonical_mix", "edge_contrast", "kept_variety")
    grids = []
    observed = []
    for index in range(16):
        grid = gen.generate(700 + index, index)
        assert gen.self_check(grid) == []
        roles = _roles(grid)
        assert roles["edge_drop"] >= 1
        grids.append(grid)
        observed.append(gen.observe_overrides(grid)["layout"])
    assert tuple(observed[:5]) == expected
    assert set(observed) == set(expected)
    for start in range(len(grids) - 2):
        window = grids[start : start + 3]
        assert any(_has_extended_noncorner_keep(grid) for grid in window)
        assert any(_has_split_same_color_edge_witness(grid) for grid in window)


def test_difficulty_bands_are_observably_distinct_without_changing_the_rule():
    options = {"grid_h": 8, "grid_w": 9, "layout": "canonical_mix"}
    grids = {
        band: gen.generate(829, 5, difficulty=band, **options)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) == 3
    for grid in grids.values():
        assert gen.observe_overrides(grid) == options
        assert gen.rule_mirror(grid) == _intended_output(grid)
        assert max(len(cells) for _, cells in _components(grid)) <= 3


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    for name in ("near_corner_radius2", "keep_two_nearest", "global_color_union"):
        rival = gen.CANONICAL_SHORTCUTS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(_global_color_union_output(pair["input"]) == pair["output"] for pair in PAIRS)


def test_generated_witnesses_refute_every_declared_rival():
    grids = [
        gen.generate(911, index, layout=layout)
        for index, layout in enumerate(("canonical_mix", "kept_variety", "edge_contrast", "dense"))
    ]
    intended = [gen.rule_mirror(grid) for grid in grids]
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(rival(grid) != answer for grid, answer in zip(grids, intended)), name
    dense = grids[-1]
    assert gen.CANONICAL_SHORTCUTS["keep_two_nearest"](dense) != gen.rule_mirror(dense)
    assert gen.CANONICAL_SHORTCUTS["near_corner_radius2"](dense) != gen.rule_mirror(dense)


def test_rule_mirror_is_pure_and_grid_validation_is_diagnostic():
    grid = gen.generate(123, 5, layout="dense")
    snapshot = deepcopy(grid)
    assert gen.rule_mirror(grid) == _intended_output(grid)
    assert grid == snapshot
    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)]):
        assert gen.self_check(malformed)


def test_workspace_semantic_probe_checks_all_cyclic_query_starts():
    probe_path = HOME / "workspace" / "semantic_probe.py"
    spec = importlib.util.spec_from_file_location("semantic_probe_515cca15a0b7", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.audit(gen, PAIRS, seed_count=2)
    assert report["canonical_shortcuts_fit_all_pairs"] is True
    assert report["lessons"] == 3 * 2 * 5
    assert report["cyclic_starts"] == [0, 1, 2, 3, 4]
    assert report["all_lessons_identifiable"] is True
    assert all(row["ambiguous"] == 0 for row in report["competitors"].values())
    assert all(row["survived_all"] == 0 for row in report["competitors"].values())
    witness = report["strongest_shortcut_witness"]
    assert witness["shortcut"] == "keep_two_nearest"
    assert witness["intended_output"] != witness["rival_output"]
