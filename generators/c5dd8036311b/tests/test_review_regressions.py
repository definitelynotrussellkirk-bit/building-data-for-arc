"""Regressions for measured profile, scalar and teaching defects."""
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("c5dd8036311b", root=ROOT)


@pytest.mark.parametrize("name,value", [
    ("seed", True), ("seed", False),
    ("seed", 1.5), ("sample_index", True), ("sample_index", False),
    ("sample_index", -1), ("sample_index", 1.5),
])
def test_invalid_scalar_call_arguments_are_rejected(name, value):
    args = {"seed": 991, "sample_index": 0, name: value}
    with pytest.raises(ValueError):
        GEN.generate(**args)


def signature(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


@pytest.mark.parametrize("seed", [-1, 2**32, 153800779826655, 2**100])
def test_integer_seeds_are_not_truncated_to_uint32(seed):
    # The semantic/profile checks use 48-bit seeds; GenCtx accepts Python ints.
    first = GEN.generate(seed, 3037, difficulty="medium")
    assert GEN.self_check(first) == []
    assert first == GEN.generate(seed, 3037, difficulty="medium")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_exact_canonical_profiles_and_large_scenes(band):
    canonical = {signature(pair["input"]) for pair in canonical_pairs("c5dd8036311b", root=ROOT)}
    grids = [GEN.generate(1729, i, difficulty=band) for i in range(160)]
    assert sum(signature(g) in canonical for g in grids) >= 24
    assert any(max(len(g), len(g[0])) > 20 for g in grids)
    assert any(len(g) == len(g[0]) == 30 for g in grids)
    assert all(GEN.self_check(g) == [] for g in grids)


def test_previous_linear_seed_index_alias_is_broken():
    assert GEN.generate(1, 2) != GEN.generate(19, 21)


def test_four_pair_lessons_have_distinct_marker_profiles_before_deduplication():
    # Distinct marker multisets imply distinct inputs, even when all geometric
    # randomness happens to coincide. This protects the teaching schedule from
    # the production sampler's within-lesson duplicate rejection.
    for seed in (0, 1, 17, 1729):
        for start in range(48):
            profiles = []
            for index in range(start, start + 4):
                grid = GEN.generate(seed, index)
                bar = next(row for row in grid if 1 in row)
                profiles.append((bar.count(2), bar.count(8)))
            assert len(set(profiles)) == 4, (seed, start, profiles)


def test_declared_shortcuts_fit_all_canonical_pairs_but_have_generated_refutations():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert len(shortcuts) >= 5, "Missing executable canonical-fitting shortcut declarations"
    pairs = canonical_pairs("c5dd8036311b", root=ROOT)
    for name, rival in shortcuts.items():
        assert all(rival(deepcopy(p["input"])) == p["output"] for p in pairs), name
        assert any(
            rival(g := GEN.generate(1729, i)) != GEN.rule_mirror(g)
            for i in range(8)
        ), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_start_and_query_rotation_retains_teaching_witness(band):
    hook = getattr(GEN, "lesson_identifiable", None)
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert callable(hook) and rivals, "Missing executable lesson contract"
    assert GEN.EXAMPLES_NEEDED == 3
    for seed in (0, 1, 17, 1729):
        for start in range(16):
            pairs = []
            for index in range(start, start + 4):
                grid = GEN.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [p for i, p in enumerate(pairs) if i != query_index]
                assert hook(deepcopy(demos), deepcopy(query)) == []
                for name, rival in rivals.items():
                    fits = all(rival(deepcopy(p["input"])) == p["output"] for p in demos)
                    assert not fits or rival(deepcopy(query["input"])) == query["output"], (
                        band, seed, start, query_index, name
                    )


def test_lesson_contract_detects_the_previously_missing_adjacency_witness():
    hook = getattr(GEN, "lesson_identifiable", None)
    assert callable(hook), "Missing executable lesson contract"
    demos = canonical_pairs("c5dd8036311b", root=ROOT)[:3]
    grid = [[0] * 8 for _ in range(9)]
    grid[4] = [2, 8, 1, 2, 1, 8, 1, 2]
    query = {"input": grid, "output": GEN.rule_mirror(grid)}
    reasons = hook(demos, query)
    assert reasons and any("adjacent" in reason for reason in reasons)


def test_large_dense_case_preserves_bar_and_has_independent_column_semantics():
    grid = [[0] * 30 for _ in range(30)]
    grid[20] = [1] * 30
    for col, color in ((0, 2), (1, 8), (8, 2), (15, 8), (21, 2), (29, 2)):
        grid[20][col] = color
    assert GEN.self_check(grid) == []
    out = GEN.rule_mirror(grid)
    assert out[20] == grid[20]
    assert [out[r][0] for r in range(16, 20)] == [2, 1, 1, 1]
    assert [out[r][1] for r in range(17, 20)] == [8, 1, 1]
    assert out[15] == grid[15] and out[21:] == grid[21:]
