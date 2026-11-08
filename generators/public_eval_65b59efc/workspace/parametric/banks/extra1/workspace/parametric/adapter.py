"""Native matched-input adapter, with all resources in this directory."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
from functools import lru_cache
from pathlib import Path

BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_table_'+hashlib.sha256(str(BASE).encode()).hexdigest(),BASE/'prototype.py')
P=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(P)
MODES=P.MODES
PARAMETER='tile_orientation'


def mode_of(settings):
    if type(settings) is not dict or set(settings)!={PARAMETER} or type(settings[PARAMETER]) is not str or settings[PARAMETER] not in MODES:
        raise ValueError('settings must name exactly tile_orientation=as_drawn|clockwise')
    return settings[PARAMETER]


def program(settings):
    mode=mode_of(settings)
    return (BASE/('canonical.rkt' if mode==MODES[0] else 'clockwise.rkt')).read_text()


@lru_cache(maxsize=64)
def bank(seed):
    demos=[P.sample(seed,i) for i in range(6)]
    queries=[P.sample(seed,100+i,stress=(i==3)) for i in range(4)]
    return demos,queries


def generate(seed,settings,demos=3,queries=4):
    mode=mode_of(settings)
    P.integer(seed,0,2**63-1,'seed');P.integer(demos,2,6,'demos');P.integer(queries,1,4,'queries')
    train,test=bank(seed)
    return {'train':[{'input':copy.deepcopy(g),'output':P.solve(g,mode)} for g in train[:demos]],
            'test':[{'input':copy.deepcopy(g),'output':P.solve(g,mode)} for g in test[:queries]],
            'settings':copy.deepcopy(settings),'seed':seed,'program_solution':program(settings)}


def public_view(episode,index):
    P.integer(index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':copy.deepcopy(episode['test'][index]['input'])}]}


def teaching_audit(episode,mode):
    tables=[P.policy_outputs(p['input']) for p in episode['train']]
    survivors=[k for k in tables[0] if all(t[k]==p['output'] for t,p in zip(tables,episode['train']))]
    wrong=[k for k in survivors if any(P.policy_outputs(p['input'])[k]!=p['output'] for p in episode['test'])]
    return {'policies':list(tables[0]),'survivors':survivors,'query_disagreeing_survivors':wrong}


def sequential_description(grid):
    d=P.analyse(grid)
    return {'step_a':'Decode source-color templates, the overlaid middle layout and bottom recolor legend.',
            'intermediate':'An input-derived source-color dictionary of template offsets and target colors, plus the merged layout.',
            'step_b':'Rotate recovered offsets clockwise in the alternative setting and stamp the selected recolored template at every occupied layout cell.',
            'why_b_depends_on_a':'The input-specific offsets, correspondence and layout determine which output pixels exist; solid tiles cannot substitute for extraction.',
            'value':{'tile_size':d['n'],'templates':d['templates'],'layout':d['layout']}}
