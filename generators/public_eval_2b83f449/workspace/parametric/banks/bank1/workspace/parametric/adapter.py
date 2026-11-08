"""Matched-input native authoring adapter. Python labels are claims only."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
from pathlib import Path
from functools import lru_cache

HOME=Path(__file__).resolve().parents[2]
SOURCE=HOME/'generator.py'
SPEC=importlib.util.spec_from_file_location('_pipe_generator_'+hashlib.sha256(str(SOURCE).encode()).hexdigest(),SOURCE)
G=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(G)
MODES=('down','up')


def _mode(settings):
    if type(settings) is not dict or set(settings)!={'mode'} or type(settings['mode']) is not str or settings['mode'] not in MODES:
        raise ValueError('settings must name exactly mode=down|up')
    return settings['mode']


def program(settings):
    mode=_mode(settings)
    return (HOME/'reference.rkt' if mode=='down' else Path(__file__).with_name('up.rkt')).read_text()


@lru_cache(maxsize=64)
def _bank(seed):
    # Greedy deterministic teaching search, setting independent; no query answers.
    # Max 64 candidate scenes; unresolved finite rivals cause an explicit failure.
    candidates=[G.sample(seed,1000+i)for i in range(64)]
    tables=[G.policy_outputs(g)for g in candidates]
    obligations={(m,p)for m in MODES for p in tables[0] if p!=m}
    demos=[]; used=set()
    for _ in range(2):
        scores=[sum(t[m]!=t[p]for m,p in obligations) if i not in used else -1 for i,t in enumerate(tables)]
        i=max(range(len(scores)),key=scores.__getitem__);used.add(i);demos.append(candidates[i])
        obligations={pair for pair in obligations if tables[i][pair[0]]==tables[i][pair[1]]}
    # Behavioral equivalences are allowed only if all independently sampled queries agree.
    demos += [G.sample(seed,2000+i)for i in range(4)]
    queries=[G.sample(seed,3000+i,size=size) for i,size in enumerate(((9,12),(15,20),(21,26),(29,30)))]
    all_inputs=demos+queries
    if len({str(g)for g in all_inputs})!=len(all_inputs):raise RuntimeError('duplicate generated grid')
    for mode in MODES:
        ep={'train':[{'input':g,'output':G.solve(g,mode)}for g in demos[:2]],'test':[{'input':g,'output':G.solve(g,mode)}for g in queries]}
        audit=teaching_audit(ep,mode)
        if audit['query_disagreeing_survivors']:raise RuntimeError(f'finite teaching ambiguity: {audit}')
    return demos,queries


def teaching_audit(episode,mode):
    train=[G.policy_outputs(p['input'])for p in episode['train']]
    survivors=[name for name in train[0] if all(t[name]==p['output'] for t,p in zip(train,episode['train']))]
    query_tables=[G.policy_outputs(p['input'])for p in episode['test']]
    wrong=[name for name in survivors if any(t[name]!=p['output']for t,p in zip(query_tables,episode['test']))]
    return {'policies':list(train[0]),'survivors':survivors,'query_disagreeing_survivors':wrong,'scope':'finite declared policies only'}


def generate(seed,settings,demos=2,queries=4):
    mode=_mode(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('seed must be integer 0..2**63-1')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or queries!=4:raise ValueError('exactly four private queries required')
    train,test=_bank(seed)
    return {'train':[{'input':copy.deepcopy(g),'output':G.solve(g,mode)}for g in train[:demos]],
            'test':[{'input':copy.deepcopy(g),'output':G.solve(g,mode)}for g in test],
            'program_solution':program(settings),'settings':copy.deepcopy(settings),'seed':seed}


def sequential_description(grid):
    net=G.install(grid)
    paths=[]
    for cells in G.components(net):
        markers=[p for p in cells if grid[p[0]][p[1]]==3]
        if markers:
            region=set(cells)
            paths.append({'tokens':len(markers),'endpoints':[list(p)for p in cells if len(G.neighbors(p,region))<=1]})
    return {'step_a':'Install every orange bridge, split its strip cells with magenta, and recover cyan paths.',
            'intermediate':'The input-dependent cyan path components, their endpoints and token counts.',
            'step_b':'Pack each path\'s green tokens from its gravity-selected endpoint inward.',
            'why_b_depends_on_a':'Bridges connect different strips while dividers and holes terminate other routes; original strip components select wrong destinations.',
            'value':{'token_bearing_paths':paths}}
