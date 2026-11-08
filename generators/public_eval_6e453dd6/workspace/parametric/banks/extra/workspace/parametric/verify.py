"""Re-run bounded source-bound audits after authoring preflight.

Usage from the packet root:
  python3 review.py run python3 generators/public_eval_6e453dd6/workspace/parametric/verify.py \
    --preflight ../checks/public_eval_6e453dd6/preflight --out ../checks/public_eval_6e453dd6/audit
Output is private controller evidence; public/ contains individually revealed views.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
HOME=BASE.parent.parent
ROOT=next(p for p in HOME.parents if (p/'shared/runtime/arc_repl').is_dir())
TASK=HOME.name

def sha(raw): return hashlib.sha256(raw).hexdigest()
def raw(obj): return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def save(path,obj): path.write_bytes(raw(obj))

def load_adapter():
    spec=importlib.util.spec_from_file_location('_audit_'+TASK,BASE/'adapter.py')
    a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
    return a

def check_binding(root,binding):
    root=Path(root).resolve()
    if not binding.get('files'): raise ValueError('Missing source binding')
    for row in binding['files']:
        p=root/row['path']
        if p.is_symlink() or not p.resolve().is_relative_to(root) or not p.is_file() or sha(p.read_bytes())!=row['sha256']:
            raise ValueError('Stale or unsafe source: '+row['path'])

def validate_public(view, expected_id=None):
    from reviewer_support import public_challenge_bytes
    if type(view) is not dict or set(view)!={'train','test'}:
        raise ValueError('Only train/test are visible')
    if type(view['train']) is not list or type(view['test']) is not list or len(view['test'])!=1 or not 2<=len(view['train'])<=6:
        raise ValueError('Exactly one current query and 2..6 demos')
    if any(type(p) is not dict or set(p)!={'input','output'} for p in view['train']) or any(type(p) is not dict or set(p)!={'input'} for p in view['test']):
        raise ValueError('Hidden field in public pairs')
    b=public_challenge_bytes(view)
    inputs=[raw(p['input']) for p in view['train']+view['test']]
    if len(inputs)!=len(set(inputs)): raise ValueError('Duplicate input')
    if expected_id is not None and sha(b)!=expected_id: raise ValueError('Public hash mismatch')
    return b

def negative_case(good,kind):
    p=copy.deepcopy(good); identifier=None
    if kind=='answer': p['test'][0]['output']=[[0]]
    elif kind=='settings': p['settings']={'projection':'largest_hole'}
    elif kind=='bool': p['test'][0]['input'][0][0]=True
    elif kind=='duplicate': p['test'][0]['input']=copy.deepcopy(p['train'][0]['input'])
    elif kind=='query_count': p['test'].append(copy.deepcopy(p['test'][0]))
    elif kind=='bad_id': identifier='0'*64
    else: raise ValueError('Unknown negative control')
    return validate_public(p,identifier)

def descriptions():
    return {'step_a':'Right-dock each black component, flood the background to recover genuinely enclosed cavities, and identify wall-contacting cavity rows.',
            'intermediate':'The ordered eligible cavity components, their actual areas, and their wall-contact row sets after docking.',
            'step_b':'Select the greatest-area eligible cavity (top/left tie-break), then project its contact rows in red through the wall.',
            'why_b_depends_on_a':'The selector consumes enclosed-region areas and contact eligibility, not black object sizes or bounding boxes. The wrong-intermediate program preserves the same final docked shapes but supplies pre-docking eligibility; this changes only the projection decision.'}

def pack_witness(binding, identity, cases):
    """Use the owner's exact two-field execution envelope; retain full hashes separately."""
    if identity.get('backend')!='racket' or identity.get('protected') is not True:
        raise ValueError('A live protected Racket identity is required')
    return {'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':TASK,
            'source_binding':binding,**descriptions(),
            'racket':{'backend':'racket','protected':True},
            'runtime_identity':identity,'cases':cases}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=32)
    args=p.parse_args(argv)
    if not 1<=args.seeds<=256: raise ValueError('Use 1..256 bounded seeds')
    q=json.loads((args.preflight/'preflight.json').read_bytes()); check_binding(ROOT,q['source_binding'])
    if q.get('status')!='passed' or q.get('owner_accepted') is not False: raise ValueError('Expected unapproved passing preflight')
    for name,digest in q['evidence_sha256'].items():
        if sha((args.preflight/name).read_bytes())!=digest: raise ValueError('Changed preflight evidence')
    a=load_adapter(); c=a.CORE
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    from arcpuzzles.review_witness import _validate_programs
    from reviewer_support import public_challenge_bytes
    for path in BASE.glob('*.rkt'):
        _validate_programs([{'program':path.read_text(),'counterfactual_program':path.read_text()}])
    episodes=0;checks=0;stress=0;totals=set();shapes=set();findings=[]
    for seed in range(args.seeds):
        for demos in (2,3,6):
            for mode in c.MODES:
                e=a.generate(seed,{'projection':mode},demos,4); episodes+=1
                if len({raw(x['input']) for sp in ('train','test') for x in e[sp]})!=demos+4: raise ValueError('Duplicate inputs')
                for pair in e['train']+e['test']:
                    info=c.analyze(pair['input']); totals.add(info['eligible_count']); shapes.add((len(pair['input']),len(pair['input'][0])))
                stress+=sum(len(x['input'])==len(x['input'][0])==30 for x in e['test'])
                for rival in c.RIVALS:
                    checks+=1
                    # Errors are fatal: an undefined rival is not teaching evidence.
                    fits=all(c.rival(x['input'],rival,mode)==x['output'] for x in e['train'])
                    changes=[i for i,x in enumerate(e['test']) if c.rival(x['input'],rival,mode)!=x['output']]
                    if fits and changes: findings.append({'seed':seed,'demos':demos,'mode':mode,'rival':rival,'query_indices':changes})
    args.out.mkdir(parents=True,exist_ok=False); public=args.out/'public';public.mkdir()
    save(args.out/'adversarial.json',{'status':'failed' if findings else 'passed','episodes':episodes,'seeds':args.seeds,'named_rival_checks':checks,'rivals':list(c.RIVALS),'findings':findings,'intermediates':sorted(totals),'grid_sizes':sorted(shapes),'stress_queries':stress,'source_binding':q['source_binding'],'limits':'Finite Python claim/rival audit; protected parity is reported separately. Not universal uniqueness.'})
    if findings: raise ValueError('Named-rival teaching failures: '+str(findings[:3]))
    execution=json.loads((args.preflight/'execution.json').read_bytes()); projections=[];mutations=0
    for ei,e in enumerate(execution['episodes']):
        ids=[]
        for i in range(4):
            v=a.public_view(e,i); b=validate_public(v); identifier=sha(b)
            if b!=public_challenge_bytes(v): raise ValueError('Different public serialization')
            (public/(identifier+'.json')).write_bytes(b);ids.append(identifier)
        initial=validate_public(a.public_view(e,0))
        variants=[]
        y=copy.deepcopy(e);y['test']=y['test'][:1];variants.append(y)
        y=copy.deepcopy(e);y['program_solution']='PRIVATE';y['settings']={'secret':True};y['seed']=None;variants.append(y)
        y=copy.deepcopy(e)
        for pair in y['test']: pair['output']={'secret':'not a grid'}
        variants.append(y)
        y=copy.deepcopy(e);y['test']=[y['test'][0],{}, {'input':'not a grid'}];variants.append(y)
        for y in variants:
            if validate_public(a.public_view(y,0))!=initial: raise ValueError('Private metadata changed first turn')
            mutations+=1
        y=copy.deepcopy(e);y['test'][0]['input'][0][0]=(y['test'][0]['input'][0][0]+1)%10
        if validate_public(a.public_view(y,0))==initial: raise ValueError('Visible mutation was ignored')
        if a.public_view(a.generate(e['seed'],e['settings'],len(e['train']),1),0)!=a.public_view(e,0): raise ValueError('First turn changed with query count')
        projections.append({'episode_index':ei,'public_ids':ids,'private_source_order':a.source_order(e['seed'])})
    negatives=[]
    good=a.public_view(execution['episodes'][0],0)
    for kind in ('answer','settings','bool','duplicate','query_count','bad_id'):
        try: negative_case(good,kind)
        except ValueError: negatives.append(kind)
        else: raise ValueError('Negative control accepted: '+kind)
    save(args.out/'public-export.json',{'status':'passed','public_views':sum(len(x['public_ids']) for x in projections),'private_mutations':mutations,'positive_controls':len(projections),'negative_controls_rejected':negatives,'episodes':projections,'source_binding':q['source_binding'],'limits':'One file per revealed query. Directory listing and all receipts stay controller-private.'})
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime'); evaluations=0
    try:
        for seed in (5,19,61):
            for mode in c.MODES:
                e=a.generate(seed,{'projection':mode},6,4)
                for pair in e['train']+e['test']:
                    output=_grid(apply(e['program_solution'],pair['input']));evaluations+=1
                    if output!=pair['output']: raise ValueError(f'Racket/Python mismatch seed={seed} mode={mode}')
        candidate=None
        counter=(BASE/'raw_contact.rkt').read_text()
        for e in execution['episodes']:
            if e['settings']!={'projection':'largest_hole'}: continue
            for pair in e['test']:
                if len(pair['input'])==len(pair['input'][0])==30 and c.solve(pair['input'],'largest_hole',strategy='raw_contact')!=pair['output']:
                    candidate=(e,pair);break
            if candidate:break
        if not candidate: raise ValueError('No preflight-bound 30x30 witness')
        e,pair=candidate;normal=_grid(apply(e['program_solution'],pair['input']));wrong=_grid(apply(counter,pair['input']));evaluations+=2
        if normal!=pair['output'] or wrong==normal: raise ValueError('Invalid causal replay')
        if wrong!=c.solve(pair['input'],'largest_hole',strategy='raw_contact'):raise ValueError('Ablation mirror differs')
        meta=c.analyze(pair['input']);delta=sum(x!=y for r,s in zip(normal,wrong) for x,y in zip(r,s))
        witness=pack_witness(q['source_binding'],identity,[{'input':pair['input'],'settings':e['settings'],'intermediate_value':{'eligible_cavity_areas':[o['area'] for o in meta['eligible']],'eligible_contact_rows':[o['contact_rows'] for o in meta['eligible']],'raw_eligible_count':len([o for o in c.cavities(meta['grid'],meta['background'],meta['wall']) if o['contact_rows']])},'program':e['program_solution'],'output':normal,'counterfactual_program':counter,'counterfactual_output':wrong,'ablation':'wrong_intermediate'}])
        save(args.out/'witness.json',witness)
        # A second evaluation guards against transcription of a first-run label.
        for program,expected in ((e['program_solution'],normal),(counter,wrong)):
            if _grid(apply(program,pair['input']))!=expected:raise ValueError('Witness repeat failed')
            evaluations+=1
        save(args.out/'causal-replay.json',{'status':'protected_author_replayed','changed_cells':delta,'racket':identity,'witness_sha256':sha((args.out/'witness.json').read_bytes()),'source_binding':q['source_binding'],'limits':'Author-run replay of both programs; intermediate interpretation is authored. Not native qualification or owner acceptance.'})
    finally: bridge.close()
    check_binding(ROOT,q['source_binding'])
    summary={'status':'passed','task_id':TASK,'episodes':episodes,'named_rival_checks':checks,'protected_racket_evaluations':evaluations,'racket':identity,'source_binding':q['source_binding'],'owner_accepted':False,'training_admitted':False}
    save(args.out/'audit.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('source_binding','racket')},sort_keys=True))

if __name__=='__main__': main()
