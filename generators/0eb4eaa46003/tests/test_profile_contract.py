"""Pixel-level regressions for the blue-row/red-column profile contract."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from itertools import product
import sys

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "0eb4eaa46003"
ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
_probe_path = ROOT / "generators" / TASK_ID / "workspace" / "profile_probe.py"
_spec = importlib.util.spec_from_file_location("profile_probe_0eb4eaa46003", _probe_path)
probe = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = probe
_spec.loader.exec_module(probe)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)
ORIGINAL_RIVAL_NAMES = frozenset((
    "copy_blue", "copy_red", "exact_blue", "exact_red", "row_only", "column_only",
    "bbox_only", "area_only", "first_candidate", "minimum_candidate_color",
    "color_4", "unordered_profiles", "third_component",
))


def test_exact_grid_height_lower_boundary():
    """Regression: accepting a scalar control must change the actual pixels."""
    grid = gen.generate(17, 1, grid_h=10, grid_w=14, shape_size=4,
                        n_distract=2, palette_size=4)
    assert len(grid) == 10
    assert all(len(row) == 14 for row in grid)


@pytest.mark.parametrize("pair_index", range(3))
def test_canonical_pairs_remain_accepted_and_have_expected_output(pair_index):
    assert len(CANONICAL) == 3
    pair = CANONICAL[pair_index]
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert probe.oracle_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("grid_h,grid_w", tuple(product((10, 24), (14, 24))))
def test_boundary_combinations_are_constructive_and_exact_in_pixels(grid_h, grid_w):
    # All 32 corners of the five-dimensional control box, without retrying or
    # consulting the generator's own object/profile/measurement helpers.
    for index, (shape_size, n_distract, palette_size) in enumerate(
            product((4, 10), (2, 3), (4, 6))):
        options = dict(grid_h=grid_h, grid_w=grid_w, shape_size=shape_size,
                       n_distract=n_distract, palette_size=palette_size)
        band = ("easy", "medium", "hard")[index % 3]
        seed = (0, 37)[index % 2]
        grid = gen.generate(seed, index, difficulty=band, **options)
        assert gen.self_check(grid, difficulty=band) == [], options
        assert probe.observed_axes(grid) == options
        assert gen.observe_overrides(grid) == options
        data = probe.scene(grid)
        assert len(data["blues"]) == len(data["reds"]) == len(data["matches"]) == 1
        output = probe.oracle_output(grid)
        assert sum(value == 8 for row in output for value in row) == shape_size
        assert {value for row in output for value in row} <= {0, 8}
        if index % 2:
            assert set(probe.refuted_rivals(grid)) == set(probe.RIVAL_NAMES)


@pytest.mark.parametrize("axis", tuple(probe.AXIS_BOUNDS))
def test_scalar_controls_reject_coercions_and_out_of_domain_values(axis):
    low, high = probe.AXIS_BOUNDS[axis]
    for value in (True, float(low), str(low), low - 1, high + 1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(17, 1, **{axis: value})


def test_removed_and_unknown_axes_are_rejected():
    assert set(gen.AXES) == set(probe.AXIS_BOUNDS)
    for options in ({"typo": 10}, {"typo": None}, {"position_bias": "scattered"},
                    {"texture": "single_cell"}, {"palette_kind": "default"}):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(17, 1, **options)


def test_none_controls_preserve_default_and_draws_are_deterministic():
    no_controls = dict.fromkeys(probe.AXIS_BOUNDS)
    for difficulty in (None, "easy", "medium", "hard"):
        for index in (0, 1):
            expected = gen.generate(37, index, difficulty=difficulty)
            assert gen.generate(37, index, difficulty=difficulty, **no_controls) == expected
            assert gen.generate(37, index, difficulty=difficulty) == expected


@pytest.mark.parametrize("argument,invalid_values", [
    ("seed", (True, 17.0, "17")),
    ("sample_index", (True, 1.0, "1", -1)),
    ("difficulty", (True, 1, 1.0, "unknown")),
])
def test_public_call_arguments_reject_unsupported_scalars(argument, invalid_values):
    for value in invalid_values:
        arguments = {"seed": 17, "sample_index": 1, "difficulty": "medium"}
        arguments[argument] = value
        with pytest.raises((TypeError, ValueError)):
            gen.generate(**arguments)
    # A signed seed remains legitimate; zero is the first legal sample index.
    accepted = gen.generate(-17, 0, difficulty=None)
    assert gen.self_check(accepted) == []
    assert accepted == gen.generate(-17, 0, difficulty=None)


def _validator_fixture():
    """A hand-authored valid scene: one target and two unequal-area decoys."""
    grid = [[0] * 14 for _ in range(10)]
    target = {(0, 0), (1, 0), (1, 1), (2, 1)}
    for color, top, left in ((1, 1, 1), (2, 1, 5), (3, 6, 1)):
        for row, column in target:
            grid[top + row][left + column] = color
    for column in range(5, 8):
        grid[6][column] = 3
    for column in range(7, 12):
        grid[8][column] = 3
    return grid


@pytest.mark.parametrize("defect", ["missing_blue", "missing_red", "multiple_blue",
                                   "multiple_red", "no_joint_target", "multiple_joint_targets"])
def test_validator_rejects_missing_or_ambiguous_profile_roles(defect):
    grid = _validator_fixture()
    assert gen.self_check(grid) == []
    before = deepcopy(grid)
    objects = probe.scene(grid)
    if defect in ("missing_blue", "missing_red", "no_joint_target"):
        selected = objects[{"missing_blue": "blues", "missing_red": "reds",
                            "no_joint_target": "matches"}[defect]][0]
        for row, column in selected.cells:
            grid[row][column] = 0
    else:
        color = {"multiple_blue": 1, "multiple_red": 2, "multiple_joint_targets": 3}[defect]
        # Reflected zigzag shares both profiles but has a different crop. Its
        # earlier bbox wins under the rule; this validator deliberately rejects
        # such ambiguous inputs instead of redefining the rule's tie breaking.
        for row, column in ((0, 1), (1, 0), (1, 1), (2, 0)):
            grid[1 + row][10 + column] = color
    if defect == "multiple_joint_targets":
        assert len(probe.scene(grid)["matches"]) == 2
        assert probe.oracle_output(grid) != probe.oracle_output(before)
    original = deepcopy(grid)
    assert gen.self_check(grid), defect
    assert grid == original


def test_validator_rejects_malformed_grids_and_nonliteral_colors():
    malformed = [None, [], [[]], [[0, 0], [0]], [0], "012", [[0] * 31]]
    for value in (True, 1.0, "1", -1, 10):
        grid = _validator_fixture()
        grid[0][0] = value
        malformed.append(grid)
    for grid in malformed:
        assert gen.self_check(grid), repr(grid)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_production_windows_refute_shortcuts_in_every_query_position(difficulty):
    assert gen.EXAMPLES_NEEDED == 3
    for seed in (0, 37):
        grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(10)]
        expected = [probe.oracle_output(grid) for grid in grids]
        predictions = [probe.rival_predictions(grid) for grid in grids]
        for index, grid in enumerate(grids):
            assert gen.self_check(grid, difficulty=difficulty) == []
            if index % 2:
                assert all(value != expected[index] for value in predictions[index].values())
        for start in range(7):
            indices = range(start, start + 4)
            assert sum(all(value != expected[index] for value in predictions[index].values())
                       for index in indices) >= 2
            # A 3-demonstration/1-query window retains a witness whichever of
            # its four positions is held out, so each rival is demonstrably
            # refuted in the visible examples even under query rotation.
            for query in indices:
                demonstration_indices = [index for index in indices if index != query]
                for rival in probe.RIVAL_NAMES:
                    assert any(predictions[index][rival] != expected[index]
                               for index in demonstration_indices), (seed, start, query, rival)


def test_even_draws_vary_shape_placement_color_and_grid_size():
    masks, positions, colors, dimensions = set(), set(), set(), set()
    for index in range(0, 32, 2):
        grid = gen.generate(101, index, difficulty="medium")
        data = probe.scene(grid)
        target = data["matches"][0]
        masks.add(target.mask)
        positions.add(target.bbox[:2])
        colors.add(target.color)
        dimensions.add((len(grid), len(grid[0])))
    assert len(masks) >= 3
    assert len(positions) >= 3
    assert len(colors) >= 2
    assert len(dimensions) >= 3


def test_even_phase_refutes_canonical_fitting_anchor_blind_profile_incidence():
    rivals = (probe.anchor_blind_incidence_prediction, probe.anchor_copy_then_incidence_prediction)
    assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL for rival in rivals)
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 37):
            for index in (0, 2, 4, 6):
                grid = gen.generate(seed, index, difficulty=difficulty)
                assert gen.self_check(grid, difficulty=difficulty) == []
                for rival in rivals:
                    assert rival(grid) != probe.oracle_output(grid), (
                        "An anchor-copy/profile-incidence shortcut still selects the target",
                        rival.__name__, difficulty, seed, index,
                    )
    assert len(gen.CANONICAL_SHORTCUTS) == 13


def test_canonical_shortcut_declarations_are_truthful_and_witnesses_refute_all_rivals():
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert callable(rival), name
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL), name
    for namespace in (gen.SEMANTIC_RIVALS, gen.LESSON_COMPETITORS):
        assert ORIGINAL_RIVAL_NAMES <= set(namespace)
        for index in (1, 3, 5):
            grid = gen.generate(71, index, difficulty="hard")
            original = deepcopy(grid)
            expected = probe.oracle_output(grid)
            for name, rival in namespace.items():
                if name in ORIGINAL_RIVAL_NAMES:
                    assert rival(grid) != expected, (name, index)
            assert grid == original
