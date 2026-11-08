"""Replay the retained seed-48 color-sorting teaching failure and its repair in Racket."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent

def load(name):
    spec=importlib.util.spec_from_file_location('_color_replay_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def color_sorted_program(adapter):
    program=adapter.program(adapter.DEFAULT)
    old='(define order (second (first candidates)))'
    new='''(define (main-color i)
     (apply min (filter (lambda (v) (not (= v 7))) (apply append (list-ref tiles i)))))
   (define order
     (sort (range n) (lambda (i j)
       (if (= (main-color i) (main-color j)) (< i j) (< (main-color i) (main-color j))))))'''
    if program.count(old)!=1:raise ValueError('canonical chain-order binding changed; adapt counterfactual explicitly')
    return program.replace(old,new,1)

def run(preflight,out):
    root=next(p for p in HERE.parents if (p/'src/arcpuzzles/parametric_worker.py').is_file())
    a=load('adapter');v=load('verify');receipt=json.loads(Path(preflight).read_text());v.verify_binding(root,receipt)
    k=next(iter(a.PARAMETERS));programs={json.dumps({k:m},sort_keys=True,separators=(',',':')):a.program({k:m}) for m in a.PARAMETERS[k]}
    v.verify_receipt_identity(receipt,HERE.parents[1].name,programs)
    fixture=HERE.parents[1]/'tests/color-shortcut-before.json';old=json.loads(fixture.read_text())
    program=a.program(a.DEFAULT);wrong=color_sorted_program(a)
    if old['program']!=program:raise ValueError('retained canonical rule changed')
    sys.path[:0]=[str(root/'src'),str(root/'shared/runtime')]
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_programs import strict_programs
    syntax=strict_programs(root,[program,wrong])
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');rows=[]
    try:
        fresh=a.generate(old['seed'],a.DEFAULT,2,4)
        for phase,split,pairs in [('before','train',old['train']),('before','test',old['test']),('after','train',fresh['train'])]:
            for index,pair in enumerate(pairs):
                actual=apply(program,pair['input']);other=apply(wrong,pair['input'])
                if actual!=pair['output']:raise ValueError('reference label mismatch')
                if other!=a.predict(pair['input'],'color_sort'):raise ValueError('Racket/Python rival mismatch')
                rows.append({'phase':phase,'split':split,'index':index,'input':pair['input'],'output':actual,'rival_output':other,'rival_matches':actual==other})
    finally:bridge.close()
    assert all(r['rival_matches'] for r in rows if r['phase']=='before' and r['split']=='train')
    assert any(not r['rival_matches'] for r in rows if r['phase']=='before' and r['split']=='test')
    assert any(not r['rival_matches'] for r in rows if r['phase']=='after')
    report={'status':'passed','source_binding':receipt['source_binding'],'racket':identity,'seed':old['seed'],
            'program':program,'counterfactual_program':wrong,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
            'evaluations':2*len(rows),'program_syntax':syntax,'cases':rows,
            'limits':'One retained before/after teaching regression. No universal uniqueness or owner acceptance.'}
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
    v.verify_binding(root,receipt)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preflight',required=True,type=Path);parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();r=run(args.preflight,args.out);print(json.dumps({'status':r['status'],'evaluations':r['evaluations'],'seed':r['seed']}))
if __name__=='__main__':main()
