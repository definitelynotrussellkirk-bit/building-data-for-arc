"""Task-local regressions for repairing the defective-copy curriculum."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    canonical_shortcut_fits,
    intended_output,
    largest_component_rival,
    load_generator,
    pair,
    signature,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
PROFILES = ("canonical", "contrast")


def test_metadata_pins_authority_and_declares_only_observable_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == "f705b8f51e62"
    assert gen.RULE_HASH == "4ad429046360"
    assert gen.VERSION == "4.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert set(gen.AXES) == {"profile", "template_size", "n_canon", "missing"}


@pytest.mark.parametrize("item", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_oracle(item):
    assert gen.self_check(item["input"]) == []
    assert gen.strict_canonical_like(item["input"]) == []
    assert intended_output(item["input"]) == item["output"]
    assert gen.rule_mirror(item["input"]) == item["output"]


@pytest.mark.parametrize("band", BANDS)
def test_every_three_consecutive_default_demonstrations_include_color_transfer_witness(band):
    for seed in range(4):
        for start in range(10):
            observed = [
                gen.observe_overrides(gen.generate(seed, start + offset, difficulty=band))["profile"]
                for offset in range(3)
            ]
            assert "contrast" in observed
            assert observed == [
                gen.schedule_profile(seed, start + offset, band) for offset in range(3)
            ]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("template_size,n_canon,missing", [(4, 2, 1), (4, 4, 2), (9, 2, 2), (9, 4, 1)])
def test_extreme_override_combinations_are_exact_observable_and_rule_correct(
    band, profile, template_size, n_canon, missing
):
    grid = gen.generate(
        37,
        11,
        difficulty=band,
        profile=profile,
        template_size=template_size,
        n_canon=n_canon,
        missing=missing,
    )
    expected = {
        "profile": profile,
        "template_size": template_size,
        "n_canon": n_canon,
        "missing": missing,
    }
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == expected
    for key, value in expected.items():
        assert signature(grid)[key] == value
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile": "typo"},
        {"template_size": 3},
        {"template_size": True},
        {"n_canon": 5},
        {"missing": 0},
        {"unknown_axis": 1},
    ],
)
def test_invalid_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_fails_closed(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", BANDS)
def test_generated_distribution_is_deterministic_diverse_and_arc_sized(band):
    serialized = set()
    output_shapes = set()
    profiles = set()
    for index in range(120):
        grid = gen.generate(500 + index, index * 7 + 3, difficulty=band)
        assert grid == gen.generate(500 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        assert 1 <= len(grid) <= 30
        assert 1 <= len(grid[0]) <= 30
        serialized.add(repr(grid))
        output_shapes.add(tuple(tuple(value != 0 for value in row) for row in intended_output(grid)))
        profiles.add(gen.observe_overrides(grid)["profile"])
    assert len(serialized) >= 100
    assert len(output_shapes) >= 20
    assert profiles == set(PROFILES)


def test_canonical_fitting_largest_component_shortcut_gets_a_generated_counterexample():
    assert canonical_shortcut_fits()
    witness = gen.generate(13, 2, profile="contrast", template_size=7, n_canon=3, missing=2)
    assert largest_component_rival(witness) != intended_output(witness)
    assert gen.CANONICAL_SHORTCUTS["crop_largest_component"](witness) != gen.rule_mirror(witness)


def test_declared_semantic_contract_names_real_rival_and_witness():
    assert set(gen.CANONICAL_SHORTCUTS) == {"crop_largest_component"}
    assert set(gen.SEMANTIC_RIVALS) == {"crop_largest_component"}
    assert set(gen.LESSON_COMPETITORS) == {"crop_largest_component"}
    assert set(gen.SEMANTIC_WITNESSES) == {"defective_color_transfer"}
    assert gen.WITNESS_RIVALS == {
        "defective_color_transfer": ["crop_largest_component"]
    }


@pytest.mark.parametrize("band", BANDS)
def test_every_three_demo_lesson_and_every_single_query_rotation_eliminates_rival(band):
    rival = gen.LESSON_COMPETITORS["crop_largest_component"]
    for start in range(12):
        pairs = [pair(gen.generate(991, start + offset, difficulty=band)) for offset in range(4)]
        demos, query = pairs[:3], pairs[3]
        assert gen.lesson_identifiable(demos, query) == []
        assert not all(rival(item["input"]) == item["output"] for item in demos)
        for query_index in range(4):
            rotated_query = pairs[query_index]
            rotated_demos = [item for index, item in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(rotated_demos, rotated_query) == []
            assert not all(rival(item["input"]) == item["output"] for item in rotated_demos)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[0] * 9 for _ in range(7)],
        [[1, 1, 0, 1, 1], [0, 1, 0, 0, 1]],  # only two full components, no defect
    ],
)
def test_self_check_rejects_malformed_or_out_of_grammar_inputs(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_structure_destroying_mutations():
    base = gen.generate(17, 3, profile="contrast", template_size=8, n_canon=3, missing=2)
    mutations = []

    all_background = [[0 for _ in row] for row in base]
    mutations.append(all_background)

    wrong_defect_color = deepcopy(base)
    observed = gen.observe_overrides(base)
    assert observed["profile"] == "contrast"
    # Repaint one cell of the defective component to split its monochrome identity.
    sizes = []
    for color, cells in gen._components(wrong_defect_color):
        sizes.append((len(cells), color, cells))
    _, _, defective_cells = min(sizes)
    row, col = defective_cells[0]
    wrong_defect_color[row][col] = 9 if wrong_defect_color[row][col] != 9 else 8
    mutations.append(wrong_defect_color)

    for changed in mutations:
        assert gen.self_check(changed)


def test_rule_mirror_is_pure():
    grid = gen.generate(31, 3, profile="contrast", template_size=9, n_canon=4, missing=2)
    original = deepcopy(grid)
    output = gen.rule_mirror(grid)
    assert grid == original
    assert output == intended_output(grid)
    assert output is not grid

@pytest.mark.parametrize(
    "band,size_bounds,copy_bounds,missing_values",
    [
        ("easy", (4, 5), (3, 4), {1}),
        ("medium", (5, 7), (2, 4), {1, 2}),
        ("hard", (7, 9), (2, 3), {2}),
    ],
)
def test_default_contrast_examples_express_difficulty_progression(
    band, size_bounds, copy_bounds, missing_values
):
    observed = [
        gen.observe_overrides(gen.generate(seed, seed, difficulty=band, profile="contrast"))
        for seed in range(1, 25)
    ]
    assert all(size_bounds[0] <= item["template_size"] <= size_bounds[1] for item in observed)
    assert all(copy_bounds[0] <= item["n_canon"] <= copy_bounds[1] for item in observed)
    assert {item["missing"] for item in observed} <= missing_values
    assert len({repr(gen.generate(seed, seed, difficulty=band)) for seed in range(1, 13)}) >= 10


def test_difficulty_bands_are_not_byte_identical_on_default_calls():
    triplets = [
        tuple(
            repr(gen.generate(seed, seed, difficulty=band))
            for band in ("easy", "medium", "hard")
        )
        for seed in range(1, 13)
    ]
    assert any(len(set(triplet)) > 1 for triplet in triplets)
