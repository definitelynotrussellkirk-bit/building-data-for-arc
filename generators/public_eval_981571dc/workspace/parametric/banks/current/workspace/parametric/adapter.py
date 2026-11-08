"""Source-local native adapter for public parent 981571dc."""
from pathlib import Path
import copy
import hashlib
import json
import random
import types

BASE=Path(__file__).resolve().parent
G=types.ModuleType('_symmetry_engine_'+hashlib.sha256(str(BASE).encode()).hexdigest())
G.__file__=str(BASE/'engine.py')
exec(compile((BASE/'engine.py').read_bytes(),G.__file__,'exec'),G.__dict__)


def value(settings):
    if (type(settings) is not dict or set(settings)!={'completion_depth'}
            or type(settings['completion_depth']) is not str
            or settings['completion_depth'] not in G.VALUES):
        raise ValueError('settings must contain exactly completion_depth: closure|transpose_only')
    return settings['completion_depth']


def program(settings):
    v=value(settings);source=(BASE/'canonical.rkt').read_text()
    anchor='(define completion "closure")'
    if source.count(anchor)!=1: raise ValueError('Canonical completion anchor changed')
    return source if v=='closure' else source.replace(anchor,'(define completion "transpose_only")',1)


def rival_program(settings,rival):
    value(settings)
    if rival not in G.RIVALS: raise ValueError('Unknown rival')
    source=program(settings);anchor='(define rival "")'
    if source.count(anchor)!=1: raise ValueError('Canonical rival anchor changed')
    return source.replace(anchor,f'(define rival "{rival}")',1)


def generate(seed,settings,demos=2,queries=4):
    v=value(settings);G.integer(seed,0,2**63-1,'seed');G.integer(demos,2,6,'demos');G.integer(queries,1,4,'queries')
    ds,qs=G.input_bank(seed)
    def pair(text):
        g=json.loads(text);return {'input':g,'output':G.solve(g,v)}
    return {'train':[pair(x) for x in ds[:demos]],'test':[pair(x) for x in qs[:queries]],
            'program_solution':program(settings)}


def present(seed,settings,demos=2,queries=4,presentation_seed=0):
    G.integer(queries,1,4,'queries');G.integer(presentation_seed,0,2**63-1,'presentation_seed')
    episode=generate(seed,settings,demos,4);order=list(range(4))
    rng=random.Random(int.from_bytes(hashlib.sha256(f'981571dc:presentation:{seed}:{presentation_seed}'.encode()).digest(),'big'))
    rng.shuffle(order)
    public=[{'train':copy.deepcopy(episode['train']),
             'test':[{'input':copy.deepcopy(episode['test'][i]['input'])}]} for i in order[:queries]]
    private={'settings':copy.deepcopy(settings),'program':episode['program_solution'],'seed':seed,
             'presentation_seed':presentation_seed,'source_indices':order,
             'source_pairs':copy.deepcopy(episode['test'])}
    return {'public':public,'private':private}


def counterfactual_program(settings):
    return rival_program(settings,'stage_b_original')


def intermediate(g,settings):
    value(settings);state=G.derive(g)
    return {'stage_a_filled':state['stage_a_filled'],'stage_b_filled':state['stage_b_filled'],
            'stage_b_from_stage_a_only':state['stage_b_from_stage_a_only'],
            'fixed_prefix_indices':[0,1],
            'suffix_mirror_formula':'m(i)=i for i<2, otherwise n+1-i'}


def dependency():
    return {
      'step_a':'Repair each erased cell whose transposed coordinate is visible, producing a transpose-completed intermediate grid.',
      'intermediate':'The input-dependent stage-A grid together with the exact cells and colors restored from transpose partners.',
      'step_b':'For every zero that remains, inspect its fixed-prefix suffix-mirror coordinates in the stage-A grid and copy the first visible donor.',
      'why_b_depends_on_a':'Some suffix-mirror donors are themselves erased in the input and exist only because A restored them. Reading B from the original grid leaves those targets zero.'}
