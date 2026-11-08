"""Focused regressions for the counted quarter-turn orbit generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import random
from pathlib import Path

import pytest


try:
    gen = importlib.import_module(
        "puzzle_generators.per_puzzle.2f91d0756f23.generator"
    )
except ModuleNotFoundError:
    # Direct repository pytest runs do not stage per-puzzle packages.
    # Load the exact task-local source so focused RED/GREEN cycles still work.
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_test", generator_path)
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
TASK_ID = "2f91d0756f23"
CANONICAL_RULE_HASH = "dc9e50b0f1e3"


def _canonical_pairs():
    canonical = Path(__file__).resolve().parents[3] / "shared/data/canonical/puzzles.jsonl"
    with canonical.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [*row["train"], row["test"]]
    raise AssertionError(f"canonical task {TASK_ID} not found in {canonical}")


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _orbit_cells(grid):
    return [
        (row, col, value)
        for row in range(1, len(grid))
        for col, value in enumerate(grid[row])
        if value not in (0, 9)
    ]


def _rotation_class(offset):
    dr, dc = offset
    rotations = []
    for _ in range(4):
        rotations.append((dr, dc))
        dr, dc = dc, -dr
    return min(rotations)


def test_rule_hash_and_python_mirror_match_every_canonical_pair():
    assert getattr(gen, "RULE_HASH", None) == CANONICAL_RULE_HASH
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._solve_official(pair["input"]) == pair["output"]


def test_canonical_shortcuts_really_fit_all_public_pairs():
    pairs = _canonical_pairs()
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    assert {"left_prefix_count", "first_two_orbits_only"} <= set(shortcuts)
    for name, rival in shortcuts.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 5, "grid_w": 5, "k": 4, "n_orbits": 5},
        {"grid_h": 14, "grid_w": 16, "k": 1, "n_orbits": 1},
        {"grid_h": 8, "grid_w": 9, "k": 3, "n_orbits": 2},
    ],
)
def test_every_advertised_override_is_exact_and_observable(band, overrides):
    grid = gen.generate(73, 11, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 2},
        {"grid_h": 4},
        {"grid_w": 17},
        {"k": 0},
        {"k": 5},
        {"n_orbits": 0},
        {"n_orbits": 6},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"k": "2"},
        {"n_orbits": None},
    ],
)
def test_invalid_overrides_are_rejected_loudly(override):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


def test_pinned_profile_census_has_exact_support_in_every_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    assert canonical_profiles == {(8, 8, 5), (9, 9, 5)}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            hits += _profile(grid) in canonical_profiles
        assert hits >= 1, band


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_any_four_consecutive_demos_cover_all_counts_and_identify_query(band):
    for start in range(12):
        grids = [gen.generate(991, start + offset, difficulty=band) for offset in range(5)]
        pairs = [
            {"input": grid, "output": gen._solve_official(grid)}
            for grid in grids
        ]
        assert {gen.observe_overrides(grid)["k"] for grid in grids[:4]} == {1, 2, 3, 4}
        assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_orbit_inputs_use_distinct_rotation_classes_and_outputs_do_not_collide():
    grid = gen.generate(
        812,
        3,
        difficulty="hard",
        grid_h=5,
        grid_w=5,
        k=4,
        n_orbits=5,
    )
    anchor = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    )
    orbit = _orbit_cells(grid)
    classes = {
        _rotation_class((row - anchor[0], col - anchor[1]))
        for row, col, _ in orbit
    }
    assert len(orbit) == len(classes) == 5

    output = gen._solve_official(grid)
    for _, _, color in orbit:
        assert sum(value == color for row in output for value in row) == 4


def test_declared_witnesses_are_actual_rival_counterexamples():
    sparse = gen.generate(41, 1, difficulty="medium")
    shifted = gen.generate(41, 2, difficulty="medium")
    dense = gen.generate(41, 3, difficulty="medium")

    assert gen.SEMANTIC_WITNESSES["nonprefix_header"](sparse)
    assert gen.SEMANTIC_RIVALS["left_prefix_count"](sparse) != gen._solve_official(sparse)

    assert gen.SEMANTIC_WITNESSES["rotation_direction"](shifted)
    assert gen.SEMANTIC_RIVALS["opposite_rotation"](shifted) != gen._solve_official(shifted)

    assert gen.SEMANTIC_WITNESSES["more_than_two_orbits"](dense)
    assert gen.SEMANTIC_RIVALS["first_two_orbits_only"](dense) != gen._solve_official(dense)

    assert gen.SEMANTIC_WITNESSES["count_controls_turns"](sparse)
    assert gen.SEMANTIC_RIVALS["always_four_turns"](sparse) != gen._solve_official(sparse)


def test_self_check_rejects_structural_impostors():
    valid = gen.generate(19, 3, grid_h=9, grid_w=9, k=4, n_orbits=4)

    bad_header_color = copy.deepcopy(valid)
    bad_header_color[0][-1] = 2
    assert gen.self_check(bad_header_color)

    lower_blue = copy.deepcopy(valid)
    lower_blue[1][0] = 1
    assert gen.self_check(lower_blue)

    second_anchor = copy.deepcopy(valid)
    second_anchor[1][0] = 9
    assert gen.self_check(second_anchor)

    duplicate_orbit_class = copy.deepcopy(valid)
    anchor = next(
        (row, col)
        for row, values in enumerate(valid)
        for col, value in enumerate(values)
        if value == 9
    )
    first_row, first_col, _ = _orbit_cells(valid)[0]
    dr, dc = first_row - anchor[0], first_col - anchor[1]
    rr, cc = anchor[0] + dc, anchor[1] - dr
    if rr == 0:
        rr, cc = anchor[0] - dr, anchor[1] - dc
    duplicate_orbit_class[rr][cc] = 8
    assert any("rotation class" in reason for reason in gen.self_check(duplicate_orbit_class))


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(1207, 8, difficulty="hard")
    second = gen.generate(1207, 8, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == state
