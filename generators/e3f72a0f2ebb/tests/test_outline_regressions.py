"""Portable task-domain regressions for the per-component bounding-box frame.

The mirror below is independent of generator helpers.  Canonical labels and
actual Racket execution constrain it; it never supplies generation labels.
"""
from __future__ import annotations

import importlib.util
import json

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK_ID = "e3f72a0f2ebb"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("outline_regression_subject", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def components(grid):
    """Same-color, four-connected components in row-major discovery order."""
    pending = {(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value}
    result = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        stack, cells = [start], {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    stack.append(point)
                    cells.add(point)
        result.append((color, cells))
    return result


def frame(cells):
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return ({(top, c) for c in range(left, right + 1)}
            | {(bottom, c) for c in range(left, right + 1)}
            | {(r, left) for r in range(top, bottom + 1)}
            | {(r, right) for r in range(top, bottom + 1)})


def render_components(grid, groups):
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in groups:
        for r, c in frame(cells):
            result[r][c] = color
    return result


def mirror(grid):
    return render_components(grid, components(grid))


def per_color_rival(grid):
    """Plausible rival: treat all pixels of a color as one object."""
    groups = {}
    for color, cells in components(grid):
        groups.setdefault(color, set()).update(cells)
    return render_components(grid, groups.items())


def scene(*objects):
    grid = [[0] * 12 for _ in range(10)]
    for color, origin, cells in objects:
        for r, c in cells:
            rr, cc = r + origin[0], c + origin[1]
            assert grid[rr][cc] == 0
            grid[rr][cc] = color
    return grid


L_SHAPE = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}
IDENTITY_SHAPES = {
    "singleton": {(0, 0)},
    "horizontal_line": {(0, 0), (0, 1), (0, 2)},
    "vertical_line": {(0, 0), (1, 0), (2, 0)},
    "solid_2x2": {(0, 0), (0, 1), (1, 0), (1, 1)},
    "thin_2x3": {(r, c) for r in range(2) for c in range(3)},
    "hollow_3x3": {(r, c) for r in range(3) for c in range(3)
                    if r in (0, 2) or c in (0, 2)},
}
IDENTITY_SCENES = {
    name: scene((8, (1, 1), cells), (2, (6, 7), L_SHAPE))
    for name, cells in IDENTITY_SHAPES.items()
}
REPEATED_COLOR_SCENE = scene((3, (1, 1), L_SHAPE),
                             (3, (6, 7), L_SHAPE))
# Orthogonally disconnected, diagonally touching same-color objects distinguish
# four- from eight-connectivity without any output overlap.
DIAGONAL_SCENE = scene((4, (1, 1), {(0, 0), (0, 1), (1, 1)}),
                       (4, (3, 3), {(0, 0), (1, 0), (1, 1)}))


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}")
def test_all_canonical_inputs_are_in_validator_domain(pair):
    assert GEN.self_check(pair["input"]) == []
    assert mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("name", sorted(IDENTITY_SCENES))
def test_lawful_identity_components_are_accepted(name):
    grid = IDENTITY_SCENES[name]
    assert GEN.self_check(grid) == []
    output = mirror(grid)
    identity = {(r, c) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value == 8}
    assert all(output[r][c] == 8 for r, c in identity)
    assert {(r, c) for r, row in enumerate(output)
            for c, value in enumerate(row) if value == 8} == identity
    assert output != grid  # The companion still teaches the changing rule.


@pytest.mark.parametrize("name", sorted(IDENTITY_SHAPES))
def test_a_single_lawful_identity_object_is_in_the_rule_domain(name):
    grid = scene((8, (1, 1), IDENTITY_SHAPES[name]))
    assert GEN.self_check(grid) == []
    assert mirror(grid) == grid


def test_solid_rectangle_has_an_interior_to_erase():
    grid = scene((8, (1, 1), {(r, c) for r in range(3) for c in range(3)}))
    assert GEN.self_check(grid) == []
    assert mirror(grid)[2][2] == 0
    assert mirror(grid) != grid


def test_color_grouping_rival_fits_canonical_but_not_repeated_components():
    assert all(per_color_rival(pair["input"]) == pair["output"]
               for pair in CANONICAL)
    assert GEN.self_check(REPEATED_COLOR_SCENE) == []
    assert len(components(REPEATED_COLOR_SCENE)) == 2
    assert per_color_rival(REPEATED_COLOR_SCENE) != mirror(REPEATED_COLOR_SCENE)


@pytest.mark.parametrize("band,index", [("easy", 610), ("medium", 26), ("hard", 140)])
def test_reproduced_generated_frames_do_not_interfere(band, index):
    # Baseline seed 503 lets legal separated polyomino pixels acquire
    # colliding frames.  Test the public generation outcome, not a helper.
    grid = GEN.generate(503, index, difficulty=band)
    assert GEN.self_check(grid, difficulty=band) == []
    groups = components(grid)
    for i, (_, cells) in enumerate(groups):
        for _, other_cells in groups[i + 1:]:
            assert not frame(cells) & frame(other_cells)
            assert not frame(cells) & other_cells
            assert not frame(other_cells) & cells


def test_saved_frame_collision_is_excluded_from_admitted_generation_domain():
    path = SOURCE.parent / "counterexamples" / "baseline-frame-interference-seed503-index26.json"
    witness = json.loads(path.read_text())
    assert witness["generator_sha256"] == "fed11c7fd24ea1f929b98322752a5e1a4345dcfcf8406285a5db5d93eb4bb85b"
    groups = components(witness["input"])
    assert frame(groups[0][1]) & frame(groups[1][1]) == {(4, 6)}
    assert GEN.self_check(witness["input"])


def test_canonical_rule_and_independent_mirror_match_actual_racket():
    inputs = [pair["input"] for pair in CANONICAL]
    inputs.extend(IDENTITY_SCENES.values())
    inputs.extend([REPEATED_COLOR_SCENE, DIAGONAL_SCENE])
    inputs.extend(GEN.generate(119, index, difficulty=band)
                  for band in ("easy", "medium", "hard") for index in range(3))
    result = Catalog(root=ROOT).apply(TASK_ID, inputs, timeout=120)
    assert result["executed_rule_hash"] == "8d3a7f6a327b"
    assert result["rule_hash_matches_catalog"] is True
    assert len(result["results"]) == len(inputs)
    for grid, row in zip(inputs, result["results"], strict=True):
        assert row["output"] == mirror(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(7, 8), (7, 18), (18, 8), (18, 18)])
def test_all_legal_object_color_counts_at_dimension_extremes(band, height, width):
    """Small grids and cross-band overrides must still realize every object."""
    for count in (2, 3, 4):
        for colors in range(1, count + 1):
            requested = {"grid_h": height, "grid_w": width,
                         "n_blobs": count, "n_distinct_colors": colors}
            for index in (0, 1, 2, 3):
                grid = GEN.generate(71, index, difficulty=band, **requested)
                groups = components(grid)
                observed = {"grid_h": len(grid), "grid_w": len(grid[0]),
                            "n_blobs": len(groups),
                            "n_distinct_colors": len({c for c, _ in groups})}
                assert observed == requested
                assert GEN.observe_overrides(grid) == observed
                assert GEN.self_check(grid, difficulty=band) == []
                assert grid == GEN.generate(71, index, difficulty=band, **requested)
                for i, (_, cells) in enumerate(groups):
                    for _, other_cells in groups[i + 1:]:
                        assert not frame(cells) & frame(other_cells)
                        assert not frame(cells) & other_cells
                        assert not frame(other_cells) & cells


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_axis_can_be_requested_independently_in_every_schedule_phase(band):
    axes = {"grid_h": (7, 18), "grid_w": (8, 18),
            "n_blobs": (2, 3, 4), "n_distinct_colors": (1, 2, 3, 4)}
    for key, values in axes.items():
        for value in values:
            for index in range(4):
                grid = GEN.generate(92, index, difficulty=band, **{key: value})
                groups = components(grid)
                observed = {"grid_h": len(grid), "grid_w": len(grid[0]),
                            "n_blobs": len(groups),
                            "n_distinct_colors": len({c for c, _ in groups})}
                assert observed[key] == value
                assert GEN.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("key,value", [
    ("palette_kind", "warm"), ("anchor_corner", True),
    ("asymmetry_force", True), ("palette_size", 2),
    ("position_bias", "fixed"), ("texture", "single_blob"),
    ("unknown_control", 1),
])
def test_removed_and_unknown_controls_fail_explicitly(key, value):
    assert key not in GEN.AXES
    with pytest.raises(ValueError):
        GEN.generate(41, 0, **{key: value})


@pytest.mark.parametrize("key,value", [
    ("grid_h", 6), ("grid_h", 19), ("grid_h", 10.0), ("grid_h", "10"),
    ("grid_w", 7), ("grid_w", 19), ("grid_w", 10.0), ("grid_w", "10"),
    ("n_blobs", 1), ("n_blobs", 5), ("n_blobs", 2.0), ("n_blobs", "2"),
    ("n_distinct_colors", 0), ("n_distinct_colors", 5),
    ("n_distinct_colors", 1.0), ("n_distinct_colors", "1"),
    ("n_distinct_colors", True),
])
def test_exact_integer_controls_reject_invalid_values(key, value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(41, 0, **{key: value})


@pytest.mark.parametrize("count,colors", [(2, 3), (2, 4), (3, 4)])
def test_more_distinct_colors_than_objects_is_explicitly_incompatible(count, colors):
    with pytest.raises(ValueError):
        GEN.generate(41, 0, n_blobs=count, n_distinct_colors=colors)

