"""Regression checks for profile loss, silent controls, and shortcut lessons.

Expected branch behavior is independently extracted from grid cells. These
tests fail if a band loses canonical-scale support, positions encode topology,
or a legal default lesson hides the only evidence against a canonical rival.
"""
from __future__ import annotations

import importlib.util

import pytest
from reviewer_support import find_root


_root = find_root(__file__)
_source = _root / "generators" / "1ee7274bdbb0" / "generator.py"
if not _source.is_file():
    _source = _root / "puzzle_generators" / "per_puzzle" / "1ee7274bdbb0" / "generator.py"
_spec = importlib.util.spec_from_file_location("test_curriculum_subject", _source)
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)


def tiles(grid):
    height, width = len(grid), len(grid[0])
    rows = [-1] + [r for r in range(height) if all(v == 9 for v in grid[r])] + [height]
    cols = [-1] + [c for c in range(width) if all(row[c] == 9 for row in grid)] + [width]
    result = []
    for a, b in zip(rows, rows[1:]):
        for x, y in zip(cols, cols[1:]):
            motif = {(r - a - 1, c - x - 1) for r in range(a + 1, b)
                     for c in range(x + 1, y) if grid[r][c] == 2}
            markers = {(r - a - 1, c - x - 1) for r in range(a + 1, b)
                       for c in range(x + 1, y) if grid[r][c] == 3}
            result.append((b - a - 1, motif, markers))
    return result


def connected(cells):
    reached = {min(cells)}
    pending = list(reached)
    while pending:
        r, c = pending.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in reached:
                reached.add(neighbor)
                pending.append(neighbor)
    return reached == cells


def distinguishes(grid, rival):
    local_tiles = tiles(grid)
    first_marked = bool(local_tiles[0][2])
    for index, (size, motif, markers) in enumerate(local_tiles):
        intended = bool(markers)
        if rival == "center_only":
            alternative = (size // 2, size // 2) in markers
        elif rival == "single_marker_center_only":
            alternative = bool(markers) and (len(markers) != 1 or (size // 2, size // 2) in markers)
        elif rival == "skip_two_markers":
            alternative = bool(markers) and len(markers) != 2
        elif rival == "skip_three_markers":
            alternative = bool(markers) and len(markers) != 3
        elif rival == "alternating_tiles":
            alternative = first_marked if index % 2 == 0 else not first_marked
        else:
            raise AssertionError(rival)
        rotated = {(c, size - 1 - r) for r, c in motif}
        if intended != alternative and rotated != motif:
            return True
    return False


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_band_keeps_canonical_profile_support(band):
    population = [generator.generate(17, index, difficulty=band) for index in range(60)]
    hits = [g for g in population if len(g) == 3 and len(g[0]) == 11
            and {v for row in g for v in row} == {0, 2, 3, 9}]
    assert hits, f"{band} lost the canonical 3x11/four-color profile"
    assert sum(not generator.strict_canonical_like(g) for g in population) >= 18


def test_unknown_override_is_rejected_even_when_none():
    for value in (3, None):
        with pytest.raises((TypeError, ValueError), match="[Uu]nknown|[Uu]nrecognized"):
            generator.generate(0, 0, n_flag_cell=value)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_lessons_and_each_query_rotation_refute_canonical_rivals(band):
    rival_names = ("center_only", "single_marker_center_only", "skip_two_markers",
                   "skip_three_markers", "alternating_tiles")
    train_count = generator.EXAMPLES_NEEDED
    for seed in (0, 17, 20261007):
        # Includes every cyclic start across two periods and multiple RNG families.
        population = [generator.generate(seed, i, difficulty=band)
                      for i in range(14 + train_count)]
        for start in range(14):
            window = population[start:start + train_count + 1]
            for rival in rival_names:
                differences = [distinguishes(g, rival) for g in window]
                for query_index, query_differs in enumerate(differences):
                    if query_differs:
                        assert any(value for i, value in enumerate(differences) if i != query_index), (
                            band, seed, start, query_index, rival, differences
                        )


def test_canonical_topology_and_equal_adjacent_size_are_in_generated_support():
    population = [tiles(generator.generate(20261007, i, difficulty="easy")) for i in range(120)]
    assert any(not connected(items[0][1]) for items in population), "anchor topology is fixed"
    assert any(connected(items[1][1]) for items in population), "second topology is fixed"
    assert any(len(items[0][1]) == len(items[1][1]) for items in population), "first two counts are forced distinct"


def test_explicit_markers_override_the_schedule():
    for band in ("easy", "medium", "hard"):
        for count in (1, 2, 3):
            for index in range(6):
                grid = generator.generate(9, index, difficulty=band, n_flag_cells=count)
                assert {len(m) for _, _, m in tiles(grid) if m} == {count}
