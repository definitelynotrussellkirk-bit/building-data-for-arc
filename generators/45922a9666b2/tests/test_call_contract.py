"""Regression for strict public seed and sample-index arguments."""
import pytest

from reviewer_support import find_root, load_selected_generator


generator, _, _ = load_selected_generator("45922a9666b2", root=find_root(__file__))


@pytest.mark.parametrize("axis", ("seed", "sample_index"))
def test_invalid_scalars_are_rejected_before_generation(axis):
    invalid = [True, False, 1.0, 1.75, "1"]
    if axis == "sample_index":
        invalid.append(-1)
    for difficulty in (None, "easy", "medium", "hard"):
        for value in invalid:
            kwargs = {"seed": 991, "sample_index": 0, "difficulty": difficulty}
            kwargs[axis] = value
            with pytest.raises(ValueError, match=axis):
                generator.generate(**kwargs)


def test_integer_seeds_and_nonnegative_indices_remain_supported():
    for seed, index in ((0, 0), (-1, 7), (2**64, 2**32)):
        first = generator.generate(seed, index)
        assert generator.self_check(first) == []
        assert first == generator.generate(seed, index)
