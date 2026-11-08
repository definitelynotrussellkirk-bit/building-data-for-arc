"""Public call arguments must fail explicitly instead of aliasing valid draws."""
import pytest

from reviewer_support import find_root, load_selected_generator

GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(
    "77e3acd21c5d", root=find_root(__file__)
)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_a_literal_integer(seed, band):
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(seed, 0, difficulty=band)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("index", [True, False, 1.0, 1.75, "1", None])
def test_sample_index_requires_a_literal_integer(index, band):
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(991, index, difficulty=band)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_negative_sample_index_is_rejected(band):
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(991, -1, difficulty=band)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, [], {}])
def test_difficulty_requires_none_or_a_string(difficulty):
    with pytest.raises(TypeError, match="difficulty"):
        GEN.generate(991, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", ["", "Easy", "__invalid_difficulty__"])
def test_unknown_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(991, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", [-2**100, -1, 0, 2**48 + 17, 2**100])
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_signed_and_wide_integer_seeds_remain_supported(seed, band):
    grid = GEN.generate(seed, 0, difficulty=band)
    assert GEN.self_check(grid) == []
    assert GEN.generate(seed, 0, difficulty=band) == grid
