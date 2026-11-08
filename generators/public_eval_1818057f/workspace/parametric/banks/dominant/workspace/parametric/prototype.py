"""Native rule and private episode layer for public 1818057f."""
from __future__ import annotations

from pathlib import Path
import copy
import random

from reviewer_support import find_root, load_selected_generator

TASK_ID = 'public_eval_1818057f'
import importlib.util, hashlib
_local=Path(__file__).resolve().parents[2]/'generator.py'
_spec=importlib.util.spec_from_file_location('_local_'+hashlib.sha256(str(_local).encode()).hexdigest(),_local)
_base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_base)
integer = _base.integer
solve = _base.solve
sample = _base.sample
analyse = _base.analyse
intermediate = _base.intermediate
rival_solve = _base.rival_solve
MARK_SCOPES = _base.MARK_SCOPES


def settings(value):
    if (type(value) is not dict or set(value) != {'mark_scope'}
            or type(value['mark_scope']) is not str or value['mark_scope'] not in MARK_SCOPES):
        raise ValueError('settings must name one declared mark_scope')
    return value['mark_scope']


def program(value):
    scope = settings(value)
    name = 'canonical.rkt' if scope == 'all' else 'dominant.rkt'
    return Path(__file__).with_name(name).read_text()


def generate(seed, value, demos, queries):
    scope = settings(value)
    integer(seed, 0, 2**63 - 1, 'seed')
    integer(demos, 2, 6, 'demos')
    integer(queries, 1, 4, 'queries')
    train_inputs = [sample(seed, i) for i in range(demos)]
    query_bank = [sample(seed, 100 + i) for i in range(4)]
    all_inputs = train_inputs + query_bank
    import json
    if len({json.dumps(g, separators=(',', ':')) for g in all_inputs}) != len(all_inputs):
        raise ValueError('duplicate demo/query input')
    return {'train': [{'input': g, 'output': solve(g, scope)} for g in train_inputs],
            'test': [{'input': g, 'output': solve(g, scope)} for g in query_bank[:queries]],
            'program_solution': program(value)}


def public_turns(episode, presentation_seed, stop_after=4):
    integer(presentation_seed, 0, 2**63 - 1, 'presentation_seed')
    integer(stop_after, 1, 4, 'stop_after')
    if type(episode) is not dict or len(episode.get('test', [])) != 4:
        raise ValueError('materialize the complete four-query bank first')
    order = list(range(4))
    random.Random(presentation_seed).shuffle(order)
    train = [{'input': copy.deepcopy(p['input']), 'output': copy.deepcopy(p['output'])}
             for p in episode['train']]
    return [{'train': copy.deepcopy(train),
             'test': [{'input': copy.deepcopy(episode['test'][i]['input'])}]}
            for i in order[:stop_after]]
