"""Portable regressions for border-object semantics and exact sampling controls."""
from __future__ import annotations

import copy
import itertools

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from puzzle_generators.helpers.selfcheck import components

TASK = "9b37d4bbfb7e"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def grid_with(cells, h=6, w=7):
    grid = [[0] * w for _ in range(h)]
    for color, points in cells:
        for r, c in points:
            grid[r][c] = color
    return grid


def border(comp, grid):
    return any(r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1)
               for r, c in comp["cells"])


def expected_output(grid):
    """Test oracle; independently cross-checked against Racket by the retained probe."""
    out = copy.deepcopy(grid)
    for comp in components(grid, same_color=True, connectivity=4):
        if border(comp, grid):
            for r, c in comp["cells"]:
                out[r][c] = 0
    return out


def test_validator_keeps_cardinally_touching_colors_separate():
    grid = grid_with([(2, [(0, 2)]), (3, [(1, 2), (2, 2)])])
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("bad", [[], [[]], [[0], [0, 0]], [[0, True]],
                                      [[0, 1.0]], [[0, -1]], [[0, 10]], None])
def test_validator_explains_malformed_inputs(bad):
    reasons = GEN.self_check(bad)
    assert isinstance(reasons, list) and reasons


def test_canonical_pairs_are_accepted_and_test_oracle_matches():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert expected_output(pair["input"]) == pair["output"]


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="[Uu]nknown"):
        GEN.generate(17, 0, n_blbos=5)


@pytest.mark.parametrize("name", ["seed", "sample_index", "grid_h", "grid_w",
                                  "n_blobs", "n_distinct_colors", "palette_size"])
@pytest.mark.parametrize("value", [True, False, 1.0, "1", -1])
def test_invalid_scalar_controls_are_rejected(name, value):
    args = {"seed": 17, "sample_index": 0}
    args[name] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**args)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("count,colors", [(n, k) for n in range(2, 7)
                                         for k in range(2, n + 1)])
def test_smallest_canvas_honors_actual_components_and_colors(band, count, colors):
    grid = GEN.generate(19, 3, difficulty=band, grid_h=6, grid_w=7,
                        n_blobs=count, n_distinct_colors=colors)
    assert len(grid) == 6 and all(len(row) == 7 for row in grid)
    assert len(components(grid, same_color=True, connectivity=4)) == count
    assert len({v for row in grid for v in row} - {0}) == colors
    assert GEN.self_check(grid, difficulty=band) == []
    observed = GEN.observe_overrides(grid)
    assert observed["n_blobs"] == count
    assert observed["n_distinct_colors"] == colors


@pytest.mark.parametrize("colors", range(2, 7))
def test_palette_alias_has_exact_pixel_observation(colors):
    grid = GEN.generate(29, 0, n_blobs=6, palette_size=colors)
    assert GEN.observe_overrides(grid)["palette_size"] == colors


@pytest.mark.parametrize("overrides,axes", [
    ({"n_blobs": 2, "n_distinct_colors": 3}, {"n_blobs", "n_distinct_colors"}),
    ({"n_blobs": 2, "palette_size": 3}, {"n_blobs", "palette_size"}),
    ({"palette_size": 2, "n_distinct_colors": 3}, {"palette_size", "n_distinct_colors"}),
    ({"texture": "warm", "palette_kind": "cool"}, {"texture", "palette_kind"}),
])
def test_incompatible_controls_name_the_conflicting_axes(overrides, axes):
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, **overrides)
    assert axes <= set(caught.value.incompatible_axes)


@pytest.mark.parametrize("kind", ["default", "warm", "cool", "varied"])
def test_palette_and_texture_aliases_agree(kind):
    assert GEN.generate(23, 2, texture=kind) == GEN.generate(23, 2, palette_kind=kind)
    grid = GEN.generate(23, 2, texture=kind, palette_kind=kind)
    assert GEN.self_check(grid) == []


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    assert hasattr(GEN, "CANONICAL_SHORTCUTS")
    assert len(GEN.CANONICAL_SHORTCUTS) >= 6
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in canonical_pairs(TASK, root=ROOT):
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_defaults_retain_the_canonical_three_object_structure(band):
    signatures = []
    for seed in range(12):
        grid = GEN.generate(seed, 0, difficulty=band)
        comps = components(grid, same_color=True, connectivity=4)
        signatures.append((len(comps), len({v for row in grid for v in row} - {0}),
                           sum(not border(comp, grid) for comp in comps),
                           sum(len(comp["cells"]) == 1 for comp in comps)))
    assert (3, 3, 1, 0) in signatures


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_consecutive_four_demo_lessons_survive_every_query_holdout(band):
    assert getattr(GEN, "EXAMPLES_NEEDED", None) == 4
    assert getattr(GEN, "LESSON_SCHEDULE_PERIOD", None) == 4
    for seed, start in itertools.product([0, 17, 104729], range(4)):
        grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(5)]
        outputs = [expected_output(g) for g in grids]
        for name, rival in GEN.LESSON_COMPETITORS.items():
            matches = [rival(g) == out for g, out in zip(grids, outputs)]
            for query in range(5):
                assert not all(matches[i] for i in range(5) if i != query), (seed, start, name, query)


def test_generation_is_deterministic_and_does_not_mutate_overrides():
    overrides = {"grid_h": 7, "grid_w": 8, "n_blobs": 5,
                 "n_distinct_colors": 3, "texture": "cool"}
    original = dict(overrides)
    first = GEN.generate(7, 4, **overrides)
    assert first == GEN.generate(7, 4, **overrides)
    assert overrides == original

