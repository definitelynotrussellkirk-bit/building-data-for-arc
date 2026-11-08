"""Authoring helpers for the d59b0160 public family."""
import hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_d59_family_adapter',HERE/'adapter.py');a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
generate=a.generate;engine=a.engine

def strict_grid(g):engine.grid_check(g);return [row[:] for row in g]

def public_view(episode,index):
    root=next(p for p in HERE.parents if (p/'shared/runtime').is_dir())
    if str(root/'shared/runtime') not in sys.path:sys.path.insert(0,str(root/'shared/runtime'))
    from reviewer_support import public_challenge_bytes
    if type(index) is not int or index<0:raise ValueError('Exact nonnegative query index required')
    try:view={'train':[{'input':p['input'],'output':p['output']} for p in episode['train']], 'test':[{'input':episode['test'][index]['input']}]}
    except (KeyError,IndexError,TypeError) as exc:raise ValueError('Malformed visible challenge') from exc
    return public_challenge_bytes(view)

def surviving_rivals(ep):
    finish=next(s['finish'] for s in a.SETTINGS if a.program(s)==ep['program_solution'])
    return [n for n in engine.rivals(finish) if all(engine.rival_output(p['input'],finish,n)==p['output'] for p in ep['train'])]

def dependency():
    return {'step_a':'Read the three-color L-key and remove every rectangular panel containing the complete key set.',
            'intermediate':'For each panel surviving stage A, the positive count of key colors missing from that panel.',
            'step_b':'Select the minimum positive missing-count class and recolor its complete marker payload to 9.',
            'why_b_depends_on_a':'Panels with missing count zero are removed by stage A; selecting before filtering chooses a deleted complete panel instead of the closest survivor.'}

def causal_value(g):
    i=engine.analyze(g);return {'key_colors':i['key_colors'],'missing_by_panel':{str(p['id']):p['missing'] for p in i['panels']},
        'complete_ids':i['complete_ids'],'closest_survivor_ids':i['closest_survivor_ids']}
