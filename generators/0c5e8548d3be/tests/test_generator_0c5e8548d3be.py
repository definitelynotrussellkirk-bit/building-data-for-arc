"""Behavioral regressions for the rotation-equivalence-matrix generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    class_sizes,
    color_output,
    count_output,
    dihedral_output,
    facts,
    has_mirror_only_pair,
    has_rotation_not_exact,
    load_generator,
    relation_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_canonical_examples_are_accepted_and_python_oracle_matches_labels():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert relation_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_validation_ignores_unrelated_metadata():
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"], meta={"source": "canonical"}) == []
        assert gen.self_check(pair["input"], meta={"overrides": {}}) == []


def test_public_contract_is_minimal_rule_bound_and_exactly_observable():
    assert gen.RULE_HASH == "c0e3bdee7bdc"
    assert set(gen.AXES) == {"grid_h", "shape_size", "relation_profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.HELPFUL_TEXTURES == ()

    for difficulty in (None, "easy", "medium", "hard"):
        for grid_h in (5, 8):
            for shape_size in (4, 8, 12):
                for relation_profile in (0, 1, 2):
                    requested = {
                        "grid_h": grid_h,
                        "shape_size": shape_size,
                        "relation_profile": relation_profile,
                    }
                    grid = gen.generate(9001, 37, difficulty=difficulty, **requested)
                    assert gen.self_check(grid, meta={"overrides": requested}) == []
                    assert gen.observe_overrides(grid) == requested
                    assert class_sizes(grid) == {
                        0: (2, 2),
                        1: (1, 3),
                        2: (1, 1, 2),
                    }[relation_profile]


@pytest.mark.parametrize(
    "key,value",
    [
        ("__unknown_axis__", 1),
        ("grid_h", 4), ("grid_h", 9), ("grid_h", True), ("grid_h", 5.0),
        ("shape_size", 3), ("shape_size", 13), ("shape_size", False),
        ("relation_profile", -1), ("relation_profile", 3), ("relation_profile", "0"),
    ],
)
def test_unknown_and_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(3, 4, **{key: value})


@pytest.mark.parametrize("difficulty", ["typo", "", True, 3, 0.5])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        gen.generate(3, 4, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_none_override_means_unset(difficulty):
    baseline = gen.generate(22, 7, difficulty=difficulty)
    for axis in gen.AXES:
        assert gen.generate(22, 7, difficulty=difficulty, **{axis: None}) == baseline


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_default_grid_contains_the_semantic_counterexamples(difficulty):
    unique_inputs = set()
    for index in range(60):
        grid = gen.generate(7000 + index, 17 * index + 5, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(7000 + index, 17 * index + 5, difficulty=difficulty)
        assert gen.rule_mirror(grid) == relation_output(grid)
        info = facts(grid)
        assert len(set(info["counts"])) == 1
        assert len({next(iter(colors)) for colors in info["colors"]}) == 4
        assert all(8 not in row for row in grid)
        assert has_rotation_not_exact(grid)
        assert has_mirror_only_pair(grid)
        intended = relation_output(grid)
        assert count_output(grid) != intended
        assert dihedral_output(grid) != intended
        assert color_output(grid) != intended
        unique_inputs.add(repr(grid))
    assert len(unique_inputs) >= 58


def test_default_schedule_supplies_canonical_support_all_profiles_and_live_bands():
    assert gen.MIN_STRICT_FRAC >= 0.50
    by_band = {}
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(41, index, difficulty=difficulty) for index in range(12)]
        by_band[difficulty] = grids
        assert sum(not gen.strict_canonical_like(grid) for grid in grids) == 9
        assert {facts(grid)["relation_profile"] for grid in grids} == {0, 1, 2}
        assert any(len(grid) == 5 for grid in grids)
    assert by_band["easy"] != by_band["medium"]
    assert by_band["medium"] != by_band["hard"]
    assert by_band["easy"] != by_band["hard"]


def test_declared_semantic_contract_refutes_every_competitor_in_each_demo():
    assert set(gen.LESSON_COMPETITORS) == {
        "cell_count_equivalence",
        "exact_shape_without_rotation",
        "reflection_equivalence",
        "same_panel_color",
    }
    for difficulty in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(991, sample_index, difficulty=difficulty)
            demos.append({"input": grid, "output": relation_output(grid)})
        query_grid = gen.generate(991, gen.EXAMPLES_NEEDED, difficulty=difficulty)
        query = {"input": query_grid, "output": relation_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert all(rival(pair["input"]) != pair["output"] for pair in demos), name
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert all(witness(pair["input"]) for pair in demos), name


def test_replay_returns_fresh_grids_and_preserves_global_rng():
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(77, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert second == gen.generate(77, 9, difficulty="hard")
    assert before == middle == after


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(71, 8, grid_h=5, shape_size=7, relation_profile=0)
    assert gen.self_check(valid) == []

    broken_separator = deepcopy(valid)
    broken_separator[0][5] = 1
    assert "separator" in " ".join(gen.self_check(broken_separator)).lower()

    output_color_in_input = deepcopy(valid)
    row, col = next(
        (row, col)
        for row, values in enumerate(output_color_in_input)
        for col, value in enumerate(values)
        if value != 0
    )
    output_color_in_input[row][col] = 8
    assert "color 8" in " ".join(gen.self_check(output_color_in_input)).lower()

    empty_panel = deepcopy(valid)
    for row in empty_panel:
        row[0:5] = [0] * 5
    assert "nonempty" in " ".join(gen.self_check(empty_panel)).lower()


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 0]], [[True] * 23 for _ in range(5)], [[0.0] * 23 for _ in range(5)]],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list)
    assert errors
    assert all(isinstance(error, str) and error for error in errors)


def test_declared_finite_output_codomain_is_exactly_covered():
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 13
    outputs = {
        repr(gen.rule_mirror(gen.generate(seed, sample_index, difficulty=difficulty)))
        for difficulty in ("easy", "medium", "hard")
        for seed in range(16)
        for sample_index in range(12)
    }
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN
