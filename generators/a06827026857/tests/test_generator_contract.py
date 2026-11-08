"""Behavioral regressions for the returned sampler, usable after relocation."""
import importlib.util
from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
TASK = "a06827026857"
SOURCE = next(path for path in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("assigned_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_requested_square_count_is_not_silently_shortened():
    grid = GEN.generate(0, 0, difficulty="medium", grid_h=8, grid_w=8,
                        square_count=3)
    assert sum(value != 0 for row in grid for value in row) == 27


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_small_declared_dimensions_work_in_every_band(band):
    grid = GEN.generate(17, 0, difficulty=band, grid_h=5, grid_w=12,
                        square_count=2)
    assert (len(grid), len(grid[0])) == (5, 12)
    assert sum(value != 0 for row in grid for value in row) == 18


def test_unknown_override_is_not_silently_ignored():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, square_cout=2)


@pytest.mark.parametrize("value", [8.5, "8"])
def test_dimensions_do_not_coerce_nonintegers(value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, grid_h=value)


@pytest.mark.parametrize("kind", ["ragged", "bad_color", "boolean", "full_canvas"])
def test_validator_rejects_malformed_or_trivial_grids(kind):
    grid = [[0] * 6 for _ in range(6)]
    for r in range(3):
        for c in range(3):
            grid[r][c] = 4
    if kind == "ragged":
        grid[-1].pop()
    elif kind == "bad_color":
        grid[-1][-1] = 10
    elif kind == "boolean":
        grid[-1][-1] = True
    else:
        grid = [[4] * 6 for _ in range(6)]
    assert GEN.self_check(grid)


def test_canonical_inputs_remain_accepted():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert pairs
    assert all(not GEN.self_check(pair["input"]) for pair in pairs)


def _window_count(grid):
    """Independent raw-pixel observation; no generator geometry helpers."""
    return sum(grid[r][c] != 0 and all(
        grid[r + y][c + x] == grid[r][c] for y in range(3) for x in range(3))
        for r in range(len(grid) - 2) for c in range(len(grid[0]) - 2))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("case", ["clean", "repeated", "attached", "overlap", "mixed"])
@pytest.mark.parametrize("count", [1, 2, 5])
def test_exact_controls_have_their_promised_pixels(band, case, count):
    axes = dict(grid_h=19, grid_w=19, square_count=count, case=case)
    if case == "repeated" and count == 1:
        with pytest.raises(ValueError) as caught:
            GEN.generate(37, 3, difficulty=band, **axes)
        assert set(caught.value.incompatible_axes) <= set(axes)
        return
    grid = GEN.generate(37, 3, difficulty=band, **axes)
    assert GEN.observe_overrides(grid) == axes
    assert GEN.self_check(grid) == []
    foreground = sum(v != 0 for row in grid for v in row)
    windows = _window_count(grid)
    appendage = int(case in ("attached", "mixed"))
    if case in ("overlap", "mixed"):
        assert foreground - 9 * count - appendage in (12, 16)
        assert windows - count in (2, 4)
    else:
        assert foreground == 9 * count + appendage
        assert windows == count


def test_impossible_joint_controls_fail_instead_of_losing_objects():
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, grid_h=5, grid_w=5, square_count=2, case="clean")
    assert {"grid_h", "grid_w", "square_count"} <= set(caught.value.incompatible_axes)


def test_draw_is_reproducible_after_unrelated_draws():
    wanted = GEN.generate(819, 7, difficulty="hard")
    GEN.generate(23, 0, difficulty="easy", case="repeated")
    assert GEN.generate(819, 7, difficulty="hard") == wanted


CORNER_ATTACHMENT = [
    [4, 4, 4, 4, 0],
    [4, 4, 4, 0, 0],
    [4, 4, 4, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]
CORNER_OUTPUT = [
    [4, 0, 4, 0, 0],
    [0, 0, 0, 0, 0],
    [4, 0, 4, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]


def test_declared_shortcuts_fit_canonical_but_fail_corner_attachment():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert GEN.self_check(CORNER_ATTACHMENT) == []
    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            before = deepcopy(pair["input"])
            assert rival(pair["input"]) == pair["output"], name
            assert pair["input"] == before, name
        assert rival(CORNER_ATTACHMENT) != CORNER_OUTPUT, name


def test_ambiguous_lesson_is_rejected_and_a_refuting_demo_resolves_it():
    demos = canonical_pairs(TASK, root=ROOT)[:3]
    query = {"input": CORNER_ATTACHMENT, "output": CORNER_OUTPUT}
    before = deepcopy((demos, query))
    reasons = GEN.lesson_identifiable(demos, query)
    assert all(any(name in reason for reason in reasons) for name in GEN.LESSON_COMPETITORS)
    assert GEN.lesson_identifiable([query, *demos[:2]], query) == []
    assert (demos, query) == before


@pytest.mark.parametrize("second_origin", [(0, 3), (3, 3)])
def test_validator_enforces_separation_between_different_colors(second_origin):
    grid = [[0] * 8 for _ in range(8)]
    for color, (top, left) in ((2, (0, 0)), (3, second_origin)):
        for r in range(top, top + 3):
            for c in range(left, left + 3):
                grid[r][c] = color
    assert GEN.self_check(grid)


def test_default_mixed_distribution_contains_more_than_two_base_squares():
    counts = set()
    for seed in range(24):
        grid = GEN.generate(seed, 1, difficulty="hard")
        foreground = sum(v != 0 for row in grid for v in row)
        # One appendage plus a 12- or 16-pixel overlap block; all other
        # foreground belongs to nine-pixel base targets.
        extra = {4: 13, 8: 17}[foreground % 9]
        counts.add((foreground - extra) // 9)
    assert counts <= {2, 3, 4, 5}
    assert len(counts) > 1 and max(counts) > 2
