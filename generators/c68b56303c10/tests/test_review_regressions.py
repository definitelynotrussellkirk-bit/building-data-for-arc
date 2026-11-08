"""Portable regressions for the red/green bbox-intersection generator."""

from collections import Counter
from itertools import product

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "c68b56303c10"
ROOT = find_root(__file__)
CANONICAL_PAIRS = canonical_pairs(TASK_ID, root=ROOT)
DIFFICULTIES = (None, "easy", "medium", "hard")
BANDS = ("easy", "medium", "hard")


@pytest.fixture(scope="module")
def generator():
    module, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    return module


def _profile(grid):
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


def _intersection_output(grid):
    """Independent bbox oracle, also checked against every canonical label."""
    bounds = []
    for color in (2, 3):
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        assert cells, f"Missing color {color}"
        rows, cols = zip(*cells)
        bounds.append((min(rows), min(cols), max(rows), max(cols)))
    red, green = bounds
    height = min(red[2], green[2]) - max(red[0], green[0]) + 1
    width = min(red[3], green[3]) - max(red[1], green[1]) + 1
    assert height > 0 and width > 0, "Red/green bounding boxes must intersect"
    return [[8] * width for _ in range(height)]


def _assert_valid_input(generator, grid, difficulty):
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert grid[0]
    assert all(type(value) is int and value in (0, 2, 3) for row in grid for value in row)
    assert generator.self_check(grid, difficulty=difficulty) == []
    return _intersection_output(grid)


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize(
    "pair",
    CANONICAL_PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
)
def test_canonical_inputs_are_valid_in_every_difficulty(generator, pair, difficulty):
    assert generator.self_check(pair["input"], difficulty=difficulty) == []
    assert _intersection_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
@pytest.mark.parametrize("n_red,n_green", tuple(product((2, 8), repeat=2)))
def test_exact_count_overrides_cross_difficulty_bands(generator, difficulty, n_red, n_green):
    grid = generator.generate(0, 0, difficulty=difficulty, n_red=n_red, n_green=n_green)
    counts = Counter(value for row in grid for value in row)
    assert counts[2] == n_red
    assert counts[3] == n_green
    _assert_valid_input(generator, grid, difficulty)


@pytest.mark.parametrize(
    "axis,numeric_value", (("grid_h", 10), ("grid_w", 12), ("n_red", 4), ("n_green", 4))
)
@pytest.mark.parametrize("convert", (bool, float, str), ids=("bool", "float", "string"))
def test_integer_overrides_reject_coercion(generator, axis, numeric_value, convert):
    # Numeric equivalents are in the default band's range, so a rejection must
    # be about the type rather than an accidentally out-of-range value.
    value = convert(numeric_value)
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, **{axis: value})


def test_stale_palette_override_is_rejected(generator):
    with pytest.raises(ValueError):
        generator.generate(0, 0, palette_kind="warm")


@pytest.mark.parametrize(
    "invalid_values",
    ((None,), ("bad",), (False,), (None, "bad", False)),
    ids=("none", "string", "bool", "mixed-none-string-bool"),
)
def test_self_check_reports_invalid_cell_values_without_crashing(generator, invalid_values):
    grid = [[0] * 10 for _ in range(8)]
    for r, c in ((1, 2), (6, 6), (3, 4)):
        grid[r][c] = 2
    for r, c in ((1, 6), (6, 2), (4, 5)):
        grid[r][c] = 3
    for column, value in enumerate(invalid_values):
        grid[0][column] = value

    reasons = generator.self_check(grid)

    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) and reason for reason in reasons)


@pytest.fixture(scope="module")
def sampled_profiles(generator):
    result = {}
    for difficulty in BANDS:
        profiles = []
        for sample_index in range(20):
            grid = generator.generate(0, sample_index, difficulty=difficulty)
            _assert_valid_input(generator, grid, difficulty)
            profiles.append(_profile(grid))
        result[difficulty] = profiles
    return result


@pytest.mark.parametrize("difficulty", BANDS)
def test_each_band_reaches_an_exact_canonical_input_profile(sampled_profiles, difficulty):
    canonical = {_profile(pair["input"]) for pair in CANONICAL_PAIRS}
    hits = sum(profile in canonical for profile in sampled_profiles[difficulty])
    assert hits >= 1, f"No exact canonical (height,width,total-colors) hit in {difficulty}"


def test_pooled_canonical_profile_support_meets_floors(sampled_profiles):
    canonical = {_profile(pair["input"]) for pair in CANONICAL_PAIRS}
    envelope = tuple((min(values), max(values)) for values in zip(*canonical))
    sampled = [profile for profiles in sampled_profiles.values() for profile in profiles]
    exact_hits = sum(profile in canonical for profile in sampled)
    envelope_hits = sum(
        all(low <= value <= high for value, (low, high) in zip(profile, envelope))
        for profile in sampled
    )
    assert exact_hits / len(sampled) >= 0.05, (exact_hits, len(sampled))
    assert envelope_hits / len(sampled) >= 0.25, (envelope_hits, len(sampled))


def test_hard_draws_retain_substantial_canonical_output_size_support(generator):
    canonical_shapes = {
        (len(pair["output"]), len(pair["output"][0])) for pair in CANONICAL_PAIRS
    }
    hits = 0
    for sample_index in range(200):
        grid = generator.generate(0, sample_index, difficulty="hard")
        output = _assert_valid_input(generator, grid, "hard")
        hits += (len(output), len(output[0])) in canonical_shapes
    assert hits >= 20, f"Only {hits}/200 hard draws have a canonical output size"
