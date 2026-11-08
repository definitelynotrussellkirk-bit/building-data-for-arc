"""Three exact policies, common teaching, disjoint original query banks.

Even seeds draw the accepted relay bank, odd seeds the independent vertical
bank, both with source seed floor(seed/2). No Racket program is rewritten.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from math import isqrt
from pathlib import Path
import sys
from reviewer_support import public_challenge_bytes

HERE = Path(__file__).resolve().parent
SECONDARY_SETTINGS = ('next_repeated', 'big_side_relay', 'preserve_vertical')

def _load(path):
    name = '_b5_union_' + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

relay = _load(HERE / 'family.py')
vertical = _load(HERE / 'branches' / 'incoming' / 'prototype.py')

def _setting(settings):
    if type(settings) is not dict or set(settings) != {'secondary'}:
        raise ValueError('settings must contain exactly secondary')
    value = settings['secondary']
    if type(value) is not str or value not in SECONDARY_SETTINGS:
        raise ValueError('unknown secondary policy')
    return value

def program(settings):
    policy = _setting(settings)
    if policy == 'preserve_vertical':
        return vertical.program({'placement': policy})
    return relay.program(settings)

def _pack(grid, policy):
    # The incoming analyzer's only extra restriction on original relay inputs
    # is tied vertical centers. Exact preserve_vertical.rkt defines ties as
    # not-above; retain that behavior explicitly instead of counting an error.
    facts = vertical.analyze(grid)
    errors = [e for e in facts['errors'] if e != 'role vertical centers tie']
    if errors:
        raise ValueError('; '.join(errors))
    bg = facts['background']; big = facts['big_color']; b = facts['big_side']
    single = facts['single_color']
    if policy == 'big_side_relay':
        from collections import Counter
        counts = Counter(c for row in grid for c in row)
        matches = [c for c,n in counts.items() if c not in (bg,big) and n == b]
        if len(matches)>1:
            raise ValueError('ambiguous relay')
        small = matches[0] if matches else None
        s = isqrt(b) if small is not None else 0
        if small is not None and s*s != b:
            raise ValueError('non-square relay mass')
    else:
        small = facts['small_color']; s = facts['small_side']
    h = max(b,s + int(single is not None)); sc = 2 if single is not None else 0
    bc = sc+s+1; w=bc+b
    if max(h,w)>30:
        raise ValueError('output exceeds ARC bounds')
    out=[[bg]*w for _ in range(h)]
    for r in range(b):
        for c in range(bc,bc+b): out[r][c]=big
    if small is not None:
        for r in range(h-s,h):
            for c in range(sc,sc+s): out[r][c]=small
    if single is not None: out[-1][0]=single
    if policy == 'preserve_vertical' and not facts['big_above']:
        out=[row[::-1] for row in out[::-1]]
    return out

def solve_python(grid, policy):
    if policy not in SECONDARY_SETTINGS:
        raise ValueError('unknown policy')
    return _pack(grid,policy)

def sample_inputs(seed, *, demos=3, queries=4):
    relay._strict_int('seed',seed,0,2**63-1)
    relay._strict_int('demos',demos,3,6)
    relay._strict_int('queries',queries,1,4)
    source_seed=seed//2
    old=relay.sample_inputs(source_seed,demos=6,queries=4)
    # Shared teaching is chosen without inspecting queries or their labels.
    teaching=old[:2]+[vertical.sample_input(source_seed,'train',2)]
    if seed%2 == 0:
        indices = (2, 3, 4, 5)
        start = source_seed % len(indices)
        teaching += [old[indices[(start+i) % len(indices)]] for i in range(3)]
        tests=old[6:]
    else:
        indices = (0, 1, 3, 4, 5)
        start = source_seed % len(indices)
        teaching += [vertical.sample_input(source_seed,'train',indices[(start+i) % len(indices)]) for i in range(3)]
        tests=[vertical.sample_input(source_seed,'test',i) for i in range(4)]
    selected=teaching[:demos]+tests[:queries]
    keys=[json.dumps(g,separators=(',',':')) for g in selected]
    if len(set(keys)) != len(keys):
        raise RuntimeError('duplicate inputs')
    return deepcopy(selected)

def generate(seed, settings, demos, queries):
    policy=_setting(settings)
    inputs=sample_inputs(seed,demos=demos,queries=queries)
    pairs=[{'input':g,'output':solve_python(g,policy)} for g in inputs]
    return {'train':pairs[:demos], 'test':pairs[demos:],
            'program_solution':program(settings),
            'settings':deepcopy(settings),
            'sampler_provenance':{'bank':'relay' if seed%2==0 else 'vertical',
                                   'source_seed':seed//2}}

def public_turn(episode, query_index=0):
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('invalid query index')
    return json.loads(public_challenge_bytes({'train':episode['train'],
                                              'test':[episode['test'][query_index]]}))
