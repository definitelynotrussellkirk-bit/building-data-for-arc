from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "2c7b1545edf9"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_inputs():
    path = Path(__file__).parents[1] / "data/canonical/puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for pair in row["train"]:
            yield pair["input"]
        test = row["test"]
        for pair in test if isinstance(test, list) else [test]:
            yield pair["input"]


def test_canonical_inputs_are_accepted():
    inputs = list(_canonical_inputs())
    assert len(inputs) == 5
    assert all(gen.self_check(grid) == [] for grid in inputs)
    assert all(gen.canonical_like(grid) for grid in inputs)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("selection_mode", gen.SELECTION_MODES)
@pytest.mark.parametrize("color_layout", gen.COLOR_LAYOUTS)
def test_selection_and_color_branches(difficulty, selection_mode, color_layout):
    overrides = {"selection_mode": selection_mode, "color_layout": color_layout}
    if selection_mode != "unique_largest" and color_layout == "repeated_distractor":
        overrides["n_blobs"] = 4
    grid = gen.generate(731, 2, difficulty=difficulty, **overrides)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert observed["selection_mode"] == selection_mode
    assert observed["color_layout"] == color_layout


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 9},
        {"grid_h": 14},
        {"grid_w": 10},
        {"grid_w": 14},
        {"n_blobs": 3},
        {"n_blobs": 5},
        {"grid_h": 9, "grid_w": 10, "n_blobs": 3},
        {"grid_h": 14, "grid_w": 14, "n_blobs": 5},
    ],
)
def test_boundary_overrides_are_realized(difficulty, overrides):
    grid = gen.generate(991, 0, difficulty=difficulty, **overrides)
    observed = gen.observe_overrides(grid)
    for key, value in overrides.items():
        assert observed[key] == value


def test_incompatible_tied_repeated_three_blob_request_rejects_loudly():
    with pytest.raises(ValueError, match="requires n_blobs>=4"):
        gen.generate(
            17,
            0,
            difficulty="easy",
            selection_mode="tied_leftmost",
            color_layout="repeated_distractor",
            n_blobs=3,
        )


def test_five_pair_schedule_teaches_every_branch():
    for seed in range(10):
        observed = [
            gen.observe_overrides(gen.generate(seed, index, difficulty="medium"))
            for index in range(5)
        ]
        demonstrations = observed[:4]
        assert {item["selection_mode"] for item in demonstrations} == set(gen.SELECTION_MODES)
        assert {item["color_layout"] for item in demonstrations} == set(gen.COLOR_LAYOUTS)


def test_repeated_distractor_defeats_total_color_frequency_shortcut():
    grid = gen.generate(
        3001,
        3,
        difficulty="medium",
        selection_mode="unique_largest",
        color_layout="repeated_distractor",
        n_blobs=3,
    )
    analysis = gen._analysis(grid)
    selected = analysis["selected"]
    selected_color = next(iter(selected["colors"]))
    counts = {
        color: sum(value == color for row in grid for value in row)
        for color in range(1, 10)
    }
    assert max(counts, key=counts.get) != selected_color
    assert gen.self_check(grid) == []


def test_self_check_rejects_structural_impostors():
    valid = gen.generate(44, 0, difficulty="medium", selection_mode="unique_largest", n_blobs=5)
    blank = [[0 for _ in row] for row in valid]
    singleton = [[0 for _ in row] for row in valid]
    singleton[1][1] = 2
    solid_targets = [row[:] for row in valid]
    analysis = gen._analysis(solid_targets)
    target = analysis["selected"]
    for row in range(target["r1"], target["r2"] + 1):
        for col in range(target["c1"], target["c2"] + 1):
            solid_targets[row][col] = next(iter(target["colors"]))
    too_many = [row[:] for row in valid]
    inserted = False
    for row in range(1, len(too_many) - 1):
        for col in range(1, len(too_many[0]) - 1):
            if too_many[row][col] != 0:
                continue
            if all(
                too_many[row + drow][col + dcol] == 0
                for drow, dcol in gen._CARDINALS
            ):
                too_many[row][col] = 9
                inserted = True
                break
        if inserted:
            break
    assert inserted
    for impostor in (blank, singleton, solid_targets, too_many):
        assert gen.self_check(impostor)


def test_deterministic_fresh_returns_and_global_random_state():
    random.seed(9173)
    before = random.getstate()
    first = gen.generate(82, 4, difficulty="hard")
    after = random.getstate()
    second = gen.generate(82, 4, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
