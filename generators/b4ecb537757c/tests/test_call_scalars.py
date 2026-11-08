"""Call arguments must not silently coerce into another seeded experiment."""
import pytest
from reviewer_support import find_root, load_selected_generator

GEN, _, _ = load_selected_generator("b4ecb537757c", root=find_root(__file__))

@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None])
def test_seed_is_an_integer_without_coercion(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(value, 0)

@pytest.mark.parametrize("value", [True, False, 1.0, "1", -1, None])
def test_sample_index_is_a_nonnegative_integer(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, value)

@pytest.mark.parametrize("value", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_unknown_difficulty_is_rejected(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, difficulty=value)
