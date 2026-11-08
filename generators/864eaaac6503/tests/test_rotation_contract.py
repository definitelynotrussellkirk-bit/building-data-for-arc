"""Portable regressions for the selected rotation generator's public contract."""
from copy import deepcopy
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "864eaaac6503"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


@pytest.mark.parametrize("name,value", [
    ("seed", True), ("seed", 1.5), ("seed", "2"), ("seed", -1),
    ("sample_index", False), ("sample_index", 2.0), ("sample_index", -1),
    ("difficulty", True), ("difficulty", 0), ("difficulty", "unknown"),
    ("grid_h", 3.0), ("grid_w", "3"), ("palette_size", True),
    ("bg_density", float("nan")), ("noise_overlay", float("inf")),
    ("border_mode", "unknown"), ("typo_axis", 1),
])
def test_invalid_scalar_and_unknown_controls_are_rejected(name, value):
    args = {"seed": 17, "sample_index": 0, "difficulty": "easy"}
    args[name] = value
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(**args)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_controls_are_independent_of_default_difficulty(band):
    grid = GEN.generate(17, 0, difficulty=band, grid_h=30, grid_w=2, palette_size=10)
    assert (len(grid), len(grid[0])) == (30, 2)
    assert len({v for row in grid for v in row}) == 10
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("texture", [
    "noise", "sparse", "blob", "stripes", "gradient", "checkerboard", "frame", "ring", "plus",
])
def test_palette_count_survives_each_texture(texture):
    grid = GEN.generate(17, 0, grid_h=3, grid_w=3, palette_size=9, texture=texture)
    assert len({v for row in grid for v in row}) == 9
    assert GEN.observe_overrides(grid)["palette_size"] == 9


def test_impossible_palette_capacity_is_explicit():
    with pytest.raises(ValueError) as raised:
        GEN.generate(17, 0, grid_h=2, grid_w=2, palette_size=5)
    assert set(raised.value.incompatible_axes) == {"grid_h", "grid_w", "palette_size"}


@pytest.mark.parametrize("grid", [
    [], [[]], [[0, 1], [0]], [[0, True], [1, 0]], [[0, 1.0], [1, 0]],
    [[0, -1], [1, 0]], [[0, 10], [1, 0]], [[0, 0], [0, 0]],
    [[0, 1]] * 31,
])
def test_validator_rejects_malformed_arc_grids_without_crashing(grid):
    assert GEN.self_check(grid)


def test_validator_preserves_canonical_and_lawful_small_shapes():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert ccw(pair["input"]) == pair["output"]
    # These are lawful under the unrestricted rotation authority. Do not
    # shrink the validator to make generic tiny-shape heuristics pass.
    for grid in (
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[1, 1, 0], [1, 1, 0], [0, 0, 0]],
        [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
    ):
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_has_canonical_support_and_teaches_rotations(band):
    grids = [GEN.generate(73, i, difficulty=band) for i in range(24)]
    assert sum(not GEN.strict_canonical_like(g) for g in grids) == 12
    for grid in grids:
        assert GEN.self_check(grid) == []
        assert ccw(grid) != grid
    for start in range(20):
        pairs = [{"input": g, "output": ccw(g)} for g in grids[start:start + 4]]
        for query_index in range(4):
            demos = [p for i, p in enumerate(pairs) if i != query_index]
            query = pairs[query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                assert not (all(rival(p["input"]) == p["output"] for p in demos)
                            and rival(query["input"]) != query["output"])


def test_repeatability_and_canonical_shortcut_scope():
    first = GEN.generate(91, 1, difficulty="hard")
    untouched = deepcopy(first)
    assert GEN.generate(91, 1, difficulty="hard") == first
    GEN.lesson_identifiable([{"input": first, "output": ccw(first)}],
                            {"input": first, "output": ccw(first)})
    assert first == untouched
    for rival in GEN.CANONICAL_SHORTCUTS.values():
        for pair in canonical_pairs(TASK, root=ROOT):
            assert rival(pair["input"]) == pair["output"]


def test_border_constraints_and_palette_are_jointly_realized():
    grid = GEN.generate(19, 0, grid_h=5, grid_w=5, palette_size=10, border_mode="always_bg")
    assert len({v for row in grid for v in row}) == 10
    border = grid[0] + grid[-1] + [row[0] for row in grid] + [row[-1] for row in grid]
    assert set(border) == {0}
    with pytest.raises(ValueError):
        GEN.generate(19, 0, grid_h=2, border_mode="always_bg")


def test_duplicate_filter_keeps_two_informative_examples_at_regression_seed():
    # The production runner advances past duplicate pairs. The first repair
    # emitted the same E input at indices 1 and 3 for this seed; raw-window
    # checks passed while accepted indices [0,1,2,4] lost a rotation witness.
    pairs, seen = [], set()
    for index in range(20):
        grid = GEN.generate(21212, index, difficulty="easy")
        key = tuple(tuple(row) for row in grid)
        if key in seen:
            continue
        seen.add(key)
        pairs.append({"input": grid, "output": ccw(grid)})
        if len(pairs) == 4:
            break
    assert len(pairs) == 4
    assert sum(not GEN.strict_canonical_like(p["input"]) for p in pairs) <= 2
    for index, query in enumerate(pairs):
        assert GEN.lesson_identifiable([p for i, p in enumerate(pairs) if i != index], query) == []


def test_extended_examples_refute_partial_foreground_rotation():
    from puzzle_generators.helpers.objects import find_objects
    # This seed exposed an independently searched partial-construction rival
    # in the first after battery. The check uses an input-only hypothesis.
    for index in (11, 13):
        grid = GEN.generate(163210477420611, index, difficulty="easy")
        components = find_objects(grid, univalued=True, bg=0)
        selected = min(components, key=lambda obj: min(cell for _, cell in obj))
        masked = [[0 for _ in row] for row in grid]
        for color, (r, c) in selected:
            masked[r][c] = color
        assert ccw(masked) != ccw(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_consecutive_extended_pairs_cannot_be_duplicates(band):
    for seed in (0, 73, 21212):
        extended = [GEN.generate(seed, i, difficulty=band) for i in range(1, 17, 2)]
        for left, right in zip(extended, extended[1:]):
            assert (min(len(left), len(left[0])) % 2) != (min(len(right), len(right[0])) % 2)
