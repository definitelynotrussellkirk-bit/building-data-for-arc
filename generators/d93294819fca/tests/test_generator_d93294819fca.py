"""Portable regressions for the smallest-green-component curriculum."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d93294819fca"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _components_4(grid, color=3):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return sorted(result, key=min)


def _intended(grid):
    """Independent reading of the unchanged canonical rule."""
    components = _components_4(grid)
    minimum = min(map(len, components))
    winners = [cells for cells in components if len(cells) == minimum]
    if len(winners) != 1:
        raise ValueError("oracle requires one uniquely smallest green component")
    out = deepcopy(grid)
    for r, c in winners[0]:
        out[r][c] = 4
    return out


def _smallest_rank(grid):
    components = _components_4(grid)
    minimum = min(map(len, components))
    return next(i for i, cells in enumerate(components) if len(cells) == minimum)


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_inputs_are_lawful_and_match_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]


def test_rule_pin_and_public_axis_contract_are_exact():
    assert GEN.RULE_HASH == "c778849809a2"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "component_profile", "marker_count"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_declared_strict_floor_leaves_margin_below_periodic_half():
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert GEN.MIN_STRICT_FRAC == pytest.approx(0.40)
    assert GEN.MIN_STRICT_FRAC < 2 / GEN.LESSON_SCHEDULE_PERIOD


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 8, "grid_w": 10, "component_profile": "canonical_234", "marker_count": 0},
        {"grid_h": 9, "grid_w": 11, "component_profile": "canonical_235", "marker_count": 1},
        {"grid_h": 10, "grid_w": 12, "component_profile": "varied_134", "marker_count": 2},
        {"grid_h": 11, "grid_w": 13, "component_profile": "varied_345", "marker_count": 0},
        {"grid_h": 12, "grid_w": 14, "component_profile": "two_24", "marker_count": 1},
        {"grid_h": 12, "grid_w": 10, "component_profile": "four_1235", "marker_count": 2},
    ],
)
def test_every_advertised_override_round_trips_in_every_band(band, requested):
    grid = GEN.generate(71, 5, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert _intended(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"texture": "tied_smallest"},
        {"palette_kind": "warm"},
        {"n_blobs": 3},
        {"grid_h": True},
        {"grid_w": 9},
        {"component_profile": None},
        {"component_profile": 234},
        {"component_profile": "not_a_profile"},
        {"marker_count": True},
        {"marker_count": 3},
    ],
)
def test_invalid_unknown_and_retired_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("bad_index", [True, False, -1])
def test_sample_index_must_be_a_nonnegative_exact_integer(bad_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, bad_index)


@pytest.mark.parametrize("bad_band", ["", "expert", 1, False])
def test_unknown_difficulty_is_rejected(bad_band):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=bad_band)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_four_phase_schedule_teaches_position_and_fixed_size_counterexamples(band):
    grids = [GEN.generate(913, index, difficulty=band) for index in range(4)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert [item["component_profile"] for item in observed] == [
        "canonical_234",
        "varied_134",
        "canonical_235",
        "varied_345",
    ]
    assert [item["marker_count"] for item in observed] == [2, 1, 1, 1]
    assert {_smallest_rank(grid) for grid in grids} == {0, 1, 2}
    assert [GEN.strict_canonical_like(grid) == [] for grid in grids] == [
        True,
        False,
        True,
        False,
    ]
    assert [min(map(len, _components_4(grid))) for grid in grids] == [2, 1, 2, 3]


@pytest.mark.parametrize("seed", range(24))
def test_default_draws_are_deterministic_lawful_rule_active_and_do_not_touch_global_rng(seed):
    for band in (None, "easy", "medium", "hard"):
        state = random.getstate()
        grid = GEN.generate(seed, seed % 7, difficulty=band)
        assert random.getstate() == state
        assert GEN.generate(seed, seed % 7, difficulty=band) == grid
        assert GEN.self_check(grid) == []
        assert _intended(grid) != grid


def test_semantic_contract_names_real_counterexamples():
    grids = [GEN.generate(177, index, difficulty="medium") for index in range(4)]
    assert any(GEN.SEMANTIC_WITNESSES["smallest_not_first"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["smallest_not_last"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["winner_not_size_two"](grid) for grid in grids)
    assert "fixed_size_two" in GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(grid) != _intended(grid) for grid in grids), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_query_rotation_of_a_four_pair_window_refutes_declared_rivals(band, start):
    pairs = []
    for sample_index in range(start, start + 4):
        grid = GEN.generate(3715546571, sample_index, difficulty=band)
        pairs.append({"input": grid, "output": _intended(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == [], (
            band,
            start,
            query_index,
            GEN.lesson_identifiable(demos, query),
        )


def test_fixed_size_two_really_fits_all_canonical_pairs_but_not_the_curriculum():
    shortcut = GEN.CANONICAL_SHORTCUTS["fixed_size_two"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _pairs())
    varied = GEN.generate(24680, 1, difficulty="medium")
    assert shortcut(varied) != _intended(varied)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert GEN.self_check(grid)


def test_retained_fixed_size_two_counterexample_is_minimal_and_replayable():
    path = HOME / "counterexamples" / "fixed-size-two.json"
    case = json.loads(path.read_text())
    assert GEN.self_check(case["input"]) == []
    assert _intended(case["input"]) == case["intended_output"]
    assert GEN.CANONICAL_SHORTCUTS["fixed_size_two"](case["input"]) == case["shortcut_output"]
    assert case["shortcut_output"] != case["intended_output"]
