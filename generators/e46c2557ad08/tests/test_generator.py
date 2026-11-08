"""Regression and semantic-contract tests for e46c2557ad08."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "e46c2557ad08"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"reviewed_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

H_DOMINO = frozenset({(0, 0), (0, 1)})
V_DOMINO = frozenset({(0, 0), (1, 0)})
BANDS = (None, "easy", "medium", "hard")


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[tuple[int, set[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                cr, cc = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (cr + dr, cc + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            found.append((color, cells))
    return found


def _normalize(cells: set[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _intended_output(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for color, cells in _components(grid):
        if color == 5 and _normalize(cells) == H_DOMINO:
            for row, col in cells:
                output[row][col] = 8
    return output


def _observed(grid: list[list[int]]) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "domino_count": sum(
            color == 5 and _normalize(cells) == H_DOMINO
            for color, cells in _components(grid)
        ),
    }


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": _intended_output(grid)}


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_pin_and_public_surface_are_narrow_and_exact():
    assert GEN.RULE_HASH == "bba257d19e2b"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "domino_count"}
    assert GEN.EXAMPLES_NEEDED == 2
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_h3",
        "canonical_square",
        "canonical_h4",
        "mixed",
    )


@pytest.mark.parametrize(
    "pair",
    _canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _intended_output(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 8, "grid_w": 9, "domino_count": 1},
        {"grid_h": 8, "grid_w": 16, "domino_count": 6},
        {"grid_h": 14, "grid_w": 9, "domino_count": 6},
        {"grid_h": 14, "grid_w": 16, "domino_count": 6},
    ],
)
def test_boundary_overrides_round_trip_in_every_band(band, requested):
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert _observed(grid) == requested
    assert GEN.observe_overrides(grid) == requested


def test_every_documented_integer_combination_is_constructive():
    for height in range(8, 15):
        for width in range(9, 17):
            for count in range(1, 7):
                requested = {
                    "grid_h": height,
                    "grid_w": width,
                    "domino_count": count,
                }
                grid = GEN.generate(3107, count, difficulty="hard", **requested)
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"palette_kind": "default"},
        {"texture": "all_dominoes"},
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 8},
        {"grid_w": 17},
        {"domino_count": 0},
        {"domino_count": 7},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"domino_count": "2"},
    ],
)
def test_invalid_or_retired_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", BANDS)
def test_four_sample_windows_cover_profiles_and_both_semantic_witnesses(band):
    expected_profiles = set(GEN.SCHEDULE_PROFILES)
    for start in range(8):
        profiles = {
            GEN.schedule_profile(9001, index, difficulty=band)
            for index in range(start, start + 4)
        }
        assert profiles == expected_profiles
        for index in range(start, start + 4):
            grid = GEN.generate(9001, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert set(value for row in grid for value in row) <= {0, 5}
            expected = _intended_output(grid)
            assert expected != grid
            assert all(witness(grid) for witness in GEN.SEMANTIC_WITNESSES.values())
            assert all(rival(grid) != expected for rival in GEN.SEMANTIC_RIVALS.values())


def test_lesson_contract_rejects_named_rivals_for_every_rotation():
    for start in range(12):
        demos = [_pair(GEN.generate(7331, start + offset)) for offset in range(2)]
        query = _pair(GEN.generate(7331, start + 2))
        assert GEN.lesson_identifiable(demos, query) == []


def test_generation_is_deterministic_and_does_not_mutate_rule_inputs():
    first = GEN.generate(412, 111, difficulty="hard")
    assert first == GEN.generate(412, 111, difficulty="hard")
    original = deepcopy(first)
    GEN.rule_mirror(first)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(first)
    assert first == original


@pytest.mark.parametrize(
    "bad_grid",
    [None, [], [[]], [[0], [0, 5]], [[True] * 9 for _ in range(8)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(bad_grid):
    assert GEN.self_check(bad_grid)
