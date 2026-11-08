"""Focused regression tests for the 6c93e8516229 topology sampler."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "6c93e8516229"
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 3
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _topology(cells):
    points = set(cells)
    corners = 0
    degree3 = 0
    degree4 = 0
    for r, c in cells:
        neighbors = [
            (dr, dc)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if (r + dr, c + dc) in points
        ]
        if len(neighbors) == 2:
            first, second = neighbors
            if first[0] != second[0] and first[1] != second[1]:
                corners += 1
        elif len(neighbors) == 3:
            degree3 += 1
        elif len(neighbors) == 4:
            degree4 += 1
    color = 2 if degree3 else (6 if corners == 2 else 1)
    return {"color": color, "corners": corners, "degree3": degree3, "degree4": degree4}


def _independent_output(grid):
    result = [row[:] for row in grid]
    for cells in _components(grid):
        color = _topology(cells)["color"]
        for r, c in cells:
            result[r][c] = color
    return result


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_rule_hash_is_pinned_to_selected_canonical_authority():
    assert getattr(GEN, "RULE_HASH", None) == "6b0505b049ac"


def test_selected_active_racket_target_matches_canonical_authority_text():
    root = find_root(__file__)
    canonical_path = root / "shared/data/canonical/puzzles.jsonl"
    canonical_code = None
    for line in canonical_path.read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID or record.get("content_hash") == TASK_ID:
            canonical_code = record["program_solution"]
            break
    assert canonical_code is not None

    authority_path = (
        root
        / "shared/data/base/solutions/training"
        / f"e509e548__{TASK_ID}.json"
    )
    selected = json.loads(authority_path.read_text())
    assert selected["racket_target"]["target_code"] == canonical_code


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert _independent_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "expected",
    [
        {"grid_h": 10, "grid_w": 11, "component_count": 3},
        {"grid_h": 10, "grid_w": 11, "component_count": 8},
        {"grid_h": 14, "grid_w": 12, "component_count": 5},
        {"grid_h": 19, "grid_w": 21, "component_count": 8},
    ],
)
def test_exact_override_contract_is_constructive_and_observable(band, expected):
    grid = GEN.generate(901, 17, difficulty=band, **expected)
    assert GEN.observe_overrides(grid) == expected
    assert GEN.self_check(grid) == []
    assert _independent_output(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 9},
        {"grid_h": True},
        {"grid_w": 22},
        {"component_count": 2},
        {"component_count": 4.0},
        {"texture": "full_grid"},
    ],
)
def test_invalid_or_retired_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        GEN.generate(1, 0, **overrides)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((1, True), {}),
        ((1, -1), {}),
        ((1, 0), {"difficulty": True}),
        ((1, 0), {"difficulty": 0}),
        ((1, 0), {"difficulty": "__invalid_difficulty__"}),
    ],
)
def test_invalid_top_level_call_arguments_fail_loudly(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_covers_canonical_profiles_and_object_counts(band):
    canonical_profiles = {(10, 11, 3), (19, 21, 8), (14, 12, 5), (14, 16, 6)}
    observed = set()
    for sample_index in range(24):
        grid = GEN.generate(1200, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        observed.add((len(grid), len(grid[0]), len(_components(grid))))
    assert observed & canonical_profiles
    assert len({count for _h, _w, count in observed}) >= 2


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_generated_board_has_all_three_rule_classes(band):
    for sample_index in range(30):
        grid = GEN.generate(3300, sample_index, difficulty=band)
        classes = {_topology(cells)["color"] for cells in _components(grid)}
        assert classes == {1, 2, 6}


def test_schedule_emits_exactness_counterexamples():
    grids = [GEN.generate(7700, i, difficulty="medium") for i in range(6)]
    stats = [_topology(cells) for grid in grids for cells in _components(grid)]
    assert any(item["color"] == 1 and item["degree4"] for item in stats)
    assert any(item["color"] == 1 and item["corners"] >= 3 for item in stats)


def test_declared_shortcuts_fit_canonical_but_are_refuted_by_each_three_demo_window():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert set(shortcuts) == {"any_junction_red", "at_least_two_corners_magenta"}
    for name, rival in shortcuts.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs()), name
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            demos = [GEN.generate(8800, start + offset, difficulty=band) for offset in range(3)]
            for name, rival in shortcuts.items():
                assert any(rival(grid) != _independent_output(grid) for grid in demos), (
                    band,
                    start,
                    name,
                )


def test_each_three_of_four_query_rotation_refutes_declared_shortcuts():
    shortcuts = GEN.CANONICAL_SHORTCUTS
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            inputs = [GEN.generate(9100, start + offset, difficulty=band) for offset in range(4)]
            for held_out in range(4):
                demos = [grid for index, grid in enumerate(inputs) if index != held_out]
                for name, rival in shortcuts.items():
                    assert any(rival(grid) != _independent_output(grid) for grid in demos), (
                        band,
                        start,
                        held_out,
                        name,
                    )


def test_difficulty_bands_are_not_byte_identical():
    triples = []
    for sample_index in range(12):
        triples.append(
            tuple(
                tuple(tuple(row) for row in GEN.generate(9900, sample_index, difficulty=band))
                for band in ("easy", "medium", "hard")
            )
        )
    assert any(len(set(triple)) == 3 for triple in triples)
