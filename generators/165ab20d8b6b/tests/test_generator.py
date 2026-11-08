"""Task-local regressions for the orthogonal-contact-shell generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "165ab20d8b6b"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = {(row, col)}
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                for dr, dc in CARDINAL:
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        cells.add(point)
                        stack.append(point)
            result.append((color, cells))
    return result


def independent_rule(grid):
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    for color, cells in _components(grid):
        shell = {
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in CARDINAL
            if 0 <= r + dr < height
            and 0 <= c + dc < width
            and (r + dr, c + dc) not in cells
            and grid[r + dr][c + dc] == 0
        }
        for row, col in shell:
            output[row][col] = color
    return output


def _exterior_background(grid):
    height, width = len(grid), len(grid[0])
    todo = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 0 and (r in (0, height - 1) or c in (0, width - 1))
    ]
    seen = set(todo)
    while todo:
        row, col = todo.pop()
        for dr, dc in CARDINAL:
            point = (row + dr, col + dc)
            if (
                0 <= point[0] < height
                and 0 <= point[1] < width
                and point not in seen
                and grid[point[0]][point[1]] == 0
            ):
                seen.add(point)
                todo.append(point)
    return seen


def independent_external_only_rival(grid):
    height, width = len(grid), len(grid[0])
    exterior = _exterior_background(grid)
    output = [[0] * width for _ in range(height)]
    for color, cells in _components(grid):
        for row, col in exterior:
            if any((row + dr, col + dc) in cells for dr, dc in CARDINAL):
                output[row][col] = color
    return output


def _shells(grid):
    height, width = len(grid), len(grid[0])
    answer = []
    for _, cells in _components(grid):
        answer.append(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in CARDINAL
                if 0 <= r + dr < height
                and 0 <= c + dc < width
                and (r + dr, c + dc) not in cells
                and grid[r + dr][c + dc] == 0
            }
        )
    return answer


def test_rule_pin_and_honest_axis_contract():
    assert GEN.RULE_HASH == "63879e6d755e"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_blobs", "scene_profile"}
    assert GEN.AXES["scene_profile"]["valid"] == "canonical|broad|hole_witness"


def test_all_canonical_inputs_are_accepted_and_owned():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(8, 9), (14, 16)])
@pytest.mark.parametrize("n_blobs", [1, 4])
@pytest.mark.parametrize("scene_profile", ["canonical", "broad", "hole_witness"])
def test_exact_override_boundaries_are_constructive_and_observable(
    band, grid_h, grid_w, n_blobs, scene_profile
):
    grid = GEN.generate(
        917,
        23,
        difficulty=band,
        grid_h=grid_h,
        grid_w=grid_w,
        n_blobs=n_blobs,
        scene_profile=scene_profile,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_blobs": n_blobs,
        "scene_profile": scene_profile,
    }
    assert GEN.rule_mirror(grid) == independent_rule(grid)
    shells = _shells(grid)
    assert all(not shells[i] & shells[j] for i in range(len(shells)) for j in range(i))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 8},
        {"grid_w": 17},
        {"n_blobs": 0},
        {"n_blobs": 5},
        {"scene_profile": "unknown"},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"n_blobs": "2"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_external_only_shortcut_fits_canonical_but_hole_profile_refutes_it():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert all(independent_external_only_rival(p["input"]) == p["output"] for p in pairs)
    assert set(GEN.CANONICAL_SHORTCUTS) == {"external_shell_only"}
    assert set(GEN.SEMANTIC_RIVALS) == {"external_shell_only"}

    grid = GEN.generate(41, 7, grid_h=8, grid_w=9, n_blobs=4, scene_profile="hole_witness")
    truth = independent_rule(grid)
    rival = independent_external_only_rival(grid)
    assert GEN.SEMANTIC_WITNESSES["enclosed_hole"](grid)
    assert GEN.SEMANTIC_RIVALS["external_shell_only"](grid) == rival
    assert truth != rival
    assert GEN.rule_mirror(grid) == truth


def test_profiles_are_structurally_distinct_and_default_schedule_covers_them():
    for profile in ("canonical", "broad", "hole_witness"):
        grid = GEN.generate(73, 3, scene_profile=profile)
        assert GEN.observe_overrides(grid)["scene_profile"] == profile

    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(1201, index, difficulty=band) for index in range(96)]
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert {item["scene_profile"] for item in observed} == {
            "canonical",
            "broad",
            "hole_witness",
        }
        assert {item["n_blobs"] for item in observed} == {1, 2, 3, 4}
        assert any(
            item["scene_profile"] == "canonical"
            and item["n_blobs"] == 2
            and item["grid_h"] in {8, 9, 10}
            and item["grid_w"] in {9, 10, 11}
            for item in observed
        )


def test_generation_is_deterministic_fresh_and_helper_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(16):
            first = GEN.generate(303, index, difficulty=band)
            second = GEN.generate(303, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first) == []
            before = deepcopy(first)
            GEN.rule_mirror(first)
            for fn in GEN.SEMANTIC_RIVALS.values():
                fn(first)
            for fn in GEN.SEMANTIC_WITNESSES.values():
                fn(first)
            assert first == before


def test_self_check_rejects_malformed_border_and_shell_collisions():
    assert GEN.self_check(None)
    assert GEN.self_check([])
    assert GEN.self_check([[0], [0, 1]])

    border = GEN.generate(8, 2, grid_h=8, grid_w=9, n_blobs=1, scene_profile="broad")
    color, cells = _components(border)[0]
    row, col = min(cells)
    moved = deepcopy(border)
    moved[row][col] = 0
    moved[0][0] = color
    assert GEN.self_check(moved)

    overlap = [[0] * 9 for _ in range(8)]
    overlap[3][2] = overlap[3][3] = 2
    overlap[3][5] = overlap[3][6] = 4
    assert any("shell" in message.lower() for message in GEN.self_check(overlap))
