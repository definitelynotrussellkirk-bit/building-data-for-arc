"""Strict call-argument regression for the selected generator in either layout."""
import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("7fc158ab7b70", root=find_root(__file__))


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_must_be_an_integer_not_a_coercible_scalar(seed, difficulty):
    with pytest.raises(TypeError, match="seed must be an int"):
        GEN.generate(seed, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [-17, 0, 991, 2**80 + 1])
def test_actual_integer_seeds_remain_supported_and_deterministic(seed, difficulty):
    first = GEN.generate(seed, 7, difficulty=difficulty)
    second = GEN.generate(seed, 7, difficulty=difficulty)
    assert first == second
    assert first is not second
    assert GEN.self_check(first) == []
