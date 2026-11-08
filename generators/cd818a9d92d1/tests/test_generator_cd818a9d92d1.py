from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.cd818a9d92d1 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        for split in ("train", "test"):
            for pair in row.get(split, ()):  # both canonical source rows
                yield pair["input"]


def test_canonical_inputs_are_accepted_across_both_source_rows():
    inputs = list(_canonical_inputs())
    assert len(inputs) == 6
    profiles = []
    for grid in inputs:
        assert gen.self_check(grid) == []
        profiles.append(gen.observe_overrides(grid)["branch_profile"])
    assert set(profiles) == {
        "canonical_one_bend_one_distractor",
        "canonical_one_bend_two_distractors",
        "canonical_two_bends_one_distractor",
    }


def test_on_column_blocker_bends_and_off_column_gray_is_inert():
    grid = [[0] * 8 for _ in range(7)]
    grid[-1][1] = 2
    grid[-1][4] = 2
    grid[3][1] = 5  # on-column: bend right
    grid[1][6] = 5  # off-column: preserve only

    assert gen.self_check(grid) == []
    out = gen.rule_mirror(grid)

    # Repeated bottom guide.
    assert all(out[r][4] == 2 for r in range(7))
    # Original marked column is cleared only above the blocker.
    assert [out[r][1] for r in range(7)] == [0, 0, 0, 5, 2, 2, 2]
    # The right-shifted path includes the row immediately below the blocker.
    assert [out[r][2] for r in range(7)] == [2, 2, 2, 2, 2, 0, 0]
    # Off-column gray stays gray and does not create a red continuation.
    assert out[1][6] == 5
    assert all(out[r][7] == 0 for r in range(7))


def test_self_check_rejects_targeted_structure_destroying_impostors():
    good = gen.generate(41, 7, difficulty="medium")
    assert gen.self_check(good) == []

    impostors = []
    impostors.append([[0 for _ in row] for row in good])

    no_off = copy.deepcopy(good)
    markers = {c for c, value in enumerate(no_off[-1]) if value == 2}
    for r, row in enumerate(no_off[:-1]):
        for c, value in enumerate(row):
            if value == 5 and c not in markers:
                no_off[r][c] = 0
    impostors.append(no_off)

    bottom_gray = copy.deepcopy(good)
    bottom_gray[-1][0] = 5
    impostors.append(bottom_gray)

    adjacent_markers = copy.deepcopy(good)
    cols = [c for c, value in enumerate(adjacent_markers[-1]) if value == 2]
    adjacent_markers[-1][cols[-1]] = 0
    adjacent_markers[-1][cols[0] + 1] = 2
    impostors.append(adjacent_markers)

    foreign_color = copy.deepcopy(good)
    foreign_color[0][0] = 7
    impostors.append(foreign_color)

    for grid in impostors:
        assert gen.self_check(grid), grid


def test_boundary_overrides_are_exact_and_incompatibilities_are_loud():
    compact = gen.generate(
        3,
        2,
        difficulty="easy",
        grid_h=5,
        grid_w=6,
        branch_profile="compact_one_bend_one_distractor",
    )
    assert len(compact) == 5 and len(compact[0]) == 6
    assert gen.observe_overrides(compact) == {
        "grid_h": 5,
        "grid_w": 6,
        "branch_profile": "compact_one_bend_one_distractor",
    }

    expanded = gen.generate(
        3,
        2,
        difficulty="hard",
        grid_h=16,
        grid_w=18,
        branch_profile="expanded_three_bends_one_distractor",
    )
    assert len(expanded) == 16 and len(expanded[0]) == 18
    assert gen.observe_overrides(expanded) == {
        "grid_h": 16,
        "grid_w": 18,
        "branch_profile": "expanded_three_bends_one_distractor",
    }

    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(
            3,
            2,
            difficulty="easy",
            grid_w=6,
            branch_profile="expanded_two_bends_two_distractors",
        )
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(
            3,
            2,
            difficulty="easy",
            grid_h=5,
            branch_profile="expanded_two_bends_two_distractors",
        )


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(991)
    state_before = random.getstate()
    first = gen.generate(99, 17, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(99, 17, difficulty="hard")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9
    assert second[0][0] != 9


def test_every_declared_profile_has_positive_witnesses_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.BRANCH_PROFILES):
            grid = gen.generate(
                seed=700 + index,
                sample_index=900 + index,
                difficulty=band,
                branch_profile=profile,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid)["branch_profile"] == profile
