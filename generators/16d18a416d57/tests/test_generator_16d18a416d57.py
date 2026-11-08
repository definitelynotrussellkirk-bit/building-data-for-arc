"""Portable regressions for the largest-blue-component curriculum."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "16d18a416d57"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _components_4(grid, color=1):
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
    largest_size = max(map(len, components))
    winners = [cells for cells in components if len(cells) == largest_size]
    if len(winners) != 1:
        raise ValueError("oracle requires one uniquely largest blue component")
    out = deepcopy(grid)
    for r, c in winners[0]:
        out[r][c] = 7
    return out


def _largest_rank(grid):
    components = _components_4(grid)
    largest_size = max(map(len, components))
    return next(i for i, cells in enumerate(components) if len(cells) == largest_size)


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_inputs_are_lawful_and_match_independent_oracle(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]


def test_rule_pin_and_public_axis_contract_are_exact():
    assert GEN.RULE_HASH == "54df007aec53"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "component_profile"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_declared_strict_floor_leaves_margin_below_the_periodic_half():
    assert GEN.MIN_STRICT_FRAC == pytest.approx(0.40)
    assert GEN.MIN_STRICT_FRAC < 2 / GEN.LESSON_SCHEDULE_PERIOD


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 8, "grid_w": 10, "component_profile": "canonical_245"},
        {"grid_h": 9, "grid_w": 11, "component_profile": "canonical_345"},
        {"grid_h": 10, "grid_w": 12, "component_profile": "two_35"},
        {"grid_h": 11, "grid_w": 13, "component_profile": "varied_246"},
        {"grid_h": 12, "grid_w": 14, "component_profile": "four_2346"},
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
        {"texture": "no_motifs"},
        {"texture": "equal_sizes"},
        {"palette_kind": "warm"},
        {"grid_h": True},
        {"grid_w": 9},
        {"component_profile": None},
        {"component_profile": 245},
        {"component_profile": "not_a_profile"},
    ],
)
def test_invalid_unknown_and_retired_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_four_phase_schedule_covers_canonical_support_and_varied_winner_sizes(band):
    grids = [GEN.generate(913, index, difficulty=band) for index in range(4)]
    profiles = [GEN.observe_overrides(grid)["component_profile"] for grid in grids]
    assert profiles == ["canonical_245", "varied_246", "canonical_345", "varied_246"]
    assert {_largest_rank(grid) for grid in grids} == {0, 1, 2}
    assert [GEN.strict_canonical_like(grid) == [] for grid in grids] == [True, False, True, False]
    assert [max(map(len, _components_4(grid))) for grid in grids] == [5, 6, 5, 6]


@pytest.mark.parametrize("seed", range(24))
def test_default_draws_are_deterministic_lawful_and_rule_active(seed):
    for band in (None, "easy", "medium", "hard"):
        grid = GEN.generate(seed, seed % 7, difficulty=band)
        assert GEN.generate(seed, seed % 7, difficulty=band) == grid
        assert GEN.self_check(grid) == []
        assert _intended(grid) != grid


def test_semantic_contract_names_real_counterexamples():
    grids = [GEN.generate(177, index, difficulty="medium") for index in range(3)]
    assert any(GEN.SEMANTIC_WITNESSES["largest_not_first"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["largest_not_last"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["bbox_area_tie_selects_smaller"](grid) for grid in grids)
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(grid) != _intended(grid) for grid in grids), name


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert GEN.self_check(grid)

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(6))
def test_every_query_rotation_of_a_four_pair_window_refutes_declared_rivals(band, start):
    """Every 3-demo subset must distinguish every declared lesson competitor."""
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

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_lesson_refutes_a_fixed_size_five_shortcut_in_every_rotation(band):
    assert "fixed_size_five" in GEN.LESSON_COMPETITORS
    pairs = []
    winner_sizes = []
    for sample_index in range(4):
        grid = GEN.generate(24680, sample_index, difficulty=band)
        components = _components_4(grid)
        winner_sizes.append(max(map(len, components)))
        pairs.append({"input": grid, "output": _intended(grid)})
    assert sum(size != 5 for size in winner_sizes) >= 2
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == []
