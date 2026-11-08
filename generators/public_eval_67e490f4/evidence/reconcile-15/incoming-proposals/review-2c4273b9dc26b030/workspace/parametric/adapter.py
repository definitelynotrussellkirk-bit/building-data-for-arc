from pathlib import Path
from copy import deepcopy
import importlib.util, random, hashlib, json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_shapevote_engine',HERE/'engine.py');E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
VALUES=('dihedral','translation_only')
def validate(settings):
    if type(settings) is not dict or set(settings)!={'match_mode'} or settings['match_mode'] not in VALUES: raise ValueError('settings')
    return settings['match_mode']
def program(settings):
    mode=validate(settings);s=(HERE/'canonical.rkt').read_text()
    old='(define match-mode "dihedral")'
    if s.count(old)!=1:raise ValueError('anchor')
    return s if mode=='dihedral' else s.replace(old,'(define match-mode "translation_only")',1)
def generate(seed,settings,demos=2,queries=4):
    mode=validate(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('seed')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries')
    def pair(i,stress=False):
        g=E.make(seed,i,stress);return {'input':g,'output':E.solve(g,mode)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(100+i,i==3) for i in range(queries)],'program_solution':program(settings)}
def present(seed,settings,demos=2,queries=4,presentation_seed=0):
    ep=generate(seed,settings,demos,4); order=list(range(4));random.Random(f'67e490f4:{seed}:{presentation_seed}').shuffle(order)
    public=[{'train':deepcopy(ep['train']),'test':[{'input':deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]]
    return {'public':public,'private':{'settings':deepcopy(settings),'program':ep['program_solution'],'seed':seed,'presentation_seed':presentation_seed,'source_indices':order,'source_pairs':deepcopy(ep['test'])}}
def rival_program(settings,rival):
    validate(settings)
    if rival=='translation_only':return program({'match_mode':'translation_only'})
    if rival=='identity':return '(rule! (lambda (g) g))'
    raise ValueError('rival')
def counterfactual_program(settings):return rival_program(settings,'translation_only')
def intermediate(g,settings):
    mode=validate(settings);st=E.derive(g,mode)
    return {'box':st['box'],'hole_votes':[{'shape':E.norm(x['hole']),'counts':x['counts'],'winner':x['winner']} for x in st['holes']]}
def dependency():
    return {'step_a':'Segment external monochrome cue objects and tableau holes, then tally color votes for each dihedral shape class.','intermediate':'Input-dependent table of each hole shape, matching cue-color counts, and its majority winner.','step_b':'Crop the tableau and fill every enclosed hole from the winner stored by stage A.','why_b_depends_on_a':'The output color of a hole is absent from the tableau itself and changes when an external cue vote is recolored or rotated; B cannot choose it without A.'}
def public_bytes(ep,query_index=0):
    v={'train':deepcopy(ep['train']),'test':[{'input':deepcopy(ep['test'][query_index]['input'])}]};return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
