from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.8ff1ff513757.generator")


def _canonical_inputs():
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        pairs = list(row["train"])
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        pairs.extend(test)
        return [
            [[int(ch) for ch in text_row] for text_row in pair["input"]]
            for pair in pairs
        ]
    raise AssertionError("canonical task not found")


def _solve(grid):
    return [list(row) for row in grid if any(v != 0 for v in row)]


def test_canonical_inputs_are_accepted():
    inputs = _canonical_inputs()
    assert len(inputs) == 3
    assert all(gen.self_check(grid) == [] for grid in inputs)
    assert all(gen.strict_canonical_like(grid) == [] for grid in inputs)


def test_rule_hash_and_exact_overrides_are_observable():
    assert gen.RULE_HASH == "ed6dfa957511"
    cases = (
        dict(grid_h=6, grid_w=5, n_active_rows=2, n_distinct_colors=2),
        dict(grid_h=12, grid_w=12, n_active_rows=6, n_distinct_colors=6),
    )
    for sample_index, overrides in enumerate(cases):
        grid = gen.generate(9173, sample_index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert _solve(grid) != grid


def test_incompatible_and_unknown_overrides_reject_loudly():
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=6, n_active_rows=6)
    with pytest.raises(ValueError):
        gen.generate(1, 0, palette_kind="warm")


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(4815162342)
    state = random.getstate()
    first = gen.generate(44, 7, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(44, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(44, 7, difficulty="medium")


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(99, 2, grid_h=8, grid_w=8, n_active_rows=3, n_distinct_colors=3)
    assert gen.self_check(valid) == []

    adjacent = copy.deepcopy(valid)
    active = [r for r, row in enumerate(adjacent) if any(row)]
    adjacent[active[0] + 1] = adjacent[active[0]][:]
    assert any("separated" in e for e in gen.self_check(adjacent))

    one_row = [[0] * 8 for _ in range(8)]
    one_row[2][1], one_row[2][6] = 1, 2
    assert any("2..6" in e for e in gen.self_check(one_row))

    one_color = copy.deepcopy(valid)
    for row in one_color:
        for c, value in enumerate(row):
            if value:
                row[c] = 4
    assert any("two distinct" in e for e in gen.self_check(one_color))

    no_blank_column = [[0] * 8 for _ in range(8)]
    no_blank_column[1] = [1, 2, 1, 2, 1, 2, 1, 2]
    no_blank_column[3] = [2, 1, 2, 1, 2, 1, 2, 1]
    no_blank_column[5] = [3, 4, 3, 4, 3, 4, 3, 4]
    assert any("all-zero column" in e for e in gen.self_check(no_blank_column))

    solid_masks = [[0] * 8 for _ in range(8)]
    solid_masks[1][2:4] = [1, 2]
    solid_masks[3][2:4] = [2, 1]
    assert any("singleton or" in e for e in gen.self_check(solid_masks))


def test_four_sample_lesson_is_identifiable():
    seed = 20260724
    pairs = []
    for sample_index in range(4):
        inp = gen.generate(seed, sample_index)
        pairs.append({"input": inp, "output": _solve(inp)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, "1", -1])
def test_sample_index_requires_a_nonnegative_literal_integer(bad_sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(123, bad_sample_index)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, "1"])
def test_seed_requires_a_literal_integer(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 6.0),
        ("grid_w", "6"),
        ("n_active_rows", True),
        ("n_distinct_colors", "3"),
    ],
)
def test_exact_integer_overrides_do_not_coerce_other_scalar_types(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(123, 0, **{axis: value})


def test_default_schedule_anchors_every_canonical_profile_in_every_band():
    expected = [(6, 6, 5), (7, 7, 4), (8, 8, 5)]
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(gen.SCHEDULE_PROFILES[:3]) == (
        "canonical_6x6",
        "canonical_7x7",
        "canonical_8x8",
    )
    for band in ("easy", "medium", "hard"):
        observed = [
            _profile(gen.generate(20261011, sample_index, difficulty=band))
            for sample_index in range(3)
        ]
        assert observed == expected


def test_impossible_height_active_row_pairs_are_declared_and_rejected():
    expected = {
        (height, active_rows)
        for height in range(6, 13)
        for active_rows in range(2, 7)
        if height < 2 * active_rows
    }
    declared = {
        (entry["grid_h"], entry["n_active_rows"])
        for entry in gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS
    }
    assert declared == expected

    for height, active_rows in sorted(expected):
        with pytest.raises(ValueError):
            gen.generate(
                991,
                0,
                grid_h=height,
                n_active_rows=active_rows,
            )

    for height, active_rows in ((6, 3), (8, 4), (10, 5), (12, 6)):
        grid = gen.generate(
            991,
            0,
            grid_h=height,
            n_active_rows=active_rows,
        )
        assert gen.observe_overrides(grid)["grid_h"] == height
        assert gen.observe_overrides(grid)["n_active_rows"] == active_rows


def _canonical_pairs_with_outputs():
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        pairs = list(row["train"])
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        pairs.extend(test)
        return [
            {
                "input": [[int(ch) for ch in text_row] for text_row in pair["input"]],
                "output": [[int(ch) for ch in text_row] for text_row in pair["output"]],
            }
            for pair in pairs
        ]
    raise AssertionError("canonical task not found")


def _blank_rows(grid):
    return [index for index, row in enumerate(grid) if not any(row)]


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    pairs = _canonical_pairs_with_outputs()
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "preserve_trailing_blank_rows",
        "remove_one_internal_separator",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_four_slot_schedule_refutes_each_canonical_shortcut_under_every_rotation():
    seed = 20261011
    pairs = []
    for sample_index in range(4):
        inp = gen.generate(seed, sample_index, difficulty="medium")
        pairs.append({"input": inp, "output": gen.rule_mirror(inp)})

    slot3 = pairs[3]["input"]
    blank = _blank_rows(slot3)
    active = [r for r, row in enumerate(slot3) if any(row)]
    assert blank[0] == 0
    assert blank[-1] == len(slot3) - 1
    assert any(
        active[0] < row and row + 1 < active[-1] and row + 1 in blank
        for row in blank
    )

    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []

    trailing = gen.CANONICAL_SHORTCUTS["preserve_trailing_blank_rows"]
    one_separator = gen.CANONICAL_SHORTCUTS["remove_one_internal_separator"]
    assert trailing(pairs[1]["input"]) != pairs[1]["output"]
    assert trailing(pairs[3]["input"]) != pairs[3]["output"]
    assert one_separator(pairs[2]["input"]) != pairs[2]["output"]
    assert one_separator(pairs[3]["input"]) != pairs[3]["output"]


def test_retained_trailing_blank_counterexample_replays_exactly():
    from reviewer_support import find_root

    root = find_root(__file__)
    fixture = (
        root
        / "generators"
        / gen.TASK_ID
        / "counterexamples"
        / "generator-shortcuts"
        / "counterexample.json"
    )
    record = json.loads(fixture.read_text())
    grid = record["input"]

    assert record["generator_sha256"] == "848dc677b1ec180c1fced2b9f1bc451310c131b1ed2c6c1f67394f3649535256"
    assert gen.self_check(grid) == []
    assert gen.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
        **record["overrides"],
    ) == grid
    assert gen.rule_mirror(grid) == record["intended_racket_output"]
    assert (
        gen.CANONICAL_SHORTCUTS[record["rival_name"]](grid)
        == record["rival_output"]
    )
    assert record["rival_output"] != record["intended_racket_output"]
