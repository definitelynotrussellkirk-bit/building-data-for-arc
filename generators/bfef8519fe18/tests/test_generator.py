"""Task-local contract tests for the seeded-room flood generator."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "bfef8519fe18"
HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

ROOT = find_root(__file__)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
CANONICAL_PROFILES = {(7, 8, 5), (8, 9, 5)}
IRREGULAR_LAYOUTS = {
    "dogleg_vertical_2",
    "dogleg_horizontal_2",
    "dogleg_vertical_cross_4",
    "dogleg_horizontal_cross_4",
}


def _independent_fill(grid: list[list[int]]) -> list[list[int]]:
    """Independent implementation of the selected connected-room rule."""
    height = len(grid)
    width = len(grid[0])
    output = deepcopy(grid)
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 1
    }
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        colors = {
            grid[row][col]
            for row, col in component
            if grid[row][col] != 0
        }
        if len(colors) == 1:
            color = next(iter(colors))
            for row, col in component:
                if grid[row][col] == 0:
                    output[row][col] = color
    return output


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": _independent_fill(grid)}


def test_rule_pin_and_semantic_contract_are_declared():
    assert GEN.RULE_HASH == "77ee2c0d890d"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.LESSON_SCHEDULE_PERIOD == 8
    assert set(GEN.SEMANTIC_RIVALS) == {
        "identity",
        "canonical_t_top_only",
        "rectangular_rooms_only",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "canonical_t_top_only",
        "rectangular_rooms_only",
    }
    assert set(GEN.SEMANTIC_WITNESSES) >= {
        "fillable_rooms",
        "noncanonical_layout",
        "irregular_rooms",
    }


def test_all_canonical_pairs_are_accepted_and_match_independent_oracle():
    assert len(PAIRS) == 3
    for pair in PAIRS:
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert _independent_fill(source) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("layout", [
    "vertical_2",
    "horizontal_2",
    "t_top_3",
    "t_bottom_3",
    "t_left_3",
    "t_right_3",
    "cross_4",
    "dogleg_vertical_2",
    "dogleg_horizontal_2",
    "dogleg_vertical_cross_4",
    "dogleg_horizontal_cross_4",
])
@pytest.mark.parametrize("shape", [(7, 8), (14, 16)])
def test_every_exact_layout_and_shape_control_is_realized(band, layout, shape):
    height, width = shape
    requested = {"grid_h": height, "grid_w": width, "layout": layout}
    grid = GEN.generate(17, 29, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert _independent_fill(grid) != grid


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_anchors_profiles_and_covers_room_counts(band):
    grids = [GEN.generate(8000 + index, index, difficulty=band) for index in range(32)]
    observations = [GEN.observe_overrides(grid) for grid in grids]
    profiles = {_profile(grid) for grid in grids}
    room_counts = {GEN.scene_facts(grid)["room_count"] for grid in grids}
    assert CANONICAL_PROFILES <= profiles
    assert room_counts == {2, 3, 4}
    assert sum(item["layout"] in IRREGULAR_LAYOUTS for item in observations) == 16
    assert all(GEN.self_check(grid) == [] for grid in grids)


def test_every_four_pair_window_and_rotation_distinguishes_declared_rivals():
    for start in range(24):
        pairs = [
            _pair(GEN.generate(91_000 + start, start + offset, difficulty="medium"))
            for offset in range(4)
        ]
        irregular = [
            GEN.observe_overrides(pair["input"])["layout"] in IRREGULAR_LAYOUTS
            for pair in pairs
        ]
        assert sum(irregular) == 2
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []


def test_canonical_shortcuts_fit_public_pairs_but_irregular_witnesses_refute_them():
    for pair in PAIRS:
        assert GEN.CANONICAL_SHORTCUTS["canonical_t_top_only"](pair["input"]) == pair["output"]
        assert GEN.CANONICAL_SHORTCUTS["rectangular_rooms_only"](pair["input"]) == pair["output"]

    witnesses = [
        GEN.generate(1200 + index, 1 + 2 * index, layout="dogleg_vertical_2")
        for index in range(8)
    ]
    assert all(GEN.SEMANTIC_WITNESSES["irregular_rooms"](grid) for grid in witnesses)
    for grid in witnesses:
        expected = _independent_fill(grid)
        assert GEN.SEMANTIC_RIVALS["canonical_t_top_only"](grid) != expected
        assert GEN.SEMANTIC_RIVALS["rectangular_rooms_only"](grid) != expected


@pytest.mark.parametrize("overrides", [
    {"unknown": 1},
    {"grid_h": 6},
    {"grid_h": 15},
    {"grid_h": True},
    {"grid_w": 7},
    {"grid_w": 17},
    {"grid_w": 8.0},
    {"layout": "not-a-layout"},
    {"layout": 2},
])
def test_invalid_or_unknown_controls_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_generation_is_deterministic_and_does_not_touch_global_random_state():
    random.seed(20261007)
    before = random.getstate()
    first = GEN.generate(412, 111, difficulty="hard")
    second = GEN.generate(412, 111, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == before


def test_self_check_rejects_structural_damage_and_malformed_grids():
    valid = GEN.generate(4, 2, grid_h=8, grid_w=9, layout="t_top_3")
    broken_border = deepcopy(valid)
    broken_border[0][0] = 0
    extra_seed = deepcopy(valid)
    room = GEN.scene_facts(extra_seed)["rooms"][0]
    zero = next((r, c) for r, c in room if extra_seed[r][c] == 0)
    extra_seed[zero[0]][zero[1]] = 9
    illegal = deepcopy(valid)
    illegal[1][1] = 10
    boolean = deepcopy(valid)
    boolean[1][1] = True
    ragged = deepcopy(valid)
    ragged[-1].pop()
    for grid in (None, [], [[]], ragged, broken_border, extra_seed, illegal, boolean):
        errors = GEN.self_check(grid)
        assert errors
        assert all(isinstance(error, str) and error for error in errors)


def test_racket_authority_matches_independent_oracle_on_generated_layouts():
    from arcpuzzles import Catalog

    grids = [
        GEN.generate(70_000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        for index in range(12)
    ]
    receipt = Catalog(ROOT).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        _independent_fill(grid) for grid in grids
    ]


def test_generation_and_analysis_do_not_enumerate_the_full_wall_corpus(monkeypatch):
    """A single draw/validation must stay bounded at maximum dimensions.

    The old implementation rebuilt every possible dogleg-cross wall merely to
    classify one returned grid.  That made the official lint cohort stall.
    This sentinel keeps generation and scene analysis on their direct geometry
    paths instead of the exhaustive diagnostic enumerator.
    """
    def forbidden(*_args, **_kwargs):
        raise AssertionError("exhaustive wall enumeration reached hot path")

    monkeypatch.setattr(GEN, "_wall_candidates", forbidden)
    grid = GEN.generate(
        99,
        3,
        difficulty="hard",
        grid_h=14,
        grid_w=16,
        layout="dogleg_horizontal_cross_4",
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 14,
        "grid_w": 16,
        "layout": "dogleg_horizontal_cross_4",
    }


def test_retained_irregular_counterexample_refutes_both_canonical_shortcuts():
    import json

    artifact = json.loads(
        (HOME / "counterexamples" / "irregular_room_shortcuts.json").read_text()
    )
    grid = artifact["input"]
    expected = artifact["expected_output"]
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["layout"] in IRREGULAR_LAYOUTS
    assert GEN.rule_mirror(grid) == expected
    for name in ("canonical_t_top_only", "rectangular_rooms_only"):
        assert GEN.CANONICAL_SHORTCUTS[name](grid) == artifact["rival_outputs"][name]
        assert artifact["rival_outputs"][name] != expected
