"""Task-local authoring hooks, isolated from the runtime's thin adapter."""
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_beam_family_adapter_'+str(HERE),HERE/'adapter.py')
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
    return [name for name in a.model.RIVALS
            if all(a.model.rival(p['input'],finish,name)==p['output'] for p in episode['train'])]


def dependency():
    return {'step_a':'Trace the emitter and every reached green-port beam with breadth-first relay activation.',
            'intermediate':'Input-derived reached-object set and minimum relay-hop depth for every reached object.',
            'step_b':'Select the complete deepest activation-depth class and recolor only those reached objects to 9.',
            'why_b_depends_on_a':'Object geometry, source size and reading order do not determine causal depth; unreachable large decoys and turns require the traced network. The counterfactual replaces depth with reached-object area.'}


def causal_value(g):
    info=analyze(g)
    return {'depths':info['depths'], 'object_sizes':{i:len(o['cells']) for i,o in enumerate(info['objects'])},
            'selected_deepest':[i for i,d in info['depths'].items() if d==max(info['depths'].values())]}
