"""Focused regression tests for generator b962e7deb312."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b962e7deb312"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_matches_canonical_and_selected_authority():
    row = _canonical_row()
    base = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/f2c80d62966a/M29__b962e7deb312.json"
        ).read_text()
    )
    assert MODULE.RULE_HASH == "84f1bd44bdef"
    assert MODULE.RULE_HASH == _normalized_hash(row["program_solution"])
    assert MODULE.RULE_HASH == _normalized_hash(
        base["racket_target"]["target_code"]
    )


def test_every_canonical_input_is_accepted_and_solved_by_the_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == MODULE._normalize_grid(
            pair["output"]
        )
        assert pair["input"] == original


def test_default_schedule_cycles_all_canonical_profiles_in_every_band():
    expected = list(MODULE.CANONICAL_PROFILES)
    for band in ("easy", "medium", "hard"):
        observed = []
        for sample_index in range(5):
            grid = MODULE.generate(7331, sample_index, difficulty=band)
            palette = len({value for row in grid for value in row})
            observed.append((len(grid), len(grid[0]), palette))
            assert MODULE.self_check(grid, difficulty=band) == []
            assert MODULE.strict_canonical_like(grid) == []
        assert observed == expected


def test_difficulty_is_deterministic_but_not_dead():
    grids = {
        band: MODULE.generate(117, 2, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({json.dumps(grid) for grid in grids.values()}) == 3
    assert grids["easy"] == MODULE.generate(117, 2, difficulty="easy")


@pytest.mark.parametrize(
    "case,expected",
    [
        ({"grid_h": 8}, {"grid_h": 8}),
        ({"grid_h": 11}, {"grid_h": 11}),
        ({"grid_w": 11}, {"grid_w": 11}),
        ({"grid_w": 13}, {"grid_w": 13}),
        ({"n_blobs": 2}, {"n_blobs": 2}),
        ({"n_blobs": 3}, {"n_blobs": 3}),
        ({"largest_size": 6}, {"largest_size": 6}),
        ({"largest_size": 12}, {"largest_size": 12}),
    ],
)
def test_each_declared_override_boundary_is_observable(case, expected):
    grid = MODULE.generate(90210, 4, difficulty="hard", **case)
    observed = MODULE.observe_overrides(grid)
    assert MODULE.self_check(grid, difficulty="hard") == []
    for axis, value in expected.items():
        assert observed[axis] == value


def test_combined_boundary_overrides_are_exact():
    case = {"grid_h": 8, "grid_w": 13, "n_blobs": 3, "largest_size": 12}
    grid = MODULE.generate(19, 1, difficulty="easy", **case)
    assert MODULE.observe_overrides(grid) == case
    assert MODULE.self_check(grid) == []


def test_unknown_override_names_are_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(19, 1, difficulty="easy", grid_height=8)


def test_replay_is_fresh_and_process_global_rng_is_untouched():
    random.seed(481516)
    state = random.getstate()
    first = MODULE.generate(55, 7, difficulty="medium")
    second = MODULE.generate(55, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    pristine = copy.deepcopy(second)
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(55, 7, difficulty="medium") == pristine
    assert random.getstate() == state


def test_generated_outputs_are_exact_largest_component_crops():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = MODULE.generate(seed, seed * 7 + 2, difficulty=band)
            output = MODULE.rule_mirror(grid)
            largest = max(
                MODULE._components(grid), key=lambda component: component["size"]
            )
            assert output == MODULE._crop(grid, largest)
            assert output != grid


def test_self_check_rejects_targeted_impostors():
    blank = [[0] * 11 for _ in range(8)]

    singleton = copy.deepcopy(blank)
    singleton[2][3] = 4

    tied = copy.deepcopy(blank)
    for r, c in ((1, 1), (1, 2), (2, 1), (2, 2)):
        tied[r][c] = 4
    for r, c in ((5, 7), (5, 8), (6, 7), (6, 8)):
        tied[r][c] = 6

    multicolor = MODULE.generate(1337, 0, difficulty="medium")
    largest = max(
        MODULE._components(multicolor), key=lambda component: component["size"]
    )
    r, c = largest["cells"][0]
    old_color = multicolor[r][c]
    replacement = next(
        color
        for color in range(1, 10)
        if color != old_color
        and color not in {value for row in multicolor for value in row}
    )
    multicolor[r][c] = replacement

    tiny_component = MODULE.generate(2024, 1, difficulty="hard")
    smallest = min(
        MODULE._components(tiny_component), key=lambda component: component["size"]
    )
    for r, c in smallest["cells"]:
        tiny_component[r][c] = 0
    r, c = smallest["cells"][0]
    tiny_component[r][c] = 9

    for impostor in (blank, singleton, tied, multicolor, tiny_component):
        assert MODULE.self_check(impostor), impostor


def test_all_named_semantic_witnesses_fire_in_each_band():
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in MODULE.SEMANTIC_WITNESSES}
        for index in range(90):
            grid = MODULE.generate(5000 + index, index, difficulty=band)
            for name, predicate in MODULE.SEMANTIC_WITNESSES.items():
                hits[name] += bool(predicate(grid))
        assert all(count > 0 for count in hits.values()), (band, hits)


def test_five_demo_schedule_identifies_the_largest_component_rule():
    pairs = []
    for sample_index in range(6):
        grid = MODULE.generate(8128, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    assert MODULE.lesson_identifiable(pairs[:5], pairs[5]) == []


def test_pinned_widest_bbox_regression_lesson_is_identifiable():
    seed = 139711249722443
    pairs = []
    for sample_index in range(11, 17):
        grid = MODULE.generate(seed, sample_index, difficulty="easy")
        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
    assert MODULE.lesson_identifiable(pairs[:5], pairs[5]) == []


def test_every_five_sample_sliding_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for sample_index in range(start, start + 6):
                grid = MODULE.generate(60013 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
            assert MODULE.lesson_identifiable(pairs[:5], pairs[5]) == [], (
                band,
                start,
            )
