"""Focused regressions for the exact same-colour degree-1 generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.6e175c009c2a.generator")
from scripts.canonical_profile_gate import canonical_pairs


ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError(f"canonical task {gen.TASK_ID} not found")


def test_canonical_pairs_rule_hash_and_shortcut_baseline() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        snapshot = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == snapshot
    normalized = " ".join(_canonical_row()["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_every_exact_override_is_observable_at_full_boundaries() -> None:
    for band in ("easy", "medium", "hard"):
        for grid_h in (7, 14):
            for grid_w in (8, 14):
                for profile in gen.SCHEDULE_PROFILES:
                    grid = gen.generate(
                        9001,
                        37,
                        difficulty=band,
                        grid_h=grid_h,
                        grid_w=grid_w,
                        scene_profile=profile,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "scene_profile": profile,
                    }
    with pytest.raises(KeyError, match="unknown override"):
        gen.generate(1, 2, difficulty="easy", typo_axis="ignored-before-repair")


def test_every_sliding_five_demo_window_is_identifiable() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(31337, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                31337, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            assert {
                gen.observe_overrides(pair["input"])["scene_profile"]
                for pair in demos
            } == set(gen.SCHEDULE_PROFILES)


def test_generated_witnesses_refute_every_named_rival() -> None:
    grids = [
        gen.generate(101, index, difficulty="medium")
        for index in range(gen.EXAMPLES_NEEDED)
    ]
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in grids), name
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name


def test_self_check_rejects_four_targeted_impostors() -> None:
    valid = gen.generate(77, 2, difficulty="medium")
    assert gen.self_check(valid) == []

    one_colour = copy.deepcopy(valid)
    first_colour = next(value for row in one_colour for value in row if value)
    for row in one_colour:
        for col, value in enumerate(row):
            if value:
                row[col] = first_colour

    output_only = gen.rule_mirror(valid)
    solid = [[1 for _ in row] for row in valid]
    isolated = [[0] * 8 for _ in range(7)]
    for row, col, colour in (
        (0, 0, 2), (0, 3, 2), (3, 0, 2),
        (2, 5, 7), (5, 2, 7), (6, 7, 7),
    ):
        isolated[row][col] = colour

    for name, grid in {
        "one_colour": one_colour,
        "output_only": output_only,
        "solid_no_background": solid,
        "isolated_only": isolated,
    }.items():
        assert gen.self_check(grid), name


def test_negative_canonical_recombination_is_loud_but_oracle_executable() -> None:
    first = copy.deepcopy(canonical_pairs(gen.TASK_ID)[0]["input"])
    recoloured = [
        [4 if value == 2 else 9 if value == 7 else value for value in row]
        for row in first
    ]
    assert gen.self_check(recoloured) == []
    assert gen.strict_canonical_like(recoloured)
    assert len(gen.rule_mirror(recoloured)) == len(recoloured)


def test_replay_returns_fresh_grids_and_preserves_global_rng() -> None:
    random.seed(424242)
    before = random.getstate()
    first = gen.generate(51, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(51, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(51, 7, difficulty="hard")
