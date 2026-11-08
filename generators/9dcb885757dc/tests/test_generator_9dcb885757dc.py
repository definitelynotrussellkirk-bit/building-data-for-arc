from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

GENERATOR_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GENERATOR_DIR.parents[1]
MODULE_PATH = GENERATOR_DIR / "generator.py"

spec = importlib.util.spec_from_file_location("review_generator_9dcb885757dc", MODULE_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _canonical_row() -> dict:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def _pair(grid: list[list[int]]) -> dict:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_owned_strict_and_mirrored_exactly() -> None:
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_profile_and_style_realizes_all_exact_override_boundaries() -> None:
    for height in (7, 8):
        for width in (7, 10):
            for count in (5, 6):
                for profile in gen.PROFILE_NAMES:
                    for style in gen.COMPONENT_STYLES:
                        grid = gen.generate(
                            300 + height + width + count,
                            count,
                            difficulty="medium",
                            grid_h=height,
                            grid_w=width,
                            n_components=count,
                            scene_profile=profile,
                            component_style=style,
                        )
                        assert gen.self_check(grid, difficulty="medium") == []
                        assert gen.strict_canonical_like(grid) == []
                        assert gen.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "n_components": count,
                            "scene_profile": profile,
                            "component_style": style,
                        }


def test_default_schedule_covers_every_degree_branch_in_each_window() -> None:
    for start in range(18):
        grids = [
            gen.generate(91, index, difficulty="hard")
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        ]
        observed = [gen.observe_overrides(grid) for grid in grids]
        assert 2 <= gen.EXAMPLES_NEEDED <= 5
        assert gen.EXAMPLES_NEEDED == len(gen.SCHEDULE_PROFILES)
        assert {row["scene_profile"] for row in observed} == set(gen.SCHEDULE_PROFILES)
        assert {row["component_style"] for row in observed} == set(gen.COMPONENT_STYLES)
        degrees = {
            degree
            for grid in grids
            for degree in gen.semantic_observables(grid)["degrees"]
        }
        assert degrees == set(range(6))


def test_named_witnesses_really_refute_their_claimed_rivals() -> None:
    candidates = [
        gen.generate(47, index, difficulty="medium")
        for index in range(3 * gen.EXAMPLES_NEEDED)
    ]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        firing = [grid for grid in candidates if witness(grid)]
        assert firing, witness_name
        for rival_name in rival_names:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != gen.rule_mirror(grid) for grid in firing), (
                witness_name,
                rival_name,
            )


def test_each_scheduled_lesson_refutes_every_declared_competitor() -> None:
    for start in range(12):
        demos = [
            _pair(gen.generate(501, start + index, difficulty="easy"))
            for index in range(gen.EXAMPLES_NEEDED)
        ]
        query = _pair(
            gen.generate(501, start + gen.EXAMPLES_NEEDED, difficulty="easy")
        )
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_unknown_or_invalid_overrides_are_rejected_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="ignored-before-repair")
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError):
        gen.generate(1, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="legendary")


def test_declared_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_deterministic_fresh_returns_and_global_rng_purity() -> None:
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


def test_rule_mirror_returns_fresh_output_without_mutating_input() -> None:
    grid = gen.generate(19, 2, difficulty="hard")
    original = copy.deepcopy(grid)
    output = gen.rule_mirror(grid)
    assert grid == original
    assert output is not grid
    assert output[0] is not grid[0]
    assert output != grid


def test_difficulty_bands_are_distinct_without_changing_graph_semantics() -> None:
    grids = {
        band: gen.generate(83, 4, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) == 3
    facts = {band: gen.semantic_observables(grid) for band, grid in grids.items()}
    assert {facts[band]["degree_multiset"] for band in facts} == {
        facts["easy"]["degree_multiset"]
    }
    assert {facts[band]["scene_profile"] for band in facts} == {
        facts["easy"]["scene_profile"]
    }
