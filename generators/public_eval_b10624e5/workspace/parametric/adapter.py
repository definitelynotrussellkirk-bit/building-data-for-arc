"""Native matched-input adapter, with all resources in this directory."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
from functools import lru_cache
from pathlib import Path

BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_panel_'+hashlib.sha256(str(BASE).encode()).hexdigest(),BASE/'prototype.py')
P=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(P)
MODES=P.MODES
PARAMETER='orientation'


def mode_of(settings):
    if type(settings) is not dict or set(settings)!={PARAMETER} or type(settings[PARAMETER]) is not str or settings[PARAMETER] not in MODES:
        raise ValueError('settings must name exactly orientation=panel_reflections|preserve_orientation')
    return settings[PARAMETER]


def program(settings):
    mode=mode_of(settings)
    return (BASE/('canonical.rkt' if mode==MODES[0] else 'preserve_orientation.rkt')).read_text()


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
    d=P.analyse(grid);s=d['source']
    return {'step_a':'Identify the uniquely decorated panel and recover its red anchor bounding box, native side length and colored pixels.',
            'intermediate':'The source anchor origin and native side, plus source-panel pixel geometry and target anchor records.',
            'step_b':'Use each target/native size ratio to reconstruct the decoration, with panel-relative reflections in the canonical mode and preserved orientation in the alternative.',
            'why_b_depends_on_a':'The same target size requires different source-coordinate lookup when the input source anchor changes; a fixed native side cannot reproduce the inferred geometry.',
            'value':{'source_panel':s['panel'],'source_anchor':s['anchor'],'native_side':s['size'],'source_decoration':s['decoration'],
                     'targets':[{'panel':p['panel'],'anchor':p['anchor'],'side':p['size']} for p in d['panels'] if p is not s]}}
