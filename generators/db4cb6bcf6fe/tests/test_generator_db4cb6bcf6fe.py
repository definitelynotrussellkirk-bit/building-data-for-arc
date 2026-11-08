from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "generators" / "db4cb6bcf6fe" / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))

_spec = importlib.util.spec_from_file_location("reviewed_db4cb6bcf6fe", GENERATOR_PATH)
assert _spec is not None and _spec.loader is not None
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def _canonical_pairs() -> list[dict]:
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "db4cb6bcf6fe":
            return [*row["train"], row["test"]]
    raise AssertionError("canonical task db4cb6bcf6fe was not found")


def _pair(seed: int, sample_index: int, difficulty: str | None = None) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_mirror_and_shortcuts_match_every_canonical_pair() -> None:
    assert gen.RULE_HASH == "38e335f43e6f"
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "raw_markers",
        "bbox_dimensions",
        "completed_area",
    }

    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
            assert shortcut(pair["input"]) == pair["output"], name


def test_scene_profile_is_the_only_override_and_round_trips() -> None:
    assert set(gen.AXES) == {"scene_profile"}
    assert tuple(gen.SCENE_PROFILES) == tuple(gen.PROFILE_DIMS)

    for profile, expected_dims in gen.PROFILE_DIMS.items():
        for difficulty in (None, "easy", "medium", "hard"):
            grid = gen.generate(
                23,
                7,
                difficulty=difficulty,
                scene_profile=profile,
            )
            assert (len(grid), len(grid[0])) == expected_dims
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.self_check(grid, difficulty=difficulty) == []

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, invented_axis="nope")
    with pytest.raises(ValueError, match="scene_profile"):
        gen.generate(0, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="nightmare")


def test_every_generated_case_refutes_each_plausible_shortcut() -> None:
    assert set(gen.SEMANTIC_RIVALS) == set(gen.CANONICAL_SHORTCUTS)
    assert set(gen.LESSON_COMPETITORS) == set(gen.CANONICAL_SHORTCUTS)
    assert set(gen.WITNESS_RIVALS) == set(gen.SEMANTIC_WITNESSES)

    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(4):
            for sample_index in range(12):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                truth = gen.rule_mirror(grid)
                assert gen.self_check(grid, difficulty=difficulty) == []
                assert gen.strict_canonical_like(grid) == []

                for name, rival in gen.SEMANTIC_RIVALS.items():
                    assert rival(grid) != truth, (difficulty, seed, sample_index, name)

                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    assert witness(grid) is True, (difficulty, seed, sample_index, name)
                    assert gen.WITNESS_RIVALS[name]


def test_every_consecutive_three_demo_lesson_is_identifiable() -> None:
    for difficulty in (None, "easy", "medium", "hard"):
        pairs = [_pair(71, index, difficulty) for index in range(12)]
        for start in range(0, len(pairs) - gen.EXAMPLES_NEEDED):
            demos = pairs[start : start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []


def test_generation_is_deterministic_and_does_not_touch_global_random() -> None:
    random.seed(81321)
    before = random.getstate()
    first = gen.generate(9821, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(9821, 17, difficulty="hard")

    assert before == after
    assert first == second


def test_generated_truth_has_both_positive_and_negative_relations() -> None:
    for sample_index in range(24):
        output = gen.rule_mirror(gen.generate(5, sample_index))
        off_diagonal = [
            value
            for r, row in enumerate(output)
            for c, value in enumerate(row)
            if r != c
        ]
        assert 8 in off_diagonal
        assert 0 in off_diagonal


def test_declared_finite_output_codomain_is_fully_realized() -> None:
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 13
    outputs = {
        tuple(tuple(row) for row in gen.rule_mirror(gen.generate(seed, index, difficulty=band)))
        for band in ("easy", "medium", "hard")
        for seed in range(8)
        for index in range(24)
    }
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN
