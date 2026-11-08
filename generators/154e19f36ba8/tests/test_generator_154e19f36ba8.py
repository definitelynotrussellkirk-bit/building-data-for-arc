from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.154e19f36ba8.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MODULE.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def test_rule_hash_and_canonical_three_seed_regression() -> None:
    assert MODULE.RULE_HASH == "8e0517e0f046"
    row = _canonical_row()
    three_seed_pairs = [
        pair
        for pair in row["train"] + row["test"]
        if sum(value == 8 for grid_row in pair["input"] for value in grid_row) == 3
    ]
    assert len(three_seed_pairs) == 2
    for pair in three_seed_pairs:
        assert MODULE.self_check(copy.deepcopy(pair["input"])) == []
        assert MODULE.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_all_canonical_pairs_match_python_mirror() -> None:
    row = _canonical_row()
    for pair in row["train"] + row["test"]:
        assert MODULE.self_check(copy.deepcopy(pair["input"])) == []
        assert MODULE.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_scene_profile_schedule_and_exact_overrides() -> None:
    scheduled = {
        MODULE.schedule_profile(991, index, "hard")
        for index in range(len(MODULE.SCENE_PROFILES))
    }
    assert scheduled == set(MODULE.SCENE_PROFILES)
    for index, profile in enumerate(MODULE.SCENE_PROFILES):
        grid = MODULE.generate(
            500 + index,
            70 + index,
            difficulty=("easy", "medium", "hard")[index % 3],
            scene_profile=profile,
        )
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.self_check(
            grid, meta={"overrides": {"scene_profile": profile}}
        ) == []


def test_targeted_impostors_are_rejected() -> None:
    grid = MODULE.generate(
        404,
        11,
        difficulty="medium",
        scene_profile="horizontal_forward_3",
    )
    info = MODULE._analysis(grid)
    assert info["errors"] == []

    broken_wall = copy.deepcopy(grid)
    wall_r, wall_c = next(
        (r, c)
        for r, row in enumerate(broken_wall)
        for c, value in enumerate(row)
        if value == 2
    )
    broken_wall[wall_r][wall_c] = 0

    novel_wall_color = copy.deepcopy(grid)
    for r, row in enumerate(novel_wall_color):
        for c, value in enumerate(row):
            if value == 2:
                novel_wall_color[r][c] = 5

    off_diagonal = copy.deepcopy(grid)
    seeds = sorted(
        (r, c)
        for r, row in enumerate(off_diagonal)
        for c, value in enumerate(row)
        if value == 8
    )
    middle = seeds[1]
    off_diagonal[middle[0]][middle[1]] = 0
    replacement = (middle[0], middle[1] + 2)
    assert off_diagonal[replacement[0]][replacement[1]] == 0
    off_diagonal[replacement[0]][replacement[1]] = 8

    extra_seed = copy.deepcopy(grid)
    added = next(
        (r, c)
        for r, row in enumerate(extra_seed)
        for c, value in enumerate(row)
        if value == 0 and (r, c) not in info["paths"]["chosen"]["cells"]
    )
    extra_seed[added[0]][added[1]] = 8

    for impostor in (broken_wall, novel_wall_color, off_diagonal, extra_seed):
        assert MODULE.self_check(impostor)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    state_before = random.getstate()
    first = MODULE.generate(123456, 17, difficulty="hard")
    state_after = random.getstate()
    second = MODULE.generate(123456, 17, difficulty="hard")
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_declared_rival_claims_hold_on_each_profile() -> None:
    for index, profile in enumerate(MODULE.SCENE_PROFILES):
        grid = MODULE.generate(
            9000 + index,
            index,
            difficulty="medium",
            scene_profile=profile,
        )
        authoritative = MODULE.rule_mirror(grid)
        for witness_name, rival_names in MODULE.WITNESS_RIVALS.items():
            if not MODULE.SEMANTIC_WITNESSES[witness_name](grid):
                continue
            assert any(
                MODULE.SEMANTIC_RIVALS[rival_name](grid) != authoritative
                for rival_name in rival_names
            )
