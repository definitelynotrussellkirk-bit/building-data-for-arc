"""Focused behavioral tests for the opt-in rectangle/color-selection adapter."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


def adapter():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/adapter.py"
    assert path.is_file(), "native parametric adapter must exist"
    spec = importlib.util.spec_from_file_location("rectangle_color_adapter_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture():
    # A 4-cell red component wins inside; two disconnected blue triominoes
    # have greater combined area. A 7-cell yellow object lies outside.
    rows = [
        "44444440000",
        "03000000030",
        "00110002200",
        "00100002200",
        "00000000000",
        "00110000000",
        "00100000000",
        "00000000000",
        "03000500030",
        "00000000000",
    ]
    grid = [[int(c) for c in row] for row in rows]
    # Exactly two opposite green corners, not four.
    grid[1][9] = grid[8][1] = 0
    return grid


def test_interior_component_color_ignores_global_size_and_total_color_area():
    a = adapter()
    grid = fixture()
    before = copy.deepcopy(grid)
    out = a.solve(grid, {"color_source": "largest_interior"})
    assert out[1] == [0, 3, 2, 2, 2, 2, 2, 2, 2, 2, 0]
    assert out[8] == [0, 2, 2, 2, 2, 5, 2, 2, 2, 3, 0]
    assert out[0] == grid[0]
    assert out[2][2:4] == [1, 1]
    assert out[2][7:9] == [2, 2]
    assert grid == before


def test_canonical_setting_preserves_all_occupied_cells():
    a = adapter()
    out = a.solve(fixture(), {"color_source": "cyan"})
    assert out[1] == [0, 3, 8, 8, 8, 8, 8, 8, 8, 8, 0]
    assert out[8][5] == 5
    assert out[2][2:4] == [1, 1]


def test_counts_are_independent_and_first_turn_has_no_future_query_leak():
    a = adapter()
    settings = {"color_source": "largest_interior"}
    one = a.generate(17, settings, 3, 1)
    four = a.generate(17, settings, 3, 4)
    assert len(four["train"]) == 3 and len(four["test"]) == 4
    assert one["train"] == four["train"]
    assert one["test"][0] == four["test"][0]
    public = a.public_turn(four, 0)
    assert public == a.public_turn(one, 0)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    public["train"][0]["input"][0][0] = 9
    assert four == a.generate(17, settings, 3, 4)


def test_matched_settings_and_substantive_thirty_by_thirty_query():
    a = adapter()
    cyan = a.generate(1, {"color_source": "cyan"}, 2, 4)
    chosen = a.generate(1, {"color_source": "largest_interior"}, 2, 4)
    assert [p["input"] for p in cyan["train"] + cyan["test"]] == [
        p["input"] for p in chosen["train"] + chosen["test"]]
    pairs = chosen["train"] + chosen["test"]
    assert len({tuple(map(tuple, p["input"])) for p in pairs}) == 6
    last = chosen["test"][-1]
    assert (len(last["input"]), len(last["input"][0])) == (30, 30)
    changes = sum(x != y for rx, ry in zip(last["input"], last["output"])
                  for x, y in zip(rx, ry))
    assert changes >= 85, "large stress must paint a substantial long border"
    assert sum(v != 0 for row in last["input"] for v in row) >= 80


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5), (True, 4), (3, 4.0)])
def test_invalid_counts_fail_explicitly(demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(0, {"color_source": "cyan"}, demos, queries)


def test_invalid_parameters_grids_and_exact_size_controls():
    a = adapter()
    for settings in ({}, {"color_source": "other"}, {"color_source": "cyan", "extra": 1}):
        with pytest.raises(ValueError):
            a.generate(0, settings, 3, 4)
    grid = fixture()
    grid[2][2] = True
    with pytest.raises(ValueError):
        a.solve(grid, {"color_source": "cyan"})
    for height, width in ((11, 12), (30, 31), (12.0, 12), (True, 12)):
        with pytest.raises(ValueError):
            a.generate(0, {"color_source": "cyan"}, 3, 4, height=height, width=width)
    for height, width in ((12, 12), (12, 30), (30, 12), (30, 30)):
        episode = a.generate(0, {"color_source": "largest_interior"}, 2, 4,
                             height=height, width=width)
        assert all((len(p["input"]), len(p["input"][0])) == (height, width)
                   for p in episode["train"] + episode["test"])


def test_empty_and_tied_interiors_are_outside_admitted_grammar():
    a = adapter()
    empty = fixture()
    for r in range(2, 8):
        for c in range(2, 9):
            empty[r][c] = 0
    with pytest.raises(ValueError, match="interior object"):
        a.solve(empty, {"color_source": "largest_interior"})
    tied = fixture()
    tied[2][7] = 0  # Red and each blue component now have three cells.
    with pytest.raises(ValueError, match="unique largest"):
        a.solve(tied, {"color_source": "largest_interior"})


def test_demo_count_does_not_resample_query_prefix_or_global_random_state():
    import random
    a = adapter()
    random.seed(47)
    state = random.getstate()
    settings = {"color_source": "largest_interior"}
    two = a.generate(0, settings, 2, 4)
    six = a.generate(0, settings, 6, 4)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert random.getstate() == state


def painted_color(pair):
    return next(y for rx, ry in zip(pair["input"], pair["output"])
                for x, y in zip(rx, ry) if x != y)


def test_two_demo_lesson_rejects_excluding_cyan_objects():
    a = adapter()
    for seed in (0, 2, 17):
        e = a.generate(seed, {"color_source": "largest_interior"}, 2, 4)
        colors = {painted_color(pair) for pair in e["train"]}
        assert 8 in colors and len(colors) == 2


def test_two_demo_lesson_distinguishes_component_size_from_color_area_rank():
    from collections import Counter
    a = adapter()
    e = a.generate(0, {"color_source": "largest_interior"}, 2, 4)
    winner_is_most_frequent = []
    for pair in e["train"]:
        grid = pair["input"]
        points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
        r0, r1 = sorted(p[0] for p in points)
        c0, c1 = sorted(p[1] for p in points)
        counts = Counter(grid[r][c] for r in range(r0 + 1, r1)
                         for c in range(c0 + 1, c1) if grid[r][c])
        winner_is_most_frequent.append(counts[painted_color(pair)] == max(counts.values()))
    assert set(winner_is_most_frequent) == {True, False}


def test_mandatory_demos_change_winner_position_relative_to_outside_strip():
    a = adapter()
    e = a.generate(0, {"color_source": "largest_interior"}, 2, 4)
    quadrants = []
    for pair in e["train"]:
        grid = pair["input"]
        color = painted_color(pair)
        # Normalize the outside strip to the top, using only green marker geometry.
        for _ in range(4):
            points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
            r0, r1 = sorted(p[0] for p in points)
            c0, c1 = sorted(p[1] for p in points)
            if r0 > 0:
                break
            grid = [list(row) for row in zip(*grid[::-1])]
        cells = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)
                 if grid[r][c] == color]
        quadrants.append((sum(r for r, _ in cells) / len(cells) > (r0 + r1) / 2,
                          sum(c for _, c in cells) / len(cells) > (c0 + c1) / 2))
    assert len(set(quadrants)) == 2


def test_mandatory_lessons_separate_four_from_eight_connectivity():
    a = adapter()
    e = a.generate(0, {"color_source": "largest_interior"}, 2, 4)
    witnesses = []
    for pair in e["train"]:
        info = a.analyze(pair["input"])
        for i, left in enumerate(info["components"]):
            for right in info["components"][i + 1:]:
                if left["color"] != right["color"]:
                    continue
                diagonal_contact = any(abs(r - s) == abs(c - t) == 1
                                       for r, c in left["cells"] for s, t in right["cells"])
                witnesses.append(diagonal_contact and
                                 left["size"] + right["size"] > info["selected"]["size"])
    assert any(witnesses), "a demo must reject merging merely diagonal neighbors"


def test_mandatory_lessons_require_clipping_before_component_selection():
    a = adapter()
    e = a.generate(0, {"color_source": "largest_interior"}, 2, 4)
    witnesses = []
    for pair in e["train"]:
        info = a.analyze(pair["input"])
        r0, c0, r1, c1 = info["rectangle"]
        for group in a.components(pair["input"]):
            inside = sum(r0 < r < r1 and c0 < c < c1 for r, c in group["cells"])
            witnesses.append(0 < inside < info["selected"]["size"] < group["size"]
                             and group["color"] != painted_color(pair))
    assert any(witnesses), "a demo must reject measuring a boundary-crossing object before clipping"
