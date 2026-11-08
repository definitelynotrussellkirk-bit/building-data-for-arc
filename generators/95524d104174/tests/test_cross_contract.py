"""Behavioral regressions for canonical coverage and exact cross controls."""
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("95524d104174", root=ROOT)


def cross(h, w, r, c, vertical=1, horizontal=2, winner=0):
    grid = [[0] * w for _ in range(h)]
    for row in grid:
        row[c] = vertical
    grid[r] = [horizontal] * w
    grid[r][c] = (vertical, horizontal)[winner]
    return grid


def test_validator_accepts_every_canonical_input_including_horizontal_winner():
    for pair in canonical_pairs("95524d104174", root=ROOT):
        assert GEN.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w", [(4, 4), (4, 14), (14, 4)])
@pytest.mark.parametrize("winner", [0, 1])
def test_exact_dimensions_colors_and_winner_are_honored_in_every_band(band, h, w, winner):
    g = GEN.generate(2026, 7, difficulty=band, grid_h=h, grid_w=w,
                     vertical_color=3, horizontal_color=2, crossing_winner=winner)
    assert len(g) == h and all(len(row) == w for row in g)
    rows = [r for r in range(h) if all(g[r])]
    cols = [c for c in range(w) if all(g[r][c] for r in range(h))]
    assert len(rows) == len(cols) == 1
    r, c = rows[0], cols[0]
    assert g[0][c] == 3 and g[r][0] == 2
    assert g[r][c] == (3, 2)[winner]
    assert GEN.self_check(g) == []


@pytest.mark.parametrize("damage", ["gap", "stray", "extra_row", "extra_col", "third_center"])
def test_validator_rejects_structural_damage(damage):
    g = cross(6, 7, 2, 3)
    if damage == "gap":
        g[0][3] = 0
    elif damage == "stray":
        g[0][0] = 1
    elif damage == "extra_row":
        g[4] = [2] * 7
        g[4][3] = 1
    elif damage == "extra_col":
        for row in g:
            row[5] = 1
    else:
        g[2][3] = 3
    assert GEN.self_check(g)


@pytest.mark.parametrize("g", [[], [[]], [[0, 1], [0]], [[0, True], [1, 2]], [[0, 10], [1, 2]]])
def test_validator_reports_malformed_grids_without_crashing(g):
    assert GEN.self_check(g)


def test_observer_measures_pixels_even_when_horizontal_line_wins():
    g = cross(4, 6, 1, 2, vertical=4, horizontal=9, winner=1)
    observed = GEN.observe_overrides(g)
    assert observed == {"grid_h": 4, "grid_w": 6, "vertical_color": 4,
                        "horizontal_color": 9, "crossing_winner": 1}


@pytest.mark.parametrize("kw", [{"typo_axis": 7}, {"grid_h": True}, {"grid_w": 7.2},
                                {"vertical_color": "3"}, {"grid_h": 3},
                                {"crossing_winner": 2}])
def test_invalid_or_unknown_controls_fail_explicitly(kw):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **kw)


def test_equal_explicit_line_colors_are_a_declared_incompatibility():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, vertical_color=2, horizontal_color=2)
    for color in range(1, 10):
        g = GEN.generate(0, color, horizontal_color=color)
        assert len({v for row in g for v in row} - {0}) == 2


def test_default_sampler_reaches_small_margin_one_and_both_overlap_winners():
    hits = {"four": False, "margin_one": False, "horizontal": False}
    for band in ("easy", "medium", "hard"):
        for index in range(100):
            g = GEN.generate(2026, index, difficulty=band)
            h, w = len(g), len(g[0])
            r = next(r for r in range(h) if all(g[r]))
            c = next(c for c in range(w) if all(g[r][c] for r in range(h)))
            hits["four"] |= h == w == 4
            hits["margin_one"] |= min(r, c, h - 1 - r, w - 1 - c) == 1
            hits["horizontal"] |= g[r][c] == g[r][0]
    assert all(hits.values()), hits


def test_generation_is_deterministic_and_validation_does_not_mutate():
    a = GEN.generate(7, 11, difficulty="hard")
    b = GEN.generate(7, 11, difficulty="hard")
    assert a == b
    snapshot = deepcopy(a)
    assert GEN.self_check(a) == []
    assert a == snapshot


@pytest.mark.parametrize("name,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", 1.75), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", 1.0),
    ("sample_index", 1.75), ("sample_index", -1), ("sample_index", "1"),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", "__invalid_difficulty__"),
])
def test_invalid_call_arguments_are_rejected_before_rng_construction(name, value):
    arguments = {"seed": 0, "sample_index": 0, "difficulty": "easy", name: value}
    with pytest.raises(ValueError):
        GEN.generate(**arguments)
