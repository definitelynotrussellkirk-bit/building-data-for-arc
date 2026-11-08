"""Focused region-ownership regressions, portable in selected review runtimes."""
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
gen, _, _ = load_selected_generator('6470a9c16f7b', root=ROOT)

def frames(grid):
    result = []
    for color in {v for row in grid for v in row if v}:
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
        r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
        outline = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                   if r in (r1, r2) or c in (c1, c2)}
        if r2 - r1 >= 2 and c2 - c1 >= 2 and cells == outline:
            result.append((color, r1, c1, r2, c2))
    return sorted(result, key=lambda f: (f[3] - f[1] + 1) * (f[4] - f[2] + 1))


def ownership_label(grid):
    nested = frames(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                owner = next((f for f in nested if f[1] < r < f[3] and f[2] < c < f[4]), None)
                if owner:
                    out[r][c] = owner[0]
    return out


def test_normal_draw_exercises_inner_frame_ownership():
    grid = gen.generate(0, 0)
    nested = frames(grid)
    assert len(nested) >= 2, 'normal samples must contain nested hollow frames, not a solid inner bar'
    out = ownership_label(grid)
    inner_color = nested[0][0]
    assert any(v == 0 and out[r][c] == inner_color
               for r, row in enumerate(grid) for c, v in enumerate(row))


def test_self_check_rejects_the_previous_solid_bar_family():
    grid = [[0] * 11 for _ in range(9)]
    for r in range(1, 8):
        for c in range(1, 10):
            if r in (1, 7) or c in (1, 9):
                grid[r][c] = 2
    grid[4][3:8] = [3] * 5
    assert gen.self_check(grid), 'a bar does not demonstrate nested-region ownership'

import pytest


@pytest.mark.parametrize('difficulty', [None, 'easy', 'medium', 'hard'])
@pytest.mark.parametrize('seed', range(8))
def test_generated_family_has_two_distinct_ownership_witnesses(difficulty, seed):
    grid = gen.generate(seed, seed % 3, difficulty=difficulty)
    assert gen.self_check(grid) == []
    nested = frames(grid)
    assert len(nested) == (3 if difficulty == 'hard' else 2)
    out = ownership_label(grid)
    changed_to = {out[r][c] for r, row in enumerate(grid) for c, value in enumerate(row)
                  if value == 0 and out[r][c] != 0}
    assert nested[0][0] in changed_to
    assert nested[-1][0] in changed_to
    assert grid == gen.generate(seed, seed % 3, difficulty=difficulty)


@pytest.mark.parametrize('count,h,w', [(2, 7, 7), (2, 14, 16), (3, 9, 9), (3, 14, 16)])
def test_frame_and_grid_overrides_are_consumed(count, h, w):
    grid = gen.generate(17, 0, n_frames=count, grid_h=h, grid_w=w, frame_h=h, frame_w=w,
                        palette_size=count, n_distinct_colors=count)
    assert (len(grid), len(grid[0])) == (h, w)
    assert gen.self_check(grid) == []
    assert len(frames(grid)) == count
    assert frames(grid)[-1][1:] == (0, 0, h - 1, w - 1)


@pytest.mark.parametrize('palette', ['warm', 'cool', 'default', 'varied'])
def test_palette_alias_and_cardinality_alias(palette):
    grid = gen.generate(5, 0, texture=palette, palette_size=3)
    assert len(frames(grid)) == 3
    assert {v for row in grid for v in row if v} <= set(gen.PALETTES[palette])
    assert grid == gen.generate(5, 0, palette_kind=palette, n_distinct_colors=3)


@pytest.mark.parametrize('overrides', [
    {'grid_h': 6}, {'grid_w': 6}, {'grid_h': 15}, {'grid_w': 17},
    {'n_frames': 3, 'grid_h': 8}, {'frame_h': 6}, {'frame_w': 6},
    {'grid_h': 8, 'frame_h': 9}, {'n_frames': 1}, {'n_frames': 4},
    {'n_frames': 2, 'palette_size': 3}, {'n_distinct_colors': 4},
    {'palette_kind': 'unknown'}, {'texture': 'cool', 'palette_kind': 'warm'},
    {'grid_h': True}, {'frame_w': 7.5}, {'n_frames': '2'},
])
def test_impossible_or_invalid_overrides_rejected(overrides):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(1, 0, **overrides)


def test_self_check_rejects_broken_border_and_invalid_colors():
    grid = gen.generate(0, 0)
    _, r1, c1, _, _ = frames(grid)[0]
    grid[r1][c1] = 0
    assert gen.self_check(grid)
    grid = gen.generate(0, 0)
    grid[0][0] = True
    assert gen.self_check(grid)


@pytest.mark.parametrize('texture', gen.DEGENERATE_TEXTURES)
def test_degenerate_modes_remain_explicit_invalid_examples(texture):
    assert gen.self_check(gen.generate(0, 0, texture=texture))


@pytest.mark.parametrize('outlines', [
    [(1, 1, 7, 9, 2), (3, 3, 3, 5, 3)],
    [(1, 1, 9, 9, 4), (2, 2, 7, 7, 6), (4, 4, 3, 3, 3)],
    [(1, 1, 9, 9, 2), (2, 2, 7, 7, 7), (4, 4, 3, 3, 5)],
])
def test_self_check_accepts_canonical_frame_geometries(outlines):
    grid = [[0] * 11 for _ in range(11)]
    for r0, c0, height, width, color in outlines:
        for r in range(r0, r0 + height):
            for c in range(c0, c0 + width):
                if r in (r0, r0 + height - 1) or c in (c0, c0 + width - 1):
                    grid[r][c] = color
    assert gen.self_check(grid) == []


@pytest.mark.parametrize('overrides', [
    {'unknown_axis': 3}, {'grid_h': '9'}, {'palette_kind': 2}, {'n_frames': []},
    {'texture': 'no_frame', 'grid_h': 9}, {'texture': 'no_frame', 'palette_kind': 'warm'},
    {'texture': 'no_frame', 'n_frames': True},
])
def test_invalid_overrides_are_rejected_before_degenerate_dispatch(overrides):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(0, 0, **overrides)
