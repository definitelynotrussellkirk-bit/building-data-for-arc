"""Native family: infer oriented ports, then copy infinite or measured rays."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from puzzle_generators.base import stable_rng
from reviewer_support import public_challenge_id, public_challenge_bytes
HERE=Path(__file__).resolve().parent;HOME=HERE.parent.parent
path=HOME/'generator.py';name='_rays_base_'+hashlib.sha256(str(path).encode()).hexdigest()
spec=importlib.util.spec_from_file_location(name,path);base=importlib.util.module_from_spec(spec)
sys.modules[name]=base;spec.loader.exec_module(base)
SETTINGS=('boundary','source_length')
solve=base.solve
public_id=public_challenge_id


def _setting(settings):
    if type(settings) is not dict or set(settings)!={'ray_extent'}:raise ValueError('exactly one ray_extent required')
    value=settings['ray_extent']
    if type(value) is not str or value not in SETTINGS:raise ValueError('invalid ray_extent')
    return value


def program(settings):
    value=_setting(settings)
    return (HOME/'reference.rkt' if value=='boundary' else HERE/'source_length.rkt').read_text()


def generate(seed,settings,demos=3,queries=4):
    value=_setting(settings)
    if type(seed) is not int:raise TypeError('exact integer seed required')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(i):
        inp=base.generate(seed,i);return {'input':inp,'output':solve(inp,value)}
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(100+i) for i in range(4)][:queries],
            'program_solution':program(settings)}


def rivals(grid,extent):
    other='source_length' if extent=='boundary' else 'boundary'
    canonical=solve(grid,extent);bg,_,_=base.analyze(grid)
    constant=[[1 if grid[r][c]==bg and v!=bg else v for c,v in enumerate(row)] for r,row in enumerate(canonical)]
    return {'opposite_extent':solve(grid,other), 'source_only':solve(grid,extent,scope='source_only'),
            'same_index_without_template_reversal':solve(grid,extent,port_rule='same_index'),
            'reverse_all_ports':solve(grid,extent,port_rule='reverse'),
            'first_seed_only':solve(grid,extent,scope='first_seed'),
            'rotations_without_reflections':solve(grid,extent,scope='rotations_only'),
            'one_cell_rays':solve(grid,extent,length_override=1),
            'fixed_blue_new_cells':constant}


def ambiguities(episode,extent):
    names=set(rivals(episode['train'][0]['input'],extent))
    for p in episode['train']:
        predictions=rivals(p['input'],extent)
        names={n for n in names if predictions[n]==p['output']}
    return sorted(n for n in names if any(rivals(p['input'],extent)[n]!=p['output'] for p in episode['test']))


def present(episode,presentation_seed,limit=4):
    if type(presentation_seed) is not int or type(limit) is not int or not 1<=limit<=4:
        raise ValueError('integer seed and 1..4 limit required')
    if len(episode.get('test',[]))!=4:raise ValueError('all four private queries required')
    order=list(range(4));stable_rng(presentation_seed,'ray-presentation','1').shuffle(order)
    views=[]
    for i in order[:limit]:
        view={'train':deepcopy(episode['train']),'test':[{'input':deepcopy(episode['test'][i]['input'])}]}
        views.append(json.loads(public_challenge_bytes(view)))
    return {'views':views,'private':{'source_indices':order[:limit],'presentation_seed':presentation_seed}}
