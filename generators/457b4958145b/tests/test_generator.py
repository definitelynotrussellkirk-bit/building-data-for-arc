"""Focused public regressions for hub-ordered component packing."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

# Bind imports to this test's own checkout/runtime, including relocated copies.
for ancestor in Path(__file__).resolve().parents:
    for runtime in (ancestor / "shared" / "runtime", ancestor):
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    else:
        continue
    break

from reviewer_support import canonical_pairs, find_root

TASK_ID = "457b4958145b"
BANDS = (None, "easy", "medium", "hard")


@pytest.fixture(scope="module")
def generator():
    root = find_root(__file__)
    paths = (root / "generators" / TASK_ID / "generator.py",
             root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
    path = next(path for path in paths if path.is_file())
    spec = importlib.util.spec_from_file_location("hub_order_regression_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def components(grid):
    """Measure observable monochrome 4-connected objects independently."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row)
                 if color not in (0, 9)}
    result = []
    while remaining:
        first = remaining.pop()
        color = grid[first[0]][first[1]]
        obj, queue = {first}, [first]
        while queue:
            r, c = queue.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    obj.add(neighbor)
                    queue.append(neighbor)
        result.append(obj)
    return result


def assert_valid_generated_scene(generator, grid, *, n_components=None, palette=None):
    assert grid and grid[0]
    assert len({len(row) for row in grid}) == 1
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    colors = {value for row in grid for value in row}
    assert {0, 9} <= colors
    objects = components(grid)
    assert len(objects) in (3, 4, 5)
    if n_components is not None:
        assert len(objects) == n_components
    if palette is not None:
        assert len(colors) == palette
    assert generator.self_check(grid) == []
    # The fixed rule extends bbox-height-2 crops downward, clipping to the grid.
    # Every generated crop must retain three rows before hconcat packs it.
    for obj in objects:
        top = min(r for r, _ in obj)
        bottom = max(r for r, _ in obj)
        bbox_height = bottom - top + 1
        padded_bottom = min(len(grid) - 1, bottom + (bbox_height == 2))
        assert padded_bottom - top + 1 == 3, sorted(obj)


def test_all_canonical_inputs_are_accepted_without_mutation(generator):
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    assert any(sum(value == 9 for row in pair["input"] for value in row) == 4
               for pair in pairs)
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert generator.self_check(grid) == [], (pair["split"], pair["pair_index"])
        assert grid == snapshot


@pytest.mark.parametrize("grid", [None, [], [[]], [[0, 9], [1]],
                                      [[0, "9"]], [[0, 1.5]], [[0, True]],
                                      [[0, -1]], [[0, 10]], [[0, {}]],
                                      [0], "09", {"grid": [[0, 9]]}])
def test_malformed_grids_return_diagnostics_without_mutation(generator, grid):
    snapshot = copy.deepcopy(grid)
    errors = generator.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) and error for error in errors)
    assert grid == snapshot


def test_palette_override_counts_background_and_hub_and_adapts_objects(generator):
    for alias in ("palette_size", "n_distinct_colors"):
        grid = generator.generate(13, 0, difficulty="easy", **{alias: 7})
        assert_valid_generated_scene(generator, grid, n_components=5, palette=7)


@pytest.mark.parametrize("axis,value", [("grid_h", value) for value in range(10, 17)]
                         + [("grid_w", value) for value in range(12, 19)]
                         + [("n_components", value) for value in range(3, 6)])
def test_advertised_bounds_are_allowed_in_every_band(generator, axis, value):
    for band in BANDS:
        grid = generator.generate(23, 0, difficulty=band, **{axis: value})
        assert_valid_generated_scene(generator, grid,
                                     n_components=value if axis == "n_components" else None)
        if axis == "grid_h":
            assert len(grid) == value
        elif axis == "grid_w":
            assert len(grid[0]) == value


@pytest.mark.parametrize("axis,value", [("palette_kind", "default"),
                                          ("texture", "default"),
                                          ("position_bias", "hub_with_angular_components"),
                                          ("density", "sparse")])
def test_removed_noop_axes_are_rejected(generator, axis, value):
    with pytest.raises(ValueError, match=axis):
        generator.generate(0, 0, **{axis: value})


@pytest.mark.parametrize("sample_index", [True, 1.0, "1", -1, None])
def test_sample_index_requires_nonnegative_python_integer(generator, sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        generator.generate(0, sample_index)


@pytest.mark.parametrize("seed", [True, 1.0, "1", None])
def test_seed_requires_python_integer(generator, seed):
    with pytest.raises(ValueError, match="seed"):
        generator.generate(seed, 0)


@pytest.mark.parametrize("axis,low,high", [("grid_h", 10, 16), ("grid_w", 12, 18),
                                           ("n_components", 3, 5),
                                           ("palette_size", 3, 7),
                                           ("n_distinct_colors", 3, 7)])
def test_invalid_axis_scalars_are_rejected(generator, axis, low, high):
    for value in (True, float(low), str(low), low - 1, high + 1):
        with pytest.raises(ValueError, match=axis):
            generator.generate(0, 0, **{axis: value})


def test_none_override_keeps_axis_unpinned(generator):
    grid = generator.generate(97, 1, grid_h=None, grid_w=None, n_components=None,
                              palette_size=None, n_distinct_colors=None)
    assert_valid_generated_scene(generator, grid)
    assert grid == generator.generate(97, 1)


@pytest.mark.parametrize("alias", ["palette_size", "n_distinct_colors"])
def test_total_palette_and_component_count_are_independent_when_compatible(generator, alias):
    for band in BANDS:
        for n in range(3, 6):
            for palette in range(3, n + 3):
                overrides = {"grid_h": 10, "grid_w": 12,
                             "n_components": n, alias: palette}
                snapshot = dict(overrides)
                grid = generator.generate(191, palette, difficulty=band, **overrides)
                assert overrides == snapshot
                assert_valid_generated_scene(generator, grid, n_components=n, palette=palette)


def test_palette_aliases_agree_on_pixels(generator):
    for palette in range(3, 8):
        first = generator.generate(101, 2, palette_size=palette)
        second = generator.generate(101, 2, n_distinct_colors=palette)
        both = generator.generate(101, 2, palette_size=palette, n_distinct_colors=palette)
        assert first == second == both


def test_incompatible_aliases_name_both_axes(generator):
    with pytest.raises(ValueError) as exc:
        generator.generate(0, 0, palette_size=3, n_distinct_colors=4)
    message = str(exc.value)
    assert "palette_size" in message and "n_distinct_colors" in message
    assert any(word in message.lower() for word in ("incompat", "conflict", "agree"))
    assert set(exc.value.incompatible_axes) == {"palette_size", "n_distinct_colors"}


@pytest.mark.parametrize("alias", ["palette_size", "n_distinct_colors"])
def test_pinned_palette_cannot_exceed_object_colors_plus_background_and_hub(generator, alias):
    with pytest.raises(ValueError) as exc:
        generator.generate(0, 0, n_components=3, **{alias: 6})
    message = str(exc.value)
    assert "n_components" in message and alias in message
    assert any(word in message.lower() for word in ("incompat", "conflict", "exceed"))
    assert set(exc.value.incompatible_axes) == {"n_components", alias}


def test_self_check_counts_components_instead_of_distinct_object_colors(generator):
    grid = generator.generate(37, 1, n_components=3, palette_size=3)
    assert len(components(grid)) == 3
    assert len({value for row in grid for value in row} - {0, 9}) == 1
    assert generator.self_check(grid) == []
    for r, c in components(grid)[0]:
        grid[r][c] = 0
    assert len(components(grid)) == 2
    errors = generator.self_check(grid)
    assert errors and any("component" in error.lower() or "object" in error.lower()
                          for error in errors)


def test_default_samples_are_deterministic_and_have_three_row_rule_crops(generator):
    for band in BANDS:
        for seed, index in ((0, 0), (7, 1), (29, 3), (101, 11), (1009, 19)):
            first = generator.generate(seed, index, difficulty=band)
            snapshot = copy.deepcopy(first)
            assert_valid_generated_scene(generator, first)
            assert first == snapshot
            second = generator.generate(seed, index, difficulty=band)
            assert first == second
            second[0][0] = (second[0][0] + 1) % 10
            assert first == snapshot


def test_difficulty_changes_default_object_count_distribution(generator):
    easy = [len(components(generator.generate(seed, 0, difficulty="easy"))) for seed in range(40)]
    hard = [len(components(generator.generate(seed, 0, difficulty="hard"))) for seed in range(40)]
    assert sum(easy) < sum(hard)
    assert set(easy) <= {3, 4, 5} and set(hard) <= {3, 4, 5}
