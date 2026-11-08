"""Native centroid-addressed routing; exact one-hop authority and two-hop variant.

The second address is read from the ORIGINAL panel at the first destination.
Applying the canonical rearrangement twice would be idempotent and is not this
rule. The historical transpose prototype remains separate and unchanged.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from typing import Any
from reviewer_support import find_root, load_selected_generator

TASK_ID = '250925d67253'
HERE = Path(__file__).resolve().parent
PARAMETER = 'route_policy'
VALUES = ('one_hop', 'two_hop')
_GEN = None


def generator():
    global _GEN
    if _GEN is None:
        _GEN, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    return _GEN


def setting(settings: dict[str, str]) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f'settings must contain exactly {PARAMETER}')
    value = settings[PARAMETER]
    if type(value) is not str or value not in VALUES:
        raise ValueError(f'{PARAMETER} must be one of {VALUES}')
    return value


def program(settings: dict[str, str]) -> str:
    value = setting(settings)
    return (HERE / 'rules' / ('identity.rkt' if value == 'one_hop' else 'two_hop.rkt')).read_text()


def intermediate(grid: list[list[int]]) -> dict[str, Any]:
    gen = generator()
    p = gen._target_mapping(grid)
    if sorted(p) != list(range(9)):
        raise ValueError('centroid destinations must form a permutation')
    return {'mapping': p, 'second_destinations': [p[p[s]] for s in range(9)]}


def apply(grid: list[list[int]], value: str) -> list[list[int]]:
    setting({PARAMETER: value})
    info = intermediate(grid)
    return generator()._apply_mapping(grid, info['mapping'] if value == 'one_hop' else info['second_destinations'])


def _hop_source(count: int, transpose: bool = False) -> str:
    base = (HERE / 'rules/identity.rkt').read_text()
    start = base.index('(let ((tgt (target-pos')
    end = base.index('(and', start)
    bindings = ['(hop1 (target-pos (fst sp) (snd sp)))']
    bindings += [f'(hop{i} (target-pos (fst hop{i-1}) (snd hop{i-1})))' for i in range(2, count+1)]
    target = f'(cons (snd hop{count}) (fst hop{count}))' if transpose else f'hop{count}'
    bindings.append(f'(tgt {target})')
    return base[:start] + '(let* (' + ' '.join(bindings) + ')\n' + base[end:]


def hypotheses() -> dict[str, str]:
    base = program({PARAMETER: 'one_hop'})
    return {
        'one_hop': base,
        'two_hop': program({PARAMETER: 'two_hop'}),
        'three_hop': _hop_source(3),
        'inverse': base.replace('(src (find-source tbr tbc))', '(src (target-pos tbr tbc))'),
        'transpose': (HERE / 'rules/transpose.rkt').read_text(),
        'two_hop_transpose': _hop_source(2, True),
        'source_order': '(rule! (lambda (g) g))',
    }


def predict(grid: list[list[int]], hypothesis: str) -> list[list[int]]:
    p = intermediate(grid)['mapping']
    if hypothesis in VALUES:
        return apply(grid, hypothesis)
    if hypothesis == 'three_hop':
        mapping = [p[p[p[s]]] for s in range(9)]
    elif hypothesis == 'inverse':
        mapping = [p.index(s) for s in range(9)]
    elif hypothesis == 'transpose':
        mapping = [3*(t % 3) + t//3 for t in p]
    elif hypothesis == 'two_hop_transpose':
        mapping = [3*(p[t] % 3) + p[t]//3 for t in p]
    elif hypothesis == 'source_order':
        return deepcopy(grid)
    else:
        raise ValueError(f'unknown hypothesis: {hypothesis}')
    return generator()._apply_mapping(grid, mapping)


def teaching_findings(episode: dict, value: str) -> list[str]:
    """Bounded finite-rival check; NOT a universal identifiability claim."""
    return [name for name in hypotheses() if name != value
            and all(predict(p['input'], name) == p['output'] for p in episode['train'])
            and any(predict(p['input'], name) != p['output'] for p in episode['test'])]


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict:
    value = setting(settings)
    if type(seed) is not int:
        raise TypeError('seed must be an exact integer, not bool')
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError('demos must be an exact integer in 2..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an exact integer in 1..4')
    gen = generator()
    inputs, seen = [], set()
    # Construct the same maximal lesson before slicing, independent of setting
    # and requested counts. No query response influences demo selection.
    for slot in range(10):
        for attempt in range(32):
            # Balanced fixed-point profiles, marker density and palettes. Every
            # grid contains target-0 motifs that refute centroid proxy shortcuts.
            grid = gen.generate(seed, slot*32+attempt, difficulty='hard',
                                permutation_kind='derangement' if slot % 2 == 0 else 'mixed_fixed',
                                marker_density='sparse' if slot % 3 == 0 else 'dense',
                                palette_band='low' if slot % 2 == 0 else 'high')
            key = tuple(map(tuple, grid))
            if key not in seen:
                seen.add(key); inputs.append(grid); break
        else:
            raise RuntimeError(f'failed to sample a distinct input at slot {slot}')
    pairs = [{'input': g, 'output': apply(g, value)} for g in inputs]
    return {'train': pairs[:demos], 'test': pairs[6:6+queries],
            'program_solution': program(settings)}


def public_turn(episode: dict, query_index: int) -> dict:
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('query_index must select one existing query')
    return deepcopy({'train': [{'input': p['input'], 'output': p['output']} for p in episode['train']],
                     'test': [{'input': episode['test'][query_index]['input']}]})
