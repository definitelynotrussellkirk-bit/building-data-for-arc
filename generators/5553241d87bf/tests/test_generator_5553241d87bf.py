from __future__ import annotations

import copy
import importlib
import random
from collections import Counter

import pytest

from reviewer_support import canonical_pairs as load_canonical_pairs, find_root


TASK = "5553241d87bf"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)


def canonical_pairs():
    return load_canonical_pairs(TASK, root=ROOT, labeled_only=True)


def bounds(size, separators):
    points = [-1, *separators, size]
    return [(points[i] + 1, points[i + 1] - 1) for i in range(len(points) - 1) if points[i + 1] - points[i] > 1]


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    sep_rows = [r for r in range(height) if all(grid[r][c] == 0 for c in range(width))]
    sep_cols = [c for c in range(width) if all(grid[r][c] == 0 for r in range(height))]
    row_bounds, col_bounds = bounds(height, sep_rows), bounds(width, sep_cols)
    template = None
    for ri, (r0, r1) in enumerate(row_bounds):
        for ci, (c0, c1) in enumerate(col_bounds):
            if any(grid[r][c] not in (0, background) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
                template = ri, ci
                break
        if template is not None:
            break
    tr0, tr1 = row_bounds[template[0]]
    tc0, tc1 = col_bounds[template[1]]
    pattern = [row[tc0 : tc1 + 1] for row in grid[tr0 : tr1 + 1]]
    output = copy.deepcopy(grid)
    targets = []
    for ri, (r0, r1) in enumerate(row_bounds):
        for ci, (c0, c1) in enumerate(col_bounds):
            if (ri, ci) != template and any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
                targets.append((ri, ci))
                for dr, pattern_row in enumerate(pattern):
                    output[r0 + dr][c0 : c0 + len(pattern_row)] = pattern_row
    return output, template, pattern, targets, sep_rows, sep_cols


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = canonical_pairs()[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"]
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, band):
    grid = MODULE.generate(40_000 + len(profile), 17, difficulty=band, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    expected, template, pattern, targets, _, _ = independent_oracle(grid)
    assert not analysis["errors"]
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected
    assert analysis["facts"]["template_index"] == template
    assert [list(row) for row in analysis["facts"]["pattern"]] == pattern
    assert list(analysis["facts"]["targets"]) == targets
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    changed = sum(before != after for input_row, output_row in zip(grid, expected) for before, after in zip(input_row, output_row))
    assert changed / (len(grid) * len(grid[0])) >= MODULE.MIN_SYNTHETIC_CHANGE_RATE


@pytest.mark.parametrize("size", [3, 4, 5])
@pytest.mark.parametrize("category", ["corner", "center", "edge"])
def test_square_profiles_recover_size_and_template_position(size, category):
    profile = f"cell{size}_{category}_template"
    grid = MODULE.generate(51 + size, size, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["cell_height"] == facts["cell_width"] == size
    assert MODULE._position_category(facts) == category
    assert not facts["pattern_zeros"]
    assert max(facts["dot_counts"].values()) == 1


def test_rectangular_profile_uses_unequal_cell_axes():
    grid = MODULE.generate(61, 2, difficulty="medium", scene_profile="rectangular_cells")
    facts = MODULE._analysis(grid)["facts"]
    assert facts["cell_height"] != facts["cell_width"]


def test_multiple_dots_still_trigger_one_exact_stamp():
    grid = MODULE.generate(63, 3, difficulty="hard", scene_profile="multiple_dot_shapes")
    facts = MODULE._analysis(grid)["facts"]
    assert min(facts["dot_counts"].values()) >= 2
    for row_index, col_index in facts["targets"]:
        row0 = facts["row_bounds"][row_index][0]
        col0 = facts["col_bounds"][col_index][0]
        actual = tuple(tuple(facts["output"][row0 + dr][col0 + dc] for dc in range(facts["cell_width"])) for dr in range(facts["cell_height"]))
        assert actual == facts["pattern"]


def test_template_zero_is_copied_literally_into_targets():
    grid = MODULE.generate(67, 4, difficulty="hard", scene_profile="template_with_zero")
    facts = MODULE._analysis(grid)["facts"]
    assert facts["pattern_zeros"]
    drow, dcol = facts["pattern_zeros"][0]
    for row_index, col_index in facts["targets"]:
        row0 = facts["row_bounds"][row_index][0]
        col0 = facts["col_bounds"][col_index][0]
        assert facts["output"][row0 + drow][col0 + dcol] == 0


def test_separators_template_and_unmarked_cells_remain_unchanged():
    grid = MODULE.generate(71, 5, difficulty="hard", scene_profile="cell5_edge_template")
    facts = MODULE._analysis(grid)["facts"]
    output = facts["output"]
    assert all(output[r] == grid[r] for r in facts["separator_rows"])
    assert all(output[r][c] == grid[r][c] for c in facts["separator_cols"] for r in range(len(grid)))
    template = facts["template_index"]
    tr0, tr1 = facts["row_bounds"][template[0]]
    tc0, tc1 = facts["col_bounds"][template[1]]
    assert [row[tc0 : tc1 + 1] for row in output[tr0 : tr1 + 1]] == [row[tc0 : tc1 + 1] for row in grid[tr0 : tr1 + 1]]


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="medium", scene_profile="multiple_dot_shapes")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="medium", scene_profile="multiple_dot_shapes")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(73, 6, difficulty="medium", scene_profile="multiple_dot_shapes") == second


@pytest.mark.parametrize("grid", [[], [[]], [[0] * 8 for _ in range(6)], [[0] * 7 for _ in range(31)], [[0] * 8 for _ in range(8)] + [[0] * 7], [[False] * 8 for _ in range(8)], [[10] * 8 for _ in range(8)]])
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_no_template_no_separators_and_too_few_targets_fail_closed():
    assert MODULE.self_check([[7] * 9 for _ in range(9)])
    blank_cells = [[7, 7, 7, 0, 7, 7, 7], [7, 7, 7, 0, 7, 7, 7], [7, 7, 7, 0, 7, 7, 7], [0] * 7, [7, 7, 7, 0, 7, 7, 7], [7, 7, 7, 0, 7, 7, 7], [7, 7, 7, 0, 7, 7, 7]]
    assert MODULE.self_check(blank_cells)
    one_target = copy.deepcopy(blank_cells)
    one_target[0][0], one_target[5][5] = 2, 0
    assert MODULE.self_check(one_target)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "c3"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert set(MODULE.SCENE_PROFILES) == set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
