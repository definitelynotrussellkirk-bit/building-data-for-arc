"""Focused regression tests for generator 9a7579840f41."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.9a7579840f41.generator"
)


def test_rule_hash_and_exact_axis_observer_boundaries():
    assert MODULE.RULE_HASH == "7dd342fe1468"
    for band in ("easy", "medium", "hard"):
        for grid_h, grid_w, n_turns, template_size, start_axis in (
            (7, 12, 1, 2, "horizontal"),
            (10, 18, 5, 5, "vertical"),
            (16, 12, 5, 2, "horizontal"),
            (16, 18, 1, 5, "vertical"),
        ):
            overrides = {
                "grid_h": grid_h,
                "grid_w": grid_w,
                "n_turns": n_turns,
                "template_size": template_size,
                "start_axis": start_axis,
            }
            grid = MODULE.generate(37, 19, difficulty=band, **overrides)
            assert MODULE.observe_overrides(grid) == overrides
            assert MODULE.self_check(grid) == []



def test_every_official_joint_profile_is_constructible():
    official_profiles = (
        {"grid_h": 7, "grid_w": 14, "n_turns": 2, "template_size": 3, "start_axis": "vertical"},
        {"grid_h": 9, "grid_w": 15, "n_turns": 2, "template_size": 3, "start_axis": "vertical"},
        {"grid_h": 10, "grid_w": 16, "n_turns": 3, "template_size": 2, "start_axis": "vertical"},
    )
    for sample_index, overrides in enumerate(official_profiles):
        grid = MODULE.generate(901, sample_index, difficulty="easy", **overrides)
        assert MODULE.observe_overrides(grid) == overrides
        assert MODULE.self_check(grid) == []


def test_official_linked_profiles_have_default_witnesses_in_every_band():
    profiles = set(MODULE._CANONICAL_AXIS_PROFILES)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        matches = 0
        for offset in range(200):
            grid = MODULE.generate(120000 + band_index * 1000 + offset, 31 + offset * 13, difficulty=band)
            observed = MODULE.observe_overrides(grid)
            profile = (
                observed["grid_h"], observed["grid_w"], observed["n_turns"],
                observed["template_size"], observed["start_axis"],
            )
            matches += int(profile in profiles)
        assert matches >= 10, (band, matches)

def test_default_draws_are_structural_deterministic_fresh_and_rng_pure():
    path_families = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            state = random.getstate()
            first = MODULE.generate(seed, seed * 17 + 3, difficulty=band)
            assert random.getstate() == state
            replay = MODULE.generate(seed, seed * 17 + 3, difficulty=band)
            assert replay == first
            assert replay is not first
            assert all(a is not b for a, b in zip(first, replay))
            assert MODULE.self_check(first) == []
            observed = MODULE.observe_overrides(first)
            assert 7 <= observed["grid_h"] <= 16
            assert 12 <= observed["grid_w"] <= 18
            assert 1 <= observed["n_turns"] <= 5
            assert 2 <= observed["template_size"] <= 5
            assert observed["start_axis"] in {"horizontal", "vertical"}
            path, error = MODULE._trace_wire_from_start(first)
            assert error is None
            path_families.add(
                "reversal" if MODULE._has_direction_reversal(path) else "staircase"
            )
    assert path_families == {"staircase", "reversal"}



def test_removed_metadata_only_controls_are_rejected_loudly():
    removed = {
        "density": "sparse",
        "path_variant": 1,
        "position_bias": "template_with_wire",
        "palette_kind": "warm",
        "palette_size": 3,
        "n_distinct_colors": 3,
        "texture": "warm",
    }
    for key, value in removed.items():
        with pytest.raises(ValueError):
            MODULE.generate(3, 4, difficulty="medium", **{key: value})

def test_declared_task_semantic_impostors_are_rejected():
    fixtures = MODULE.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert MODULE.self_check(copy.deepcopy(grid)), name


def test_recoloring_template_to_absent_feature_is_rejected():
    grid = MODULE.generate(812, 5, difficulty="hard")
    assert all(value != 2 for row in grid for value in row)
    impostor = [[2 if value == 4 else value for value in row] for row in grid]
    errors = MODULE.self_check(impostor)
    assert any("unexpected colors" in error for error in errors)
    assert any("color-4 template" in error for error in errors)


def _entry_geometry(grid):
    path, error = MODULE._trace_wire_from_start(grid)
    assert error is None
    start = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    )
    entry = (path[0][0] - start[0], path[0][1] - start[1])
    first_wire_step = (
        path[1][0] - path[0][0],
        path[1][1] - path[0][1],
    )
    return entry, first_wire_step


def test_generated_marker_enters_perpendicular_to_wire_on_both_sides():
    entry_sides = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(40):
            grid = MODULE.generate(
                810_000 + band_index * 10_000 + offset,
                37 * offset + 5,
                difficulty=band,
            )
            entry, first_wire_step = _entry_geometry(grid)
            assert entry[0] * first_wire_step[0] + entry[1] * first_wire_step[1] == 0
            entry_sides.add(
                entry[0] * first_wire_step[1] - entry[1] * first_wire_step[0]
            )
    assert entry_sides == {-1, 1}


def test_semantic_contract_matches_canonical_and_refutes_marker_as_wire():
    pairs = canonical_pairs(
        MODULE.TASK_ID, root=find_root(__file__), labeled_only=True
    )
    assert pairs
    for pair in pairs:
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]

    lessons = []
    witness = "perpendicular_entry_refutes_marker_inclusive_corners"
    rival = "marker_inclusive_local_corners"
    for index, band in enumerate(("easy", "medium", "hard", "medium")):
        grid = MODULE.generate(7_000 + index, index, difficulty=band)
        output = MODULE.rule_mirror(grid)
        assert MODULE.SEMANTIC_WITNESSES[witness](grid)
        assert MODULE.SEMANTIC_RIVALS[rival](grid) != output
        lessons.append({"input": grid, "output": output})

    assert MODULE.lesson_identifiable(lessons[:3], lessons[3]) == []


def _collinear_entry_mutant():
    for seed in range(900_000, 900_200):
        grid = MODULE.generate(seed, seed * 13 + 7, difficulty="medium")
        path, error = MODULE._trace_wire_from_start(grid)
        assert error is None
        start = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 7
        )
        first_step = (
            path[1][0] - path[0][0],
            path[1][1] - path[0][1],
        )
        candidate = (
            path[0][0] - first_step[0],
            path[0][1] - first_step[1],
        )
        r, c = candidate
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            continue
        if grid[r][c] != 0:
            continue
        wire = set(path)
        touched = {
            (r + dr, c + dc)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if (r + dr, c + dc) in wire
        }
        if touched != {path[0]}:
            continue
        mutant = [row[:] for row in grid]
        mutant[start[0]][start[1]] = 0
        mutant[r][c] = 7
        return mutant
    raise AssertionError("no lawful collinear marker mutation found")


def test_self_check_rejects_collinear_start_entry():
    errors = MODULE.self_check(_collinear_entry_mutant())
    assert any("perpendicular" in error for error in errors)


def test_every_generated_sample_refutes_marker_inclusive_corner_shortcut():
    witness = "perpendicular_entry_refutes_marker_inclusive_corners"
    rival = "marker_inclusive_local_corners"
    cases = [(991_083, 1_414, "easy")]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        cases.extend(
            (930_000 + band_index * 10_000 + offset, 17 * offset + 3, band)
            for offset in range(80)
        )

    for seed, sample_index, band in cases:
        grid = MODULE.generate(seed, sample_index, difficulty=band)
        intended = MODULE.rule_mirror(grid)
        assert MODULE.SEMANTIC_WITNESSES[witness](grid), (
            seed,
            sample_index,
            band,
        )
        assert MODULE.SEMANTIC_RIVALS[rival](grid) != intended
