"""Task-local regressions. Run explicitly; the repository suite excludes this path."""
from __future__ import annotations

import importlib.util
import itertools
import random
import sys
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
_spec = importlib.util.spec_from_file_location("review_c6b14e07214c", TASK / "generator.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)
from src.core.canonical_pairs import load_task_pairs

CANONICAL = load_task_pairs("c6b14e07214c", REPO / "shared/data/canonical/puzzles.jsonl")


@pytest.mark.parametrize("pair", CANONICAL, ids=["train0", "train1", "test0"])
def test_regression_canonical_inputs_are_in_domain(pair):
    assert gen.self_check(pair["input"]) == []


def test_regression_grid_dimensions_are_not_ignored():
    g = gen.generate(17, 0, difficulty="easy", grid_h=14, grid_w=15)
    assert (len(g), len(g[0])) == (14, 15)


def test_regression_unknown_and_mistyped_overrides_fail_loudly():
    with pytest.raises((ValueError, TypeError), match="unknown"):
        gen.generate(17, 0, misspelled_axis=3)
    for value in (True, 9.5, "10"):
        with pytest.raises((ValueError, TypeError)):
            gen.generate(17, 0, grid_h=value)


def test_regression_noninteger_and_out_of_palette_cells_are_rejected():
    grid = gen.generate(17, 0)
    for bad in (True, 0.0, -1, 10):
        mutated = [row[:] for row in grid]
        seed = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 7))
        mutated[seed[0]][seed[1]] = bad
        assert gen.self_check(mutated), repr(bad)


def test_source_contract_has_rule_pin_and_executable_rivals():
    assert getattr(gen, "RULE_HASH", None) == "d219d22bc8a3"
    for attr in ("strict_canonical_like", "observe_overrides", "lesson_identifiable", "schedule_profile"):
        assert callable(getattr(gen, attr, None)), attr
    for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS", "SEMANTIC_WITNESSES"):
        assert getattr(gen, attr, {}), attr


def test_all_exact_boundary_combinations_in_every_band():
    assert callable(getattr(gen, "observe_overrides", None))
    names = ("grid_h", "grid_w", "frame_h", "frame_w", "n_seeds", "n_interior_sevens")
    for band in ("easy", "medium", "hard"):
        for index, vals in enumerate(itertools.product((9, 22), (9, 22), (5, 9), (5, 9), (2, 6), (0, 2))):
            requested = dict(zip(names, vals))
            grid = gen.generate(4100 + index, index, difficulty=band, **requested)
            assert gen.self_check(grid) == [], (band, requested)
            assert gen.observe_overrides(grid) == requested


def test_default_stream_has_all_three_profiles_in_every_cyclic_window():
    assert callable(getattr(gen, "schedule_profile", None))
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(3):
                profiles = [gen.schedule_profile(seed, start + i, band) for i in range(3)]
                assert set(profiles) == set(gen.SCHEDULE_PROFILES)
                grids = [gen.generate(seed, start + i, difficulty=band) for i in range(3)]
                for name, predicate in gen.SEMANTIC_WITNESSES.items():
                    assert any(predicate(grid) for grid in grids), (band, seed, start, name)


def test_declared_canonical_shortcuts_fit_every_usable_canonical_pair():
    assert getattr(gen, "CANONICAL_SHORTCUTS", {})
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in CANONICAL), name


def test_fresh_deterministic_grids_and_global_rng_purity():
    random.seed(173)
    state = random.getstate()
    first = gen.generate(91, 43, difficulty="hard")
    second = gen.generate(91, 43, difficulty="hard")
    assert random.getstate() == state
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_explicit_malformed_geometry_is_rejected():
    assert callable(getattr(gen, "mutation_fixtures", None))
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name


def test_both_small_teaching_phases_cover_canonical_scale_without_seed_tuning():
    # Two-thirds of the cycle stays at canonical scale. The many-source phase
    # carries size extrapolation; exact size overrides still work everywhere.
    for band in ('easy', 'medium', 'hard'):
        for seed in range(12):
            for index in range(3):
                if gen.schedule_profile(seed, index, band) == 'many_sources':
                    continue
                grid = gen.generate(seed, index, difficulty=band)
                assert 9 <= len(grid) <= 10 and 9 <= len(grid[0]) <= 10
                assert 4 <= len({v for row in grid for v in row}) <= 5
