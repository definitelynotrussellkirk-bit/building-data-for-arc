from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.8b320727aa72.generator")

ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    rows = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        for split in ("train", "test"):
            rows.extend(pair["input"] for pair in row.get(split) or [])
    return rows


def test_all_canonical_inputs_pass_self_check():
    inputs = _canonical_inputs()
    assert len(inputs) == 8
    for grid in inputs:
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generated_grid_has_exact_24_plus_1_erasure_grammar(difficulty):
    for seed in range(12):
        grid = gen.generate(seed, seed % 5, difficulty=difficulty)
        assert gen.self_check(grid, difficulty=difficulty) == []
        observed = gen.observe_overrides(grid)
        assert 5 <= observed["n_filled_in_tile"] <= 12
        assert 1 <= observed["n_disagreements"] <= 5
        assert 1 <= observed["palette_size"] <= 5
        assert 0 <= observed["corrupt_tile_index"] <= 24


def test_exact_override_boundaries_are_observed():
    cases = [
        {
            "n_filled_in_tile": 5,
            "n_disagreements": 5,
            "palette_size": 5,
            "background_color": 5,
            "separator_color": 2,
            "corrupt_tile_index": 0,
            "anchor_position": False,
            "tile_layout": "frame",
            "disagreement_distribution": "edge",
        },
        {
            "n_filled_in_tile": 12,
            "n_disagreements": 1,
            "palette_size": 1,
            "background_color": 9,
            "separator_color": 4,
            "corrupt_tile_index": 24,
            "anchor_position": True,
            "tile_layout": "diagonal",
            "disagreement_distribution": "center",
        },
    ]
    exact = {
        "n_filled_in_tile",
        "n_disagreements",
        "palette_size",
        "background_color",
        "separator_color",
        "corrupt_tile_index",
        "anchor_position",
    }
    for index, case in enumerate(cases):
        grid = gen.generate(100 + index, 2, difficulty="hard", **case)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert {key: observed[key] for key in exact} == {
            key: case[key] for key in exact
        }


def test_self_check_rejects_targeted_impostors():
    grid = gen.generate(44, 3, difficulty="medium")
    observed = gen.observe_overrides(grid)
    anomaly_index = observed["corrupt_tile_index"]
    tr, tc = divmod(anomaly_index, 5)
    tr *= 6
    tc *= 6

    bad_separator = copy.deepcopy(grid)
    bad_separator[5][0] = (bad_separator[5][0] + 1) % 10

    reserved_marker = copy.deepcopy(grid)
    reserved_marker[0][0] = 1

    non_background_replacement = copy.deepcopy(grid)
    consensus_index = 0 if anomaly_index != 0 else 1
    cr, cc = divmod(consensus_index, 5)
    cr *= 6
    cc *= 6
    changed = next(
        (r, c)
        for r in range(5)
        for c in range(5)
        if grid[tr + r][tc + c] != grid[cr + r][cc + c]
    )
    r, c = changed
    illegal = next(
        color
        for color in range(10)
        if color not in {
            1,
            observed["background_color"],
            observed["separator_color"],
            grid[cr + r][cc + c],
        }
    )
    non_background_replacement[tr + r][tc + c] = illegal

    second_anomaly = copy.deepcopy(grid)
    second_index = next(
        index for index in range(25) if index not in {anomaly_index, consensus_index}
    )
    sr, sc = divmod(second_index, 5)
    sr *= 6
    sc *= 6
    second_anomaly[sr + r][sc + c] = observed["background_color"]

    for mutation in (
        bad_separator,
        reserved_marker,
        non_background_replacement,
        second_anomaly,
    ):
        assert gen.self_check(mutation)


def test_deterministic_replay_returns_fresh_objects():
    first = gen.generate(7, 9, difficulty="hard")
    replay = gen.generate(7, 9, difficulty="hard")
    assert first == replay
    assert first is not replay
    assert all(left is not right for left, right in zip(first, replay))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != replay


def test_sequential_lesson_schedule_breaks_first_tile_shortcut():
    grids = [gen.generate(2026, sample_index, difficulty="medium") for sample_index in range(4)]
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert observed[0]["corrupt_tile_index"] == 0
    assert all(gen.self_check(grid) == [] for grid in grids)
    overridden = gen.generate(2026, 0, corrupt_tile_index=24)
    assert gen.observe_overrides(overridden)["corrupt_tile_index"] == 24
