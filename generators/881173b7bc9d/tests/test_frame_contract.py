"""Public sampler contracts and independently supplied canonical examples."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "881173b7bc9d"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
SOURCE = next(p / "generator.py" for p in HERE.parents
              if (p / "generator.py").is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_frame_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


@pytest.mark.parametrize("grid", [
    [[1]], [[0, 0], [0, 0]], [[1, 0, 2], [0, 0, 0], [3, 0, 4]],
    [[-1]], [[10]], [[True]], [[1.0]], [["1"]], [[1, 2], [3]],
])
def test_validator_rejects_impostors_and_invalid_colors(grid):
    assert GEN.self_check(grid), "An input with no lawful frame was accepted"


def test_validator_preserves_every_canonical_input():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == [], pair


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,count", [(7, 1), (7, 5), (18, 1), (18, 5)])
def test_exact_dimension_and_count_endpoints_in_every_band(band, height, count):
    grid = GEN.generate(27, 3, difficulty=band, grid_h=height, n_frames=count)
    assert len(grid) == height
    observed = GEN.observe_overrides(grid)
    assert observed["n_frames"] == count
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("axis", ["grid_h", "n_frames"])
@pytest.mark.parametrize("value", [True, 7.5, "7"])
def test_integer_axes_do_not_coerce_nonintegers(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


def test_unknown_axis_is_not_silently_ignored():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, n_farmes=3)


@pytest.mark.parametrize("phase", range(4))
def test_additional_frames_do_not_attach_to_a_core_border(phase):
    # Phase 2's rightmost core border touches the canvas edge. Appending a
    # same-color frame at the old width would merge two intended components.
    grid = GEN.generate(10, phase, n_frames=5)
    assert GEN.observe_overrides(grid)["n_frames"] == 5
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("kind,colors", [
    ("warm", {0, 2, 4, 6, 8, 9}),
    ("cool", {0, 1, 3, 5, 7, 8}),
])
def test_palette_controls_change_the_returned_grid(kind, colors):
    grid = GEN.generate(13, 1, palette_kind=kind)
    assert {v for row in grid for v in row} == colors
    assert GEN.observe_overrides(grid)["palette_kind"] == kind
    assert GEN.generate(13, 1, texture=kind) == grid


@pytest.mark.parametrize("kind,size", [("default", 5), ("varied", 7)])
def test_random_palette_modes_realize_all_their_colors(kind, size):
    grid = GEN.generate(19, 3, palette_kind=kind)
    assert len({v for row in grid for v in row}) == size
    assert GEN.observe_overrides(grid)["palette_kind"] == kind


@pytest.mark.parametrize("left,right", [(a, b) for a in
    ("default", "warm", "cool", "varied") for b in
    ("default", "warm", "cool", "varied") if a != b])
def test_conflicting_palette_aliases_are_rejected(left, right):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, palette_kind=left, texture=right)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_density_is_effective(band):
    sparse = GEN.generate(71, 1, difficulty=band, density="sparse")
    dense = GEN.generate(71, 1, difficulty=band, density="dense")
    count = lambda g: sum(v != 0 for row in g for v in row)
    assert count(dense) > count(sparse)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_canonical_scale_and_palette_support(band):
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({v for row in p["input"] for v in row}))
                for p in canonical_pairs(TASK, root=ROOT, labeled_only=True)}
    grids = [GEN.generate(100 + i, i, difficulty=band) for i in range(20)]
    assert any((len(g), len(g[0]), len({v for row in g for v in row}))
               in profiles for g in grids)
