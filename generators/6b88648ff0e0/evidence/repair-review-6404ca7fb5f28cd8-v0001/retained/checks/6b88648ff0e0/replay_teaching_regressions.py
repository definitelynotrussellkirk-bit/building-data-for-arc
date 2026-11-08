"""Replay minimal before/after lessons under the real reference and rival programs."""
from pathlib import Path
import hashlib,importlib.util,json
from reviewer_support import find_root
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
root=find_root(__file__);folder=Path(__file__).resolve().parent
p=root/'generators/6b88648ff0e0/workspace/parametric/adapter.py'
s=importlib.util.spec_from_file_location('_strip_regression_adapter',p);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
initial=json.loads((folder/'teaching-before.private.json').read_text())
records=[{'seed':0,'mode':'top_to_bottom','rival':'fixed_0','episode':initial[0]['episode']}]
records+=json.loads((folder/'ordering-before.private.json').read_text())
base=a.program({'stack_order':'top_to_bottom'})
anchor='(all-rows (apply append strips))'
comparisons={
 'fixed_0':'(> (count-if (lambda (v) (= v 0)) (apply append a)) (count-if (lambda (v) (= v 0)) (apply append b)))',
 'row_sum':'(> (apply + (apply append a)) (apply + (apply append b)))',
 'lexicographic':'(let loop ((xs (apply append a)) (ys (apply append b))) (cond ((empty? xs) #f) ((< (first xs) (first ys)) #t) ((> (first xs) (first ys)) #f) (else (loop (rest xs) (rest ys)))))',
}
runtime=root/'shared/runtime';evaluations=0;results=[]
with _local_imports(runtime,p.parent):
 apply,identity,bridge=_real_evaluator(runtime)
 try:
  for record in records:
   rival,mode,seed=record['rival'],record['mode'],record['seed'];before=record['episode']
   wrong=base.replace(anchor,f'(all-rows (apply append (sort strips (lambda (a b) {comparisons[rival]}))))')
   after=a.generate(seed,{'stack_order':mode},2,4)
   query=next(p for p in before['test'] if a.claim(p['input'],rival,intended=mode)!=p['output'])
   repaired=next(p for p in after['train'] if a.claim(p['input'],rival,intended=mode)!=p['output'])
   rows=[]
   for name,pair in [('old_demo_0',before['train'][0]),('old_demo_1',before['train'][1]),('separating_query',query),('repaired_demo',repaired)]:
    g=pair['input'];right=apply(before['program_solution'],g);bad=apply(wrong,g);evaluations+=2
    assert right==pair['output']
    assert bad==a.claim(g,rival,intended=mode)
    rows.append({'name':name,'input':g,'output':right,'rival_output':bad,'equal':right==bad})
   assert [r['equal'] for r in rows]==[True,True,False,False]
   results.append({'seed':seed,'mode':mode,'rival':rival,'program':before['program_solution'],'rival_program':wrong,'cases':rows})
 finally:bridge.close()
report={'task_id':a.TASK,'status':'regressions_repaired','adapter_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'racket':identity,'racket_evaluations':evaluations,'regressions':results,'limits':'Exact finite pre-repair lessons and their repaired distinguishing demos. No universal uniqueness or training admission.'}
(folder/'teaching-regressions.private.json').write_text(json.dumps(report,sort_keys=True)+'\n')
print(json.dumps({'status':report['status'],'regressions':len(results),'racket_evaluations':evaluations}))
