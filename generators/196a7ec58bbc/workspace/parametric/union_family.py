"""Disjoint union of four accepted quadrant rules and marker normalization.

The retained native_family supplies the four unchanged programs and scene
construction. All five choices share input draws. A unique color-9 corner marker
is inert under the old rules and sets orientation under marker_to_top_left.
"""
from __future__ import annotations
from copy import deepcopy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('quadrant_union_retained', HERE/'native_family.py')
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
RULES = ('whole_clockwise', 'whole_counterclockwise',
         'largest_component_clockwise', 'largest_component_counterclockwise',
         'marker_to_top_left')
DEFAULT = {'rule': 'whole_clockwise'}
SETTINGS = tuple({'rule': rule} for rule in RULES)


def normalize_settings(settings=None):
    if settings is None:
        return dict(DEFAULT)
    if type(settings) is not dict:
        raise ValueError('settings must be a dictionary')
    # Preserve the prior explicitly selected settings API.
    if not set(settings) - {'source_mode', 'handedness'}:
        old = _base.normalize_settings(settings)
        return {'rule': old['source_mode']+'_'+old['handedness']}
    if set(settings) != {'rule'} or type(settings['rule']) is not str or settings['rule'] not in RULES:
        raise ValueError('settings must name one declared rule')
    return dict(settings)


def _legacy(rule):
    source, hand = rule.rsplit('_', 1)
    return {'source_mode': source, 'handedness': hand}


def program(settings=None):
    rule = normalize_settings(settings)['rule']
    if rule == 'marker_to_top_left':
        return (HERE/'marker_to_top_left.rkt').read_text()
    return _base.program(_legacy(rule))


def python_apply(grid, settings=None):
    rule = normalize_settings(settings)['rule']
    if rule != 'marker_to_top_left':
        return _base.python_apply(grid, _legacy(rule))
    source = _base._square(grid)
    n = len(source)
    corners = ((0,0),(0,n-1),(n-1,n-1),(n-1,0))
    hits = [i for i,(r,c) in enumerate(corners) if source[r][c] == 9]
    if len(hits) != 1 or sum(v == 9 for row in source for v in row) != 1:
        raise ValueError('expected one unique color-9 corner marker')
    for _ in range((-hits[0]) % 4):
        source = _base._old._rotate_cw(source)
    return _base._old.solve(source, handedness='clockwise')


def _scene(seed, slot):
    g = _base._scene(seed, slot)
    # Keep all old object/color relationships while reserving the marker color.
    if any(9 in row for row in g):
        used = {v for row in g for v in row}
        replacement = next(v for v in range(1,9) if v not in used)
        g = [[replacement if v == 9 else v for v in row] for row in g]
    selected = {tuple(p) for p in _base.analyze_scene(g)['selected']['cells']}
    n = len(g)
    corners = ((0,0),(0,n-1),(n-1,n-1),(n-1,0))
    available = [i for i,p in enumerate(corners) if p not in selected]
    if not available:
        raise RuntimeError('scene has no non-target corner for a marker')
    start = available[0]
    r,c = corners[start]
    g[r][c] = 9
    # First two demonstrations normalize different rotations, defeating a
    # fixed-rotation shortcut. Counts/settings do not enter the sampler.
    target = (1,3,2,0,3,2,1,2,3,1)[slot]
    for _ in range((target-start) % 4):
        g = _base._old._rotate_cw(g)
    _base.analyze_scene(g)
    return g


def generate(seed, settings=None, demos=3, queries=4):
    _base._integer(seed, 'seed', 0, 2**63-1)
    _base._integer(demos, 'demos', 2, 6)
    _base._integer(queries, 'queries', 1, 4)
    setting = normalize_settings(settings)
    bank = [_scene(seed, slot) for slot in range(10)]
    if len({repr(g) for g in bank}) != 10:
        raise RuntimeError('duplicate constructive inputs')
    def pair(g):
        return {'input': deepcopy(g), 'output': python_apply(g, setting)}
    return {'train':[pair(g) for g in bank[:demos]],
            'test':[pair(g) for g in bank[6:6+queries]],
            'program_solution':program(setting), 'settings':setting,
            'meta':{'status':'proposed_owner_pending', 'training_admitted':False,
                    'seed':seed, 'input_rng_independent_of_settings_and_counts':True,
                    'input_side_range':[2,15], 'output_side_range':[4,30],
                    'label_basis':'Python claims; protected Racket required'}}
