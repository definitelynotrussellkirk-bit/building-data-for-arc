from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import load_generator

gen = load_generator()


def test_rejects_unknown_override_axis():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)


def test_declares_only_real_constructive_axes():
    assert set(gen.AXES) == {
        "grid_h", "grid_w", "n_pairs", "palette_kind", "orientation_family"
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    dict(grid_h=7, grid_w=13, n_pairs=4,
         palette_kind="high", orientation_family="diagonal"),
    dict(grid_h=13, grid_w=7, n_pairs=3,
         palette_kind="low", orientation_family="axis_aligned"),
])
def test_honors_every_override_in_every_band(band, options):
    from reference_probe import observed

    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


def test_canonical_pairs_match_independent_authority_translation():
    from reference_probe import canonical_pairs, reference_output

    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]


def test_generated_inputs_are_deterministic_and_authority_lawful():
    from reference_probe import reference_output

    for band in (None, "easy", "medium", "hard"):
        for index in range(40):
            grid = gen.generate(1000 + index, index * 7, difficulty=band)
            assert grid == gen.generate(1000 + index, index * 7, difficulty=band)
            assert gen.self_check(grid) == []
            output = reference_output(grid)
            assert len(output) == len(grid)
            assert len(output[0]) == len(grid[0])
            assert any(value == 8 for row in output for value in row)


def test_strict_canonical_hook_accepts_all_canonical_inputs():
    from reference_probe import canonical_pairs

    assert hasattr(gen, "strict_canonical_like")
    for pair in canonical_pairs():
        assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_has_canonical_profile_and_strict_support_in_each_band(band):
    exact = 0
    strict = 0
    for seed in range(20):
        grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
        profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        exact += profile in {(9, 9, 3), (10, 10, 3), (11, 11, 3)}
        strict += gen.strict_canonical_like(grid) == []
    assert exact >= 1
    assert strict >= 1


def test_fixed_color_role_shortcut_fits_canonical_but_fails_swapped_roles():
    from reference_probe import (
        canonical_pairs, fixed_color_roles_output, reference_output,
        swapped_roles_witness,
    )

    assert "fixed_color_roles" in gen.CANONICAL_SHORTCUTS
    rival = gen.CANONICAL_SHORTCUTS["fixed_color_roles"]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]
        assert fixed_color_roles_output(pair["input"]) == pair["output"]

    witness = swapped_roles_witness()
    assert gen.self_check(witness) == []
    assert rival(witness) == fixed_color_roles_output(witness)
    assert rival(witness) != reference_output(witness)


def test_semantic_witness_binds_fixed_role_rival_to_real_counterexamples():
    from reference_probe import reference_output, swapped_roles_witness

    name = "fixed_color_role_counterexample"
    assert name in gen.SEMANTIC_WITNESSES
    assert "fixed_color_roles" in gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS[name] == ["fixed_color_roles"]
    witness = swapped_roles_witness()
    assert gen.SEMANTIC_WITNESSES[name](witness) is True
    assert gen.SEMANTIC_RIVALS["fixed_color_roles"](witness) != reference_output(witness)

    emitted = gen.generate(
        17, 1, grid_h=7, grid_w=7, n_pairs=2,
        palette_kind="low", orientation_family="axis_aligned",
    )
    assert gen.SEMANTIC_WITNESSES[name](emitted) is True
    assert gen.SEMANTIC_RIVALS["fixed_color_roles"](emitted) != reference_output(emitted)


def test_every_three_pair_window_and_rotation_refutes_fixed_color_roles():
    from reference_probe import reference_output

    assert gen.EXAMPLES_NEEDED == 2
    assert gen.LESSON_COMPETITORS["fixed_color_roles"] is gen.SEMANTIC_RIVALS["fixed_color_roles"]
    for start in range(12):
        pairs = []
        for index in range(start, start + 3):
            grid = gen.generate(
                99, index, difficulty="medium", grid_h=10, grid_w=10,
                n_pairs=2, palette_kind="low", orientation_family="axis_aligned",
            )
            pairs.append({"input": grid, "output": reference_output(grid)})
        for query_index in range(3):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            query = pairs[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            assert any(
                gen.LESSON_COMPETITORS["fixed_color_roles"](pair["input"]) != pair["output"]
                for pair in demos
            )


@pytest.mark.parametrize("difficulty", ["__invalid_difficulty__", 1, True])
def test_rejects_invalid_difficulty_scalars(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_rejects_noninteger_seed(seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, -1])
def test_rejects_invalid_sample_index(sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(0, sample_index)
