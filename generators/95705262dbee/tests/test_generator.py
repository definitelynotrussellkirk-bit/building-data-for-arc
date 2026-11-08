"""Portable regression tests for the size-sort-and-pack generator."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "95705262dbee"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


@pytest.mark.parametrize("pair", _canonical())
def test_canonical_inputs_are_accepted_and_python_mirror_matches_labels(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_scheduled_draws_are_strict_deterministic_and_cover_all_profiles(band):
    profiles = set()
    grid_profiles = set()
    for index in range(24):
        grid = gen.generate(7123, index, difficulty=band)
        assert grid == gen.generate(7123, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        observed = gen.observe_overrides(grid)
        profiles.add(observed["size_profile"])
        grid_profiles.add((observed["grid_h"], observed["grid_w"]))
        assert gen.rule_mirror(grid) != grid
    assert profiles == set(gen.SIZE_PROFILES)
    assert grid_profiles == set(gen.CANONICAL_GRID_PROFILES)


def test_difficulty_bands_are_observably_distinct_for_the_same_draw():
    for seed in range(8):
        grids = [
            gen.generate(seed, seed % gen.LESSON_SCHEDULE_PERIOD, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({repr(grid) for grid in grids}) == 3


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["canonical_345", "canonical_358", "canonical_458"])
def test_exact_overrides_are_observable_in_every_band(band, profile):
    expected = {"grid_h": 12, "grid_w": 14, "size_profile": profile}
    grid = gen.generate(91, 17, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 9},
        {"grid_h": 13},
        {"grid_w": 11},
        {"grid_w": 15},
        {"grid_h": True},
        {"grid_w": 12.5},
        {"size_profile": "unknown"},
        {"size_profile": 345},
    ],
)
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_generated_examples_refute_named_single_example_shortcuts():
    for index in range(24):
        grid = gen.generate(441, index)
        truth = gen.rule_mirror(grid)
        assert gen.SEMANTIC_RIVALS["descending_area"](grid) != truth
        assert gen.SEMANTIC_RIVALS["input_order"](grid) != truth
        assert gen.SEMANTIC_RIVALS["color_order"](grid) != truth
        if gen.observe_overrides(grid)["size_profile"] != "canonical_345":
            assert gen.SEMANTIC_RIVALS["bbox_area"](grid) != truth


def test_every_three_demo_window_refutes_all_declared_competitors():
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        pairs = []
        for offset in range(4):
            grid = gen.generate(1201, start + offset, difficulty="medium")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        demos, query = pairs[:3], {"input": pairs[3]["input"]}
        assert gen.lesson_identifiable(demos, query) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_declared_semantic_witnesses_change_the_named_rival_prediction():
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        rival_names = gen.WITNESS_RIVALS[name]
        found = False
        for index in range(gen.LESSON_SCHEDULE_PERIOD * 2):
            grid = gen.generate(808, index)
            if witness(grid):
                found = True
                truth = gen.rule_mirror(grid)
                assert all(gen.SEMANTIC_RIVALS[rival](grid) != truth for rival in rival_names)
                break
        assert found, name


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert gen.self_check(grid), name
