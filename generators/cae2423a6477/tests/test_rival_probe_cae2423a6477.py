from __future__ import annotations

import importlib.util
from pathlib import Path

TASK = "cae2423a6477"
REPO = Path(__file__).resolve().parents[3]
TOOL_PATH = REPO / "generators" / TASK / "workspace" / "rival_probe.py"
CURRENT_GENERATOR = REPO / "generators" / TASK / "generator.py"


def _load_tool():
    assert TOOL_PATH.is_file(), "workspace/rival_probe.py must exist"
    spec = importlib.util.spec_from_file_location("rival_probe", TOOL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _legacy_hollow_scene() -> tuple[list[list[int]], list[list[int]]]:
    """Return a true frame beside the old frame-plus-nub negative."""

    grid = [[0 for _ in range(11)] for _ in range(6)]
    true_frame = {
        (row, col)
        for row in range(1, 4)
        for col in range(1, 4)
        if row in {1, 3} or col in {1, 3}
    }
    nubbed_ring = {
        (row, col)
        for row in range(1, 4)
        for col in range(6, 9)
        if row in {1, 3} or col in {6, 8}
    }
    nubbed_ring.add((2, 9))
    for row, col in true_frame | nubbed_ring:
        grid[row][col] = 3

    expected = [list(row) for row in grid]
    for row, col in true_frame:
        expected[row][col] = 7
    return grid, expected


def test_probe_reproduces_legacy_shortcut_and_accepts_strengthened_lessons():
    probe = _load_tool()

    legacy_input, legacy_output = _legacy_hollow_scene()
    closed_loop = probe.CANDIDATES["closed_unbranched_loop"]
    assert probe._paint_matching(legacy_input, closed_loop) == legacy_output

    after = probe.probe_generator(CURRENT_GENERATOR, seeds_per_band=4)
    assert after["surviving_rivals"] == []
    assert after["candidates"]["closed_unbranched_loop"]["canonical_fit"]
    assert after["candidates"]["rectangular_hole"]["canonical_fit"]
    assert after["candidates"]["closed_unbranched_loop"]["surviving_windows"] == 0
    assert after["candidates"]["rectangular_hole"]["surviving_windows"] == 0
