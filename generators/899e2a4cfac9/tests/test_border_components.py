"""Portable regressions for border removal and the generator's teaching contract.

The oracle segments same-color orthogonal components independently.  Canonical
labels come from the local ledger, never from the generator or a cached probe.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
for ancestor in HOME.parents:
    if (ancestor / "shared/runtime/reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor / "shared/runtime"))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("border_component_generator", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs("899e2a4cfac9", root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def components(grid, *, diagonal=False, same_color=True):
    """Set-based flood fill, independent of production segmentation."""
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    result = []
    moves = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    while pending:
        start = min(pending)
        pending.remove(start)
        color = grid[start[0]][start[1]]
        found, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in moves:
                point = (r + dr, c + dc)
                if point in pending and (not same_color or grid[point[0]][point[1]] == color):
                    pending.remove(point)
                    found.add(point)
                    todo.append(point)
        result.append(found)
    return result


def border(grid, cells):
    return any(r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1) for r, c in cells)


def oracle(grid, rival=None):
    groups = components(grid, diagonal=rival == "same_color_8", same_color=rival != "nonzero_4")
    output = [[0] * len(grid[0]) for _ in grid]
    largest = max(map(len, groups), default=0)
    largest_inside = max((len(cells) for cells in groups if not border(grid, cells)), default=0)
    border_colors = {grid[r][c] for cells in groups if border(grid, cells) for r, c in cells}
    for cells in groups:
        keep = not border(grid, cells)
        if rival == "erase_domino":
            keep = len(cells) != 2
        elif rival == "keep_largest":
            keep = len(cells) == largest
        elif rival == "border_colors_global":
            keep = grid[next(iter(cells))[0]][next(iter(cells))[1]] not in border_colors
        elif rival == "border_cells_only":
            cells = {point for point in cells if not border(grid, [point])}
            keep = True
        elif rival == "drop_singletons":
            keep = keep and len(cells) > 1
        elif rival == "largest_interior":
            keep = keep and len(cells) == largest_inside
        if keep:
            for r, c in cells:
                output[r][c] = grid[r][c]
    return output


RIVALS = ("erase_domino", "keep_largest", "border_colors_global", "same_color_8", "nonzero_4", "border_cells_only",
          "drop_singletons", "largest_interior")


def fixture(parts, h=7, w=8):
    grid = [[0] * w for _ in range(h)]
    for color, cells in parts:
        for r, c in cells:
            grid[r][c] = color
    return grid


PROBES = {
    "size_role_swap": fixture([(2, [(0, 1), (1, 1), (1, 2)]), (3, [(3, 1), (4, 1)]),
                               (4, [(3, 4), (4, 4), (4, 5)]), (7, [(5, 7), (6, 7)])]),
    "same_color_diagonal_contact": fixture([(2, [(0, 1), (1, 1), (2, 2), (3, 2), (3, 3)]),
                                            (4, [(3, 5), (4, 5), (4, 6)]), (7, [(5, 7), (6, 7)])]),
    "different_color_edge_contact": fixture([(2, [(0, 1), (1, 1)]), (3, [(2, 1), (3, 1), (3, 2)]),
                                             (4, [(3, 5), (4, 5), (4, 6)]), (7, [(5, 7), (6, 7)])]),
    "same_color_disconnected_roles": fixture([(2, [(0, 1), (1, 1), (3, 1), (4, 1), (4, 2)]),
                                              (4, [(3, 5), (4, 5), (4, 6)]), (7, [(5, 7), (6, 7)])]),
}


def test_canonical_inputs_are_accepted_and_independent_oracle_matches_labels():
    assert PAIRS
    for pair in PAIRS:
        assert GEN.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])
        assert oracle(pair["input"]) == pair["output"]


def test_one_interior_component_is_sufficient():
    grid = fixture([(2, [(0, 1), (1, 1)]), (3, [(3, 3), (4, 3), (4, 4)]),
                    (4, [(5, 7), (6, 7)])])
    assert GEN.self_check(grid) == []
    assert sum(not border(grid, cells) for cells in components(grid)) == 1


def test_malformed_grids_are_rejected_without_raising():
    for bad in (None, [], [[]], [[0, 1], [2]], [[-1]], [[10]], [["2"]], [[2.0]], [[True]]):
        assert GEN.self_check(bad), repr(bad)
    # Invalid colors must fail even when object counts and both border roles
    # would otherwise pass.  A single-cell bad grid only tests degeneracy.
    for bad_color in (-1, 10, "2", 2.0, True):
        grid = deepcopy(PROBES["size_role_swap"])
        grid[2][6] = bad_color
        assert GEN.self_check(grid), repr(bad_color)


def test_no_border_and_no_survivor_inputs_are_rejected():
    for grid in (fixture([(2, [(2, 2)]), (3, [(4, 4)])]),
                 fixture([(2, [(0, 2)]), (3, [(6, 4)])]), fixture([])):
        assert GEN.self_check(grid)


def test_contact_probes_use_same_color_four_connectivity():
    for name, grid in PROBES.items():
        assert GEN.self_check(grid) == [], name
        assert {frozenset(c) for c in GEN._components(grid)} == {frozenset(c) for c in components(grid)}, name
    diagonal = PROBES["same_color_diagonal_contact"]
    orthogonal = PROBES["different_color_edge_contact"]
    assert oracle(diagonal)[2][2] == 2 and oracle(diagonal, "same_color_8")[2][2] == 0
    assert oracle(orthogonal)[2][1] == 3 and oracle(orthogonal, "nonzero_4")[2][1] == 0


def test_equal_size_objects_can_have_opposite_border_roles():
    grid = PROBES["size_role_swap"]
    output = oracle(grid)
    assert output[0][1] == 0 and output[3][4] == 4
    assert output[5][7] == 0 and output[3][1] == 3
    assert oracle(grid, "erase_domino") != output
    assert oracle(grid, "keep_largest") != output


def test_axis_domains_describe_the_exact_supported_integer_controls():
    expected = {"grid_h": "6..12", "grid_w": "7..14", "n_blobs": "3..7", "n_distinct_colors": "3..6"}
    for name, domain in expected.items():
        assert GEN.AXES[name]["type"] == "int"
        assert GEN.AXES[name]["valid"] == domain


def test_count_and_dimension_overrides_are_observed_from_actual_cells():
    assert callable(getattr(GEN, "observe_overrides", None))
    requests = [(6, 7, 3, 3), (6, 7, 3, 4), (6, 7, 4, 3), (6, 14, 5, 4), (12, 7, 6, 5), (12, 14, 7, 6)]
    for band in BANDS:
        for h, w, blobs, colors in requests:
            grid = GEN.generate("exact-controls", 2, difficulty=band, grid_h=h, grid_w=w,
                                n_blobs=blobs, n_distinct_colors=colors)
            actual = {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(components(grid)),
                      "n_distinct_colors": len({v for row in grid for v in row})}
            assert actual == dict(zip(actual, (h, w, blobs, colors)))
            observed = GEN.observe_overrides(grid)
            assert all(observed[name] == value for name, value in actual.items())
            assert GEN.self_check(grid) == []


def test_single_color_count_request_adjusts_unpinned_blob_count():
    grid = GEN.generate("six-colors", 0, n_distinct_colors=6)
    assert len({v for row in grid for v in row}) == 6
    assert len(components(grid)) >= 6
    assert GEN.self_check(grid) == []


def test_invalid_and_incompatible_overrides_raise():
    invalid = [{"unknown_typo": 4}, {"grid_h": 5}, {"grid_h": 13}, {"grid_w": 6}, {"grid_w": 15},
               {"n_blobs": 2}, {"n_blobs": 8}, {"n_distinct_colors": 2}, {"n_distinct_colors": 7},
               {"n_blobs": 4, "n_distinct_colors": 5}, {"n_blobs": 3, "n_distinct_colors": 5},
               {"n_blobs": 3, "n_distinct_colors": 6}]
    invalid.extend({key: bad} for key in ("grid_h", "grid_w", "n_blobs", "n_distinct_colors")
                   for bad in (True, 6.0, "6"))
    for override in invalid:
        with pytest.raises((ValueError, TypeError)):
            GEN.generate(0, 0, **override)


def test_default_draws_are_deterministic_varied_and_semantically_valid():
    for band in BANDS:
        corpus = []
        for index in range(24):
            grid = GEN.generate("default-regression", index, difficulty=band)
            assert grid == GEN.generate("default-regression", index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert 3 <= len(components(grid)) <= 7
            assert 3 <= len({v for row in grid for v in row}) <= 6
            assert {frozenset(c) for c in GEN._components(grid)} == {frozenset(c) for c in components(grid)}
            corpus.append(tuple(map(tuple, grid)))
        assert len(set(corpus)) >= 12, band


def test_every_rich_default_draw_refutes_all_eight_independent_rivals():
    # Odd indices supply rich witnesses; even indices preserve the canonical
    # three-object teaching profile.  Lessons combine both profiles.
    for band in BANDS:
        for index in range(1, 25, 2):
            grid = GEN.generate("all-rival-regression", index, difficulty=band)
            expected = oracle(grid)
            for name in RIVALS:
                assert oracle(grid, name) != expected, (band, index, name)


def test_semantic_declarations_have_executable_truthful_witnesses():
    for attribute in ("SEMANTIC_RIVALS", "SEMANTIC_WITNESSES", "WITNESS_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        assert isinstance(getattr(GEN, attribute, None), dict), attribute
    assert len(GEN.SEMANTIC_RIVALS) >= 6
    assert GEN.SEMANTIC_WITNESSES and GEN.CANONICAL_SHORTCUTS
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    for index in range(1, 25, 2):
        grid = GEN.generate("witness-regression", index)
        original = deepcopy(grid)
        covered = set()
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                assert GEN.WITNESS_RIVALS[name], name
                for rival in GEN.WITNESS_RIVALS[name]:
                    assert rival in GEN.SEMANTIC_RIVALS
                    assert GEN.SEMANTIC_RIVALS[rival](grid) != oracle(grid), (name, rival)
                    covered.add(rival)
        assert set(GEN.SEMANTIC_RIVALS) <= covered
        assert grid == original


def test_only_declared_canonical_shortcuts_are_required_to_fit_all_labels():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert shortcuts
    for name, rival in shortcuts.items():
        assert callable(rival), name
        for pair in PAIRS:
            assert rival(pair["input"]) == pair["output"], (name, pair["split"], pair["pair_index"])


def test_three_demo_lessons_refute_rivals_for_independent_query_holdouts():
    assert callable(getattr(GEN, "lesson_identifiable", None))
    competitors = getattr(GEN, "LESSON_COMPETITORS", {})
    assert competitors
    for band in BANDS:
        demos = [{"input": GEN.generate("lesson-regression", index, difficulty=band)} for index in range(3)]
        for demo in demos:
            demo["output"] = oracle(demo["input"])
        original = deepcopy(demos)
        for index in (9, 17):
            query = {"input": GEN.generate("query-holdout", index, difficulty=band)}
            query["output"] = oracle(query["input"])
            query_before = deepcopy(query)
            for name, rival in competitors.items():
                if rival(query["input"]) != query["output"]:
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos), name
            assert GEN.lesson_identifiable(demos, query) == []
            assert query == query_before
        assert demos == original


def test_simple_and_rich_defaults_have_their_required_survivor_profiles():
    for band in BANDS:
        for index in range(16):
            grid = GEN.generate("survivor-profiles", index, difficulty=band)
            groups = components(grid)
            inside = [cells for cells in groups if not border(grid, cells)]
            if index % 2 == 0:
                assert len(groups) == 3, (band, index)
                assert len(inside) == 1, (band, index)
                assert len({v for row in grid for v in row}) == 4, (band, index)
            else:
                assert len(groups) == 7, (band, index)
                assert any(len(cells) == 1 for cells in inside), (band, index)
                assert any(len(cells) > 1 for cells in inside), (band, index)


def test_invalid_sample_indices_are_rejected():
    for index in (True, False, 1.0, "1", -1):
        with pytest.raises((ValueError, TypeError)):
            GEN.generate("invalid-index", index)


def test_consecutive_four_pair_windows_are_identifiable_in_all_query_rotations():
    declared = getattr(GEN, "LESSON_COMPETITORS", {})
    assert declared
    for band in BANDS:
        # Both even and odd starts must work; consecutive windows are the
        # production lesson shape and every pair can become its query.
        for start in range(8):
            pairs = [{"input": GEN.generate("rotation-regression", index, difficulty=band)}
                     for index in range(start, start + 4)]
            for pair in pairs:
                pair["output"] = oracle(pair["input"])
            before = deepcopy(pairs)
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                for name, rival in declared.items():
                    if rival(query["input"]) != query["output"]:
                        assert any(rival(demo["input"]) != demo["output"] for demo in demos), (band, start, query_index, name)
                # Independently test the two additional canonical-fitting
                # hypotheses even if a declaration accidentally omits them.
                for name in ("drop_singletons", "largest_interior"):
                    if oracle(query["input"], name) != query["output"]:
                        assert any(oracle(demo["input"], name) != demo["output"] for demo in demos), (band, start, query_index, name)
                assert GEN.lesson_identifiable(demos, query) == []
            assert pairs == before


def test_each_band_keeps_canonical_shape_and_palette_support():
    signatures = {(len(p["input"]), len(p["input"][0]), len({v for row in p["input"] for v in row}))
                  for p in PAIRS}
    for band in BANDS:
        hits = 0
        for index in range(64):
            grid = GEN.generate("canonical-support", index, difficulty=band)
            signature = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += signature in signatures
        assert hits >= 8, (band, hits, 64)

