"""Native parametric adapter contract for the chamber-count family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "4f1ec6a61342"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
ADAPTER = HOME / "workspace" / "parametric" / "adapter.py"
DIRECT = {"mode": "direct"}
RELAY = {"mode": "height_relay"}


def _load_adapter():
    assert ADAPTER.is_file(), "native parametric adapter is missing"
    spec = importlib.util.spec_from_file_location("_chamber_parametric_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    path = canonical_path(ROOT)
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical authority row is missing")


def _rooms(grid):
    h, w = len(grid), len(grid[0])
    seen = {(0, 0)}
    result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 5:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = rr + dr, cc + dc
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen and grid[point[0]][point[1]] != 5
                            and point != (0, 0)):
                        seen.add(point)
                        stack.append(point)
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            assert len(cells) == (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
            result.append({
                "cells": cells,
                "seeds": sum(grid[rr][cc] == 2 for rr, cc in cells),
                "height": max(rs) - min(rs) + 1,
            })
    return result


def _painted_cells(output):
    return {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 8}


def test_parametric_adapter_exists_and_exports_contract():
    adapter = _load_adapter()
    assert callable(adapter.program)
    assert callable(adapter.generate)


def test_canonical_default_program_matches_exact_authority():
    adapter = _load_adapter()
    assert adapter.program(DIRECT) == _canonical_program()


def test_inputs_are_matched_across_settings_and_counts_are_independent():
    adapter = _load_adapter()
    direct = adapter.generate(17, DIRECT, demos=3, queries=4)
    relay = adapter.generate(17, RELAY, demos=3, queries=4)
    assert len(direct["train"]) == len(relay["train"]) == 3
    assert len(direct["test"]) == len(relay["test"]) == 4
    direct_inputs = [p["input"] for p in direct["train"] + direct["test"]]
    relay_inputs = [p["input"] for p in relay["train"] + relay["test"]]
    assert direct_inputs == relay_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in direct_inputs}) == 7
    assert direct["program_solution"] == adapter.program(DIRECT)
    assert relay["program_solution"] == adapter.program(RELAY)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_every_scene_has_unique_direct_and_height_relay_targets(seed):
    adapter = _load_adapter()
    direct = adapter.generate(seed, DIRECT, demos=3, queries=4)
    relay = adapter.generate(seed, RELAY, demos=3, queries=4)
    for direct_pair, relay_pair in zip(
            direct["train"] + direct["test"], relay["train"] + relay["test"]):
        grid = direct_pair["input"]
        assert grid == relay_pair["input"]
        rooms = _rooms(grid)
        control = grid[0][0]
        cue = [room for room in rooms if room["seeds"] == control]
        assert len(cue) == 1
        cue = cue[0]
        assert 2 <= cue["height"] <= 6
        assert cue["height"] != control
        destination = [room for room in rooms if room["seeds"] == cue["height"]]
        assert len(destination) == 1
        destination = destination[0]
        assert destination is not cue
        assert _painted_cells(direct_pair["output"]) == set(cue["cells"])
        assert _painted_cells(relay_pair["output"]) == set(destination["cells"])
        assert direct_pair["output"] != relay_pair["output"]


def test_supported_count_boundaries_and_large_stress_query():
    adapter = _load_adapter()
    for demos, queries in ((2, 1), (2, 4), (6, 1), (6, 4)):
        episode = adapter.generate(23, RELAY, demos=demos, queries=queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        for pair in episode["train"] + episode["test"]:
            assert 1 <= len(pair["input"]) <= 30
            assert 1 <= len(pair["input"][0]) <= 30
    full = adapter.generate(23, RELAY, demos=3, queries=4)
    assert (len(full["test"][-1]["input"]), len(full["test"][-1]["input"][0])) == (30, 30)


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({"mode": "unknown"}, 3, 4),
        ({"mode": "direct", "extra": 1}, 3, 4),
        ({}, 3, 4),
        (DIRECT, 1, 4),
        (DIRECT, 7, 4),
        (DIRECT, 3, 0),
        (DIRECT, 3, 5),
        (DIRECT, True, 4),
    ],
)
def test_invalid_settings_and_counts_are_rejected(settings, demos, queries):
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(5, settings, demos=demos, queries=queries)


def _paint_room(grid, selected):
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for room in selected:
        for r, c in room["cells"]:
            out[r][c] = 8
    return out


def _finite_rivals(grid, mode):
    rooms = _rooms(grid)
    control = grid[0][0]
    cue = next(room for room in rooms if room["seeds"] == control)
    if mode == "direct":
        ordered = sorted(rooms, key=lambda room: room["seeds"])
        clipped = min(control, 3)
        clamped_index = min(control, len(ordered) - 1)
        return {
            "ordinal_rank": _paint_room(grid, ordered[control:control + 1]),
            "clamped_ordinal_rank": _paint_room(grid, ordered[clamped_index:clamped_index + 1]),
            "distinct_seed_columns": _paint_room(
                grid,
                [room for room in rooms
                 if len({c for r, c in room["cells"] if grid[r][c] == 2}) == control],
            ),
            "clipped_control": _paint_room(
                grid, [room for room in rooms if room["seeds"] == clipped]),
        }
    cr = sum(r for r, _ in cue["cells"]) / len(cue["cells"])
    cc = sum(c for _, c in cue["cells"]) / len(cue["cells"])
    ordered = sorted(
        [room for room in rooms if room is not cue],
        key=lambda room: abs(sum(r for r, _ in room["cells"]) / len(room["cells"]) - cr)
        + abs(sum(c for _, c in room["cells"]) / len(room["cells"]) - cc),
    )
    largest = max(room["seeds"] for room in rooms)
    width = max(c for _, c in cue["cells"]) - min(c for _, c in cue["cells"]) + 1
    return {
        "nearest_to_cue": _paint_room(grid, ordered[:1]),
        "farthest_from_cue": _paint_room(grid, ordered[-1:]),
        "cue_width_as_count": _paint_room(
            grid, [room for room in rooms if room["seeds"] == width]),
        "largest_seed_count": _paint_room(
            grid, [room for room in rooms if room["seeds"] == largest]),
        "height_plus_one": _paint_room(
            grid, [room for room in rooms if room["seeds"] == cue["height"] + 1]),
    }


@pytest.mark.parametrize("seed", [0, 17, 991])
@pytest.mark.parametrize("settings", [DIRECT, RELAY])
def test_three_visible_demos_refute_finite_plausible_rivals(seed, settings):
    adapter = _load_adapter()
    episode = adapter.generate(seed, settings, demos=3, queries=4)
    mode = settings["mode"]
    rivals = [_finite_rivals(pair["input"], mode) for pair in episode["train"]]
    for name in rivals[0]:
        assert any(rival[name] != pair["output"]
                   for rival, pair in zip(rivals, episode["train"])), name
