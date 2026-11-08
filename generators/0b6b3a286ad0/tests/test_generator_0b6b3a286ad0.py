"""Regression and curriculum tests for the template-key lookup generator."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "0b6b3a286ad0"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
SPEC = importlib.util.spec_from_file_location(
    f"test_generator_{TASK_ID}", ROOT / "generators" / TASK_ID / "generator.py"
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs() -> list[dict]:
    for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            test = row["test"]
            return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))
    raise AssertionError(f"missing canonical task {TASK_ID}")


def pair(seed: int, sample_index: int, difficulty: str, **overrides: object) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def test_metadata_and_all_canonical_pairs_are_recognized() -> None:
    assert GEN.RULE_HASH == "950fe1e7c618"
    assert GEN.VERSION == "4.0.0"
    pairs = canonical_pairs()
    assert len(pairs) == 3
    assert [GEN.semantic_observables(p["input"])["texture"] for p in pairs] == [
        "match",
        "rotated_decoy",
        "near_miss",
    ]
    for p in pairs:
        before = copy.deepcopy(p["input"])
        assert GEN.self_check(p["input"]) == []
        assert GEN.strict_canonical_like(p["input"]) == []
        assert GEN.rule_mirror(p["input"]) == p["output"]
        assert p["input"] == before


def test_exact_axes_are_realized_and_unknown_overrides_fail() -> None:
    for panel_h in GEN.PANEL_HEIGHTS:
        for texture in GEN.TEXTURES:
            grid = GEN.generate(1000 + panel_h, panel_h, difficulty="medium", panel_h=panel_h, texture=texture)
            observed = GEN.observe_overrides(grid)
            assert observed["panel_h"] == panel_h
            assert observed["texture"] == texture
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, difficulty="easy", typo_axis="match")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_v2_textures_embed_key2_and_never_accidentally_match_key1() -> None:
    for texture in ("no_match", "rotated_decoy", "near_miss"):
        for index in range(24):
            grid = GEN.generate(2000 + index, index, difficulty="hard", texture=texture)
            facts = GEN.semantic_observables(grid)
            assert facts["texture"] == texture
            assert facts["key1_matches"] == 0
            assert facts["key2_matches"] >= 1
            assert GEN.rule_mirror(grid) == facts["value2"]


def test_wildcard_examples_refute_zero_strict_matching() -> None:
    for index in range(16):
        grid = GEN.generate(3000 + index, index, difficulty="medium", texture="wildcard")
        facts = GEN.semantic_observables(grid)
        assert facts["texture"] == "wildcard"
        assert facts["key1_matches"] >= 1
        assert facts["wildcard_noise_cells"] >= 1
        assert GEN.rule_mirror(grid) == facts["value1"]
        assert GEN.SEMANTIC_RIVALS["zero_strict_match"](grid) == facts["value2"]


def test_five_slot_schedule_is_identifiable_from_every_start() -> None:
    assert GEN.EXAMPLES_NEEDED == len(GEN.SCHEDULE_PROFILES) == 5
    for difficulty in ("easy", "medium", "hard"):
        for start in range(10):
            demos = [pair(4000 + start, start + offset, difficulty) for offset in range(GEN.EXAMPLES_NEEDED)]
            query = pair(4000 + start, start + GEN.EXAMPLES_NEEDED, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            textures = {GEN.semantic_observables(p["input"])["texture"] for p in demos}
            assert textures == set(GEN.TEXTURES)
            for rival in GEN.LESSON_COMPETITORS.values():
                assert any(rival(p["input"]) != p["output"] for p in demos)


def test_declared_witnesses_fire_and_refute_named_rivals() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(5000 + i, i, difficulty=difficulty) for i in range(25)]
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (difficulty, name)
            for grid in firing[:8]:
                official = GEN.rule_mirror(grid)
                assert any(
                    GEN.SEMANTIC_RIVALS[rival_name](grid) != official
                    for rival_name in GEN.WITNESS_RIVALS[name]
                )


def test_determinism_freshness_diversity_and_global_rng() -> None:
    random.seed(24680)
    state = random.getstate()
    first = GEN.generate(77, 9, difficulty="hard")
    second = GEN.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 9
    assert GEN.generate(77, 9, difficulty="hard") == second
    grids = [GEN.generate(6000 + i, i, difficulty="medium") for i in range(200)]
    assert len({freeze(grid) for grid in grids}) >= 190
    assert all((len(grid), len(grid[0]), len({v for row in grid for v in row})) in {(6, 25, 5), (7, 26, 5)} for grid in grids)


def test_task_specific_mutations_are_rejected() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 7
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_difficulty_bands_use_distinct_canonical_profiles() -> None:
    for index in range(12):
        easy = GEN.generate(7000 + index, index, difficulty="easy")
        medium = GEN.generate(7000 + index, index, difficulty="medium")
        hard = GEN.generate(7000 + index, index, difficulty="hard")
        assert len(easy) == 6
        assert len(hard) == 7
        assert len({freeze(easy), freeze(medium), freeze(hard)}) >= 2
        assert GEN.self_check(easy) == GEN.self_check(medium) == GEN.self_check(hard) == []


def test_examples_needed_is_a_literal_for_solve_episode_static_reading() -> None:
    import ast

    source = (ROOT / "generators" / TASK_ID / "generator.py").read_text()
    assignment = next(
        statement
        for statement in ast.parse(source).body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "EXAMPLES_NEEDED" for target in statement.targets)
    )
    assert isinstance(assignment.value, ast.Constant)
    assert assignment.value.value == 5
