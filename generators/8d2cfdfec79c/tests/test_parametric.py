"""Behavioral contract for the proposed visible-border parameter family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def _load():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "Native parametric adapter is missing"
    spec = importlib.util.spec_from_file_location("visible_border_adapter_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load()


def inversion_input():
    grid = [[0] * 10 for _ in range(8)]
    for r, c, color in ((0, 0, 2), (7, 9, 2), (0, 7, 7), (7, 1, 7)):
        grid[r][c] = color
    return grid


def test_native_adapter_exists():
    _load()


def test_canonical_program_is_exact_selected_authority(adapter):
    rows = [json.loads(line) for line in
            (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    selected = next(row for row in rows if row["task_id"] == "8d2cfdfec79c")
    assert adapter.program({"mode": "outline"}) == selected["program_solution"]


def test_occlusion_changes_the_selected_rectangle(adapter):
    grid = inversion_input()
    boundary = [2, 7, 7, 7, 7, 7, 7, 7, 2, 2]
    interior = [2, 7, 7, 7, 7, 7, 7, 7, 0, 2]
    expected = [boundary] + [interior] * 6 + [boundary]
    assert adapter.predict(grid, "fill_most_visible") == expected
    state = adapter.intermediate(grid)
    assert state["visible_counts"] == {2: 18, 7: 26}
    assert state["winner"] == 7
    assert state["raw_perimeter_winner"] == 2


def test_tie_breaks_by_first_appearance_and_preserves_crossing_borders(adapter):
    grid = [[0] * 10 for _ in range(8)]
    for r, c, color in ((0, 1, 5), (3, 3, 5), (2, 3, 8), (5, 5, 8),
                        (4, 3, 2), (5, 0, 2)):
        grid[r][c] = color
    state = adapter.intermediate(grid)
    assert state["visible_counts"] == {5: 8, 8: 8, 2: 8}
    assert state["winner"] == 5
    output = adapter.predict(grid, "fill_most_visible")
    assert output[1][2] == output[2][2] == 5
    assert output[3][3] == 8  # This input clue was overwritten by B's border.
    assert output[4][3] == output[5][3] == 2


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 4)])
def test_episode_counts_unique_inputs_and_shared_input_stream(adapter, demos, queries):
    outline = adapter.generate(17, {"mode": "outline"}, demos, queries)
    filled = adapter.generate(17, {"mode": "fill_most_visible"}, demos, queries)
    assert len(outline["train"]) == demos
    assert len(outline["test"]) == queries
    for split in ("train", "test"):
        assert [p["input"] for p in outline[split]] == [p["input"] for p in filled[split]]
    keys = [json.dumps(p["input"]) for split in ("train", "test") for p in outline[split]]
    assert len(keys) == len(set(keys))
    assert any(a["output"] != b["output"] for a, b in zip(outline["train"], filled["train"]))
    again = adapter.generate(17, {"mode": "outline"}, demos, queries)
    assert again == outline
    outline["train"][0]["input"][0][0] = 99
    assert adapter.generate(17, {"mode": "outline"}, demos, queries) == again


def test_four_queries_include_substantive_30_by_30(adapter):
    episode = adapter.generate(0, {"mode": "fill_most_visible"}, 3, 4)
    large = [pair for pair in episode["test"]
             if (len(pair["input"]), len(pair["input"][0])) == (30, 30)]
    assert large, "The supported four-query lesson must exercise the 30x30 boundary"
    for pair in large:
        occupied = [(r, c) for r, row in enumerate(pair["input"])
                    for c, color in enumerate(row) if color]
        assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= 25
        assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 25
        assert sum(bool(color) for row in pair["output"] for color in row) >= 200


def test_two_demos_teach_preserving_other_borders_inside_the_winner(adapter):
    episode = adapter.generate(0, {"mode": "fill_most_visible"}, 2, 4)
    witnesses = []
    for pair in episode["train"]:
        state = adapter.intermediate(pair["input"])
        winner = state["winner"]
        r0, c0, r1, c1 = state["boxes"][winner]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                prior = state["outlines"][r][c]
                if prior not in (0, winner):
                    witnesses.append((r, c))
                    assert pair["output"][r][c] == prior
    assert witnesses, "Two demos do not distinguish zero-only fill from overwriting interior borders"


@pytest.mark.parametrize("seed", [0, 1, 17, 33])
def test_two_demos_teach_that_a_thin_rectangle_can_win(adapter, seed):
    episode = adapter.generate(seed, {"mode": "fill_most_visible"}, 2, 4)
    witnessed = False
    for pair in episode["train"]:
        state = adapter.intermediate(pair["input"])
        r0, c0, r1, c1 = state["boxes"][state["winner"]]
        thin_winner = min(r1 - r0, c1 - c0) == 1
        fillable_other = any(min(b[2] - b[0], b[3] - b[1]) > 1
                             for color, b in state["boxes"].items()
                             if color != state["winner"])
        if thin_winner and fillable_other:
            assert pair["output"] == state["outlines"]
            witnessed = True
    assert witnessed, "No demo distinguishes selecting all rectangles from excluding thin ones"


@pytest.mark.parametrize("seed,settings,demos,queries", [
    (True, {"mode": "outline"}, 3, 4),
    (-1, {"mode": "outline"}, 3, 4),
    (0, {"mode": "unknown"}, 3, 4),
    (0, {"mode": "outline", "extra": 1}, 3, 4),
    (0, {"mode": "outline"}, True, 4),
    (0, {"mode": "outline"}, 1, 4),
    (0, {"mode": "outline"}, 7, 4),
    (0, {"mode": "outline"}, 3, 0),
    (0, {"mode": "outline"}, 3, 5),
])
def test_invalid_requests_fail_closed(adapter, seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(seed, settings, demos, queries)
