"""Native corridor family; setting-neutral generation and finite-rival lessons."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME=Path(__file__).resolve().parents[2]
_SPEC=importlib.util.spec_from_file_location('_corridors_'+hashlib.sha256(str(HOME).encode()).hexdigest(),HOME/'generator.py')
CORE=importlib.util.module_from_spec(_SPEC);sys.modules[_SPEC.name]=CORE;_SPEC.loader.exec_module(CORE)
RIVALS=('alternate','identity','straight_only','one_turn_only','turn_any_obstacle',
        'ignore_black','fixed_column2','start_every_gap','erase_sources_only','paint_full_route')


def validate_settings(settings):
    if type(settings) is not dict or set(settings)!={'guide_update'} or type(settings['guide_update']) is not str or settings['guide_update'] not in ('local','entry'):
        raise ValueError('Expected exactly {guide_update: local|entry}')
    return settings['guide_update']


def program(settings):
    mode=validate_settings(settings);source=(HOME/'reference.rkt').read_text()
    return source if mode=='local' else source.replace('(define update-guide? #t)','(define update-guide? #f)')


def surviving_rules(demos,mode):
    survivors=['intended']
    for name in RIVALS:
        def predict(g):
            return CORE.solve(g,'entry' if mode=='local' else 'local') if name=='alternate' else CORE.solve(g,mode,rival=name)
        if all(predict(p['input'])==p['output'] for p in demos):survivors.append(name)
    return survivors


def _train_bank(seed):
    shapes=((13,17),(15,19),(17,21),(19,23),(21,25),(23,27))
    for attempt in range(64):
        first=[CORE.sample_input(CORE.rng_for(seed,'train',i,attempt),*shapes[i],profile=i%2) for i in range(2)]
        if all(surviving_rules([{'input':g,'output':CORE.solve(g,m)} for g in first],m)==['intended'] for m in ('local','entry')):
            return first+[CORE.sample_input(CORE.rng_for(seed,'train',i,attempt),*shapes[i],profile=i%2) for i in range(2,6)]
    raise RuntimeError('Finite-rival teaching sampler exhausted 64 attempts')


def generate(seed,settings,demos,queries):
    mode=validate_settings(settings)
    for value,low,high,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    train=_train_bank(seed)
    test=[CORE.sample_input(CORE.rng_for(seed,'query',i),*shape,profile=i%2)
          for i,shape in enumerate(((15,19),(19,23),(25,27),(30,30)))]
    if len({json.dumps(g) for g in train+test})!=10:raise RuntimeError('Generated inputs collided')
    pair=lambda g:{'input':g,'output':CORE.solve(g,mode)}
    return {'train':[pair(g) for g in train[:demos]],'test':[pair(g) for g in test[:queries]],'program_solution':program(settings)}
