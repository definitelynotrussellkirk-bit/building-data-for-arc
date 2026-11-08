"""Behavioral coverage for the native marker-selected parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


TASK_ID = "d9d4f0ebb48b"
HERE = Path(__file__).resolve()
PROTOTYPE = HERE.parents[1] / "workspace" / "parametric" / "prototype.py"
CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (for*/fold ((out g)) ((r (in-range 1 (- (rows g) 1))) (c (in-range 1 (- (cols g) 1)))) (let ((v (at g r c))) (if (and (not (= v 0)) (= (at g (- r 1) c) v) (= (at g (+ r 1) c) v) (= (at g r (- c 1)) v) (= (at g r (+ c 1)) v)) (paint-cells out (positions-in-rect (- r 1) (- c 1) (+ r 1) (+ c 1)) v) out)))))"


def _load():
    if not PROTOTYPE.is_file():
        pytest.fail(f"missing parametric prototype: {PROTOTYPE}")
    spec = importlib.util.spec_from_file_location("_test_d9d4_parametric", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    found = []
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            value = grid[r][c]
            if value and all(
                grid[r + dr][c + dc] == value
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                found.append((r, c))
    return found


def _literal_input() -> list[list[int]]:
    return [
        [8, 8, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 4, 4, 4, 0],
        [0, 0, 0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def test_program_default_is_exact_canonical_and_alternative_is_real():
    prototype = _load()
    local = prototype.program({"fill_color_mode": "local"})
    selected = prototype.program({"fill_color_mode": "selector_source"})
    assert local == CANONICAL_PROGRAM
    assert isinstance(selected, str) and selected.strip()
    assert selected != local


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"fill_color_mode": "unknown"}, {"fill_color_mode": "local", "extra": 1}],
)
def test_program_rejects_malformed_or_undeclared_settings(settings):
    prototype = _load()
    with pytest.raises((TypeError, ValueError)):
        prototype.program(settings)


def test_literal_selector_source_uses_second_plus_color_as_intermediate():
    prototype = _load()
    source = _literal_input()
    local = prototype.apply_mode(source, "local")
    selected = prototype.apply_mode(source, "selector_source")

    expected_local = copy.deepcopy(source)
    for r in range(1, 4):
        for c in range(1, 4):
            expected_local[r][c] = 2
    for r in range(5, 8):
        for c in range(5, 8):
            expected_local[r][c] = 4

    expected_selected = copy.deepcopy(source)
    for r in range(1, 4):
        for c in range(1, 4):
            expected_selected[r][c] = 4
    for r in range(5, 8):
        for c in range(5, 8):
            expected_selected[r][c] = 4

    assert local == expected_local
    assert selected == expected_selected
    assert source == _literal_input(), "claims must not mutate inputs"


def test_generate_uses_matched_inputs_and_independent_requested_counts():
    prototype = _load()
    settings = [
        {"fill_color_mode": "local"},
        {"fill_color_mode": "selector_source"},
    ]
    episodes = [prototype.generate(1234, item, demos=3, queries=4) for item in settings]
    assert [len(episode["train"]) for episode in episodes] == [3, 3]
    assert [len(episode["test"]) for episode in episodes] == [4, 4]
    assert episodes[0]["program_solution"] == CANONICAL_PROGRAM
    assert episodes[1]["program_solution"] != CANONICAL_PROGRAM

    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes[0][split]] == [
            pair["input"] for pair in episodes[1][split]
        ]
    all_inputs = [pair["input"] for split in ("train", "test") for pair in episodes[0][split]]
    assert len({json.dumps(grid) for grid in all_inputs}) == 7
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(episodes[0][split], episodes[1][split])
    )


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("mode", ["local", "selector_source"])
def test_supported_demo_counts_always_return_exactly_four_queries(demos, mode):
    prototype = _load()
    episode = prototype.generate(
        9000 + demos,
        {"fill_color_mode": mode},
        demos=demos,
        queries=4,
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 3},
        {"demos": 3, "queries": 5},
        {"demos": True, "queries": 4},
    ],
)
def test_generate_rejects_unsupported_counts(kwargs):
    prototype = _load()
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, {"fill_color_mode": "local"}, **kwargs)


def test_schedule_contains_minimum_and_substantive_30_by_30_stress():
    prototype = _load()
    episode = prototype.generate(41, {"fill_color_mode": "local"}, demos=3, queries=4)
    grids = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    dimensions = [(len(grid), len(grid[0])) for grid in grids]
    assert (9, 9) in dimensions
    assert (30, 30) in dimensions

    stress = grids[dimensions.index((30, 30))]
    assert sum(cell != 0 for row in stress for cell in row) >= 70
    assert any(stress[-1][c] != 0 for c in range(30))
    assert any(row[0] != 0 or row[-1] != 0 for row in stress[1:])
    assert len(_centers(stress)) >= 4


def test_every_input_has_contiguous_selector_and_distinct_reading_order_pluses():
    prototype = _load()
    episode = prototype.generate(77, {"fill_color_mode": "selector_source"}, demos=6, queries=4)
    for pair in [*episode["train"], *episode["test"]]:
        grid = pair["input"]
        centers = _centers(grid)
        plus_colors = [grid[r][c] for r, c in centers]
        selector_length = sum(cell != 0 for cell in grid[0])
        assert len(centers) >= 2
        assert len(plus_colors) == len(set(plus_colors))
        assert 1 <= selector_length <= len(centers)
        assert all(grid[0][c] != 0 for c in range(selector_length))
        assert all(grid[0][c] == 0 for c in range(selector_length, len(grid[0])))
        assert grid[0][0] not in plus_colors


def test_two_visible_demos_reject_every_other_declared_setting():
    prototype = _load()
    local = prototype.generate(314159, {"fill_color_mode": "local"}, demos=2, queries=4)
    selected = prototype.generate(314159, {"fill_color_mode": "selector_source"}, demos=2, queries=4)
    assert [pair["input"] for pair in local["train"]] == [pair["input"] for pair in selected["train"]]
    assert all(a["output"] != b["output"] for a, b in zip(local["train"], selected["train"]))
