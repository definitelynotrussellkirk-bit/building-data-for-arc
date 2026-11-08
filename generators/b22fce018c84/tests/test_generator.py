"""Regression contract for the horizontal-mirror completion generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest

TASK_ID = "b22fce018c84"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if RUNTIME.is_dir() and str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("review_b22fce018c84", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
CANONICAL_PROFILES = {(8, 10, 2), (10, 9, 2), (12, 12, 2), (8, 11, 2), (10, 12, 2)}


def rule_output(grid):
    """Independent transcription of the selected Racket rule."""
    out = [list(row) for row in grid]
    height = len(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 7:
                out[height - 1 - row][col] = 7
    return out


def cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7]


def facts(grid):
    points = cells(grid)
    height = len(grid)
    top = [(r, c) for r, c in points if 2 * r < height - 1]
    bottom = [(r, c) for r, c in points if 2 * r > height - 1]
    adjacent = any(
        (r + dr, c + dc) in set(points)
        for r, c in points
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )
    rows = len({r for r, _ in points}) < len(points)
    cols = len({c for _, c in points}) < len(points)
    return {"top": bool(top), "bottom": bool(bottom), "adjacent": adjacent,
            "same_row": rows, "same_col": cols}


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_owned_and_oracle_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]


def test_contract_metadata_and_hooks_are_complete():
    assert GEN.RULE_HASH == "149529c7164c"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_top", "top_adjacency", "bottom_column", "mixed_dual"
    )
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_markers", "position_bias"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    for name in ("observe_overrides", "schedule_profile", "lesson_identifiable"):
        assert callable(getattr(GEN, name))


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("position_bias", ["top_half", "bottom_half", "mixed"])
def test_exact_overrides_are_observable_in_every_band(difficulty, position_bias):
    options = {"grid_h": 7, "grid_w": 8, "n_markers": 8, "position_bias": position_bias}
    grid = GEN.generate(173, 19, difficulty=difficulty, **options)
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.observe_overrides(grid) == options
    assert grid == GEN.generate(173, 19, difficulty=difficulty, **options)
    assert rule_output(grid) != grid


@pytest.mark.parametrize(
    "bad",
    [
        {"typo": 1},
        {"grid_h": 6}, {"grid_h": 15}, {"grid_h": True}, {"grid_h": 7.0},
        {"grid_w": 6}, {"grid_w": 15}, {"grid_w": "7"},
        {"n_markers": 1}, {"n_markers": 9}, {"n_markers": 2.0},
        {"position_bias": "center"}, {"position_bias": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **bad)


def test_unknown_difficulty_is_rejected():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_has_required_observable_witnesses(difficulty):
    grids = [GEN.generate(8123, index, difficulty=difficulty) for index in range(4)]
    assert [GEN.schedule_profile(8123, index, difficulty) for index in range(4)] == list(GEN.SCHEDULE_PROFILES)
    observed = [facts(grid) for grid in grids]
    assert observed[0]["top"] and not observed[0]["bottom"]
    assert observed[1]["top"] and not observed[1]["bottom"]
    assert observed[1]["adjacent"] and observed[1]["same_row"]
    assert observed[2]["bottom"] and not observed[2]["top"]
    assert observed[2]["adjacent"] and observed[2]["same_col"]
    assert observed[3]["top"] and observed[3]["bottom"]
    assert observed[3]["adjacent"] and observed[3]["same_row"] and observed[3]["same_col"]
    for grid in grids:
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert rule_output(grid) != grid


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_twenty_draws_hit_canonical_profiles_and_all_schedule_profiles(difficulty):
    profiles = set()
    schedule = set()
    inputs = set()
    for index in range(20):
        grid = GEN.generate(4000 + index, index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        schedule.add(GEN.schedule_profile(4000 + index, index, difficulty))
        inputs.add(tuple(tuple(row) for row in grid))
    assert profiles & CANONICAL_PROFILES
    assert schedule == set(GEN.SCHEDULE_PROFILES)
    assert len(inputs) == 20


def test_canonical_profile_branch_is_strict_and_nontrivial():
    for index in range(0, 40, 4):
        grid = GEN.generate(3100 + index, index, difficulty="medium")
        assert GEN.strict_canonical_like(grid) == []
        assert rule_output(grid) != grid


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    expected = {"top_only", "isolated_only", "first_per_row", "first_per_column"}
    assert set(GEN.CANONICAL_SHORTCUTS) == expected
    for pair in PAIRS:
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(deepcopy(pair["input"])) == pair["output"], name


def test_bottom_counterexample_refutes_the_strongest_canonical_shortcut():
    grid = [[0] * 7 for _ in range(7)]
    grid[5][1] = 7
    grid[6][4] = 7
    assert GEN.self_check(grid) == []
    authority = rule_output(grid)
    assert GEN.CANONICAL_SHORTCUTS["top_only"](deepcopy(grid)) != authority
    assert authority[1][1] == 7 and authority[0][4] == 7


@pytest.mark.parametrize("start", range(8))
def test_every_production_window_and_query_rotation_refutes_all_competitors(start):
    pairs = []
    for offset in range(4):
        grid = GEN.generate(9917, start + offset, difficulty="medium")
        pairs.append({"input": grid, "output": rule_output(grid)})
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_declared_witness_and_rival_is_exercised(difficulty):
    grids = [GEN.generate(7210, index, difficulty=difficulty) for index in range(4)]
    expected = [rule_output(grid) for grid in grids]
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    for witness, predicate in GEN.SEMANTIC_WITNESSES.items():
        assert any(predicate(grid) for grid in grids), witness
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert any(rival(deepcopy(grid)) != output for grid, output in zip(grids, expected)), name


@pytest.mark.parametrize(
    "bad",
    [
        None, [], [[]], [[7], [7, 7]],
        [[True] * 7 for _ in range(7)],
        [[10] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(7)],
    ],
)
def test_malformed_or_out_of_grammar_grids_are_diagnostic_not_exceptions(bad):
    assert GEN.self_check(bad)


def test_self_check_rejects_centerline_and_prefilled_mirror_pairs():
    center = [[0] * 7 for _ in range(7)]
    center[3][1] = 7
    center[0][4] = 7
    assert GEN.self_check(center)
    paired = [[0] * 7 for _ in range(8)]
    paired[1][2] = paired[6][2] = 7
    assert GEN.self_check(paired)


def test_generation_does_not_mutate_global_random_state():
    import random
    before = random.getstate()
    GEN.generate(44, 9, difficulty="hard")
    assert random.getstate() == before


def test_minimal_four_cell_impostors_are_outside_the_teaching_grammar():
    short_line = [[0] * 8 for _ in range(8)]
    for col in range(4):
        short_line[4][col] = 7
    solid = [[0] * 8 for _ in range(8)]
    for row in range(2):
        for col in range(2):
            solid[row][col] = 7
    assert GEN.self_check(short_line)
    assert GEN.self_check(solid)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (4143410598, 11, "medium"),
        (2528696598, 27, "medium"),
        (4158866611, 59, "medium"),
        (1626192253, 79, "medium"),
        (2811756174, 95, "hard"),
    ],
)
def test_mixed_profile_keeps_both_reserved_adjacency_witnesses(seed, sample_index, difficulty):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    observed = facts(grid)
    assert GEN.schedule_profile(seed, sample_index, difficulty) == "mixed_dual"
    assert observed["top"] and observed["bottom"]
    assert observed["adjacent"] and observed["same_row"] and observed["same_col"]
    authority = rule_output(grid)
    assert GEN.SEMANTIC_RIVALS["first_per_row"](deepcopy(grid)) != authority
    assert GEN.SEMANTIC_RIVALS["first_per_column"](deepcopy(grid)) != authority
