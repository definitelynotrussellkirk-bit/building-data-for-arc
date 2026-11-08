"""Task-local authoring hooks, isolated from the runtime's thin adapter."""
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_contour_family_adapter_'+str(HERE),HERE/'adapter.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
generate=a.generate
analyze=a.model.analyze
COUNTERFACTUAL_FILE='wrong-intermediate.rkt'


def strict_grid(g):
    a.model.grid_check(g)
    return [row[:] for row in g]


def public_view(episode,index):
    from reviewer_support import public_challenge_bytes
    if type(index) is not int or index<0:raise ValueError('Exact nonnegative query index required')
    try:
        # Never inspect any other query, query output, or private metadata.
        view={'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
              'test':[{'input':episode['test'][index]['input']}]}
    except (KeyError,IndexError,TypeError) as exc:raise ValueError('Malformed visible challenge') from exc
    return public_challenge_bytes(view)


def surviving_rivals(episode):
    finish=next(s['finish'] for s in a.SETTINGS if a.program(s)==episode['program_solution'])
    return [name for name in a.model.rivals(finish)
            if all(a.model.rival(p['input'],finish,name)==p['output'] for p in episode['train'])]


def dependency():
    return {'step_a':'Solve the complete contour-compatible assembly, backtracking dead-end matches and deriving predecessor identities.',
            'intermediate':'The placed-cell ownership map and attachment depth of every object relative to the spanning wall.',
            'step_b':'Select all objects at maximum attachment depth and recolor exactly their assembled cells to 9.',
            'why_b_depends_on_a':'Loose size, source position and color do not determine the interlocking predecessor chain. Later pieces can move only after earlier pieces expose their contour; the counterfactual replaces depth with source area.'}


def causal_value(g):
    info=analyze(g)
    return {'steps':[{'object_id':s['id'],'depth':s['depth'],'side':s['side'],'destination':s['origin']} for s in info['steps']],
            'source_areas':[len(o['cells']) for o in info['pieces']],
            'selected_deepest':[s['id'] for s in info['steps'] if s['depth']==max(x['depth'] for x in info['steps'])]}
