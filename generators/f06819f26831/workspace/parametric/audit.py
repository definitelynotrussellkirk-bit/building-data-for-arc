"""Bounded native lesson audit. Run through the packet's protected runtime.

This tool records finite tests, never owner acceptance or training admission.
Repeated prefix requests are reported separately from distinct scene inputs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback

HERE=Path(__file__).resolve().parent
TASK=HERE.parents[1].name

def _load(name):
    path=HERE/(name+'.py')
    spec=importlib.util.spec_from_file_location(TASK+'_'+name+'_audit',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

adapter=_load('adapter')
contract=json.loads((HERE/'promotion.json').read_text())
KEY=next(iter(contract['parameters']))
MODES=contract['parameters'][KEY]

def _bytes(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def sweep(seeds):
    if type(seeds) is not int or not 1<=seeds<=100:raise ValueError('seeds must be 1..100')
    report=dict(requests=0,pairs=0,matched_inputs=0,public_turns=0,prefix_checks=0)
    unique=set();first=set();predictions={}
    for seed in range(seeds):
        full={mode:adapter.generate(seed,{KEY:mode},6,4) for mode in MODES}
        for mode in MODES:
            first.add(hashlib.sha256(_bytes(full[mode]['test'][0]['input'])).hexdigest())
        for demos in range(2,7):
            for queries in range(1,5):
                by_mode=[]
                for mode in MODES:
                    e=adapter.generate(seed,{KEY:mode},demos,queries)
                    assert e['train']==full[mode]['train'][:demos]
                    assert e['test']==full[mode]['test'][:queries]
                    report['prefix_checks']+=1
                    ins=[_bytes(p['input']) for p in e['train']+e['test']]
                    assert len(ins)==len(set(ins)), 'within-episode input duplication'
                    unique.update(ins);by_mode.append(ins)
                    for pair in e['train']+e['test']:
                        for g in pair.values():
                            assert type(g) is list and 1<=len(g)<=30 and 1<=len(g[0])<=30
                            assert all(type(row) is list and len(row)==len(g[0]) and all(type(v) is int and 0<=v<=9 for v in row) for row in g)
                        key=(mode,_bytes(pair['input']))
                        if key not in predictions:predictions[key]=adapter.predict(pair['input'],mode)
                        assert predictions[key]==pair['output']
                    for i in range(queries):
                        view=adapter.public_view(e,i)
                        assert view=={'train':e['train'],'test':[{'input':e['test'][i]['input']}]}
                        changed=copy.deepcopy(e)
                        changed['program_solution']='private different program'
                        changed['seed']=-123;changed['settings']={KEY:'private'}
                        for j,pair in enumerate(changed['test']):
                            pair['output']=[[9]]
                            if j!=i:pair['input']=[[7]]
                        assert adapter.public_view(changed,i)==view
                        report['public_turns']+=1
                    report['requests']+=1;report['pairs']+=len(ins)
                assert by_mode[0]==by_mode[1], 'setting leaked into input sampler'
                report['matched_inputs']+=1
    report.update(unique_inputs=len(unique),distinct_first_queries=len(first),seeds=seeds,failures=0,
                  limit='Finite claim-label and privacy sweep; protected labels are counted separately.')
    return report

def hypotheses(mode):
    exact=adapter.program({KEY:mode});other=next(x for x in MODES if x!=mode)
    result={'other_setting':adapter.program({KEY:other})}
    # This literal is the authority's partial-candidate predicate. Filtering
    # singletons demonstrates the retained production documentation mismatch.
    result['ignore_multicell_partials']=exact.replace('(!= v 0)',
        '(and (!= v 0) (any? (lambda (o) (and (= (obj-size o) 1) (member (list r c) (obj-cells o)))) (objects-multicolor g 0)))')
    result['least_coverage_first']=exact.replace('(> (first a) (first b))','(< (first a) (first b))')
    if mode=='largest_gain':
        result['largest_completed_area']=exact.replace('(define (score o) (gain o))','(define (score o) (obj-size o))')
        result['largest_original_partial']=exact.replace('(define (score o) (gain o))','(define (score o) (- (obj-size o) (gain o)))')
        result['smallest_original_partial']=result['largest_original_partial'].replace('(best (apply max scores))','(best (apply min scores))')
        result['first_changed']=exact.replace('(winners (filter (lambda (o) (= (score o) best)) changed))','(winners (list (first changed)))')
        result['last_changed']=exact.replace('(winners (filter (lambda (o) (= (score o) best)) changed))','(winners (list (last changed)))')
        result['only_new_cells']=exact.replace('(obj-cells (first winners)) 8)',
            '(filter (lambda (p) (= (at g (first p) (second p)) 0)) (obj-cells (first winners))) 8)')
    assert all(p!=exact for p in result.values()), 'unchanged alleged rival'
    return result

def run(output,seeds=20):
    from reviewer_support import find_root,public_challenge_bytes
    from arcpuzzles.parametric_worker import _real_evaluator
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    report={'task_id':TASK,'status':'running','training_admitted':False}
    try:
        report['sweep']=sweep(seeds)
        root=find_root(HERE)
        apply,identity,bridge=_real_evaluator(root if (root/'RUNTIME_MANIFEST.json').is_file() else root/'shared/runtime')
        report['racket']=identity;report['racket_evaluations']=0
        private=[];public={};lessons=[];findings=[]
        def execute(program,g):
            answer=apply(program,g);report['racket_evaluations']+=1;return answer
        try:
            for seed,demos in ((0,2),(17,3)):
                for mode in MODES:
                    e=adapter.generate(seed,{KEY:mode},demos,4)
                    program=e['program_solution']
                    for pair in e['train']+e['test']:
                        assert execute(program,pair['input'])==pair['output'], 'Racket/claim disagreement'
                    lesson={'seed':seed,'demos':demos,'settings':{KEY:mode},'rivals':[]}
                    for name,wrong in hypotheses(mode).items():
                        train=[execute(wrong,p['input']) for p in e['train']]
                        test=[execute(wrong,p['input']) for p in e['test']]
                        fits=all(y==p['output'] for y,p in zip(train,e['train']))
                        differs=[i for i,(y,p) in enumerate(zip(test,e['test'])) if y!=p['output']]
                        row={'name':name,'program':wrong,'train_outputs':train,'test_outputs':test,
                             'fits_demos':fits,'query_disagreements':differs}
                        lesson['rivals'].append(row)
                        if fits and differs:findings.append({'seed':seed,'settings':{KEY:mode},'rival':name,'query_indices':differs})
                    lessons.append(lesson)
                    private.append({'seed':seed,'settings':{KEY:mode},**e})
                    for i in range(4):
                        payload=public_challenge_bytes(adapter.public_view(e,i))
                        public[hashlib.sha256(payload).hexdigest()]=payload
        finally:bridge.close()
        (out/'public').mkdir()
        for name,payload in sorted(public.items()):
            (out/'public'/f'{name}.json').write_bytes(payload)
        report.update(status='pass' if not findings else 'teaching_failure',
                      public_views=len(public),lessons=lessons,teaching_findings=findings,
                      private_examples='examples.private.json',
                      limits='Finite declared-rival check, not universal uniqueness or learning benefit.')
        (out/'examples.private.json').write_bytes(_bytes(private))
        (out/'audit.json').write_bytes(_bytes(report))
        if findings:raise AssertionError(f'Teaching holes: {findings}')
        return report
    except Exception:
        (out/'failure.json').write_bytes(_bytes({'error':traceback.format_exc(),'partial_report':report}))
        raise

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True);parser.add_argument('--seeds',type=int,default=20)
    args=parser.parse_args();report=run(args.out,args.seeds)
    print(json.dumps({k:v for k,v in report.items() if k!='lessons'},sort_keys=True))

if __name__=='__main__':main()
