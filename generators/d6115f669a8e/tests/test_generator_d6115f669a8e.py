"""Task-local contract tests for d6115f669a8e.

The production Racket rule is the label authority.  Python helpers in the
selected generator are diagnostic mirrors used to test distribution quality.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == "d6115f669a8e":
                return record
    raise AssertionError("canonical task not found")


gen = _load_generator()
CANONICAL = _canonical_record()
CANONICAL_PAIRS = CANONICAL["train"] + CANONICAL["test"]


def test_authority_pin_and_canonical_examples_are_accepted():
    assert gen.RULE_HASH == "e09122d9163c"
    for pair in CANONICAL_PAIRS:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_default_five_example_cycle_is_valid_and_teaches_every_declared_competitor():
    assert gen.EXAMPLES_NEEDED == 5
    for band in (None, "easy", "medium", "hard"):
        for seed in range(3):
            demos = []
            profiles = []
            for index in range(5):
                grid = gen.generate(seed, index, difficulty=band)
                assert gen.self_check(grid) == []
                assert grid == gen.generate(seed, index, difficulty=band)
                profiles.append(gen.schedule_profile(seed, index, band))
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert set(profiles) == set(gen.SCHEDULE_PROFILES)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_every_helpful_texture_honors_exact_dimensions_and_is_lawful():
    for texture in gen.HELPFUL_TEXTURES:
        for h, w in ((7, 9), (12, 14), (18, 20)):
            grid = gen.generate(17, 4, difficulty="easy", texture=texture, grid_h=h, grid_w=w)
            assert (len(grid), len(grid[0])) == (h, w)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}


@pytest.mark.parametrize("kwargs", [
    {"typo_axis": 1},
    {"grid_h": 6},
    {"grid_h": 19},
    {"grid_w": 8},
    {"grid_w": 21},
    {"grid_h": True},
    {"grid_w": 10.5},
    {"texture": "not-a-profile"},
])
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


def test_each_band_contains_a_canonical_profile_in_every_cycle():
    canonical_profiles = {(7, 9, 4), (9, 9, 4), (9, 10, 4)}
    for band in ("easy", "medium", "hard"):
        observed = []
        strict = 0
        for index in range(10):
            grid = gen.generate(91, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            observed.append(profile)
            strict += bool(gen.strict_canonical_like(grid))
        assert canonical_profiles.intersection(observed)
        assert strict >= 2


def test_only_real_canonical_shortcuts_are_declared():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL_PAIRS), name
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(
            rival(gen.generate(301, index)) != gen.rule_mirror(gen.generate(301, index))
            for index in range(gen.EXAMPLES_NEEDED)
        ), name


def test_self_check_rejects_malformed_or_wrong_component_count_inputs():
    for grid in (None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)]):
        assert gen.self_check(grid)
    assert gen.self_check([[0] * 9 for _ in range(7)])
