from __future__ import annotations

from collections import deque
import copy
import importlib
import random

import pytest


g = importlib.import_module("puzzle_generators.per_puzzle.44690b1b635f.generator")
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def normalized_topology(grid):
    info = g._analysis(grid)
    assert not info["errors"], info["errors"]
    return tuple("".join("8" if value == 8 else "0" for value in row) for row in grid)


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    marker_positions = {}
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in (0, 8):
                marker_positions.setdefault(value, []).append((row, col))
    singleton = [color for color, cells in marker_positions.items() if len(cells) == 1]
    assert len(marker_positions) == 2 and len(singleton) == 1
    center_color = singleton[0]
    arm_color = next(color for color in marker_positions if color != center_color)
    start = marker_positions[center_color][0]
    distance = {start: 0}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in DIRS:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 8
                and (nr, nc) not in distance
            ):
                distance[(nr, nc)] = distance[(row, col)] + 1
                queue.append((nr, nc))
    output = copy.deepcopy(grid)
    for (row, col), steps in distance.items():
        if grid[row][col] == 0:
            output[row][col] = center_color if steps % 2 == 0 else arm_color
    return output


def test_procedural_maze_profile_exists_and_breaks_fixed_template_support():
    assert "procedural_maze" in g.SCENE_PROFILES
    for band in ("easy", "medium", "hard"):
        signatures = {
            normalized_topology(
                g.generate(seed, seed * 17 + 3, difficulty=band, scene_profile="procedural_maze")
            )
            for seed in range(64)
        }
        assert len(signatures) >= 60


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_procedural_maze_is_source_valid_and_matches_independent_oracle(band):
    expected_shape = {"easy": (10, 12), "medium": (13, 16), "hard": (16, 24)}[band]
    for seed in range(32):
        grid = g.generate(seed + 1000, seed * 29 + 7, difficulty=band, scene_profile="procedural_maze")
        assert (len(grid), len(grid[0])) == expected_shape
        assert g.observe_overrides(grid) == {"scene_profile": "procedural_maze"}
        assert g.self_check(
            grid,
            difficulty=band,
            meta={"overrides": {"scene_profile": "procedural_maze"}},
        ) == []
        assert g.rule_mirror(grid) == independent_oracle(grid)


def _closed_connector(grid):
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 8 or row % 2 == col % 2:
                continue
            if row % 2 == 0:
                neighbors = ((row - 1, col), (row + 1, col))
            else:
                neighbors = ((row, col - 1), (row, col + 1))
            if all(grid[r][c] != 8 for r, c in neighbors):
                return row, col
    raise AssertionError("generated perfect maze had no closed connector")


def test_structural_recognizer_rejects_cycle_and_even_even_hole():
    grid = g.generate(71, 91, difficulty="hard", scene_profile="procedural_maze")

    cycle = copy.deepcopy(grid)
    row, col = _closed_connector(cycle)
    cycle[row][col] = 0
    assert any("declared semantic lesson" in error for error in g.self_check(cycle))

    illegal_lattice_hole = copy.deepcopy(grid)
    illegal_lattice_hole[2][2] = 0
    assert any("declared semantic lesson" in error for error in g.self_check(illegal_lattice_hole))


def test_procedural_generation_is_deterministic_fresh_and_rng_isolated():
    random.seed(20261023)
    state = random.getstate()
    first = g.generate(97, 103, difficulty="hard", scene_profile="procedural_maze")
    assert random.getstate() == state
    second = g.generate(97, 103, difficulty="hard", scene_profile="procedural_maze")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


def test_default_sampler_materially_expands_normalized_topology_support():
    for band in ("easy", "medium", "hard"):
        all_topologies = set()
        procedural_topologies = set()
        public_count = 0
        for seed in range(800):
            grid = g.generate(seed, seed * 11 + 1, difficulty=band)
            profile = g.observe_overrides(grid)["scene_profile"]
            topology = normalized_topology(grid)
            all_topologies.add(topology)
            if profile == "procedural_maze":
                procedural_topologies.add(topology)
            if profile in g.PUBLIC_PROFILES:
                public_count += 1
        assert len(all_topologies) >= 55
        assert len(procedural_topologies) >= 40
        assert 100 < public_count < 220


def test_fixed_profiles_remain_valid_in_every_band():
    for band in ("easy", "medium", "hard"):
        for profile in g.PUBLIC_PROFILES + g.FIXED_GENERAL_PROFILES:
            grid = g.generate(313, 419, difficulty=band, scene_profile=profile)
            assert g.observe_overrides(grid) == {"scene_profile": profile}
            assert g.self_check(grid, difficulty=band, meta={"overrides": {"scene_profile": profile}}) == []
            assert g.rule_mirror(grid) == independent_oracle(grid)
