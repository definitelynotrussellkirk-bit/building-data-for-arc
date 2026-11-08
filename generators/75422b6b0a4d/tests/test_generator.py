"""Task-local regressions for 75422b6b0a4d.

The oracle below is intentionally independent of the production implementation.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "75422b6b0a4d"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _neighbors(point, height, width):
    row, col = point
    for dr, dc in DIR4:
        nr, nc = row + dr, col + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield nr, nc


def flood_oracle(grid):
    """Mirror the selected rule without using generator helpers."""
    source = deepcopy(grid)
    output = deepcopy(grid)
    height = len(source)
    width = len(source[0])
    for row in range(height):
        for col in range(width):
            color = source[row][col]
            if color not in (1, 2, 3, 4):
                continue
            queue = deque([(row, col)])
            seen = {(row, col)}
            while queue:
                point = queue.popleft()
                for nxt in _neighbors(point, height, width):
                    if nxt in seen:
                        continue
                    value = source[nxt[0]][nxt[1]]
                    if value not in (0, color):
                        continue
                    seen.add(nxt)
                    queue.append(nxt)
            for rr, cc in seen:
                if source[rr][cc] == 0:
                    output[rr][cc] = color
    return output


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_metadata_and_exact_axis_surface():
    assert GEN.VERSION == "3.1.0"
    assert GEN.RULE_HASH == "c8f68c67587f"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.SCHEDULE_PROFILES == ("canonical_anchor", "shortcut_witness", "broad")
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.AXES == {
        "grid_h": {"type": "int", "default": GEN.AXES["grid_h"]["default"], "valid": "7..18"},
        "grid_w": {"type": "int", "default": GEN.AXES["grid_w"]["default"], "valid": "8..20"},
        "wall_color": {"type": "color", "default": GEN.AXES["wall_color"]["default"], "valid": "5..9"},
        "n_rooms": {"type": "int", "default": GEN.AXES["n_rooms"]["default"], "valid": "2..4"},
    }


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=find_root(__file__)))
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert flood_oracle(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 8, "wall_color": 5, "n_rooms": 2},
        {"grid_h": 7, "grid_w": 10, "wall_color": 9, "n_rooms": 3},
        {"grid_h": 18, "grid_w": 20, "wall_color": 6, "n_rooms": 4},
    ],
)
def test_exact_overrides_are_constructive_observable_and_lawful(band, options):
    grid = GEN.generate(901, 17, difficulty=band, **options)
    assert GEN.observe_overrides(grid) == options
    assert GEN.self_check(grid) == []
    assert flood_oracle(grid) == GEN.rule_mirror(grid)
    assert GEN.generate(901, 17, difficulty=band, **options) == grid


@pytest.mark.parametrize(
    "options",
    [
        {"unknown": 1},
        {"grid_h": 6},
        {"grid_h": 19},
        {"grid_h": True},
        {"grid_w": 7},
        {"wall_color": 4},
        {"wall_color": 10},
        {"wall_color": "5"},
        {"n_rooms": 1},
        {"n_rooms": 5},
        {"n_rooms": 2.0},
    ],
)
def test_rejects_unknown_or_invalid_overrides(options):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **options)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_three_slot_schedule_anchors_profile_and_refutes_shortcuts(band):
    anchor = GEN.generate(110, 0, difficulty=band)
    witness = GEN.generate(110, 1, difficulty=band)
    broad = GEN.generate(110, 2, difficulty=band)

    assert GEN.schedule_profile(110, 0, band) == "canonical_anchor"
    assert GEN.schedule_profile(110, 1, band) == "shortcut_witness"
    assert GEN.schedule_profile(110, 2, band) == "broad"
    assert _profile(anchor) in {(7, 8, 6), (7, 9, 6), (7, 10, 6)}
    assert GEN.strict_canonical_like(anchor) == []

    intended = GEN.rule_mirror(witness)
    assert GEN.SEMANTIC_WITNESSES["non_rectangular_chambers"](witness)
    assert GEN.SEMANTIC_RIVALS["complete_wall_lines_only"](witness) != intended
    assert GEN.SEMANTIC_WITNESSES["non_gray_wall"](witness)
    assert GEN.SEMANTIC_RIVALS["gray_walls_only"](witness) != intended
    assert GEN.self_check(broad) == []


@pytest.mark.parametrize("start", range(12))
def test_every_three_consecutive_examples_refute_declared_shortcuts(start):
    demos = [GEN.generate(777, start + offset, difficulty="medium") for offset in range(3)]
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(grid) != GEN.rule_mirror(grid) for grid in demos), name


def test_declared_shortcuts_fit_all_canonical_labels():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_realizes_all_room_counts_and_wall_colors(band):
    room_counts = set()
    wall_colors = set()
    for index in range(90):
        grid = GEN.generate(3000 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        room_counts.add(observed["n_rooms"])
        wall_colors.add(observed["wall_color"])
    assert room_counts == {2, 3, 4}
    assert wall_colors == {5, 6, 7, 8, 9}


def test_canonical_anchor_has_seed_level_diversity():
    grids = {
        tuple(tuple(row) for row in GEN.generate(seed, 0, difficulty="easy"))
        for seed in range(40)
    }
    assert len(grids) >= 12


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[5] * 8 for _ in range(7)],
        [[0] * 8 for _ in range(7)],
    ],
)
def test_malformed_or_semantically_empty_grids_are_rejected_without_crashing(grid):
    assert GEN.self_check(grid)


def test_self_check_rejects_seedless_and_multi_seed_rooms():
    seedless = GEN.generate(41, 0, grid_h=7, grid_w=8, wall_color=5, n_rooms=2)
    multi = deepcopy(seedless)

    # Remove one seed, preserving at least one zero in its room.
    seed_positions = [
        (r, c)
        for r, row in enumerate(seedless)
        for c, value in enumerate(row)
        if value in (1, 2, 3, 4)
    ]
    r0, c0 = seed_positions[0]
    seedless[r0][c0] = 0
    assert any("seed" in message for message in GEN.self_check(seedless))

    # Add a different seed next to an existing seed inside the same chamber.
    r1, c1 = seed_positions[1]
    for nr, nc in _neighbors((r1, c1), len(multi), len(multi[0])):
        if multi[nr][nc] == 0:
            multi[nr][nc] = 4 if multi[r1][c1] != 4 else 3
            break
    assert any("seed" in message for message in GEN.self_check(multi))


def test_saved_complete_wall_lines_counterexample_replays():
    path = HOME / "counterexamples" / "complete-wall-lines-only.json"
    payload = json.loads(path.read_text())
    replay = payload["replay"]
    grid = GEN.generate(
        replay["seed"],
        replay["sample_index"],
        difficulty=replay["difficulty"],
        **replay["overrides"],
    )
    assert grid == payload["input"]
    assert GEN.rule_mirror(grid) == payload["intended_output"]
    assert GEN.SEMANTIC_RIVALS[payload["rival"]](grid) == payload["rival_output"]
    assert payload["racket_output"] == payload["intended_output"]
    assert payload["rival_output"] != payload["intended_output"]

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_in_four_pair_window_is_identifiable(band):
    # Regression for the 100-per-band rotation census: removing the sole
    # shortcut witness from demos must not resurrect a canonical-compatible rival.
    for start in range(6):
        seed = 2_348_551_452 + start
        pairs = []
        for offset in range(4):
            grid = GEN.generate(seed, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == [], (
                band,
                start,
                query_index,
                GEN.lesson_identifiable(demos, pairs[query_index]),
            )
