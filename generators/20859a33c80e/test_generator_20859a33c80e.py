from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.20859a33c80e.generator")


REPO = Path(__file__).resolve().parents[3]


def _canonical_row():
    with (REPO / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _pair(seed: int, index: int, difficulty: str = "medium"):
    grid = gen.generate(seed, index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_outputs_match_mirror():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_schedule_is_deterministic_valid_and_covers_profiles(difficulty):
    grids = [gen.generate(1729, i, difficulty=difficulty) for i in range(10)]
    assert grids == [gen.generate(1729, i, difficulty=difficulty) for i in range(10)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert {gen.observe_overrides(grid)["scene_kind"] for grid in grids} == set(gen.SCENE_KINDS)
    assert {gen.observe_overrides(grid)["color_pattern"] for grid in grids} == set(gen.COLOR_PATTERNS)


def test_every_declared_override_is_exactly_observable():
    for scene_kind in gen.SCENE_KINDS:
        for color_pattern in gen.COLOR_PATTERNS:
            grid = gen.generate(
                99,
                7,
                difficulty="easy",
                grid_h=9,
                grid_w=11,
                scene_kind=scene_kind,
                color_pattern=color_pattern,
            )
            assert gen.observe_overrides(grid) == {
                "grid_h": 9,
                "grid_w": 11,
                "scene_kind": scene_kind,
                "color_pattern": color_pattern,
            }


def test_unknown_overrides_and_malformed_inputs_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="single_chain")
    assert gen.self_check([[0, 1], [0]])
    assert gen.self_check([[0, 11], [0, 0]])
    assert gen.self_check([[1, 0], [0, 2]])  # no containment relation


def test_semantic_witnesses_fire_and_claimed_rivals_disagree():
    grids = [gen.generate(314159, i, difficulty="medium") for i in range(20)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        rivals = gen.WITNESS_RIVALS[witness_name]
        assert all(
            any(gen.SEMANTIC_RIVALS[name](grid) != gen.rule_mirror(grid) for name in rivals)
            for grid in hits
        )


def test_five_scheduled_demos_identify_the_rule():
    demos = [_pair(2026, i) for i in range(gen.EXAMPLES_NEEDED)]
    query = _pair(2026, gen.EXAMPLES_NEEDED)
    assert gen.lesson_identifiable(demos, query) == []


def test_returned_grids_are_fresh_objects():
    first = gen.generate(5, 3)
    second = gen.generate(5, 3)
    assert first == second and first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_four_structural_impostor_classes():
    two_components = [[0] * 7 for _ in range(7)]
    for c in range(1, 6):
        two_components[1][c] = two_components[5][c] = 1
    for r in range(1, 6):
        two_components[r][1] = two_components[r][5] = 1
    two_components[3][3] = 2

    no_containment = [[0] * 7 for _ in range(7)]
    no_containment[1][1], no_containment[3][3], no_containment[5][5] = 1, 2, 9

    noncontiguous = [[0] * 7 for _ in range(7)]
    for c in range(5):
        noncontiguous[0][c] = 1
    for r in range(6):
        noncontiguous[r][0] = 1
    for c in range(1, 6):
        noncontiguous[6][c] = 2
    for r in range(1, 7):
        noncontiguous[r][5] = 2
    noncontiguous[2][2] = 3

    too_many = [[0] * 12 for _ in range(12)]
    for c in range(2, 9):
        too_many[2][c] = too_many[8][c] = 1
    for r in range(2, 9):
        too_many[r][2] = too_many[r][8] = 1
    too_many[5][5] = 2
    for color, (r, c) in zip(
        range(3, 10), [(0, 0), (0, 3), (0, 6), (0, 9), (10, 0), (10, 5), (10, 10)]
    ):
        too_many[r][c] = color

    cases = {
        "too_few_components": two_components,
        "no_containment_relation": no_containment,
        "noncontiguous_depths": noncontiguous,
        "too_many_components": too_many,
    }
    for name, grid in cases.items():
        assert gen.self_check(grid), name
