"""Authoring helpers for the e376de54 public family."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_e376_family_adapter',HERE/'adapter.py');a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
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
    return {'step_a':'Order all parallel segments by lane and translate the complete spatially central segment onto every lane.',
            'intermediate':'The central segment\'s exact occupied template and each segment\'s symmetric-difference adjustment to its translated target.',
            'step_b':'Select the maximum-adjustment class and recolor its complete translated segment to 9.',
            'why_b_depends_on_a':'The winner is not the longest or shortest raw segment in general; it depends on the exact translated central template produced by stage A.'}

def causal_value(g):
    i=engine.analyze(g);return {'target_length':i['target_length'],'lengths':[o['length'] for o in i['objects']],
        'largest_adjustment_ids':i['largest_adjustment_ids'],'largest_original_ids':i['largest_original_ids']}
