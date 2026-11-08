from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK = "443eebb271d9"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _pairs():
    row = _canonical_row()
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_canonical_program():
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(rule.encode()).hexdigest()[:12]


def test_every_public_profile_replays_its_canonical_pair_exactly():
    pairs = _pairs()
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 3
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_every_general_profile_is_valid_and_recoverable_in_every_band():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for profile_index, profile in enumerate(MODULE.GENERAL_PROFILES):
            for seed in range(30):
                grid = MODULE.generate(
                    100_000 * band_index + 1_000 * profile_index + seed,
                    seed * 31,
                    difficulty=band,
                    scene_profile=profile,
                )
                analysis = MODULE._analysis(grid)
                assert not analysis["errors"]
                assert analysis["scene_profile"] == profile
                assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_default_generation_reaches_every_declared_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(4000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_oracle_repeats_top_row_and_only_third_instance_columns_downward():
    grid = MODULE.generate(12, 34, scene_profile="plus")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    row0, col0, _, _ = facts["bbox"]
    cells = set(facts["normalized"])
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if row < row0 or col < col0:
                expected = 0
            else:
                rr, cc = row - row0, col - col0
                local = (rr % facts["vstep"], cc % facts["hstep"])
                instance, row_repeat = cc // facts["hstep"], rr // facts["vstep"]
                painted = local in cells and (row_repeat == 0 or instance % 3 == 2)
                expected = (6 if instance % 3 == 2 else 7) if painted else 0
            assert output[row][col] == expected


def test_one_blank_row_and_column_define_the_period():
    grid = MODULE.generate(91, 17, scene_profile="solid_rectangle")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    row0, col0, row1, col1 = facts["bbox"]
    assert facts["hstep"] == facts["glyph_width"] + 1
    assert facts["vstep"] == facts["glyph_height"] + 1
    assert all(output[row][col1 + 1] == 0 for row in range(len(output)))
    assert all(value == 0 for value in output[row1 + 1])
    assert output[row0][col0 + 2 * facts["hstep"]] == 6
    assert output[row0 + facts["vstep"]][col0 + 2 * facts["hstep"]] == 6


def test_non_third_columns_do_not_continue_below_first_lattice_row():
    grid = MODULE.generate(5, 6, scene_profile="solid_square")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    row0, col0, _, _ = facts["bbox"]
    lower = row0 + facts["vstep"]
    assert output[lower][col0] == 0
    assert output[lower][col0 + facts["hstep"]] == 0
    assert output[lower][col0 + 2 * facts["hstep"]] == 6


def test_every_generated_lesson_has_visible_ordinary_and_extended_copies():
    for seed in range(500):
        grid = MODULE.generate(seed, seed * 19)
        assert not MODULE.self_check(grid)
        output = MODULE.rule_mirror(grid)
        assert {0, 6, 7} <= {value for row in output for value in row}
        assert output != grid


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 7
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 7], [0]],
        [[True] + [0] * 17 for _ in range(11)],
        [[6] + [0] * 17 for _ in range(11)],
        [[0] * 31 for _ in range(11)],
        [[0] * 18 for _ in range(10)],
        [[0] * 18 for _ in range(11)],
        [[7] + [0] * 17] + [[0] * 18 for _ in range(10)],
        [[0] * 18 for _ in range(11)],
    ],
)
def test_self_check_rejects_malformed_or_undeclared_impostors(grid):
    assert MODULE.self_check(grid)


def test_self_check_rejects_unknown_shape_and_insufficient_demonstration_space():
    unknown = [[0] * 20 for _ in range(13)]
    for row, col in ((2, 2), (2, 3), (3, 2), (4, 4)):
        unknown[row][col] = 7
    cramped_right = [[0] * 18 for _ in range(13)]
    for row, col in MODULE._GLYPHS["diamond"]:
        cramped_right[1 + row][2 + col] = 7
    cramped_down = [[0] * 20 for _ in range(11)]
    for row, col in MODULE._GLYPHS["diamond"]:
        cramped_down[1 + row][1 + col] = 7
    assert MODULE.self_check(unknown)
    assert MODULE.self_check(cramped_right)
    assert MODULE.self_check(cramped_down)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, mask_shape="plus")


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 7
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen


def test_axis_contract_is_literal_minimal_and_complete():
    assert set(MODULE.AXES) == {"scene_profile"}
    valid = set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert valid == set(MODULE.SCENE_PROFILES)
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
