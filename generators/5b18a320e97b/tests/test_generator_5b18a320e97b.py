from __future__ import annotations

import random

import pytest

from reviewer_support import canonical_pairs as reviewed_canonical_pairs, find_root, load_selected_generator


TASK = "5b18a320e97b"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def canonical_pairs():
    return reviewed_canonical_pairs(TASK, root=ROOT, labeled_only=True)


def independent_oracle(grid):
    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    cells = {color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color] for color in colors}
    horizontal = all(len({r for r, _ in positions}) == 1 for positions in cells.values())
    axis = 0 if horizontal else 1
    ordered = sorted(colors, key=lambda color: cells[color][0][axis])
    if horizontal:
        output = [[ordered[r]] * len(ordered) for r in range(len(ordered))]
    else:
        output = [ordered[:] for _ in ordered]
    return output, ("horizontal" if horizontal else "vertical"), tuple(ordered), cells


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
    expected, orientation, ordered, cells = independent_oracle(grid)
    assert not analysis["errors"]
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected
    assert analysis["facts"]["orientation"] == orientation
    assert analysis["facts"]["ordered_colors"] == ordered
    assert analysis["facts"]["cells_by_color"] == {color: tuple(positions) for color, positions in cells.items()}
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
@pytest.mark.parametrize("count", range(2, 8))
def test_orientation_count_and_gray_square_are_literal(orientation, count):
    profile = f"{orientation}_n{count}"
    grid = MODULE.generate(53 + count, count, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["orientation"] == orientation
    assert len(facts["ordered_colors"]) == count
    assert facts["gray_square"][2] == count
    assert sum(value == 5 for row in grid for value in row) == count * count


def test_horizontal_output_uses_solid_ordered_rows():
    grid = MODULE.generate(61, 4, scene_profile="horizontal_n6")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    assert output == [[color] * 6 for color in facts["ordered_colors"]]


def test_vertical_output_repeats_ordered_color_columns():
    grid = MODULE.generate(63, 5, scene_profile="vertical_n6")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    assert output == [list(facts["ordered_colors"]) for _ in range(6)]


@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
def test_gray_square_can_occlude_and_split_lines_without_changing_axis(orientation):
    split = None
    for seed in range(100):
        grid = MODULE.generate(70_000 + seed, seed, scene_profile=f"{orientation}_n7")
        facts = MODULE._analysis(grid)["facts"]
        for cells in facts["cells_by_color"].values():
            coordinates = sorted(col if orientation == "horizontal" else row for row, col in cells)
            if coordinates != list(range(coordinates[0], coordinates[-1] + 1)):
                split = grid, facts
                break
        if split:
            break
    assert split is not None
    grid, facts = split
    assert facts["orientation"] == orientation
    assert MODULE.rule_mirror(grid) == MODULE._analysis(grid)["output"]


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="medium", scene_profile="vertical_n5")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="medium", scene_profile="vertical_n5")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(73, 6, difficulty="medium", scene_profile="vertical_n5") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 7 for _ in range(6)],
        [[0] * 7 for _ in range(31)],
        [[0] * 7 for _ in range(7)] + [[0] * 6],
        [[False] * 7 for _ in range(7)],
        [[10] * 7 for _ in range(7)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_wrong_line_count_axes_visibility_and_gray_square_fail_closed():
    blank = [[0] * 9 for _ in range(9)]
    assert MODULE.self_check(blank)
    same_row = [[0] * 9 for _ in range(9)]
    same_row[0][0:2] = [1, 1]
    same_row[0][4:6] = [2, 2]
    for row in range(2, 4):
        for col in range(2, 4):
            same_row[row][col] = 5
    assert MODULE.self_check(same_row)
    mixed = [[0] * 9 for _ in range(9)]
    mixed[0][0] = mixed[1][1] = 1
    mixed[2][4] = mixed[3][5] = 2
    for row in range(5, 7):
        for col in range(5, 7):
            mixed[row][col] = 5
    assert MODULE.self_check(mixed)
    one_cell = [[0] * 9 for _ in range(9)]
    one_cell[0][0] = 1
    one_cell[2][0:2] = [2, 2]
    for row in range(5, 7):
        for col in range(5, 7):
            one_cell[row][col] = 5
    assert MODULE.self_check(one_cell)
    wrong_gray = MODULE.generate(87, 9, scene_profile="horizontal_n3")
    gray = [(r, c) for r, row in enumerate(wrong_gray) for c, value in enumerate(row) if value == 5]
    wrong_gray[gray[0][0]][gray[0][1]] = 0
    assert MODULE.self_check(wrong_gray)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "centered"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert set(MODULE.SCENE_PROFILES) == set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
