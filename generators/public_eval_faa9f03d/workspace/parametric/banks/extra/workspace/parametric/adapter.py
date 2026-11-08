from pathlib import Path
from copy import deepcopy
import importlib.util, random, json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_faa_engine',HERE/'engine.py');E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
VALUES=('fragmented','complete')
def validate(settings):
    if type(settings) is not dict or set(settings)!={'crossing_policy'} or settings['crossing_policy'] not in VALUES: raise ValueError('settings')
    return settings['crossing_policy']
def program(settings):
    policy=validate(settings);s=(HERE/'canonical.rkt').read_text();old='(define crossing-policy "fragmented")'
    if s.count(old)!=1: raise ValueError('anchor')
    return s if policy=='fragmented' else s.replace(old,'(define crossing-policy "complete")',1)
def generate(seed,settings,demos=2,queries=4):
    policy=validate(settings)
    if type(seed) is not int or not 0<=seed<2**63: raise ValueError('seed')
    if type(demos) is not int or not 2<=demos<=6: raise ValueError('demos')
    if type(queries) is not int or not 1<=queries<=4: raise ValueError('queries')
    def pair(i,stress=False):
        g=E.make(seed,i,stress);return {'input':g,'output':E.solve(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(100+i,i==3) for i in range(queries)],'program_solution':program(settings)}
def present(seed,settings,demos=2,queries=4,presentation_seed=0):
    ep=generate(seed,settings,demos,4);order=list(range(4));random.Random(f'faa9f03d:{seed}:{presentation_seed}').shuffle(order)
    public=[{'train':deepcopy(ep['train']),'test':[{'input':deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]]
    return {'public':public,'private':{'settings':deepcopy(settings),'program':ep['program_solution'],'seed':seed,'presentation_seed':presentation_seed,'source_indices':order,'source_pairs':deepcopy(ep['test'])}}
def rival_program(settings,rival):
    validate(settings)
    if rival=='complete':return program({'crossing_policy':'complete'})
    if rival=='identity':return '(rule! (lambda (g) g))'
    raise ValueError('rival')
def counterfactual_program(settings):return rival_program(settings,'complete')
def intermediate(g,settings): return E.intermediate(g,validate(settings))
def dependency(): return {'step_a':'Assign singleton markers to visible path colors, repair supported row/column gaps, redirect yellow-controlled arms, and count pre-repair fragments.','intermediate':'Input-dependent repaired path claims plus per-color fragmentation evidence and yellow-ray claims.','step_b':'Resolve overlapping path claims at crossings using the episode crossing policy.','why_b_depends_on_a':'Which color owns a crossing depends on fragment counts and whether that exact cell lies on a redirected yellow ray, both derived from A; B cannot infer the winner from the crossing pixel alone.'}
def public_bytes(ep,query_index=0):
    v={'train':deepcopy(ep['train']),'test':[{'input':deepcopy(ep['test'][query_index]['input'])}]};return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
