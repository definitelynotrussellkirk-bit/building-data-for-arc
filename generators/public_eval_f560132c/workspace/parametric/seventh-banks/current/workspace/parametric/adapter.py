"""Native source-local adapter for the f560132c jigsaw family."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_f560132c_adapter_prototype', HERE/'prototype.py')
P = importlib.util.module_from_spec(_spec); sys.modules[_spec.name] = P; _spec.loader.exec_module(P)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {'finish_rule'} or type(settings['finish_rule']) is not str or settings['finish_rule'] not in P.SETTINGS:
        raise ValueError('Expected exactly finish_rule=pack_only|highlight_hub')
    return settings['finish_rule']


def program(settings):
    mode = _setting(settings)
    return (HERE/('canonical.rkt' if mode == 'pack_only' else 'highlight_hub.rkt')).read_text()


def generate(seed, settings, demos=2, queries=4):
    mode = _setting(settings); P.validate_request(seed, demos, queries)
    def pair(index, query=False):
        grid = P.scene(seed, index, query=query)
        return {'input': grid, 'output': P.solve(grid, mode)}
    bank = [pair(i, True) for i in range(4)]
    order = list(range(4)); random.Random(f'f560132c-presentation:{seed}').shuffle(order)
    return {
        'train': [pair(i) for i in range(demos)],
        'test': [bank[i] for i in order[:queries]],
        'program_solution': program(settings),
        'settings': dict(settings),
        'seed': seed,
        'query_source_indices': order[:queries],
    }


def public_bytes(episode, query_index=0):
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('query_index out of range')
    visible = {
        'train': [{'input': P.checked_grid(p['input']), 'output': P.checked_grid(p['output'])} for p in episode['train']],
        'test': [{'input': P.checked_grid(episode['test'][query_index]['input'])}],
    }
    return (json.dumps(visible, sort_keys=True, separators=(',', ':'), ensure_ascii=False)+'\n').encode()
