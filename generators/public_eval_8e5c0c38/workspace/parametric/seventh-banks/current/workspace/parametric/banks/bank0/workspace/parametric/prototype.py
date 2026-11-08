"""Native episode family: per-color symmetry inference, trimming or completing."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys
from puzzle_generators.base import stable_rng
from reviewer_support import public_challenge_id, public_challenge_bytes

HERE = Path(__file__).resolve().parent
HOME = HERE.parent.parent
path = HOME/'generator.py'
name = '_symmetry_base_' + hashlib.sha256(str(path).encode()).hexdigest()
spec = importlib.util.spec_from_file_location(name, path)
base = importlib.util.module_from_spec(spec)
sys.modules[name] = base
spec.loader.exec_module(base)
SETTINGS = ('trim','complete')
solve, analyze = base.solve, base.analyze
public_id = public_challenge_id


def _setting(settings):
    if type(settings) is not dict or set(settings) != {'symmetry_action'}:
        raise ValueError('exactly one symmetry_action setting required')
    value = settings['symmetry_action']
    if type(value) is not str or value not in SETTINGS: raise ValueError('invalid symmetry_action')
    return value


def program(settings):
    action = _setting(settings)
    return (HOME/'reference.rkt' if action == 'trim' else HERE/'complete.rkt').read_text()


def generate(seed, settings, demos=3, queries=4):
    action = _setting(settings)
    if type(seed) is not int: raise TypeError('exact integer seed required')
    if type(demos) is not int or not 2 <= demos <= 6: raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1 <= queries <= 4: raise ValueError('queries must be 1..4')
    def pair(index):
        inp = base.generate(seed, index)
        return {'input':inp, 'output':solve(inp, action)}
    # Complete query bank is independent of demo count. Prefix truncation never
    # changes any other pair; public presentation is independently shuffled.
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(100+i) for i in range(4)][:queries],
            'program_solution':program(settings)}


def rivals(grid, action):
    """Finite, executable plausible alternatives; never a uniqueness proof."""
    other = 'complete' if action == 'trim' else 'trim'
    transpose = lambda a: [list(row) for row in zip(*a)]
    return {'opposite_action':solve(grid,other), 'identity':deepcopy(grid),
            'bbox_axis':solve(grid,action,axis_rule='bbox'),
            'canvas_axis':solve(grid,action,axis_rule='canvas'),
            'rightmost_tie':solve(grid,action,axis_rule='rightmost'),
            'largest_color_only':solve(grid,action,only_largest=True),
            'horizontal_axis':transpose(solve(transpose(grid),action))}


def ambiguities(episode, action):
    candidates = set(rivals(episode['train'][0]['input'], action))
    for p in episode['train']:
        answers = rivals(p['input'], action)
        candidates = {r for r in candidates if answers[r] == p['output']}
    return sorted(r for r in candidates if any(rivals(p['input'],action)[r] != p['output'] for p in episode['test']))


def present(episode, presentation_seed, limit=4):
    """Controller-only shuffled timeline; expose exactly one view at a time.

    The returned private mapping and directory listing are NOT model input.
    No view reveals settings, answers, total counts, source indices or programs.
    """
    if type(presentation_seed) is not int or type(limit) is not int or not 1 <= limit <= 4:
        raise ValueError('integer presentation seed and 1..4 view limit required')
    if len(episode.get('test',[])) != 4: raise ValueError('presentation needs all four private queries')
    order = list(range(4))
    stable_rng(presentation_seed, 'symmetry-presentation', '1').shuffle(order)
    views=[]
    for index in order[:limit]:
        view={'train':deepcopy(episode['train']), 'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
        # Reconstruct from exact canonical public bytes to strip all extra fields.
        import json
        views.append(json.loads(public_challenge_bytes(view)))
    return {'views':views, 'private':{'source_indices':order[:limit], 'presentation_seed':presentation_seed}}
