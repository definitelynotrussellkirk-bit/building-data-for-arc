"""Reusable finite rival audit and guarded preflight export/causal replay.

Run through review.py run. Artifacts remain author-private; no catalog writes,
no acceptance claims. Source drift, changed execution receipts, duplicate public
views, wrong Racket labels, and unchanged counterfactuals are fatal.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
TASK=BASE.parents[1].name

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
adapter=load(BASE/'adapter.py','_path_review_adapter')
model=adapter.kernel


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def check_binding(root,receipt):
    root=Path(root).resolve()
    for row in receipt['source_binding']['files']:
        p=root/row['path']
        if not p.resolve().is_relative_to(root) or p.is_symlink() or not p.is_file():
            raise ValueError('unsafe/missing bound source: '+row['path'])
        if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('source drift: '+row['path'])


def write_public_bundle(episodes,destination):
    """Hash only exact visible bytes; disk order has no private-seed ordering."""
    support=load(ROOT/'shared/runtime/reviewer_support.py','_path_public_serializer')
    destination=Path(destination)
    if destination.exists():raise FileExistsError('choose a new public bundle destination')
    visible={};private=[]
    for e in episodes:
        presentation_seed=7541+e['seed']
        turns=adapter.public_turns(e,presentation_seed)
        # Hidden metadata and query gold cannot affect the public projection.
        changed=copy.deepcopy(e);changed['settings']={'private_mutation':True};changed['program_solution']='hidden'
        for p in changed['test']:p['output']=[[9]]
        if turns!=adapter.public_turns(changed,presentation_seed):raise ValueError('private field leak')
        ids=[];source_indices=[]
        for turn in turns:
            raw=support.public_challenge_bytes(turn);identifier=hashlib.sha256(raw).hexdigest()
            if identifier in visible:raise ValueError('duplicate visible payload')
            visible[identifier]=raw;ids.append(identifier)
            source_indices.append(next(i for i,p in enumerate(e['test']) if p['input']==turn['test'][0]['input']))
        private.append({'seed':e['seed'],'settings':e['settings'],'view_ids':ids,
                        'source_indices':source_indices,'presentation_seed':presentation_seed,
                        'answers':[e['test'][i]['output'] for i in source_indices]})
    (destination/'public').mkdir(parents=True)
    for identifier in sorted(visible):
        (destination/'public'/f'{identifier}.json').write_bytes(visible[identifier])
    write(destination/'private.json',{'controller_only':True,'episodes':private,
        'notice':'Give the model a single public file only. Never disclose this file or directory listing.'})
    result={'status':'passed','episodes':len(episodes),'views':len(visible),
            'public_keys':['train','test'],'queries_per_view':1,'private_invariance':True,
            'creation_order':'sorted_visible_sha256','training_admitted':False}
    write(destination/'export-report.json',result)
    return result


def all_routes(graph):
    start,end=graph['endpoints'];found=[]
    def visit(node,nodes,edges):
        if node==end:
            found.append({'nodes':nodes,'edges':edges});return
        for i,e in enumerate(graph['edges']):
            if node not in e['nodes']:continue
            other=next(v for v in e['nodes'] if v!=node)
            if other not in nodes:visit(other,nodes+[other],edges+[i])
    visit(start,[start],[])
    return sorted(found,key=lambda p:p['nodes'])


def rivals(g,scope):
    graph=model.analyze(g);selected=model.choose_route(graph,scope)
    paths=all_routes(graph)
    ink=lambda p:sum(len(graph['edges'][i]['cells']) for i in p['edges'])
    first=paths[0];last=paths[-1]
    longest=max(paths,key=lambda p:(ink(p),p['nodes']))
    most=max(paths,key=lambda p:(len(p['edges']),p['nodes']))
    one=next((p for p in paths if len(p['nodes'])==3),{'nodes':[],'edges':[]})
    three=next((p for p in paths if len(p['nodes'])==5),{'nodes':[],'edges':[]})
    all_graph={'nodes':[graph['endpoints'][0]]+[i for i in range(len(graph['nodes'])) if i not in graph['endpoints']]+[graph['endpoints'][1]],'edges':list(range(len(graph['edges'])))}
    changed_endpoints=model.paint(g,graph,selected)
    for i in graph['endpoints']:
        for r,c in graph['nodes'][i]['cells']:changed_endpoints[r][c]=3
    # A total wrong four-connectivity solver: disconnected endpoints mean no-op.
    four={**graph,'edges':[]}
    for edge in graph['edges']:
        for part in model.components(edge['cells'],diagonal=False):
            ends=[i for i,n in enumerate(graph['nodes']) if any(max(abs(r-y),abs(c-x))<=1 for r,c in part for y,x in n['cells'])]
            if len(ends)==2:four['edges'].append({'nodes':ends,'cells':part})
    try:four_output=model.paint(g,four,model.choose_route(four,scope))
    except ValueError:four_output=[row[:] for row in g]
    return {
        'opposite_metric':model.solve(g,'least_ink' if scope=='fewest_edges' else 'fewest_edges'),
        'identity':g,
        'all_graph_components':model.paint(g,graph,all_graph),
        'nodes_only':model.paint(g,graph,{**selected,'edges':[]}),
        'pipes_only':model.paint(g,graph,{**selected,'nodes':[]}),
        'also_recolor_endpoints':changed_endpoints,
        'first_reading_order_path':model.paint(g,graph,first),
        'last_reading_order_path':model.paint(g,graph,last),
        'maximum_ink':model.paint(g,graph,longest),
        'maximum_hops':model.paint(g,graph,most),
        'exactly_one_intermediate':model.paint(g,graph,one),
        'exactly_three_intermediates':model.paint(g,graph,three),
        'four_connected_pipes':four_output,
    }


def run_audit(out,seeds=(0,17)):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    out=Path(out)
    if out.exists():raise FileExistsError('choose a new audit directory')
    findings=[];episodes=0;claims=0;checks=0;cache={};rows=[]
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for seed in seeds:
                for demos in (2,3,6):
                    for scope in ('fewest_edges','least_ink'):
                        e=adapter.generate(seed,{'route_metric':scope},demos,4);episodes+=1
                        predictions=[rivals(p['input'],scope) for p in e['train']+e['test']]
                        for p in e['train']+e['test']:
                            claims+=1;key=(e['program_solution'],json.dumps(p['input']))
                            if key not in cache:cache[key]=_grid(apply(key[0],p['input']))
                            if cache[key]!=p['output']:findings.append({'kind':'racket_parity','seed':seed,'scope':scope,'input':p['input']})
                        survivors=[];harmful=[]
                        for name in predictions[0]:
                            checks+=1
                            if all(predictions[i][name]==p['output'] for i,p in enumerate(e['train'])):
                                survivors.append(name)
                                if any(predictions[demos+i][name]!=p['output'] for i,p in enumerate(e['test'])):
                                    harmful.append(name)
                                    findings.append({'kind':'harmful_survivor','name':name,'seed':seed,'demos':demos,'scope':scope})
                        rows.append({'seed':seed,'demos':demos,'scope':scope,'survivors':survivors,'harmful':harmful})
        finally:bridge.close()
    result={'status':'passed' if not findings else 'failed','task_id':TASK,'episodes':episodes,
            'label_claims':claims,'protected_racket_evaluations':len(cache),'rival_checks':checks,
            'rival_names':list(predictions[0]),'lessons':rows,'findings':findings,'racket':identity,
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(BASE.glob('*')) if p.is_file() and p.suffix in ('.py','.rkt','.json')},
            'limits':'Finite named rivals and sampled seeds only; not universal uniqueness or owner acceptance.'}
    write(out/'audit.json',result)
    if findings:raise ValueError(f'{len(findings)} audit findings; see {out}/audit.json')
    return {k:result[k] for k in ('status','episodes','label_claims','protected_racket_evaluations','rival_checks')}


DEPENDENCY={
    'step_a':'Infer square nodes, the two endpoint squares, and eight-connected pipe edges; compute a minimum-total-ink endpoint route on that input-dependent graph.',
    'intermediate':'Node identities, edge incidence and pixel counts, and the ordered selected node and edge indices.',
    'step_b':'Recolor only selected pipe components to gray 5 and selected intermediate squares to green 3, leaving both endpoint squares and all off-route branches unchanged.',
    'why_b_depends_on_a':'The route is a global graph property, not a local geometric direction. Which complete components B paints cannot be selected before the graph and minimum-cost route are inferred.'}


def finalize(preflight,out):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    preflight=Path(preflight).resolve();out=Path(out)
    if out.exists():raise FileExistsError('choose a new finalized directory')
    receipt=json.loads(preflight.read_text());check_binding(ROOT,receipt)
    if receipt.get('task_id')!=TASK or receipt.get('status')!='passed':raise ValueError('wrong preflight')
    for name,sha in receipt['evidence_sha256'].items():
        if hashlib.sha256(preflight.with_name(name).read_bytes()).hexdigest()!=sha:raise ValueError('preflight evidence drift')
    execution=json.loads(preflight.with_name('execution.json').read_text())
    e=next(e for e in execution['episodes'] if e['settings']=={'route_metric':'least_ink'} and e['seed']==17)
    pair=e['test'][3];program=e['program_solution']
    old="(define metric 'least_ink)"
    if program.count(old)!=1:raise ValueError('counterfactual edit anchor is not unique')
    counterfactual=program.replace(old,"(define metric 'fewest_edges)")
    graph=model.analyze(pair['input'])
    intermediate={'nodes':[{'color':n['color'],'origin':n['cells'][0],'area':len(n['cells'])} for n in graph['nodes']],
                  'edges':[{'nodes':edge['nodes'],'ink':len(edge['cells'])} for edge in graph['edges']],
                  'endpoints':graph['endpoints'], 'selected':model.choose_route(graph,'least_ink'),
                  'counterfactual_selected':model.choose_route(graph,'fewest_edges')}
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            actual=_grid(apply(program,pair['input']));alternative=_grid(apply(counterfactual,pair['input']))
            if actual!=pair['output'] or actual==alternative:raise ValueError('causal replay mismatch or no effect')
        finally:bridge.close()
    witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':receipt['source_binding'],
             'racket':{'backend':'racket','protected':True},**DEPENDENCY,
             'cases':[{'input':pair['input'],'settings':e['settings'],'intermediate_value':intermediate,
                       'program':program,'output':actual,'counterfactual_program':counterfactual,
                       'counterfactual_output':alternative,'ablation':'wrong_intermediate'}]}
    out.mkdir(parents=True);write(out/'witness.json',witness)
    progress={'sequential_dependency':{**DEPENDENCY,'witness_path':str(out/'witness.json')}}
    validate_sequential_witness(progress,receipt,lambda p:Path(p).read_bytes())
    replay=replay_witness(ROOT,witness,timeout=60);replay['status']='reviewer_replayed'
    replay['owner_accepted']=False;write(out/'replay.json',replay)
    exports=write_public_bundle(execution['episodes'],out/'preview')
    check_binding(ROOT,receipt)
    result={'status':'passed','owner_accepted':False,'training_admitted':False,
            'causal_changed_cells':sum(a!=b for ra,rb in zip(actual,alternative) for a,b in zip(ra,rb)),
            'causal_protected_evaluations':4,'exports':exports,'racket':identity}
    write(out/'summary.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['audit','finalize'])
    p.add_argument('--out',type=Path,required=True);p.add_argument('--preflight',type=Path)
    args=p.parse_args()
    if args.command=='audit':result=run_audit(args.out)
    else:
        if not args.preflight:p.error('--preflight is required for finalize')
        result=finalize(args.preflight,args.out)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
