"""Native authoring adapter for public_eval_7491f3cf."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
_spec = importlib.util.spec_from_file_location('_panel_partition_family', HOME / 'generator.py')
family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(family)

PARAMETER = 'source_assignment'
VALUES = ('second_in_marked', 'third_in_marked')
DEFAULT = {PARAMETER: VALUES[0]}

solve = family.solve
derive = family.derive
split_panels = family.split_panels
join_panels = family.join_panels
survivors = family.survivors


def _checked(settings: dict) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f'expected exactly {{{PARAMETER!r}: value}}')
    value = settings[PARAMETER]
    if type(value) is not str or value not in VALUES:
        raise ValueError('unknown source_assignment')
    return value


def program(settings: dict) -> str:
    value = _checked(settings)
    canonical = (HERE / 'canonical.rkt').read_text()
    if value == VALUES[0]:
        return canonical
    return canonical.replace("(define source-assignment 'second_in_marked)",
                             "(define source-assignment 'third_in_marked)")


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    value = _checked(settings)
    for item, lo, hi, name in ((seed, 0, 2**63 - 1, 'seed'), (demos, 2, 6, 'demos'), (queries, 1, 4, 'queries')):
        if type(item) is not int or not lo <= item <= hi:
            raise ValueError(f'{name} outside exact integer bounds')
    def pair(index: int, query: bool) -> dict:
        grid = family._scene(seed, index, query=query)
        return {'input': grid, 'output': solve(grid, value)}
    return {
        'train': [pair(i, False) for i in range(6)][:demos],
        'test': [pair(i, True) for i in range(4)][:queries],
        'program_solution': program(settings),
    }


def public_view(episode: dict, query_index: int) -> dict:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get('test', [])):
        raise ValueError('query index outside episode')
    return {
        'train': copy.deepcopy(episode['train']),
        'test': [{'input': copy.deepcopy(episode['test'][query_index]['input'])}],
    }


def presentation_order(seed: int, count: int = 4) -> list[int]:
    if type(seed) is not int or not 0 <= seed < 2**63 or type(count) is not int or not 1 <= count <= 4:
        raise ValueError('invalid presentation request')
    rng = random.Random(int.from_bytes(hashlib.sha256(f'7491:{seed}:presentation'.encode()).digest(), 'big'))
    order = list(range(4)); rng.shuffle(order)
    return order[:count]


def public_turns(seed: int, settings: dict, demos: int, presentation_seed: int, turns: int) -> list[dict]:
    if type(turns) is not int or not 1 <= turns <= 4:
        raise ValueError('turns outside 1..4')
    episode = generate(seed, settings, demos, 4)
    return [public_view(episode, i) for i in presentation_order(presentation_seed, 4)[:turns]]


def rival_programs(settings: dict) -> dict[str, str]:
    value = _checked(settings)
    selected = program(settings)
    other = VALUES[1 - VALUES.index(value)]
    return {
        'other_setting': program({PARAMETER: other}),
        'identity': '(rule! (lambda (g) g))',
    }
