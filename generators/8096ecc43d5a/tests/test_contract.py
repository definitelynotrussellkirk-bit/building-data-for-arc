"""Portable regressions for the transform-script input contract."""
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator("8096ecc43d5a", root=ROOT)
BANDS = ("easy", "medium", "hard")


def _valid_grid():
    grid = [[0] * 8 for _ in range(8)]
    grid[0][1], grid[0][4] = 2, 1
    for r, c in ((3, 2), (4, 2), (5, 2), (5, 3), (5, 4)):
        grid[r][c] = 7
    return grid


def _invalid_grid(kind):
    grid = _valid_grid()
    if kind == "blank":
        return [[0] * 8 for _ in range(8)]
    if kind == "missing_script":
        grid[0] = [0] * 8
    elif kind == "missing_motif":
        grid[2:] = [[0] * 8 for _ in grid[2:]]
    elif kind == "illegal_code":
        grid[0][1] = 5
    elif kind == "too_many_codes":
        grid[0] = [1] * 7 + [0]
    elif kind == "separator":
        grid[1][2] = 7
    elif kind == "disconnected":
        grid[7][7] = 7
    elif kind == "multiple_motif_colors":
        grid[3][2] = 8
    elif kind == "boolean":
        grid[3][2] = True
    elif kind == "float":
        grid[3][2] = 7.0
    elif kind == "out_of_palette":
        grid[3][2] = 17
    elif kind == "ragged":
        grid[3].pop()
    return grid


@pytest.mark.parametrize("kind", (
    "blank", "missing_script", "missing_motif", "illegal_code",
    "too_many_codes", "separator", "disconnected", "multiple_motif_colors",
    "boolean", "float", "out_of_palette", "ragged",
))
def test_validator_rejects_structural_counterexamples(kind):
    assert GEN.self_check(_invalid_grid(kind)), kind


def test_validator_accepts_all_four_canonical_pairs():
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("h,w,count,color,size", (
    (7, 8, 1, 1, 3),
    (8, 9, 5, 4, 5),
    (14, 16, 6, 7, 12),
))
def test_exact_controls_work_in_every_band(band, h, w, count, color, size):
    overrides = dict(grid_h=h, grid_w=w, n_codes=count, motif_color=color, motif_size=size)
    grid = GEN.generate(193, 5, difficulty=band, **overrides)
    assert (len(grid), len(grid[0])) == (h, w)
    assert sum(value != 0 for value in grid[0]) == count
    cells = [value for row in grid[2:] for value in row if value]
    assert len(cells) == size
    assert set(cells) == {color}
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides


@pytest.mark.parametrize("value", (True, 8.0, "8", -1, 31))
def test_exact_integer_controls_reject_coercion_and_out_of_domain_values(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, grid_h=value)


def test_unknown_controls_fail_loudly():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, motif_colour=7)


@pytest.mark.parametrize("name,value", (
    ("seed", True), ("seed", "1"), ("seed", 1.0),
    ("sample_index", True), ("sample_index", -1), ("sample_index", "1"),
    ("difficulty", True), ("difficulty", 0), ("difficulty", "impossible"),
))
def test_call_arguments_reject_invalid_scalars(name, value):
    args = dict(seed=0, sample_index=0, difficulty="medium")
    args[name] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**args)


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_retains_canonical_profile_support(band):
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({v for row in p["input"] for v in row}))
                for p in canonical_pairs(GEN.TASK_ID, root=ROOT)}
    observed = []
    for index in range(20):
        grid = GEN.generate(700 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        observed.append((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert sum(profile in profiles for profile in observed) >= 1
    assert sum(8 <= h <= 9 and 8 <= w <= 10 and 3 <= colors <= 5
               for h, w, colors in observed) >= 5


def test_generation_is_deterministic_and_returns_fresh_rows():
    original = GEN.generate(87, 12, difficulty="hard")
    expected = deepcopy(original)
    original[0][0] = 99
    assert GEN.generate(87, 12, difficulty="hard") == expected
    assert len({id(row) for row in original}) == len(original)


def test_canonical_rule_hash_is_pinned():
    assert getattr(GEN, "RULE_HASH", None) == "04788c0240d6"
