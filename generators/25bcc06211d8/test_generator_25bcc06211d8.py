from __future__ import annotations

import copy
import importlib
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.canonical_profile_gate import canonical_pairs

gen = importlib.import_module("puzzle_generators.per_puzzle.25bcc06211d8.generator")


def test_canonical_inputs_and_outputs_match() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        input_grid = pair["input"]
        output_grid = pair["output"]
        assert gen.self_check(input_grid) == []
        assert gen.rule_mirror(input_grid) == output_grid


def test_default_generation_is_deterministic_fresh_and_rng_pure() -> None:
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(17, 9, difficulty="hard")
    after = random.getstate()
    replay = gen.generate(17, 9, difficulty="hard")
    assert first == replay
    assert first is not replay
    assert all(a is not b for a, b in zip(first, replay))
    assert before == after


def test_exact_override_boundaries_are_observable() -> None:
    for height in (9, 12):
        for width in (9, 12):
            for object_count in (2, 3):
                for profile in gen.CENTER_PROFILES:
                    grid = gen.generate(
                        991,
                        7,
                        difficulty="easy",
                        grid_h=height,
                        grid_w=width,
                        object_count=object_count,
                        center_profile=profile,
                    )
                    assert gen.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "object_count": object_count,
                        "center_profile": profile,
                    }
                    assert gen.self_check(grid) == []


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)


def test_ordinary_scenes_fire_and_make_two_sided_edits() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(2000 + sample_index, sample_index, difficulty=band)
            output = gen.rule_mirror(grid)
            assert output != grid
            for component in gen._components(grid):
                cross = gen._bbox_cross(component)
                assert component - cross
                assert cross - component


def test_every_schedule_window_establishes_both_tie_axes() -> None:
    for start in range(12):
        demos = []
        for index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(7000 + index, index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(9000 + start, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(copy.deepcopy(grid)), name
