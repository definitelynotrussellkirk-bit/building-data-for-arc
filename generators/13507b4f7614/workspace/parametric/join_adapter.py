"""Native, opt-in join-then-cross family; the canonical sampler is untouched.

Input draws are independent of the private join setting and of requested counts.
The first two examples constructively teach the join axis and recomputed parity.
Labels here are Python claims; protected Racket independently verifies them in
native qualification and in build_evidence.py before retention.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import random

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('arcpuzzles_13507_join_rules', _HERE / 'rules.py')
RULES = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RULES)

_DEMO_SHAPES = ((16,16), (20,20), (18,19), (17,22), (23,23), (26,26))
_QUERY_SHAPES = ((16,19), (20,24), (25,22), (30,30))


def program(settings: dict) -> str:
    return RULES.program(settings)


def _integer(value, minimum, maximum, name):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an exact integer in {minimum}..{maximum}')
    return value


def _rng(seed: int, role: str, index: int) -> random.Random:
    raw = f'13507-join-v1:{seed}:{role}:{index}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), 'big'))


def _odd(limit, rng, dense=False):
    choices = list(range(3, limit + 1, 2))
    if not choices:
        raise ValueError('slot cannot contain a nondegenerate odd rectangle')
    return choices[-1] if dense else rng.choice(choices)


def _even(limit, rng, dense=False):
    choices = list(range(2, limit + 1, 2))
    if not choices:
        raise ValueError('slot cannot contain an even rectangle')
    return choices[-1] if dense else rng.choice(choices)


def _parts(limit, phase, rng, dense=False):
    """Parity deliberately changes after joining, even for individually even parts."""
    parities = ((0,0), (0,0,0), (1,1), (1,0), (0,0,0), (1,1), (0,1,0))[phase % 7]
    lengths = [2 + p for p in parities]
    if sum(lengths) + len(lengths) - 1 > limit:
        lengths = [2,2]
    budget = (limit - (sum(lengths) + len(lengths) - 1)) // 2
    increments = budget if dense else rng.randint(0,budget)
    for _ in range(increments):
        lengths[rng.randrange(len(lengths))] += 2
    return lengths


def _paint(grid, top, left, height, width):
    for row in range(top, top + height):
        for col in range(left, left + width):
            if grid[row][col] != 0:
                raise RuntimeError('constructive scene unexpectedly overlaps')
            grid[row][col] = 4


def _bands(length, margin):
    available = length - 2 * margin - 2
    first = available // 2
    return ((margin, margin + first), (margin + first + 2, length - margin))


def _scene(seed: int, role: str, index: int):
    rng = _rng(seed, role, index)
    height, width = (_DEMO_SHAPES if role == 'demo' else _QUERY_SHAPES)[index]
    phase = index if role == 'demo' else index + 3
    dense = role == 'query' and index == 3
    margin = 0 if dense else rng.randrange(2)
    grid = [[0] * width for _ in range(height)]
    slots = [(rb,cb) for rb in _bands(height, margin) for cb in _bands(width, margin)]
    rng.shuffle(slots)
    motifs = (('horizontal','vertical','horizontal','vertical') if phase in (1,4,6)
              else ('horizontal','vertical','odd','guard'))
    for motif, ((r0,r1),(c0,c1)) in zip(motifs, slots):
        sh, sw = r1-r0, c1-c0
        if motif == 'horizontal':
            parts = _parts(sw, phase, rng, dense)
            mh, mw = _odd(sh,rng,dense), sum(parts) + len(parts) - 1
        elif motif == 'vertical':
            parts = _parts(sh, phase, rng, dense)
            mh, mw = sum(parts) + len(parts) - 1, _odd(sw,rng,dense)
        elif motif == 'odd':
            mh, mw = _odd(sh,rng,dense), _odd(sw,rng,dense)
        elif phase % 2 == 0:
            mh, mw = _odd(sh,rng,dense), _even(sw,rng,dense)
        else:
            mh, mw = _even(sh,rng,dense), _odd(sw,rng,dense)
        # Dense stress uses all four outer corners; other draws vary translations.
        if dense:
            top = r0 if r0 == 0 else r1-mh
            left = c0 if c0 == 0 else c1-mw
        else:
            top, left = rng.randint(r0,r1-mh), rng.randint(c0,c1-mw)
        if motif == 'horizontal':
            col = left
            for part in parts:
                _paint(grid,top,col,mh,part)
                col += part + 1
        elif motif == 'vertical':
            row = top
            for part in parts:
                _paint(grid,row,left,part,mw)
                row += part + 1
        else:
            _paint(grid,top,left,mh,mw)
    return grid


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    """Return independent 2..6 demos and 1..4 novel queries; no resampling loop."""
    _integer(seed,0,2**63-1,'seed')
    _integer(demos,2,6,'demos')
    _integer(queries,1,4,'queries')
    exact_program = program(settings)  # Validates exact setting keys/types.
    axis = settings['join_axis']
    train_inputs = [_scene(seed,'demo',i) for i in range(demos)]
    query_inputs = [_scene(seed,'query',i) for i in range(queries)]
    train = [{'input':g,'output':RULES.transform(g,axis)} for g in train_inputs]
    test = [{'input':g,'output':RULES.transform(g,axis)} for g in query_inputs]
    survivors = [candidate for candidate in ('none','horizontal','vertical') if all(
        RULES.transform(pair['input'],candidate) == pair['output'] for pair in train)]
    if survivors != [axis]:
        raise RuntimeError(f'constructed demonstrations do not identify {axis}: {survivors}')
    return {'train':train,'test':test,'program_solution':exact_program}
