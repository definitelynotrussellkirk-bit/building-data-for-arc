"""Reproduce the retained two-demo largest-area hole and its constructive repair."""
import json,hashlib
from pathlib import Path
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
from reviewer_support import find_root
root=find_root(__file__)
p=root/'generators/8069b5294ce4/workspace/parametric/adapter.py'
s=p.read_text(); old=s.replace("        if stream == 'demo:0':\n            th = tw = 2  # 28 selected cells versus a 50-cell non-blue component.\n",'')
assert old != s
before={'__file__':str(p),'__name__':'before_compact_repair'};exec(compile(old,str(p),'exec'),before)
after={'__file__':str(p),'__name__':'after_compact_repair'};exec(compile(s,str(p),'exec'),after)
e=before['generate'](54,{'selection':'whole_cluster'},2,4)
canonical=e['program_solution']
old_cl='(define cl (cluster-from g objs seed (range 0 (length objs))))'
new_cl='(define groups (map (lambda (i) (cluster-from g objs i (range 0 (length objs)))) (range 0 (length objs)))) (define cl (first (sort groups (lambda (a b) (> (apply + (map (lambda (i) (length (obj-cells (list-ref objs i)))) a)) (apply + (map (lambda (i) (length (obj-cells (list-ref objs i)))) b)))))))'
rival=canonical.replace(old_cl,new_cl)
runtime=root/'shared/runtime'
with _local_imports(runtime,p.parent):
 apply,identity,bridge=_real_evaluator(runtime)
 try:
  cases=[]
  grids=[('before_demo_0',e['train'][0]['input']),('before_demo_1',e['train'][1]['input']),('before_query_1',e['test'][1]['input']),('repaired_demo_0',after['generate'](54,{'selection':'whole_cluster'},2,4)['train'][0]['input'])]
  for name,g in grids:
   canonical_out=apply(canonical,g);wrong=apply(rival,g)
   assert canonical_out==after['claim'](g,'whole_cluster')
   assert wrong==after['claim'](g,'largest_area',intended='whole_cluster')
   cases.append({'name':name,'input':g,'output':canonical_out,'rival_output':wrong,'equal':canonical_out==wrong})
  assert [c['equal'] for c in cases]==[True,True,False,False]
 finally:bridge.close()
report={'task_id':'8069b5294ce4','seed':54,'status':'regression_repaired','canonical_program':canonical,'rival_program':rival,'racket':identity,'evaluations':8,'cases':cases,'pre_repair_adapter_sha256':hashlib.sha256(old.encode()).hexdigest(),'current_adapter_sha256':hashlib.sha256(s.encode()).hexdigest(),'interpretation':'Largest-area rival fit both old demos but failed query; compact repaired first demo refutes it. Old scene reproduced by removing only the recorded compact-demo fix.','authoring_failures_resolved':['Initial supplementary rival used undefined sum; corrected to apply + and rerun.']}
Path(__file__).with_name('teaching-regression.private.json').write_text(json.dumps(report,sort_keys=True)+'\n')
print(json.dumps({'status':report['status'],'evaluations':8,'equalities':[c['equal'] for c in cases]}))
