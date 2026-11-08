from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "298700c0dc02"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                test = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return row["train"] + test
    raise AssertionError(f"missing canonical task {TASK_ID}")


def test_rule_hash_and_all_canonical_inputs_are_owned():
    assert gen.RULE_HASH == "7bd61d1b9182"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_declared_axis_boundaries_are_exact_and_observable(band):
    for sample_index in range(4):
        for grid_h in (9, 13):
            for grid_w in (11, 17):
                for n_objects in (2, 4):
                    for target_is_first in (False, True):
                        grid = gen.generate(
                            127,
                            sample_index,
                            difficulty=band,
                            grid_h=grid_h,
                            grid_w=grid_w,
                            n_objects=n_objects,
                            target_is_first=target_is_first,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_objects": n_objects,
                            "target_is_first": target_is_first,
                        }


def test_default_schedule_breaks_position_size_and_proximity_shortcuts():
    grids = [gen.generate(43, index, difficulty="medium") for index in range(4)]
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert [row["n_objects"] for row in observed] == [3, 2, 4, 2]
    assert [row["target_is_first"] for row in observed] == [True, False, True, False]

    expected_witnesses = (
        "target_farther_from_bar_than_a_distractor",
        "target_smaller_than_a_distractor",
        "object_count_4",
        "target_size_tied_with_a_distractor",
    )
    for grid, witness in zip(grids, expected_witnesses):
        assert gen.SEMANTIC_WITNESSES[witness](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_demo_schedule_window_identifies_the_rule(band):
    for start in range(4):
        pairs = []
        for offset in range(4):
            grid = gen.generate(819, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        demos, query = pairs[:3], pairs[3]
        assert gen.lesson_identifiable(demos, query) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert not all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )


def test_self_check_rejects_four_targeted_impostors():
    grid = gen.generate(101, 3, difficulty="medium")
    errors, analysis = gen._analyze_grid(grid)
    assert errors == [] and analysis is not None

    missing_bar = copy.deepcopy(grid)
    missing_bar[0][analysis["bar_col"]] = 0
    assert any("full-height" in message for message in gen.self_check(missing_bar))

    stray_bar = copy.deepcopy(grid)
    stray_bar[0][analysis["bar_col"] - 1] = 5
    assert any("outside" in message for message in gen.self_check(stray_bar))

    two_symmetric = copy.deepcopy(grid)
    distractor = next(info for info in analysis["components"] if not info["symmetric"])
    for r, c in distractor["cells"]:
        two_symmetric[r][c] = 0
    # A top-row T is separate from the bottom-row target in profile P3.
    for r, c in ((0, 0), (0, 1), (0, 2), (1, 1)):
        two_symmetric[r][c] = 4
    assert any("exactly one" in message and "found 2" in message for message in gen.self_check(two_symmetric))

    no_symmetric = copy.deepcopy(grid)
    target = analysis["target"]
    assert target is not None
    found = False
    for cell in target["cells"]:
        candidate = copy.deepcopy(grid)
        candidate[cell[0]][cell[1]] = 0
        messages = gen.self_check(candidate)
        if any("exactly one" in message and "found 0" in message for message in messages):
            no_symmetric = candidate
            found = True
            break
    assert found
    assert any("found 0" in message for message in gen.self_check(no_symmetric))


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(811)
    state = random.getstate()
    first = gen.generate(8, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8, 2, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert second == gen.generate(8, 2, difficulty="hard")


def test_bad_calls_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, bogus_axis=3)
    with pytest.raises(ValueError, match="must be a boolean"):
        gen.generate(1, 1, target_is_first=1)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="extreme")
