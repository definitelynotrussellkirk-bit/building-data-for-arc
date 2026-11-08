"""Portable public contract regressions using independent component geometry.

Run through ``arcpuzzles check 0a7f0faace31 --stage task_tests``.  These probes
read canonical authoring answers and must not be used during a visible solve.
"""
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "0a7f0faace31"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_guide_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def components(grid):
    """Objects use the rule's cardinal, same-color connectivity and scan order."""
    height, width = len(grid), len(grid[0])
    visited = set()
    result = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] in (5, 7) or (row, column) in visited:
                continue
            color = grid[row][column]
            cells, stack = [], [(row, column)]
            visited.add((row, column))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def geometry(grid):
    marks = {(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == 7}
    guide = bbox(marks)
    gr0, gc0, gr1, gc1 = guide
    objects = components(grid)
    eligible = []
    outside = []
    for obj in objects:
        r0, c0, r1, c1 = bbox(obj)
        center = ((r0 + r1) // 2, (c0 + c1) // 2)
        (eligible if gr0 <= center[0] <= gr1 and gc0 <= center[1] <= gc1
         else outside).append(obj)
    assert eligible, "a generated board must have a selected component"
    r0, c0, r1, c1 = bbox(eligible[0])
    output = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    return marks, guide, eligible, outside, output


def declared_incompatibility(overrides):
    for case in getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", ()):
        if isinstance(case, dict):
            if all(key in overrides and (value is None or overrides[key] == value)
                   for key, value in case.items()):
                return True
        elif isinstance(case, (list, tuple)) and set(case) <= overrides.keys():
            return True
    return False


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT))
def test_canonical_components_and_crop(pair):
    assert geometry(pair["input"])[-1] == pair["output"]
    assert gen.self_check(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(12, 24), (24, 12)])
def test_advertised_size_extremes_override_difficulty_defaults(band, height, width):
    grid = gen.generate(731, 0, difficulty=band, grid_h=height, grid_w=width,
                        texture="plain", frame_style="corners")
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("texture", ["plain", "multi_inside", "center_out", "sticks_out"])
@pytest.mark.parametrize("style", ["corners", "two_corners", "dashed", "full"])
def test_frame_style_is_exact_or_declared_incompatible(texture, style):
    overrides = dict(texture=texture, frame_style=style)
    try:
        grid = gen.generate(881, 2, **overrides)
    except ValueError:
        assert declared_incompatibility(overrides), "unexpected joint-axis rejection"
        return
    marks, guide, _, _, _ = geometry(grid)
    r0, c0, r1, c1 = guide
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    perimeter = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                 if r in (r0, r1) or c in (c0, c1)}
    if style == "corners":
        assert marks == corners
    elif style == "two_corners":
        assert len(marks) == 2 and bbox(marks) == guide
    elif style == "full":
        assert marks == perimeter
    else:
        assert corners <= marks <= perimeter
        assert len(marks) > 4, "dashed override reduced to corner-only marks"


@pytest.mark.parametrize("key,value", [
    ("unknown_axis", 3), ("frame_style", "typo"), ("texture", "typo"),
    ("grid_h", 11), ("grid_w", 25), ("grid_h", 13.5), ("grid_w", "14"),
])
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(931, 1, **{key: value})


@pytest.mark.parametrize("texture", ["plain", "multi_inside", "center_out", "sticks_out"])
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_selected_component_crop_is_nonsolid(texture, band):
    for index in range(40):
        grid = gen.generate(1203, index, difficulty=band, texture=texture)
        output = geometry(grid)[-1]
        context = f"seed=1203 sample_index={index} band={band} texture={texture}"
        assert len({value for row in output for value in row}) >= 2, context


@pytest.mark.parametrize("texture", ["multi_inside", "center_out", "sticks_out"])
@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_texture_claim_uses_actual_rule_components(texture, band):
    for index in range(40):
        grid = gen.generate(1203, index, difficulty=band, texture=texture)
        _, guide, eligible, outside, output = geometry(grid)
        r0, c0, r1, c1 = guide
        context = f"seed=1203 sample_index={index} band={band} texture={texture}"
        assert gen.self_check(grid) == [], context
        if texture == "multi_inside":
            assert len(eligible) >= 2, context
        elif texture == "sticks_out":
            assert any(not (r0 <= r <= r1 and c0 <= c <= c1)
                       for r, c in eligible[0]), context
        elif texture == "center_out":
            assert any(any(r0 <= r <= r1 and c0 <= c <= c1 for r, c in obj)
                       for obj in outside), context
