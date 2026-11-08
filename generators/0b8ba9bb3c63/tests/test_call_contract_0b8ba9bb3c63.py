"""Regressions for scalar coercions found by the actual baseline defect lint."""
import pytest

from reviewer_support import find_root, load_selected_generator


@pytest.fixture(scope="module")
def generator():
    module, _, _ = load_selected_generator("0b8ba9bb3c63", root=find_root(__file__))
    return module


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_seed_rejects_non_integer_values(generator, bad):
    with pytest.raises(ValueError, match="seed"):
        generator.generate(bad, 0, difficulty="easy")


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None, -1])
def test_index_rejects_non_integer_and_negative_values(generator, bad):
    with pytest.raises(ValueError, match="sample_index"):
        generator.generate(991, bad, difficulty="easy")


def test_signed_integer_seed_and_zero_index_remain_usable(generator):
    grid = generator.generate(-1, 0, difficulty="easy", scene_family="generalized")
    assert generator.self_check(grid) == []
