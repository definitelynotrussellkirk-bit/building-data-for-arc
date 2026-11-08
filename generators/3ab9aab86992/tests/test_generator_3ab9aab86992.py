"""Task-local regression tests; deliberately independent component extraction."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('reviewed_generator_3ab9', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def objects(grid):
    counts = Counter(v for row in grid for v in row)
    bg = counts.most_common(1)[0][0]
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == bg or (r, c) in seen:
                continue
            todo, cells = [(r, c)], set()
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                cells.add((y, x))
                for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                    if 0 <= yy < h and 0 <= xx < w and (yy, xx) not in seen and grid[yy][xx] == color:
                        seen.add((yy, xx)); todo.append((yy, xx))
            result.append((color, cells))
    return bg, result


def assert_ls(grid, n):
    bg, objs = objects(grid)
    assert len(objs) == n
    orientations = set()
    for color, cells in objs:
        assert len(cells) == 3
        y = min(r for r, c in cells); x = min(c for r, c in cells)
        norm = frozenset((r-y, c-x) for r, c in cells)
        assert max(r for r, c in norm) == max(c for r, c in norm) == 1
        assert norm not in orientations
        orientations.add(norm)
    assert sum(v == bg for row in grid for v in row) > len(grid) ** 2 // 2
    return bg, objs


@pytest.mark.parametrize('size', [5, 7, 9, 11, 13, 15])
@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_requested_counts_are_never_silently_dropped(size, n):
    for seed in range(12):
        grid = gen.generate(seed, 0, canvas_size=size, n_corners=n)
        assert len(grid) == size
        assert_ls(grid, n)
        assert not gen.self_check(grid)


@pytest.mark.parametrize('bg', range(1, 10))
def test_background_override_is_honored(bg):
    grid = gen.generate(19, 0, canvas_size=7, n_corners=4, bg_color=bg)
    assert assert_ls(grid, 4)[0] == bg


@pytest.mark.parametrize('palette_size', [1, 2, 3, 4])
def test_exact_palette_size_with_repeated_color_components(palette_size):
    for seed in range(10):
        grid = gen.generate(seed, 2, canvas_size=5, n_corners=4, palette_size=palette_size)
        bg, objs = assert_ls(grid, 4)
        assert len({color for color, _ in objs}) == palette_size


def test_all_corners_are_real_l_triominoes_not_solid_squares():
    assert_ls(gen.generate(3, 1, texture='all_corners'), 4)


@pytest.mark.parametrize('texture', ['no_corners', 'full_grid'])
def test_explicit_uniform_diagnostics_are_negative_and_not_default(texture):
    grid = gen.generate(3, 1, texture=texture)
    assert gen.self_check(grid)
    assert len({v for row in grid for v in row}) == 1
    assert_ls(gen.generate(3, 1), len(objects(gen.generate(3, 1))[1]))
    assert len(objects(gen.generate(3, 1))[1]) >= 1


@pytest.mark.parametrize('override', [
    {'canvas_size': 4}, {'canvas_size': 6}, {'canvas_size': 17},
    {'canvas_size': True}, {'canvas_size': 7.5},
    {'n_corners': 0}, {'n_corners': 5}, {'n_corners': True},
    {'bg_color': -1}, {'bg_color': 0}, {'bg_color': 10}, {'bg_color': False},
    {'palette_size': 0}, {'palette_size': 5},
    {'n_corners': 1, 'palette_size': 2},
    {'layout': 'not-a-layout'}, {'palette_kind': 'not-a-palette'},
    {'texture': 'not-a-texture'}, {'unused_typo': 3},
    {'texture': 'warm', 'palette_kind': 'cool'},
    {'texture': 'all_corners', 'n_corners': 1},
])
def test_invalid_or_conflicting_overrides_fail_loudly(override):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize('grid', [
    [], [[]], [[1], [1, 2]], [[1, 2, 3]],
    [[8]*6 for _ in range(6)],
    [[8.0]*5 for _ in range(5)], [[True]*5 for _ in range(5)],
    [[10]*5 for _ in range(5)],
    [[2, 2, 8, 8, 8], [2, 2, 8, 8, 8], *[[8]*5 for _ in range(3)]],
    [[2, 8, 8, 8, 8], *[[8]*5 for _ in range(4)]],
    # Two different colors competing for the same TL output corner.
    [[2, 2, 8, 3, 3], [2, 8, 8, 3, 8], *[[8]*5 for _ in range(3)]],
])
def test_validator_rejects_malformed_or_ambiguous_grids(grid):
    assert gen.self_check(grid)


def test_canonical_inputs_accepted_including_zero_repetition_and_touching():
    for line in (REPO/'shared/data/canonical/puzzles.jsonl').open():
        row = json.loads(line)
        if row['task_id'] == gen.TASK_ID:
            for pair in row['train'] + row['test']:
                assert not gen.self_check(pair['input'])
            break
    else:
        pytest.fail('missing canonical task')


@pytest.mark.parametrize('layout', ['scatter', 'clustered', 'separated'])
def test_layouts_keep_requested_count(layout):
    for seed in range(20):
        grid = gen.generate(seed, 3, canvas_size=5, n_corners=4,
                            palette_size=1, layout=layout)
        assert_ls(grid, 4)


def test_seeded_determinism_and_no_global_rng_mutation():
    import random
    random.seed(2026)
    state = random.getstate()
    first = gen.generate(72, 91)
    gen.generate(99, 21)
    assert gen.generate(72, 91) == first
    assert random.getstate() == state


def test_default_support_includes_edges_zero_and_repeated_colors():
    edge = black = repeated = zero_bg = False
    for seed in range(200):
        grid = gen.generate(seed, 0)
        bg, objs = assert_ls(grid, len(objects(grid)[1]))
        assert objs
        colors = [c for c, _ in objs]
        black |= 0 in colors
        zero_bg |= bg == 0
        repeated |= len(colors) > len(set(colors))
        edge |= any(r in (0, len(grid)-1) or c in (0, len(grid)-1)
                    for _, cells in objs for r, c in cells)
    assert edge and black and repeated
    assert not zero_bg  # Racket (mode g) ignores zero; background must be nonzero.


def independent_output(grid):
    bg, objs = objects(grid)
    n = len(grid); k = (n-1)//2
    out = [[bg]*n for _ in range(n)]
    for color, cells in objs:
        r0 = min(r for r, c in cells); c0 = min(c for r, c in cells)
        norm = {(r-r0, c-c0) for r, c in cells}
        missing = next(iter({(0, 0), (0, 1), (1, 0), (1, 1)} - norm))
        bottom, right = 1-missing[0], 1-missing[1]
        r = n-1 if bottom else 0
        c = n-1 if right else 0
        for d in range(k):
            out[r + (-d if bottom else d)][c] = color
            out[r][c + (-d if right else d)] = color
    return out


def test_default_generation_never_returns_an_already_solved_grid():
    for layout in ['scatter', 'clustered', 'separated']:
        for seed in range(100):
            for n in range(1, 5):
                grid = gen.generate(seed, seed, canvas_size=5, n_corners=n, layout=layout)
                assert grid != independent_output(grid), (seed, n, layout)


def test_observable_override_contract_is_exact():
    for n in range(1, 5):
        grid = gen.generate(10, 11, canvas_size=5, bg_color=8, n_corners=n, palette_size=1)
        observed = gen.observe_overrides(grid)
        assert {key: observed[key] for key in ['canvas_size', 'bg_color', 'n_corners', 'palette_size']} == {
            'canvas_size': 5, 'bg_color': 8, 'n_corners': n, 'palette_size': 1}


def test_semantic_hook_and_complete_frame_rival():
    grid = gen.generate(3, 7, n_corners=1)
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES['incomplete_corner_set'](grid)
    assert gen.SEMANTIC_RIVALS['complete_all_corners'](grid) != independent_output(grid)
    assert gen.rule_mirror(grid) == independent_output(grid)


def test_easy_contains_dense_canonical_cardinality():
    assert any(len(objects(gen.generate(seed, 0, difficulty='easy'))[1]) == 4 for seed in range(100))


def test_reference_probe_normalizes_legacy_canonical_forms():
    probe_spec = importlib.util.spec_from_file_location('review_reference_probe', HOME/'workspace/reference_probe.py')
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    pair = {'input': ['12', '34'], 'output': ['56']}
    assert probe.canonical_pairs({'train': [pair], 'test': pair}) == [
        ('train', 0, {'input': [[1, 2], [3, 4]], 'output': [[5, 6]]}),
        ('test', 0, {'input': [[1, 2], [3, 4]], 'output': [[5, 6]]})]
    with pytest.raises(ValueError):
        probe.grid_literal([[True]])
    with pytest.raises(ValueError):
        probe.source_paths(REPO, '../escape')
    assert probe.grid_literal([[10]]) == "'((10))"


def test_zero_background_is_rejected_to_match_racket_mode_semantics():
    grid = [[0]*5 for _ in range(5)]
    grid[0][0] = grid[0][1] = grid[1][0] = 2
    assert gen.self_check(grid)
