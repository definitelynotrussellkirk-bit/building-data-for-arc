"""Three exact selection strategies over shared, anchored color-2 scenes."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import sys
HOME=Path(__file__).resolve().parent

def _load(relative,label):
    p=HOME/relative;s=importlib.util.spec_from_file_location('_4eb_union_'+label,p)
    m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
DEGREE=_load('degree_adapter.py','degree')
ANCHOR=_load('anchor/adapter.py','anchor')
SETTINGS=({'target_degree':0},{'target_degree':1},{'target_degree':'anchor_area'})

def _strategy(settings):
    if type(settings) is not dict or set(settings)!={'target_degree'}:raise ValueError('settings must contain exactly target_degree')
    value=settings['target_degree']
    if type(value) is int and value in (0,1):return value
    if type(value) is str and value=='anchor_area':return value
    raise ValueError('target_degree must be integer0/1 or strategy anchor_area; booleans/floats are forbidden')

def program(settings):
    strategy=_strategy(settings)
    return ANCHOR.program({'selection':'anchor_sized_twos'}) if strategy=='anchor_area' else DEGREE.program(settings)

def sample_inputs(seed,demos,queries):
    inputs=ANCHOR.sample_inputs(seed,demos,queries)
    for grids in inputs.values():
        for grid in grids:
            height,width=len(grid),len(grid[0])
            boundary=[(r,c) for r in range(height) for c in range(width)
                      if r in (0,height-1) or c in (0,width-1)]
            for r,c in boundary:
                if grid[r][c]==0 and all(
                    not(0<=r+dr<height and 0<=c+dc<width) or grid[r+dr][c+dc]!=2
                    for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc):
                    grid[r][c]=2
                    break
            else:raise RuntimeError('no boundary slot for retained singleton witness')
            ANCHOR.analyze(grid)
    return inputs

def generate(seed,settings,demos=3,queries=4):
    source=program(settings)
    ANCHOR._integer(seed,0,2**63-1,'seed');ANCHOR._integer(demos,2,6,'demos');ANCHOR._integer(queries,1,4,'queries')
    inputs=sample_inputs(seed,demos,queries)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    with RacketBridge() as bridge:
        if bridge.runtime_identity.get('protected') is not True:raise RuntimeError('protected Racket required')
        rule=wrap_rule(source)
        def pair(g):
            literal="'("+' '.join('('+' '.join(map(str,row))+')' for row in g)+')'
            return {'input':deepcopy(g),'output':bridge.eval_text(f'({rule} {literal})')}
        return {**{split:[pair(g) for g in grids] for split,grids in inputs.items()},'program_solution':source}

def public_turn(episode,query_index=0):
    ANCHOR._integer(query_index,0,len(episode['test'])-1,'query_index')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][query_index]['input'])}]}
