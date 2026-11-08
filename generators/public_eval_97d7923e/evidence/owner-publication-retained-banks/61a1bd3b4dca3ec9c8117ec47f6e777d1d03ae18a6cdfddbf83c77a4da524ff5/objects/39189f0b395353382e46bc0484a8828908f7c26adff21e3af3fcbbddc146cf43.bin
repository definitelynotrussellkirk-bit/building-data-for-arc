"""Source-local native adapter for public parent 97d7923e."""
from pathlib import Path
import copy
import hashlib
import json
import random
import types

BASE=Path(__file__).resolve().parent
G=types.ModuleType('_rank_relay_engine_'+hashlib.sha256(str(BASE).encode()).hexdigest())
G.__file__=str(BASE/'engine.py')
exec(compile((BASE/'engine.py').read_bytes(),G.__file__,'exec'),G.__dict__)


def value(settings):
    if (type(settings) is not dict or set(settings)!={'relay_mode'}
            or type(settings['relay_mode']) is not str or settings['relay_mode'] not in G.VALUES):
        raise ValueError('settings must contain exactly relay_mode: rank_only|selected_longest')
    return settings['relay_mode']


def program(settings):
    mode=value(settings);source=(BASE/'canonical.rkt').read_text();anchor='(define relay-mode "rank_only")'
    if source.count(anchor)!=1:raise ValueError('Canonical relay-mode anchor changed')
    return source if mode=='rank_only' else source.replace(anchor,'(define relay-mode "selected_longest")',1)


def rival_program(settings,rival):
    value(settings)
    if rival!='relay_longest_candidate':raise ValueError('Unknown Racket counterfactual')
    source=program(settings);anchor='(define rival "")'
    if source.count(anchor)!=1:raise ValueError('Canonical rival anchor changed')
    return source.replace(anchor,f'(define rival "{rival}")',1)


def generate(seed,settings,demos=2,queries=4):
    mode=value(settings);G.integer(seed,0,2**63-1,'seed');G.integer(demos,2,6,'demos');G.integer(queries,1,4,'queries')
    ds,qs=G.input_bank(seed)
    def pair(text):
        g=json.loads(text);return {'input':g,'output':G.solve(g,mode)}
    return {'train':[pair(x) for x in ds[:demos]],'test':[pair(x) for x in qs[:queries]],
            'program_solution':program(settings)}


def present(seed,settings,demos=2,queries=4,presentation_seed=0):
    G.integer(queries,1,4,'queries');G.integer(presentation_seed,0,2**63-1,'presentation_seed')
    episode=generate(seed,settings,demos,4);order=list(range(4))
    rng=random.Random(int.from_bytes(hashlib.sha256(f'97d7923e:presentation:{seed}:{presentation_seed}'.encode()).digest(),'big'))
    rng.shuffle(order)
    public=[{'train':copy.deepcopy(episode['train']),
             'test':[{'input':copy.deepcopy(episode['test'][i]['input'])}]} for i in order[:queries]]
    private={'settings':copy.deepcopy(settings),'program':episode['program_solution'],'seed':seed,
             'presentation_seed':presentation_seed,'source_indices':order,
             'source_pairs':copy.deepcopy(episode['test'])}
    return {'public':public,'private':private}


def counterfactual_program(settings):
    return rival_program(settings,'relay_longest_candidate')


def intermediate(g,settings):
    value(settings);return G.derive(g)


def dependency():
    return {
      'step_a':'Read each top-row run as a rank, order that color’s vertical wires by interior length, and recolor the ranked wire.',
      'intermediate':'The stage-A grid plus the input-dependent selected wire and selected interior length for every legend color.',
      'step_b':'Choose the longest selected wire in legend order and recolor its horizontal 9-filled relay with the winning color.',
      'why_b_depends_on_a':'The color with the longest raw candidate is deliberately different from the color whose rank-selected wire is longest. B must consume A’s selections rather than preselecting from the original candidates.'}
