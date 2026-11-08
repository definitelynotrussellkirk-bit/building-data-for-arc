from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.364829da8490.generator")


def _canonical_row():
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical task missing")


def test_canonical_inputs_are_accepted_and_mirrored_exactly():
    row = _canonical_row()
    for pair in row["train"] + row["test"]:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_profiles_realize_exact_overrides_at_dimension_boundaries():
    for height, width in ((9, 11), (16, 18)):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                200 + index,
                index,
                difficulty="medium",
                grid_h=height,
                grid_w=width,
                scene_profile=profile,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {
                "grid_h": height,
                "grid_w": width,
                "scene_profile": profile,
            }


def test_every_four_sample_window_contains_all_profiles():
    for start in range(16):
        profiles = {
            gen.observe_overrides(gen.generate(77, index, difficulty="hard"))["scene_profile"]
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        }
        assert profiles == set(gen.SCENE_PROFILES)


def test_lessons_refute_named_competitors():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(501, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(501, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(12345)
    state = random.getstate()
    first = gen.generate(41, 3, difficulty="easy")
    assert random.getstate() == state
    second = gen.generate(41, 3, difficulty="easy")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(41, 3, difficulty="easy")


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, mystery_axis="ignored-before-v2")


def test_border_touching_wall_still_fills():
    grid = gen.generate(2, 0, difficulty="easy", scene_profile="rect_pair")
    facts = gen.semantic_observables(grid)
    assert facts["border_touching_fillable_count"] >= 1
    output = gen.rule_mirror(grid)
    assert output != grid
