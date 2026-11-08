"""Public request-contract regressions for the periodic staircase generator.

Seeds are signed Python integers; sample indices are nonnegative integers.
Exact period overrides are literal integers in 4..9. None retains the public
"no override" convention. These tests use the selected source in their own tree.
"""

from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("8e6c44aee812", root=find_root(__file__))
BANDS = (None, "easy", "medium", "hard")
NON_INTEGER_CONTROLS = (
    pytest.param(False, id="false"),
    pytest.param(True, id="true"),
    pytest.param(1.0, id="integral-float"),
    pytest.param(1.75, id="fractional-float"),
    pytest.param("1", id="numeric-string"),
    pytest.param(None, id="none"),
)


@pytest.mark.parametrize("seed", NON_INTEGER_CONTROLS)
def test_generate_rejects_non_integer_seed(seed) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", NON_INTEGER_CONTROLS)
def test_generate_rejects_non_integer_sample_index(sample_index) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, sample_index)


@pytest.mark.parametrize("sample_index", (-1, -12))
def test_generate_rejects_negative_sample_index(sample_index: int) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, sample_index)


@pytest.mark.parametrize("seed", (-(2**80), -1, 0, 2**32 - 1, 2**80))
@pytest.mark.parametrize("sample_index", (0, 11, 12, 2**32, 2**80))
def test_literal_integer_controls_keep_their_documented_domain(
    seed: int, sample_index: int
) -> None:
    # GenCtx does not declare a uint32 bound for seed or a maximum index.
    grid = GEN.generate(seed, sample_index)
    assert GEN.self_check(grid) == []
    assert grid == GEN.generate(seed, sample_index)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize(
    "period",
    (
        pytest.param(False, id="false"),
        pytest.param(True, id="true"),
        pytest.param(4.0, id="lower-integral-float"),
        pytest.param(4.75, id="lower-fractional-float"),
        pytest.param(9.0, id="upper-integral-float"),
        pytest.param(9.75, id="above-upper-fractional-float"),
        pytest.param("4", id="lower-numeric-string"),
        pytest.param("9", id="upper-numeric-string"),
        pytest.param(-1, id="negative"),
        pytest.param(3, id="below-lower-bound"),
        pytest.param(10, id="above-upper-bound"),
    ),
)
def test_exact_period_rejects_coercion_and_out_of_range_values(
    period, difficulty
) -> None:
    # In particular, period=9.75 must not silently produce period 9.
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 0, difficulty=difficulty, period=period)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("period", range(4, 10))
@pytest.mark.parametrize("padding", ("none", "one"))
@pytest.mark.parametrize("pattern_class", ("distinct", "prefix_run", "complex_repeat"))
def test_every_advertised_control_combination_remains_exact(
    difficulty, period: int, padding: str, pattern_class: str
) -> None:
    requested = {
        "period": period,
        "padding": padding,
        "pattern_class": pattern_class,
    }
    grid = GEN.generate(812, 23, difficulty=difficulty, **requested)

    assert GEN.observe_overrides(grid) == requested
    assert GEN.self_check(grid) == []
    assert len(grid) == period + (padding == "one")
    assert all(len(row) == len(grid) for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
    assert grid[-1][-1] == 0 if padding == "one" else grid[-1][-1] != 0


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("sample_index", range(12))
def test_none_overrides_preserve_the_default_curriculum(difficulty, sample_index: int) -> None:
    expected = GEN.generate(812, sample_index, difficulty=difficulty)
    assert GEN.generate(
        812,
        sample_index,
        difficulty=difficulty,
        period=None,
        padding=None,
        pattern_class=None,
    ) == expected
