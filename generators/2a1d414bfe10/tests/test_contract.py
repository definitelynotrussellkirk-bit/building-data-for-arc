"""Behavioral regressions for placement, input support and exact controls."""
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "2a1d414bfe10"
ROOT = find_root(__file__)
SOURCE = next(p for p in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if p.is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_exact_two_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def supports(grid):
    result = []
    for color in (1, 2, 3):
        points = {(r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value == color}
        assert points, f"missing color {color}"
        top, left = min(r for r, c in points), min(c for r, c in points)
        result.append({(r - top, c - left) for r, c in points})
    return result


def oracle(grid):
    """Independent dense incidence-table oracle; canonical/Racket labels pin it."""
    shapes = supports(grid)
    h = 1 + max(r for shape in shapes for r, c in shape)
    w = 1 + max(c for shape in shapes for r, c in shape)
    hits = [[sum((r, c) in shape for shape in shapes)
             for c in range(w)] for r in range(h)]
    cells = [(r, c) for r in range(h) for c in range(w) if hits[r][c] == 2]
    if not cells:
        return [[0]]
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    return [[8 if hits[r][c] == 2 else 0 for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("h,w", [(8, 10), (16, 18), (9, 13), (10, 12)])
def test_exact_dimensions_at_boundaries_and_canonical_profiles(band, h, w):
    for index in (0, 1):
        grid = GEN.generate(7, index, difficulty=band, grid_h=h, grid_w=w)
        assert (len(grid), len(grid[0])) == (h, w)
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("overrides", [
    {"grid_h": 7}, {"grid_h": 17}, {"grid_w": 9}, {"grid_w": 19},
    {"grid_h": True}, {"grid_w": "12"}, {"grid_h": 9.0},
    {"grid_ww": 12}, {"texture": "missing_blob"},
])
def test_invalid_or_unknown_controls_fail_explicitly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(7, 0, **overrides)


@pytest.mark.parametrize("grid,meta", [
    ([[1, 2, 3, 10]], None),
    ([[1, 2, 3, 1.5]], None),
    ([[True, 2, 3]], None),
    ([[0]], {"texture": "missing_blob"}),
    ([[1, 2], [3]], None),
    ([], None),
    (None, None),
])
def test_validator_rejects_malformed_inputs_without_metadata_bypass(grid, meta):
    assert GEN.self_check(grid, meta=meta)


def test_placement_preserves_all_colors_at_original_overwrite_seed():
    grid = GEN.generate(205, 0, difficulty="easy")
    assert {1, 2, 3} <= {value for row in grid for value in row}
    assert GEN.self_check(grid) == []


def test_independent_normalized_bounding_boxes_are_generated():
    boxes = []
    for seed in range(30):
        shape_sets = supports(GEN.generate(seed, 0, difficulty="easy"))
        boxes.append({(max(r for r, c in s) + 1, max(c for r, c in s) + 1)
                      for s in shape_sets})
    assert any(len(shape_boxes) > 1 for shape_boxes in boxes)


@pytest.mark.parametrize("h,w", [(10, 12), (9, 11)])
def test_canonical_interleaved_layouts_are_generated(h, w):
    no_horizontal_separator = False
    no_vertical_separator = False
    for seed in range(64):
        grid = GEN.generate(seed, 0, difficulty="easy", grid_h=h, grid_w=w)
        points = [(r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value]
        top, bottom = min(r for r, c in points), max(r for r, c in points)
        left, right = min(c for r, c in points), max(c for r, c in points)
        no_horizontal_separator |= all(any(grid[r]) for r in range(top, bottom + 1))
        no_vertical_separator |= all(any(row[c] for row in grid)
                                     for c in range(left, right + 1))
    assert no_horizontal_separator, "a global blank row excludes two canonical layout families"
    assert no_vertical_separator, "placement should also support the transposed interleaving"


def test_canonical_inputs_are_supported_and_oracle_matches_all_labels():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(7, 0, difficulty="typo")


def test_declared_shortcuts_really_fit_every_canonical_label():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert shortcuts, "the canonical-fitting shortcuts must be executable"
    for pair in canonical_pairs(TASK, root=ROOT):
        for name, rival in shortcuts.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_four_pair_window_teaches_every_rival_after_any_query_rotation(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals, "lessons need executable competing hypotheses"
    for seed in range(12):
        for start in (0, 1):
            grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(4)]
            labels = [oracle(grid) for grid in grids]
            for name, rival in rivals.items():
                disagreements = [rival(g) != out for g, out in zip(grids, labels)]
                assert sum(disagreements) >= 2, (seed, start, name, disagreements)
            for query in range(4):
                demos = [{"input": grids[i], "output": labels[i]}
                         for i in range(4) if i != query]
                assert GEN.lesson_identifiable(
                    demos, {"input": grids[query], "output": labels[query]}) == []
