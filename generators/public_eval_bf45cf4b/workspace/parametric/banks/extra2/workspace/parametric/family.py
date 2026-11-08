"""Task-local authoring hooks, isolated from the runtime's thin adapter."""
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_motif_family_adapter_'+str(HERE),HERE/'adapter.py')
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
    return {'step_a':'Infer the monochrome layout and multicolor motif, then expand every occupied layout cell by the complete motif.',
            'intermediate':'The fully expanded binary foreground occupancy and its four-neighbor connected components, including cross-tile joins determined by motif boundary ports.',
            'step_b':'Select the complete maximum-area component class and recolor its occupied cells to 9.',
            'why_b_depends_on_a':'A larger pre-expansion layout cluster can split into smaller expanded components when opposing motif boundary ports do not meet. The counterfactual counts layout clusters before the required expansion.'}


def causal_value(g):
    info=analyze(g)
    return {'layout_component_sizes':[len(c) for c in a.model.components(info['layout'],info['background'])],
            'expanded_component_sizes':[len(c) for c in info['components']],
            'motif_shape':[len(info['motif']),len(info['motif'][0])],
            'selected_expanded_size':max(map(len,info['components']))}
