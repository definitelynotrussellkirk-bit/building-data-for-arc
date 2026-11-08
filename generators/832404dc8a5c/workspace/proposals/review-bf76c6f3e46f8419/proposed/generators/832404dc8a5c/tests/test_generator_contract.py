"""Portable regressions for the selected sampler; Racket remains label authority."""
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("832404dc8a5c", root=ROOT)


def expected(grid):
    """Independent test specification; never used to create training labels."""
    h, w = len(grid), len(grid[0])
    rows = {r for r in range(h) if grid[r][0] == grid[r][-1] == 4}
    cols = {c for c in range(w) if grid[0][c] == grid[-1][c] == 4}
    swap = {0: 8, 8: 0, 6: 7, 7: 6}
    return [[swap.get(v, v) if r in rows or c in cols else v
             for c, v in enumerate(row)] for r, row in enumerate(grid)]


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 6.75), ("grid_h", "6"), ("grid_w", 9.0),
    ("n_anchored_rows", True), ("n_anchored_rows", 1.5),
    ("n_anchored_cols", "2"), ("n_anchored_cols", False),
    ("zero_density", "0.5"), ("zero_density", float("nan")),
    ("zero_density", 10 ** 1000),
    ("lane_palette", "typo"), ("texture", "typo"),
    ("misspelled_axis", 1),
])
def test_invalid_controls_reject_instead_of_coercing_or_ignoring(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 1, difficulty="hard", **{axis: value})


@pytest.mark.parametrize("kwargs", [
    {"seed": True, "sample_index": 0},
    {"seed": "17", "sample_index": 0},
    {"seed": 17, "sample_index": 0.5},
    {"seed": 17, "sample_index": -1},
    {"seed": 17, "sample_index": 0, "difficulty": "typo"},
    {"seed": 17, "sample_index": 0, "difficulty": False},
])
def test_invalid_call_arguments_reject(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**kwargs)


@pytest.mark.parametrize("grid", [None, 2, [], [[]], [[0], [0, 6]],
                                  [[0.0] * 8 for _ in range(6)]])
def test_malformed_input_returns_validation_reasons(grid):
    assert GEN.self_check(grid)


def test_all_canonical_pairs_remain_accepted_and_specified():
    pairs = canonical_pairs("832404dc8a5c", root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert expected(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_large_dimensions_and_lane_counts_in_every_band(band):
    grid = GEN.generate(17, 1, difficulty=band, grid_h=30, grid_w=30,
                        n_anchored_rows=4, n_anchored_cols=4)
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    assert GEN.observe_overrides(grid)["n_anchored_rows"] == 4
    assert GEN.observe_overrides(grid)["n_anchored_cols"] == 4
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_teaches_declared_rivals_under_rotations(band):
    assert getattr(GEN, "CANONICAL_SHORTCUTS", {}), "missing executable shortcut contract"
    assert getattr(GEN, "LESSON_COMPETITORS", {}), "missing lesson rival contract"
    # Two seeds and all eight cyclic starts; complete lessons, not witness marginals.
    for seed in (0, 17):
        for start in range(8):
            pairs = []
            for index in range(start, start + 4):
                grid = GEN.generate(seed, index, difficulty=band)
                assert GEN.self_check(grid) == []
                assert grid == GEN.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": expected(grid)})
            for held_out in range(4):
                demos = [p for i, p in enumerate(pairs) if i != held_out]
                query = pairs[held_out]
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    fits = all(rival(deepcopy(p["input"])) == p["output"] for p in demos)
                    assert not (fits and rival(deepcopy(query["input"])) != query["output"]), name
                assert GEN.lesson_identifiable(demos, query) == []


def test_canonical_shortcut_claims_fit_every_canonical_label():
    assert getattr(GEN, "CANONICAL_SHORTCUTS", {}), "missing shortcut declarations"
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in canonical_pairs("832404dc8a5c", root=ROOT):
            assert rival(deepcopy(pair["input"])) == pair["output"], name


def test_every_canonical_shortcut_has_a_sound_explicit_witness():
    covered = {name for names in GEN.WITNESS_RIVALS.values() for name in names}
    assert set(GEN.CANONICAL_SHORTCUTS) <= covered
    cases = [GEN.generate(17, i, difficulty=band)
             for band in ("easy", "medium", "hard") for i in range(8)]
    cases += [GEN.generate(17, 1, grid_h=6, grid_w=8,
                          n_anchored_rows=4, n_anchored_cols=4),
              GEN.generate(17, 1, lane_palette="base"),
              GEN.generate(17, 1, lane_palette="swapped")]
    fired = set()
    for grid in cases:
        reference = expected(grid)
        for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                fired.add(witness_name)
                for name in GEN.WITNESS_RIVALS[witness_name]:
                    assert GEN.SEMANTIC_RIVALS[name](grid) != reference, (witness_name, name)
    assert fired == set(GEN.SEMANTIC_WITNESSES)


def test_declared_negative_space_and_lawful_identity_edge():
    for size in ((6, 8), (30, 30)):
        h, w = size
        assert GEN.self_check([[6] * w for _ in range(h)])
        grid = GEN.generate(17, 0, grid_h=h, grid_w=w, texture="no_anchors")
        assert GEN.self_check(grid) == []
        assert expected(grid) == grid


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_profile_floor_has_support_in_each_band(band):
    assert callable(getattr(GEN, "strict_canonical_like", None)), "missing strict manifold"
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({v for row in p["input"] for v in row}))
                for p in canonical_pairs("832404dc8a5c", root=ROOT)}
    exact = strict = 0
    for index in range(20):
        grid = GEN.generate(0, index, difficulty=band)
        profile = len(grid), len(grid[0]), len({v for row in grid for v in row})
        exact += profile in profiles
        strict += GEN.strict_canonical_like(grid) == []
    assert exact >= 5 and strict >= 5
