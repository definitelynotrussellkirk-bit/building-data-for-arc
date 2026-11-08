"""Regressions for the advertised dimensions and exact marker-count axes."""
import pytest

from reviewer_support import find_root, load_selected_generator


@pytest.fixture(scope="module")
def generator():
    module, _, _ = load_selected_generator("70c9dccdcc4d", root=find_root(__file__))
    return module


def measure(grid):
    return len(grid), len(grid[0]), sum(cell == 8 for row in grid for cell in row)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,marks", [(9, 12, 1), (9, 12, 6), (18, 24, 6)])
def test_pinned_axes_take_precedence_over_difficulty(generator, difficulty, height, width, marks):
    grid = generator.generate(17, 3, difficulty=difficulty,
                              grid_h=height, grid_w=width, n_marks=marks)
    assert measure(grid) == (height, width, marks)
    assert generator.self_check(grid) == []


@pytest.mark.parametrize("axis,value", [("grid_h", 9), ("grid_w", 24), ("n_marks", 1)])
def test_each_axis_is_observable_when_pinned_alone(generator, axis, value):
    grid = generator.generate(23, 1, **{axis: value})
    observed = dict(zip(("grid_h", "grid_w", "n_marks"), measure(grid)))
    assert observed[axis] == value


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 8), ("grid_h", 19), ("grid_w", 11),
    ("grid_w", 25), ("n_marks", 0), ("n_marks", 7),
])
def test_out_of_domain_axis_is_rejected(generator, axis, value):
    with pytest.raises(ValueError, match=axis):
        generator.generate(17, 0, **{axis: value})


@pytest.mark.parametrize("axis,value", [
    ("grid_h", True), ("grid_h", 12.0), ("grid_h", "12"),
    ("grid_w", False), ("grid_w", 16.5), ("grid_w", "16"),
    ("n_marks", True), ("n_marks", 3.0), ("n_marks", "3"),
])
def test_axis_requires_an_exact_integer(generator, axis, value):
    with pytest.raises(TypeError, match=axis):
        generator.generate(17, 0, **{axis: value})


def test_unknown_axis_is_not_silently_ignored(generator):
    with pytest.raises(ValueError, match="grid_height"):
        generator.generate(17, 0, grid_height=9)


def test_none_pins_preserve_default_semantics(generator):
    assert generator.generate(17, 2) == generator.generate(
        17, 2, grid_h=None, grid_w=None, n_marks=None)


def test_override_provenance_records_the_consumed_axes(generator):
    from puzzle_generators.base import set_ctx_observer

    contexts = []
    set_ctx_observer(contexts.append)
    try:
        generator.generate(17, 0, grid_h=9, grid_w=24, n_marks=6)
    finally:
        set_ctx_observer(None)
    assert contexts[-1].overrides_used() == {"grid_h": 9, "grid_w": 24, "n_marks": 6}


def test_pinned_generation_is_repeatable_and_keeps_frame_colors(generator):
    pins = {"grid_h": 9, "grid_w": 12, "n_marks": 6}
    first = generator.generate(91, 4, **pins)
    assert first == generator.generate(91, 4, **pins)
    assert measure(first) == (9, 12, 6)
    for color in (2, 3, 4, 5, 6, 7):
        assert sum(cell == color for row in first for cell in row) == 1
