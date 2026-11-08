"""Behavior regressions for the exposed-edge-perimeter input sampler."""
from __future__ import annotations

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "c78d339cf2f2"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def objects(grid):
    """Independent flood-fill, including touching different colors."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x}
    found = []
    while unseen:
        first = min(unseen)
        body = {first}
        unseen.remove(first)
        todo = [first]
        for r, c in todo:
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen:
                    unseen.remove(q)
                    body.add(q)
                    todo.append(q)
        found.append(body)
    return found


def rank_order(grid, metric):
    bodies = objects(grid)
    values = []
    for body in bodies:
        rows, cols = zip(*body)
        h, w = max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
        # Count shared internal edges, independently of the generator's method.
        shared = sum((r + 1, c) in body for r, c in body)
        shared += sum((r, c + 1) in body for r, c in body)
        values.append({"edge": 4 * len(body) - 2 * shared,
                       "area": len(body), "bbox_perimeter": 2 * (h + w),
                       "bbox_area": h * w}[metric])
    return sorted(range(len(bodies)), key=lambda i: values[i])


def test_accepts_every_labeled_canonical_input_including_true_ties():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []


def test_counts_spatial_components_not_foreground_colors():
    grid = [[0] * 12 for _ in range(8)]
    for r, c in [(1, 1), (1, 2), (3, 4), (3, 5), (6, 8), (6, 9)]:
        grid[r][c] = 6
    assert GEN.self_check(grid) == []
    # Three colors in a single touching component must be rejected.
    one_body = [[0] * 12 for _ in range(8)]
    one_body[1][1:4] = [2, 3, 4]
    assert GEN.self_check(one_body)


@pytest.mark.parametrize("bad", [[], [[]], [[0], [0, 1]], [[False]], [[10]], [[-1]], [["6"]]])
def test_malformed_input_is_rejected_without_an_exception(bad):
    assert GEN.self_check(bad)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_profile_and_noncanonical_size_support(band):
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({x for row in p["input"] for x in row}))
                for p in canonical_pairs(TASK, root=ROOT)}
    samples = [GEN.generate(17, i, difficulty=band) for i in range(100)]
    exact = sum((len(g), len(g[0]), len({x for row in g for x in row})) in profiles for g in samples)
    assert exact >= 10
    assert any(len(g) > 10 or len(g[0]) > 13 for g in samples)
    assert len({tuple(map(tuple, g)) for g in samples}) == len(samples)
    assert all(len(objects(g)) == 3 for g in samples)


@pytest.mark.parametrize("axis,values", [
    ("grid_h", [True, 8.5, "8", -1]),
    ("grid_w", [True, 12.5, "12", -1]),
    ("foreground", [True, 6.5, "6", 0, 10]),
])
def test_scalar_overrides_are_literal_integers(axis, values):
    for value in values:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(2, 3, **{axis: value})


def test_unknown_and_removed_placeholder_axes_are_rejected():
    for axis in ("typo", "palette_kind", "n_blobs", "density", "texture"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, **{axis: 3})


@pytest.mark.parametrize("name,values", [
    ("seed", [True, False, 1.0, 1.75, "1"]),
    ("sample_index", [True, False, 1.0, 1.75, "1", -1]),
    ("difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]),
])
def test_primary_call_arguments_are_strict(name, values):
    for value in values:
        arguments = {"seed": 991, "sample_index": 0, "difficulty": "medium"}
        arguments[name] = value
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(**arguments)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_joint_axis_boundaries_are_realized_in_every_band(band):
    for h, w, color in [(8, 12, 1), (8, 20, 9), (20, 12, 6), (20, 20, 3)]:
        grid = GEN.generate(5, 6, difficulty=band, grid_h=h, grid_w=w, foreground=color)
        assert (len(grid), len(grid[0])) == (h, w)
        assert {x for row in grid for x in row} == {0, color}
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_draw_distinguishes_geometry_metric_shortcuts(band):
    for i in range(100):
        grid = GEN.generate(23, i, difficulty=band)
        actual = rank_order(grid, "edge")
        for rival in ("area", "bbox_perimeter", "bbox_area"):
            assert rank_order(grid, rival) != actual, (band, i, rival)


@pytest.mark.parametrize("start", range(4))
def test_each_four_pair_window_has_two_tie_witnesses(start):
    assert hasattr(GEN, "SEMANTIC_WITNESSES")
    witness = GEN.SEMANTIC_WITNESSES["stable_tie"]
    grids = [GEN.generate(31, start + i) for i in range(4)]
    assert sum(witness(g) for g in grids) >= 2
    assert any(not witness(g) for g in grids)


def test_rivals_and_strict_hook_are_executable_and_honest():
    assert hasattr(GEN, "CANONICAL_SHORTCUTS")
    assert set(GEN.CANONICAL_SHORTCUTS) == {"area", "bbox_perimeter"}
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.strict_canonical_like(pair["input"]) == []
        for rival in GEN.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]


def test_generation_is_deterministic_and_returns_independent_grids():
    first = GEN.generate(41, 7)
    second = GEN.generate(41, 7)
    assert first == second
    first[0][0] = 99
    assert GEN.generate(41, 7) == second
