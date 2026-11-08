"""Focused source, adversarial and protected-label checks for c8ab3fc199b1.

These test only the proposed source; only the owner's native approval can admit it.
"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

_HOME = Path(__file__).resolve().parents[1]
_PARAM = _HOME / 'workspace' / 'parametric'
sys.path.insert(0, str(_PARAM))
sys.path.insert(0, str(_HOME.parents[1] / 'shared' / 'runtime'))


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _import('c8ab_base_under_test', _HOME / 'generator.py')
param = _import('c8ab_param_under_test', _PARAM / 'prototype.py')
attack = _import('c8ab_attack_under_test', _PARAM / 'adversarial_probe.py')


def _controlled(areas=(11, 7, 9), *, docks=(0, 6, 12)):
    """Fixed 12x18 / 4x3 bounding boxes, varied occupied-area intermediate."""
    grid = [[0] * 18 for _ in range(12)]
    for c, color in zip(docks, (2, 3, 4)):
        grid[0][c] = color
    for j, (color, area) in enumerate(zip((2, 3, 4), areas)):
        cells = {(r, 0) for r in range(4)} | {(0, c) for c in range(3)}
        for cell in ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)):
            if len(cells) < area: cells.add(cell)
        assert len(cells) == area
        for r, c in cells:
            grid[3 + r][1 + j * 6 + c] = color
    return grid


def _eval_racket(prog, grid, bridge):
    from puzzle_generators.rule_wrap import wrap_rule
    text = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    return bridge.eval_text(f'({wrap_rule(prog)} {text})')


@pytest.mark.parametrize('seed', range(24))
def test_base_is_diverse_and_legitimate(seed):
    g = base.generate(seed, 0, difficulty='medium')
    assert base.self_check(g) == []
    assert base.generate(seed, 0, difficulty='medium') == g
    assert 6 <= len(g) <= 14 and 10 <= len(g[0]) <= 16
    assert 2 <= sum(bool(v) for v in g[0]) <= 4


@pytest.mark.parametrize('n', (2, 3, 4))
def test_base_exact_count_and_size_edges(n):
    for height,width in ((6, 10), (14, 16)):
        g = base.generate(307 + n, n, grid_h=height, grid_w=width,
                          n_markers=n, n_distinct_colors=n, palette_size=n)
        assert len(g) == height and len(g[0]) == width
        assert base.self_check(g) == []
        assert sum(bool(v) for v in g[0]) == n


def test_base_invalid_and_bad_overrides():
    with pytest.raises((ValueError, TypeError)):
        base.generate(0, 0, n_markers=True)
    with pytest.raises((ValueError, TypeError)):
        base.generate(0, 0, palette_size=2, n_markers=3)
    for name in ('no_markers', 'marker_without_body'):
        assert base.self_check(base.generate(0,0,texture=name)), name
    # An unmarked body component is a lawful distractor: the Racket rule
    # selects only marked colors. Treat it as valid, not a false-positive veto.
    assert base.self_check(base.generate(0,0,texture='body_without_marker')) == []
    g = base.generate(9,0)
    g[0][0] = True
    assert base.self_check(g)


@pytest.mark.parametrize('seed', (0, 17, 23, 83))
@pytest.mark.parametrize('demos', (2, 3, 6))
def test_episode_claims_and_matched_inputs(seed,demos):
    variants = [param.generate(seed, {'dock_mode':mode}, demos, 4)
                for mode in param.MODES]
    assert [row['input'] for row in variants[0]['train']] == [
        row['input'] for row in variants[1]['train']]
    assert [row['input'] for row in variants[0]['test']] == [
        row['input'] for row in variants[1]['test']]
    for mode,episode in zip(param.MODES,variants):
        assert len(episode['train']) == demos and len(episode['test']) == 4
        assert episode['program_solution'] == param.program({'dock_mode':mode})
        unique = [json.dumps(row['input']) for row in episode['train'] + episode['test']]
        assert len(unique) == len(set(unique))
        for row in episode['train'] + episode['test']:
            assert row['output'] == param.transform(row['input'], {'dock_mode':mode})
    assert any(a['output'] != b['output'] for a,b in
               zip(variants[0]['train'],variants[1]['train']))


def test_crossed_controls_catch_bbox_height_fixed_rank_and_dock_shortcuts():
    small = _controlled((11,7,9))
    reverse = _controlled((7,11,9))
    shifted = _controlled((11,7,9), docks=(1,7,13))
    a={'dock_mode':'area_queue'}
    for g in (small,reverse,shifted):
        recs = param._extract(g)
        assert [r['height'] for r in recs] == [4,4,4]
        assert [r['bbox_area'] for r in recs] == [12,12,12]
    assert [r['area'] for r in param._extract(small)] == [11,7,9]
    assert [r['area'] for r in param._extract(reverse)] == [7,11,9]
    assert param.transform(small,a) != param.transform(reverse,a)
    assert param.transform(small,a) != param.transform(shifted,a)
    assert param.transform(small,a) != param.transform(small,{'dock_mode':'matching_color'})
    # Every fitted bbox/height/fixed permutation would miss at least one.
    for shortcut in ('height','bbox_area','width','matched','reversed'):
        assert any(attack._ranked(g,shortcut) != param.transform(g,a)
                   for g in (small,reverse)), shortcut


def test_tie_breaker_and_type_rejections():
    grid = _controlled((9,9,7))
    records = param._extract(grid)
    assert records[0]['area'] == records[1]['area'] == 9
    target = param.transform(grid, {'dock_mode':'area_queue'})
    # 2 and 3 stay left-to-right in equal-area tie; the smaller 4 stays last.
    assert target[0][0] == 2 and target[0][6] == 3
    for invalid in ({}, {'dock_mode':'other'}, {'dock_mode':False},
                    {'dock_mode':'area_queue','private_answer':1}):
        with pytest.raises(ValueError): param.program(invalid)
    with pytest.raises((TypeError,ValueError)): param.generate(True, {'dock_mode':'area_queue'},2,4)
    with pytest.raises((TypeError,ValueError)): param.generate(1, {'dock_mode':'area_queue'},1,4)
    with pytest.raises((TypeError,ValueError)): param.generate(1, {'dock_mode':'area_queue'},2,5)
    malformed=copy.deepcopy(grid);malformed[2][0]=True
    with pytest.raises(ValueError): param.transform(malformed, {'dock_mode':'area_queue'})
    malformed=copy.deepcopy(grid);malformed[2].append(0)
    with pytest.raises(ValueError): param._extract(malformed)
    malformed=copy.deepcopy(grid);malformed[0][1]=2
    with pytest.raises(ValueError): param._extract(malformed)


def test_minimum_lesson_defeats_finite_rivals():
    report=attack.audit_seeds(list(range(48)), demos=2)
    assert all(s['underidentified_rival_seed_pairs']==0 for s in report['settings'].values())


def test_protected_racket_parity_on_cross_controls_and_large_queries():
    from arc_repl.racket_bridge import RacketBridge
    with_racket = RacketBridge()
    try:
        scenes = [_controlled((11,7,9)), _controlled((7,11,9))]
        episode=param.generate(17,{'dock_mode':'area_queue'},2,4)
        scenes += [episode['test'][i]['input'] for i in range(4)]
        for mode in param.MODES:
            settings={'dock_mode':mode}
            for scene in scenes:
                assert _eval_racket(param.program(settings),scene,with_racket) == param.transform(scene, settings)
    finally:
        with_racket.close()
