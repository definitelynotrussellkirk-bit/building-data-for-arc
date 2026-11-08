from __future__ import annotations

import copy

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "9bfbec04496c"
ROOT = find_root(__file__)
GEN, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _solid_no_disagreement_mosaic() -> list[list[int]]:
    base = [[2, 3], [4, 5]]
    sep = 6
    grid = [[0 for _ in range(8)] for _ in range(8)]
    for tile_row in range(3):
        for tile_col in range(3):
            row0 = tile_row * 3
            col0 = tile_col * 3
            for row in range(2):
                for col in range(2):
                    grid[row0 + row][col0 + col] = base[row][col]
            if tile_col < 2:
                for row in range(2):
                    grid[row0 + row][col0 + 2] = sep
        if tile_row < 2:
            for col in range(8):
                grid[tile_row * 3 + 2][col] = sep
    return grid


def _labeled(grid: list[list[int]]) -> dict:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_labeled_outputs_are_exact():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_generated_grid_teaches_single_and_multi_outlier_disagreement(difficulty):
    for sample_index in range(16):
        grid = GEN.generate(401, sample_index, difficulty=difficulty)
        facts = GEN.semantic_observables(grid)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert 1 not in {value for row in grid for value in row}
        assert facts["single_outlier_cells"] >= 1
        assert facts["multi_outlier_cells"] >= 1
        assert facts["disagreement_cells"] >= 2
        output = GEN.rule_mirror(grid)
        assert sum(value == 1 for row in output for value in row) == facts["disagreement_cells"]


@pytest.mark.parametrize("n_mut", [2, 3, 4])
@pytest.mark.parametrize("multi_outliers", [2, 3, 4])
def test_observe_overrides_recovers_exact_mutation_axes(n_mut, multi_outliers):
    grid = GEN.generate(808, 3, n_mut=n_mut, multi_outliers=multi_outliers)
    assert GEN.observe_overrides(grid) == {
        "n_mut": n_mut,
        "multi_outliers": multi_outliers,
    }


def test_exact_overrides_are_observable_and_lawful_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grid = GEN.generate(
            73,
            5,
            difficulty=difficulty,
            tile_shape="3x2",
            n_mut=4,
            multi_outliers=4,
            palette_kind="cool",
        )
        facts = GEN.semantic_observables(grid)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert (facts["tile_h"], facts["tile_w"]) == (3, 2)
        assert facts["disagreement_cells"] == 4
        assert facts["max_outliers"] == 4
        assert facts["single_outlier_cells"] >= 1
        assert facts["multi_outlier_cells"] >= 1


def test_every_three_consecutive_examples_refute_a_fixed_2x2_output_shape():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            shapes = {
                tuple(GEN.semantic_observables(GEN.generate(991, start + offset, difficulty=difficulty))[key]
                      for key in ("tile_h", "tile_w"))
                for offset in range(3)
            }
            assert any(shape != (2, 2) for shape in shapes), (difficulty, start, shapes)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[1, 2], [3]],
        [[5]],
        [[5, 5], [5, 5]],
        [[5 for _ in range(8)] for _ in range(8)],
        _solid_no_disagreement_mosaic(),
    ],
)
def test_malformed_minimal_and_no_disagreement_inputs_are_rejected(grid):
    reasons = GEN.self_check(grid)
    assert isinstance(reasons, list)
    assert reasons
    assert GEN.strict_canonical_like(grid)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_an_actual_integer(seed):
    with pytest.raises(TypeError):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "0"])
def test_sample_index_requires_an_actual_integer(sample_index):
    with pytest.raises(TypeError):
        GEN.generate(11, sample_index)


def test_sample_index_must_be_nonnegative():
    with pytest.raises(ValueError):
        GEN.generate(11, -1)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "expert"])
def test_difficulty_rejects_values_outside_the_three_named_bands(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(11, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"tile_shape": "4x4"},
        {"tile_shape": 22},
        {"n_mut": True},
        {"n_mut": "3"},
        {"n_mut": 1},
        {"n_mut": 5},
        {"multi_outliers": True},
        {"multi_outliers": "2"},
        {"multi_outliers": 1},
        {"multi_outliers": 5},
        {"palette_kind": "neon"},
        {"palette_kind": 2},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(11, 0, **overrides)


def test_declared_canonical_shortcuts_fit_every_labeled_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert set(GEN.CANONICAL_SHORTCUTS) == {"eight_to_one_only", "fixed_2x2"}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert shortcut(pair["input"]) == pair["output"], name


def test_each_semantic_witness_refutes_its_named_rival():
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "single_outlier_disagreement",
        "multi_outlier_disagreement",
        "non_2x2_tile",
    }
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)

    grids = [GEN.generate(222, index, difficulty="hard") for index in range(4)]
    for grid in grids:
        official = GEN.rule_mirror(grid)
        for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                rivals = GEN.WITNESS_RIVALS[witness_name]
                assert any(GEN.SEMANTIC_RIVALS[name](grid) != official for name in rivals)

    assert all(GEN.SEMANTIC_WITNESSES["single_outlier_disagreement"](grid) for grid in grids)
    assert all(GEN.SEMANTIC_WITNESSES["multi_outlier_disagreement"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["non_2x2_tile"](grid) for grid in grids)


def test_every_three_demo_window_identifies_the_rule_against_all_competitors():
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [_labeled(GEN.generate(717, start + offset, difficulty=difficulty))
                     for offset in range(GEN.EXAMPLES_NEEDED)]
            query = _labeled(GEN.generate(717, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty))
            assert GEN.lesson_identifiable(demos, query) == [], (difficulty, start)
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    difficulty,
                    start,
                    name,
                )


def test_generation_is_deterministic_fresh_and_does_not_mutate_inputs():
    first = GEN.generate(29, 7, difficulty="medium")
    second = GEN.generate(29, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    before = copy.deepcopy(first)
    GEN.rule_mirror(first)
    GEN.self_check(first)
    GEN.semantic_observables(first)
    assert first == before
