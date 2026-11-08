"""Reject incomplete template/seed scenes without restricting lawful templates."""
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


@pytest.fixture(scope="module")
def generator():
    return load_selected_generator("78a914ac492e", root=find_root(__file__))[0]


@pytest.mark.parametrize("texture", ["no_template", "no_seeds", "full_grid"])
def test_rejects_declared_missing_object_degenerates(generator, texture):
    grid = generator.generate(17, 0, texture=texture)
    assert generator.self_check(grid), f"Accepted invalid {texture} input"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_accepts_generated_template_and_seed_scenes(generator, difficulty):
    grid = generator.generate(17, 0, difficulty=difficulty)
    assert generator.self_check(grid, difficulty=difficulty) == []


def test_accepts_canonical_input_shapes(generator):
    for pair in canonical_pairs("78a914ac492e", root=find_root(__file__)):
        assert generator.self_check(pair["input"]) == [], (
            pair["variant"], pair["split"], pair["pair_index"]
        )
