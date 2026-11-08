"""Portable regression suite for Commanded L-Links."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

TASK = "091033f57174"
HOME = Path(__file__).resolve().parents[1]
for parent in Path(__file__).resolve().parents:
    runtime = parent / "shared/runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
from reference_probe import (  # noqa: E402
    analyze,
    canonical_pairs as probe_canonical_pairs,
    exclude_command_cell_only,
    first_two_pairs_only,
    labeled,
    load_generator,
    oracle_output,
    racket_outputs,
    route_three_marker_colors,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK, root=find_root(__file__))
CANONICAL_PROFILES = {
    (len(pair["input"]), len(pair["input"][0]), len({value for row in pair["input"] for value in row}))
    for pair in PAIRS
}


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_metadata_pins_authority_and_declares_exact_contract():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "0ce03c4c47d8"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_pairs", "command", "texture"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    frozen = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]
    assert pair["input"] == frozen


def test_probe_and_test_use_same_complete_canonical_population():
    assert len(PAIRS) == 5
    assert [p["input"] for p in probe_canonical_pairs()] == [p["input"] for p in PAIRS]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 8, "grid_w": 8, "n_pairs": 1, "command": 1, "texture": "plain"},
        {"grid_h": 12, "grid_w": 12, "n_pairs": 4, "command": 2, "texture": "both"},
        {"grid_h": 9, "grid_w": 10, "n_pairs": 2, "command": 1, "texture": "three_cells"},
        {"grid_h": 10, "grid_w": 9, "n_pairs": 3, "command": 2, "texture": "cmd_color_pair"},
    ],
)
def test_exact_overrides_are_constructive_observable_and_band_independent(band, requested):
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert {key: analyze(grid)[key] for key in requested} == requested
    assert oracle_output(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 7}, {"grid_h": 13}, {"grid_h": True}, {"grid_h": 8.0},
        {"grid_w": 7}, {"grid_w": 13}, {"grid_w": "8"},
        {"n_pairs": 0}, {"n_pairs": 5}, {"n_pairs": 2.5},
        {"command": 0}, {"command": 3}, {"command": False},
        {"texture": "bogus"}, {"texture": 1},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_default_window_has_two_commands_two_guard_witnesses_and_profile_support(band):
    for start in range(12):
        grids = [gen.generate(700 + start, start + offset, difficulty=band) for offset in range(4)]
        stats = [analyze(grid) for grid in grids]
        assert sorted(row["command"] for row in stats) == [1, 1, 2, 2]
        assert sum(row["texture"] == "both" for row in stats) == 2
        assert sum(row["texture"] == "plain" for row in stats) == 2
        assert any(profile(grid) in CANONICAL_PROFILES for grid in grids)
        for held_out in range(4):
            demos = [row for index, row in enumerate(stats) if index != held_out]
            assert {row["command"] for row in demos} == {1, 2}
            assert any(row["texture"] == "both" for row in demos)
            assert any(row["n_pairs"] >= 3 for row in demos)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_query_rotation_is_identified_by_remaining_default_demos(band):
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        pairs = [labeled(gen.generate(1300 + start, start + offset, difficulty=band)) for offset in range(4)]
        for held_out in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert gen.lesson_identifiable(demos, pairs[held_out]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_domain_is_valid_deterministic_and_visible(band):
    seen = set()
    crossings = 0
    for index in range(96):
        grid = gen.generate(2100 + index, index * 7, difficulty=band)
        assert grid == gen.generate(2100 + index, index * 7, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        before = deepcopy(grid)
        expected = oracle_output(grid)
        assert expected != grid
        assert grid == before
        stats = analyze(grid)
        assert 8 <= stats["grid_h"] <= 12
        assert 8 <= stats["grid_w"] <= 12
        assert 1 <= stats["n_pairs"] <= 4
        crossings += stats["path_crossings"]
        seen.add(json.dumps(grid))
    assert len(seen) >= 90
    assert crossings > 0


def test_canonical_shortcuts_fit_all_canonical_labels_and_both_texture_refutes_each():
    shortcuts = {
        "route_three_marker_colors": route_three_marker_colors,
        "exclude_command_cell_only": exclude_command_cell_only,
        "first_two_pairs_only": first_two_pairs_only,
    }
    for shortcut in shortcuts.values():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS)
    grid = gen.generate(300, 2)  # scheduled command=1, n_pairs=3, texture=both
    expected = oracle_output(grid)
    assert analyze(grid)["texture"] == "both"
    assert analyze(grid)["n_pairs"] >= 3
    for name, shortcut in shortcuts.items():
        assert shortcut(grid) != expected, name
        assert gen.CANONICAL_SHORTCUTS[name](grid) == shortcut(grid)


def test_semantic_witnesses_fire_and_refute_their_declared_rivals():
    grids = [gen.generate(501, index) for index in range(4)]
    for witness, rival_names in gen.WITNESS_RIVALS.items():
        candidates = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness](grid)]
        assert candidates, witness
        assert any(
            gen.SEMANTIC_RIVALS[rival](grid) != oracle_output(grid)
            for grid in candidates for rival in rival_names
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "bad_command", "aligned_pair", "single_marker", "four_markers",
        "unknown_color", "ragged", "bool_cell", "too_small", "row_zero_marker",
    ],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(909, 2, grid_h=10, grid_w=10, n_pairs=2, command=1, texture="plain")
    stats = analyze(grid)
    color = stats["pair_colors"][0]
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if mutation == "bad_command":
        grid[0][0] = 9
    elif mutation == "aligned_pair":
        (r1, c1), (r2, c2) = points
        grid[r2][c2] = 0
        replacement = next(c for c in range(len(grid[0])) if c != c1 and grid[r1][c] == 0)
        grid[r1][replacement] = color
    elif mutation == "single_marker":
        r, c = points[-1]
        grid[r][c] = 0
    elif mutation == "four_markers":
        free = [(r, c) for r in range(1, len(grid)) for c in range(len(grid[0])) if grid[r][c] == 0]
        for r, c in free[:2]:
            grid[r][c] = color
    elif mutation == "unknown_color":
        grid[1][0] = 10
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "bool_cell":
        grid[1][0] = True
    elif mutation == "too_small":
        grid = [[0] * 7 for _ in range(7)]
        grid[0][0] = 1
    elif mutation == "row_zero_marker":
        grid[0][2] = 8
    assert gen.self_check(grid)


def test_helpers_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(8128, 23)
    frozen = deepcopy(grid)
    assert oracle_output(grid)
    for rival in gen.LESSON_COMPETITORS.values():
        assert rival(grid)
    assert grid == frozen


def test_retained_counterexample_matches_current_source_and_oracles():
    evidence = json.loads((HOME / "counterexamples" / "guard-shortcuts.json").read_text())
    grid = evidence["input"]
    assert gen.self_check(grid) == []
    assert oracle_output(grid) == evidence["canonical_output"]
    assert route_three_marker_colors(grid) == evidence["route_three_marker_colors_output"]
    assert exclude_command_cell_only(grid) == evidence["exclude_command_cell_only_output"]
    assert first_two_pairs_only(grid) == evidence["first_two_pairs_only_output"]
    assert all(evidence["canonical_output"] != evidence[key] for key in (
        "route_three_marker_colors_output", "exclude_command_cell_only_output", "first_two_pairs_only_output"
    ))


def test_real_racket_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in PAIRS]
    grids += [gen.generate(319, index, difficulty="hard") for index in range(16)]
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]
