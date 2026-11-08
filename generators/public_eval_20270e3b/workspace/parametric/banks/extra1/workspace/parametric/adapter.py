"""Exact-path native adapter; claims are re-executed by protected Racket."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
HOME=HERE.parents[1]
_spec=importlib.util.spec_from_file_location('_20270e3b_source',HOME/'generator.py')
_source=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_source)


def validate(settings):
    if type(settings) is not dict or set(settings)!={'mode'} or type(settings['mode']) is not str or settings['mode'] not in _source.MODES:
        raise ValueError('Settings must contain exactly one declared mode')
    return settings['mode']


def program(settings):
    mode=validate(settings)
    return (HERE/('canonical.rkt' if mode=='canonical' else 'enclosed_fill_relay.rkt')).read_text()


def generate(seed,settings,demos,queries):
    mode=validate(settings)
    _source.integer(seed,'seed');_source.integer(demos,'demos',2,6);_source.integer(queries,'queries',1,4)
    def pair(index):
        inp=_source.generate(seed,index)
        return {'input':inp,'output':_source.solve(inp,mode)}
    bank=[pair(i) for i in range(6,10)]
    order=list(range(4));random.Random(f'20270e3b-presentation:{seed}').shuffle(order)
    return {'train':[pair(i) for i in range(demos)],'test':[bank[i] for i in order][:queries],
            'program_solution':program(settings),'settings':dict(settings),'seed':seed,
            'query_source_indices':order[:queries]}


def public_bytes(episode,query_index=0):
    _source.integer(query_index,'query_index',0,len(episode['test'])-1)
    visible={'train':[{'input':_source.grid(p['input']),'output':_source.grid(p['output'])} for p in episode['train']],
             'test':[{'input':_source.grid(episode['test'][query_index]['input'])}]}
    return (json.dumps(visible,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
