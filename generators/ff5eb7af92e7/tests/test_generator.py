"""Regression tests for the ff5eb7af92e7 input distribution."""
from __future__ import annotations

from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "ff5eb7af92e7"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _intended(grid):
    """Independent Python reading of the unchanged canonical row-mode rule."""
    out = []
    for row in grid:
        counts = Counter(value for value in row if value != 0)
        if not counts:
            out.append([0] * len(row))
            continue
        winner = min(
            counts,
            key=lambda color: (-counts[color], row.index(color)),
        )
        out.append([value if value == winner else 0 for value in row])
    return out


def _palette_size(grid):
    return len({value for row in grid for value in row})


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_inputs_remain_lawful_and_match_the_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_round_trip_in_every_band(band):
    requested = {
        "grid_h": 9,
        "grid_w": 11,
        "active_rows": 5,
        "n_distinct_colors": 7,
    }
    grid = GEN.generate(17, 4, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"palette_kind": "warm"},  # retired no-op control
        {"grid_h": True},
        {"grid_w": 6},
        {"active_rows": 1},
        {"n_distinct_colors": 2},
        {"grid_h": 5, "active_rows": 6},
    ],
)
def test_invalid_or_retired_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_profile_zero_is_a_generated_canonical_profile_anchor(band):
    grid = GEN.generate(30, 0, difficulty=band)
    assert (len(grid), len(grid[0])) in {(6, 8), (5, 7), (5, 9), (5, 8)}
    assert _palette_size(grid) == 9  # background plus all eight foreground colors
    assert GEN.observe_overrides(grid)["active_rows"] == 4


@pytest.mark.parametrize("sample_index", range(9))
def test_every_ordinary_draw_contains_all_declared_shortcut_witnesses(sample_index):
    grid = GEN.generate(700 + sample_index, sample_index, difficulty="medium")
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
    assert GEN.generate(700 + sample_index, sample_index, difficulty="medium") == grid


def test_declared_canonical_shortcuts_reproduce_every_canonical_label():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in _pairs()), name


def test_strict_canonical_like_accepts_every_canonical_input():
    for pair in _pairs():
        assert GEN.strict_canonical_like(pair["input"]) == []


def test_seed_census_exercises_noncanonical_color_counts_at_fixed_index():
    observed = {
        GEN.observe_overrides(GEN.generate(seed, 0, difficulty="medium"))["n_distinct_colors"]
        for seed in range(18)
    }
    assert min(observed) <= 4
    assert max(observed) >= 8


def test_one_generated_example_refutes_every_declared_rival():
    grid = GEN.generate(901, 1, difficulty="hard")
    intended = _intended(grid)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(grid) != intended, name


def test_lesson_identifiable_reports_no_surviving_declared_rival():
    demos = []
    for index in range(2):
        grid = GEN.generate(1200 + index, index)
        demos.append({"input": grid, "output": _intended(grid)})
    query = {"input": GEN.generate(1202, 2)}
    assert GEN.lesson_identifiable(demos, query) == []


def test_self_check_rejects_ambiguous_and_single_color_rows():
    tied = [[1, 1, 2, 2, 0, 0, 0] for _ in range(5)]
    single = [[1, 1, 1, 0, 0, 0, 0] for _ in range(5)]
    assert GEN.self_check(tied)
    assert GEN.self_check(single)


def test_schedule_probe_enumerates_every_finite_profile_phase():
    probe_path = HOME / "workspace" / "probe_schedule_phases.py"
    spec = spec_from_file_location("ff5eb7af92e7_schedule_probe", probe_path)
    assert spec and spec.loader
    probe = module_from_spec(spec)
    sys.modules[spec.name] = probe
    spec.loader.exec_module(probe)

    cases = probe.schedule_cases(GEN)
    assert len(cases) == 3 * len(GEN.SCHEDULE_PROFILES)
    for band in ("easy", "medium", "hard"):
        band_cases = [case for case in cases if case["difficulty"] == band]
        assert {case["profiles"][0] for case in band_cases} == set(GEN.SCHEDULE_PROFILES)
        assert all(set(case["profiles"]) == set(GEN.SCHEDULE_PROFILES) for case in band_cases)
