"""Regressions for the formerly invisible convexification shortcut.

The geometric test uses missing integer midpoints, independently of the
generator's convex-hull implementation. Labels come from fixed examples or
the portable canonical-data helper, never from a second call to the subject.
"""
from __future__ import annotations

import importlib.util
from itertools import combinations
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "48bda9528e71"
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("concave_curriculum_subject", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
BANDS = ("easy", "medium", "hard")

MINIMAL_INPUT = [
    [4, 4, 4, 4, 8],
    [4, 2, 4, 4, 8],
    [4, 4, 8, 8, 8],
    [4, 4, 8, 8, 8],
    [8, 8, 8, 8, 8],
]
MINIMAL_OUTPUT = [
    [8, 8, 8, 8, 2],
    [8, 8, 8, 8, 2],
    [8, 8, 2, 2, 8],
    [8, 8, 2, 8, 8],
    [2, 2, 8, 8, 8],
]


def _occupied(grid):
    return {(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value != 8}


def _missing_midpoints(grid):
    cells = _occupied(grid)
    return {
        ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
        for a, b in combinations(cells, 2)
        if (a[0] + b[0]) % 2 == 0 and (a[1] + b[1]) % 2 == 0
    } - cells


def _cardinal_shell(grid):
    """Independent equivalent output on the admitted row/column-convex domain."""
    cells = _occupied(grid)
    colors = {grid[r][c] for r, c in cells}
    rare = min(colors, key=lambda color: sum(grid[r][c] == color for r, c in cells))
    output = [[8 for _ in row] for row in grid]
    for r, c in cells:
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= rr < len(grid) and 0 <= cc < len(grid[0])
                    and (rr, cc) not in cells):
                output[rr][cc] = rare
    return output


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("start", range(4))
def test_four_pair_default_windows_retain_two_distinct_concave_witnesses(band, start):
    # Removing the notched branch or allowing duplicate witness orientations
    # would leave a query rotation with only convex demonstrations.
    for seed in range(8):
        grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(4)]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert len({tuple(map(tuple, grid)) for grid in grids}) == 4
        assert sum(bool(_missing_midpoints(grid)) for grid in grids) >= 2


@pytest.mark.parametrize("value", [True, False, 1.0, "1", -1])
def test_invalid_sample_indices_are_rejected_instead_of_coerced(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, value)


@pytest.mark.parametrize("value", [5.0, 5.5, "5"])
def test_grid_size_requires_an_exact_integer(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 1, grid_size=value, scene_profile="general")


def test_unknown_override_is_not_silently_swallowed():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, grid_szie=7)


def test_canonical_shortcut_fit_and_exact_hand_derived_minimal_witness():
    assert GEN.self_check(MINIMAL_INPUT) == []
    assert _cardinal_shell(MINIMAL_INPUT) == MINIMAL_OUTPUT
    assert GEN.rule_mirror(MINIMAL_INPUT) == MINIMAL_OUTPUT
    # Every declaration must actually fit all available canonical labels.
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert rivals, "a concrete canonical-fitting rival must be executable"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    for rival in rivals.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)
        alternative = rival(MINIMAL_INPUT)
        different = [(r, c) for r in range(5) for c in range(5)
                     if alternative[r][c] != MINIMAL_OUTPUT[r][c]]
        assert different == [(2, 2)]
        assert alternative[2][2] == 8


@pytest.mark.parametrize("band", BANDS)
def test_exact_axis_combinations_cover_all_sizes_and_keep_concave_support(band):
    for size in range(5, 17):
        for index in range(4):
            grid = GEN.generate(19, index, difficulty=band,
                                grid_size=size, scene_profile="general")
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {
                "grid_size": size, "scene_profile": "general"}
            if index % 2:
                assert _missing_midpoints(grid)
        if size in (5, 7, 16):
            grid = GEN.generate(19, 1, difficulty=band,
                                grid_size=size, scene_profile="canonical")
            assert GEN.observe_overrides(grid) == {
                "grid_size": size, "scene_profile": "canonical"}
        else:
            with pytest.raises(ValueError):
                GEN.generate(19, 1, difficulty=band,
                             grid_size=size, scene_profile="canonical")


def test_clipped_smallest_canvas_notches_still_refute_every_declared_rival():
    edge_contacts = set()
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert rivals
    for seed in range(32):
        for index in (1, 3):
            grid = GEN.generate(seed, index, difficulty="hard",
                                grid_size=5, scene_profile="general")
            assert GEN.self_check(grid) == []
            assert _missing_midpoints(grid)
            expected = _cardinal_shell(grid)
            assert all(rival(grid) != expected for rival in rivals.values())
            cells = _occupied(grid)
            edge_contacts.update(name for name, active in (
                ("top", any(r == 0 for r, _ in cells)),
                ("bottom", any(r == 4 for r, _ in cells)),
                ("left", any(c == 0 for _, c in cells)),
                ("right", any(c == 4 for _, c in cells)),
            ) if active)
    assert edge_contacts == {"top", "bottom", "left", "right"}


@pytest.mark.parametrize("band", BANDS)
def test_all_query_holdouts_are_identifiable_against_declared_lesson_rivals(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals
    for seed in range(4):
        for start in range(4):
            pairs = [{"input": grid, "output": _cardinal_shell(grid)}
                     for grid in (GEN.generate(seed, start + i, difficulty=band)
                                  for i in range(4))]
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                for rival in rivals.values():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_validator_keeps_the_orthogonally_convex_domain_boundary():
    invalid = [row[:] for row in MINIMAL_INPUT]
    invalid[0][2] = 8  # Break row contiguity while preserving the other scene.
    assert any("contiguous" in reason for reason in GEN.self_check(invalid))
