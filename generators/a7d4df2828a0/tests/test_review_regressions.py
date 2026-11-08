"""Task-local review regressions. Run from an ordinary ARCpuzzles checkout.

No Python label producer is used by the generator. The geometry here is an
independent, test-only way to detect an out-of-canvas transformed footprint.
"""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / 'shared/runtime'))
SPEC = importlib.util.spec_from_file_location('a7d4df2828a0_under_test', HOME / 'generator.py')
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def grid(cells=((2, 2), (3, 2), (4, 2), (4, 3)), *, code=3, color=7, h=9, w=9):
    g = [[0] * w for _ in range(h)]
    g[0][0] = code
    for r, c in cells:
        g[r][c] = color
    return g


def motif(g):
    return {(r, c) for r, row in enumerate(g) for c, value in enumerate(row)
            if value != 0 and (r, c) != (0, 0)}


def shape(g):
    cells = motif(g)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def assert_fits(g):
    cells = motif(g)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    sh = max(r for r, _ in cells) - r0 + 1
    sw = max(c for _, c in cells) - c0 + 1
    oh, ow = (sw, sh) if g[0][0] == 1 else (sh, sw)
    assert r0 + oh <= len(g), (g[0][0], r0, oh, len(g))
    assert c0 + ow <= len(g[0]), (g[0][0], c0, ow, len(g[0]))


def test_known_legacy_clipping_input_is_rejected():
    # Version 2.0.1: easy, seed=67, sample_index=67. Racket paints 2 of 4 cells.
    g = grid(((5, 8), (6, 6), (6, 7), (6, 8)), code=1, color=5, h=7, w=9)
    assert GEN.self_check(g), 'clipping was silently admitted'


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_default_sweep_never_clips_and_is_deterministic(band):
    for seed in range(1000):
        g = GEN.generate(seed, seed, difficulty=band)
        assert_fits(g)
        assert GEN.self_check(g) == []
        if seed < 10:
            assert g == GEN.generate(seed, seed, difficulty=band)


def test_canonical_T_shape_is_in_generator_support():
    # Train[1] is a T; it is mirror-symmetric but its selected 90-degree turn moves it.
    target = frozenset({(0, 1), (1, 0), (1, 1), (1, 2)})
    observed = {shape(GEN.generate(seed, seed, difficulty='medium',
                                 grid_h=9, grid_w=9, motif_size=4, code=1))
                for seed in range(256)}
    assert target in observed


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_full_declared_axis_product_is_realized(band):
    for h, w, size, code in itertools.product(range(7, 15), range(7, 15), range(3, 7), range(1, 5)):
        requested = dict(grid_h=h, grid_w=w, motif_size=size, code=code)
        g = GEN.generate(101, 17, difficulty=band, **requested)
        assert (len(g), len(g[0]), len(motif(g)), g[0][0]) == (h, w, size, code)
        assert GEN.observe_overrides(g) == requested
        assert_fits(g)
        assert GEN.self_check(g) == []


def test_unknown_axis_is_not_silently_ignored():
    with pytest.raises(ValueError, match='unknown override'):
        GEN.generate(0, 0, typo_axis=8)


@pytest.mark.parametrize('axis,value', [('grid_h', 6), ('grid_w', 15), ('motif_size', 2),
                                       ('code', 5), ('code', True), ('grid_h', 9.5)])
def test_invalid_override_is_rejected(axis, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{axis: value})


@pytest.mark.parametrize('bad', [[], [[]], [[0], []], None, [[True] * 8 for _ in range(8)],
                                [[3] * 8 for _ in range(8)]])
def test_malformed_and_degenerate_grids_rejected_without_crashing(bad):
    assert GEN.self_check(bad)


@pytest.mark.parametrize('mutation', ['extra_color', 'same_as_control', 'disconnect',
                                     'too_many', 'invalid_color', 'touch_control', 'symmetric'])
def test_grammar_rejects_semantic_impostors(mutation):
    g = grid()
    if mutation == 'extra_color':
        g[3][2] = 5
    elif mutation == 'same_as_control':
        g = grid(color=3)
    elif mutation == 'disconnect':
        g[3][2] = 0
        g[7][7] = 7
    elif mutation == 'too_many':
        g = grid(tuple((2, c) for c in range(1, 8)))
    elif mutation == 'invalid_color':
        g[3][2] = 11
    elif mutation == 'touch_control':
        g = grid(((0, 1), (1, 1), (2, 1), (2, 2)))
    elif mutation == 'symmetric':
        g = grid(((2, 2), (2, 3), (3, 2), (3, 3)))
    assert GEN.self_check(g), mutation


def test_all_canonical_inputs_accepted_without_mutation():
    task = next(json.loads(line) for line in (REPO / 'shared/data/canonical/puzzles.jsonl').open()
                if json.loads(line)['task_id'] == GEN.TASK_ID)
    for pair in task['train'] + task['test']:
        g = pair['input']
        saved = copy.deepcopy(g)
        assert GEN.self_check(g) == []
        assert GEN.strict_canonical_like(g) == []
        assert g == saved


def test_source_pin_and_branch_contract():
    assert GEN.RULE_HASH == '089b88c1e5ad'
    assert set(GEN.BRANCH_WITNESSES) == set(GEN.SEMANTIC_WITNESSES)
    for code in range(1, 5):
        g = GEN.generate(17, 4, code=code)
        assert GEN.SEMANTIC_WITNESSES[f'code_{code}'](g)


def test_default_support_reaches_all_canvas_edges():
    touched = set()
    for seed in range(500):
        g = GEN.generate(seed, seed, difficulty='medium')
        cells = motif(g)
        if any(r == 0 for r, c in cells): touched.add('top')
        if any(c == 0 for r, c in cells): touched.add('left')
        if any(r == len(g)-1 for r, c in cells): touched.add('bottom')
        if any(c == len(g[0])-1 for r, c in cells): touched.add('right')
    assert touched == {'top', 'left', 'bottom', 'right'}
