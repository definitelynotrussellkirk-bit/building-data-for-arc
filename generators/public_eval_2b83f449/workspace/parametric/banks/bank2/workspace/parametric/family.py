"""Task-local authoring hooks, isolated from the runtime's thin adapter."""
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_gate_family_adapter_'+str(HERE),HERE/'adapter.py')
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
    flow=next(s['flow'] for s in a.SETTINGS if a.program(s)==episode['program_solution'])
    return [name for name in a.model.RIVALS
            if all(a.model.rival(p['input'],flow,name)==p['output'] for p in episode['train'])]


def dependency():
    return {'step_a':'Rewrite each orange gate as cyan side passages and a vertical magenta pole, then discover four-connected cyan paths.',
            'intermediate':'Gate-derived path membership, path endpoints and the original green population assigned to each path.',
            'step_b':'Choose the flow-selected endpoint of each derived path and pack its green population inward along that path.',
            'why_b_depends_on_a':'The gates join and split original cyan strips, so component membership and endpoints are not available from the initial strips. The counterfactual routes on the old strips while drawing the correct opened gates.'}


def causal_value(g):
    info=analyze(g)
    return {'paths':[{'endpoints':c['endpoints'],'sources':c['sources'],
                      'upper_destinations':a.model.destinations(c,'up'),
                      'lower_destinations':a.model.destinations(c,'down')}
                     for c in info['components'] if c['sources']],
            'gates':info['gates']}
