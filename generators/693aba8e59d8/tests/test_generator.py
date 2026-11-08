"""Regression tests for the color-coded rotate-and-stamp generator."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "693aba8e59d8"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)
BANDS = (None, "easy", "medium", "hard")
SHAPES = ("l4", "v5", "w5", "p5")
ORIENTATIONS = ("r0", "r90", "r180", "r270")
AXIS_NAMES = {"grid_h", "grid_w", "shape_kind", "base_orientation", "anchor_phase"}


def _cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate(grid, code):
    turns = {1: 0, 2: 1, 3: 2, 4: 3}[code]
    result = [list(row) for row in grid]
    for _ in range(turns):
        result = _cw(result)
    return result


def _base_grid(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    assert cells
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r - r0][c - c0] = 6
    return out


def _stamp(output, subgrid, anchor):
    top = anchor[0] - len(subgrid) // 2
    left = anchor[1] - len(subgrid[0]) // 2
    for dr, row in enumerate(subgrid):
        for dc, value in enumerate(row):
            rr, cc = top + dr, left + dc
            if value and 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                output[rr][cc] = value


def independent_rule(grid):
    """Hand-derived mirror of the selected Racket rule."""
    base = _base_grid(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (1, 2, 3, 4):
                _stamp(output, _rotate(base, value), (r, c))
    return output


def _cross_positions(grid):
    anchors = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value in (1, 2, 3, 4)]
    rows = sorted({r for r, _, _ in anchors})
    cols = sorted({c for _, c, _ in anchors})
    assert len(anchors) == 4 and len(rows) == 3 and len(cols) == 3
    top, middle_row, bottom = rows
    left, middle_col, right = cols
    by_position = {(r, c): value for r, c, value in anchors}
    expected = {
        "north": (top, middle_col),
        "east": (middle_row, right),
        "south": (bottom, middle_col),
        "west": (middle_row, left),
    }
    assert set(by_position) == set(expected.values())
    return expected, by_position


def independent_position_shortcut(grid):
    """Canonical-fitting shortcut: compass position, rather than color, chooses rotation."""
    base = _base_grid(grid)
    positions, _ = _cross_positions(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for name, code in (("north", 1), ("east", 2), ("south", 3), ("west", 4)):
        _stamp(output, _rotate(base, code), positions[name])
    return output


def labelled(grid):
    return {"input": deepcopy(grid), "output": independent_rule(grid)}


def _components_of_color(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo = [start]
        component = {start}
        while todo:
            r, c = todo.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    todo.append(nxt)
        components.append(component)
    return components


def _phase(grid):
    positions, by_position = _cross_positions(grid)
    colors = tuple(by_position[positions[name]] for name in ("north", "east", "south", "west"))
    return {
        (1, 2, 3, 4): 0,
        (2, 3, 4, 1): 1,
        (3, 4, 1, 2): 2,
        (4, 1, 2, 3): 3,
    }[colors]


def test_contract_is_pinned_to_selected_rule_and_observable_axes():
    assert GEN.RULE_HASH == "60c823b90a2d"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == AXIS_NAMES
    assert tuple(GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert set(GEN.SEMANTIC_RIVALS) == {
        "position_encoded",
        "no_rotation",
        "swap_quarter_turns",
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == {"position_encoded"}
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    assert GEN.WITNESS_RIVALS == {
        "permuted_anchor_roles": ("position_encoded",),
        "all_four_rotation_codes": ("no_rotation", "swap_quarter_turns"),
    }


def test_all_canonical_pairs_are_accepted_and_match_independent_rule():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for item in pairs:
        original = deepcopy(item["input"])
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert independent_rule(item["input"]) == item["output"]
        assert GEN.rule_mirror(item["input"]) == item["output"]
        assert independent_position_shortcut(item["input"]) == item["output"]
        assert GEN.CANONICAL_SHORTCUTS["position_encoded"](item["input"]) == item["output"]
        assert item["input"] == original


@pytest.mark.parametrize("shape_kind", SHAPES)
@pytest.mark.parametrize("base_orientation", ORIENTATIONS)
@pytest.mark.parametrize("anchor_phase", range(4))
def test_every_axis_boundary_combination_round_trips(shape_kind, base_orientation, anchor_phase):
    for difficulty in BANDS:
        for grid_h in (11, 13):
            for grid_w in (11, 13):
                requested = {
                    "grid_h": grid_h,
                    "grid_w": grid_w,
                    "shape_kind": shape_kind,
                    "base_orientation": base_orientation,
                    "anchor_phase": anchor_phase,
                }
                grid = GEN.generate(7301, 11, difficulty=difficulty, **requested)
                assert GEN.self_check(grid) == []
                assert GEN.strict_canonical_like(grid) == []
                assert GEN.observe_overrides(grid) == requested
                assert GEN.rule_mirror(grid) == independent_rule(grid)
                assert independent_rule(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 10}, {"grid_h": 14}, {"grid_h": True}, {"grid_h": 11.0},
        {"grid_w": 10}, {"grid_w": 14}, {"grid_w": "11"},
        {"shape_kind": "t4"}, {"shape_kind": 1},
        {"base_orientation": "r360"}, {"base_orientation": 0},
        {"anchor_phase": -1}, {"anchor_phase": 4}, {"anchor_phase": False},
        {"anchor_phase": 1.0},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ("expert", 0.5, True))
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", (True, 1.0, "1"))
def test_invalid_seed_is_rejected(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", (-1, True, False, 1.0, "1"))
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_schedule_profile_rejects_invalid_sample_indices():
    for value in (-1, True, 1.0, "1"):
        with pytest.raises((TypeError, ValueError)):
            GEN.schedule_profile(0, value)


@pytest.mark.parametrize("difficulty", BANDS)
def test_defaults_cover_canonical_profiles_all_shapes_orientations_and_phases(difficulty):
    dimensions = set()
    shapes = set()
    orientations = set()
    phases = set()
    profiles = set()
    for index in range(64):
        grid = GEN.generate(1000 + index * 17, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        dimensions.add((observed["grid_h"], observed["grid_w"]))
        shapes.add(observed["shape_kind"])
        orientations.add(observed["base_orientation"])
        phases.add(observed["anchor_phase"])
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert {(11, 11), (13, 13), (11, 13)} <= dimensions
    assert shapes == set(SHAPES)
    assert orientations == set(ORIENTATIONS)
    assert phases == set(range(4))
    assert {(11, 11, 6), (13, 13, 6), (11, 13, 6)} <= profiles


def test_seed_changes_layout_without_changing_observed_axes():
    grids = []
    observations = []
    for seed in range(24):
        grid = GEN.generate(seed, 5, difficulty="medium")
        grids.append(tuple(tuple(row) for row in grid))
        observations.append(GEN.observe_overrides(grid))
    assert len(set(grids)) >= 12
    assert all(item == observations[0] for item in observations)


def test_difficulty_changes_default_scene_without_changing_task_grammar():
    for index in range(12):
        easy = GEN.generate(500, index, difficulty="easy")
        hard = GEN.generate(500, index, difficulty="hard")
        assert easy != hard
        assert GEN.self_check(easy) == []
        assert GEN.self_check(hard) == []


@pytest.mark.parametrize("difficulty", BANDS)
def test_generated_structure_matches_the_canonical_object_and_output_support(difficulty):
    for index in range(20):
        grid = GEN.generate(4000 + index, index, difficulty=difficulty)
        assert set(v for row in grid for v in row) == {0, 1, 2, 3, 4, 6}
        components = _components_of_color(grid, 6)
        assert len(components) == 1
        base = components[0]
        assert len(base) in (4, 5)
        assert all(sum(value == color for row in grid for value in row) == 1 for color in (1, 2, 3, 4))
        output = independent_rule(grid)
        assert set(v for row in output for v in row) == {0, 6}
        assert sum(value == 6 for row in output for value in row) == 4 * len(base)
        assert all(output[r][c] == 0 for r, c in base)


def test_position_shortcut_fits_only_the_canonical_anchor_phase():
    for shape in SHAPES:
        for orientation in ORIENTATIONS:
            for phase in range(4):
                grid = GEN.generate(
                    8123,
                    phase,
                    shape_kind=shape,
                    base_orientation=orientation,
                    anchor_phase=phase,
                )
                shortcut = independent_position_shortcut(grid)
                truth = independent_rule(grid)
                assert (shortcut == truth) is (phase == 0)
                assert GEN.SEMANTIC_RIVALS["position_encoded"](grid) == shortcut


def test_each_generated_grid_refutes_rotation_ignoring_rivals():
    for difficulty in BANDS:
        for index in range(24):
            grid = GEN.generate(9000 + index, index, difficulty=difficulty)
            truth = independent_rule(grid)
            assert GEN.SEMANTIC_RIVALS["no_rotation"](grid) != truth
            assert GEN.SEMANTIC_RIVALS["swap_quarter_turns"](grid) != truth
            assert GEN.SEMANTIC_WITNESSES["all_four_rotation_codes"](grid)
            if _phase(grid):
                assert GEN.SEMANTIC_WITNESSES["permuted_anchor_roles"](grid)
                assert GEN.SEMANTIC_RIVALS["position_encoded"](grid) != truth


@pytest.mark.parametrize("difficulty", BANDS)
def test_three_demonstrations_identify_every_four_pair_window_under_query_rotation(difficulty):
    for start in range(8):
        lesson = [
            labelled(GEN.generate(12000 + start, start + offset, difficulty=difficulty))
            for offset in range(4)
        ]
        assert {_phase(pair["input"]) for pair in lesson} == {0, 1, 2, 3}
        for query_index in range(4):
            query = lesson[query_index]
            demos = lesson[:query_index] + lesson[query_index + 1 :]
            assert GEN.lesson_identifiable(demos, query) == []


def test_lesson_hook_reports_the_real_canonical_position_shortcut():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    reasons = GEN.lesson_identifiable(pairs[:3], pairs[3])
    assert any("position_encoded" in reason for reason in reasons)


@pytest.mark.parametrize("missing_value", [pytest.param(object(), id="missing-key"), None])
def test_lesson_hook_rejects_unlabelled_demonstration_without_crashing(missing_value):
    lesson = [labelled(GEN.generate(13000, index)) for index in range(4)]
    broken = deepcopy(lesson[0])
    if missing_value is None:
        broken["output"] = None
    else:
        del broken["output"]
    try:
        reasons = GEN.lesson_identifiable([broken, lesson[1], lesson[2]], lesson[3])
    except Exception as exc:  # A validator must report malformed input, not crash.
        pytest.fail(f"lesson validator raised {type(exc).__name__}: {exc}")
    assert reasons == ["demo 0 is missing an output grid"]


def test_self_check_rejects_semantically_empty_or_malformed_impostors():
    good = GEN.generate(17, 4)
    assert GEN.self_check(good) == []
    cases = [
        [],
        [[0] * 11 for _ in range(11)],
        [[0, 0], [0]],
        [[True] + [0] * 10 for _ in range(11)],
    ]
    extra_color = deepcopy(good)
    extra_color[0][0] = 9
    cases.append(extra_color)
    missing_anchor = deepcopy(good)
    for r, row in enumerate(missing_anchor):
        for c, value in enumerate(row):
            if value == 4:
                missing_anchor[r][c] = 0
    cases.append(missing_anchor)
    for grid in cases:
        assert GEN.self_check(grid), grid


def test_declared_mutation_fixtures_are_all_rejected():
    fixtures = GEN.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_generation_is_deterministic_fresh_and_global_rng_neutral():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(777, 13, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 13, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(777, 13, difficulty="hard") == second


def test_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(808, 6)
    original = deepcopy(grid)
    GEN.observe_overrides(grid)
    GEN.strict_canonical_like(grid)
    GEN.rule_mirror(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(grid)
    assert grid == original
