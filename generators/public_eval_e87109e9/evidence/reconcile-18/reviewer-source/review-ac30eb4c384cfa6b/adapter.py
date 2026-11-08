"""Native matched-input adapter for legend-controlled square rays."""
from __future__ import annotations
import copy,importlib.util,random,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_model_e87109e9',BASE/'model.py')
model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)

def _mode(settings):
    if (type(settings) is not dict or set(settings)!={'turn_policy'} or type(settings['turn_policy']) is not str
            or settings['turn_policy'] not in ('legend','opposite')):
        raise ValueError('settings must be exactly turn_policy=legend|opposite')
    return settings['turn_policy']

def program(settings):
    mode=_mode(settings);text=(BASE/'canonical.rkt').read_text()
    if mode=='legend': return text
    needle="(define turn-policy 'legend)"
    if text.count(needle)!=1: raise ValueError('Canonical setting marker drifted')
    return text.replace(needle,"(define turn-policy 'opposite)")

def generate(seed,settings,demos,queries):
    mode=_mode(settings);model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,1,4,'queries')
    def pair(g): return {'input':g,'output':model.solve(g,mode)}
    train=[pair(model.sample_input(seed,i,'demo')) for i in range(demos)]
    bank=[pair(model.sample_input(seed,i,'query')) for i in range(4)]
    random.Random(f'e87109e9:{seed}:presentation').shuffle(bank)
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'private_query_bank':bank,
            'program_solution':program(settings),'settings':dict(settings),'seed':seed}

def public_view(episode,index=0):
    model.integer(index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':model.grid_copy(p['input']),'output':model.grid_copy(p['output'])} for p in episode['train']],
            'test':[{'input':model.grid_copy(episode['test'][index]['input'])}]}

CAUSAL_DESCRIPTIONS={
 'step_a':'Decode the color-to-turn legend, then trace each square-width ray through its input-dependent sequence of obstacle collisions and outgoing directions.',
 'intermediate':'The ordered collision records for all four rays: current square position, incoming direction, obstacle color, decoded turn, and outgoing direction.',
 'step_b':'Paint the union of square footprints visited by those traced states onto the original scene while preserving every obstacle.',
 'why_b_depends_on_a':'A footprint after the first collision depends on the obstacle color and decoded left/right command. The same seed and objects produce different downstream corridors when that intermediate turn sequence is changed.'}

def causal_settings(): return {'turn_policy':'legend'}
def causal_intermediate(grid):
    a,marks,records,_=model.trace(grid,'legend')
    return {'seed_top':list(a['seed_top']),'seed_size':a['seed_size'],'legend':a['mapping'],
            'collision_records':records,'visited_background_count':sum(a['scene'][r][c]==a['bg'] for r,c in marks)}
def counterfactual_program(): return program({'turn_policy':'opposite'})
