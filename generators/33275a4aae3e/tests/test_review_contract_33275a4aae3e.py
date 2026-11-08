"""Request-contract regressions; also run through the portable task-test stage."""
import pytest
from reviewer_support import find_root, load_selected_generator

TASK_ID = "33275a4aae3e"

@pytest.fixture(scope="module")
def generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]

@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None, [], {}])
def test_seed_rejects_non_integer_scalars(generator, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(value, 0)

@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", None, -1, [], {}])
def test_sample_index_rejects_non_integer_or_negative_values(generator, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(991, value)

@pytest.mark.parametrize("value", [True, False, 0, 1.0, "__invalid_difficulty__", [], {}])
def test_difficulty_rejects_unsupported_values(generator, value):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(991, 0, difficulty=value)

@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_valid_requests_remain_lawful_and_deterministic(generator, band):
    first = generator.generate(991, 0, difficulty=band)
    second = generator.generate(991, 0, difficulty=band)
    assert first == second
    assert first is not second
    assert generator.self_check(first) == []

def test_boolean_grid_cells_are_rejected(generator):
    grid = generator.generate(991, 0)
    r, c = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0)
    grid[r][c] = False
    assert generator.self_check(grid), "Boolean False must not silently masquerade as ARC color 0"
