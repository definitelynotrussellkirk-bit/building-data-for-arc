from __future__ import annotations
import json, traceback
from pathlib import Path
from reviewer_support import find_root, load_selected_generator
TASK='08b346c559d6'
ROOT=find_root(__file__)
gen, source, source_sha=load_selected_generator(TASK, root=ROOT)

def run(request):
    try:
        g=gen.generate(request['seed'],request['sample_index'],difficulty=request.get('difficulty'),**request.get('overrides',{}))
        h=len(g); w=len(g[0]); half=h//2
        upper_nonzero=sum(v!=0 for row in g[:half] for v in row)
        return {'status':'ok','input':g,'returned_h':h,'returned_w':w,
                'upper_nonzero':upper_nonzero,'self_check':gen.self_check(g)}
    except Exception as exc:
        return {'status':'error','error_type':type(exc).__name__,'error':str(exc)}

requests={
 'odd_declared_height':{
   'seed':0,'sample_index':0,'difficulty':None,
   'overrides':{'grid_h':7,'grid_w':6,'top_marks':3,'texture':'plain'},
 },
 'dense_top_exact_three':{
   'seed':0,'sample_index':0,'difficulty':'easy',
   'overrides':{'grid_h':6,'grid_w':6,'top_marks':3,'texture':'dense_top'},
 },
 'declared_top_marks_20':{
   'seed':0,'sample_index':0,'difficulty':None,
   'overrides':{'grid_h':6,'grid_w':6,'top_marks':20,'texture':'plain'},
 },
 'declared_height_4':{
   'seed':0,'sample_index':0,'difficulty':None,
   'overrides':{'grid_h':4,'grid_w':6,'top_marks':3,'texture':'plain'},
 },
}
results={name:run(req) for name,req in requests.items()}
# Search a bounded sample to quantify dense_top's extra-mark behavior when an
# exact top_marks=3 request is accepted.
dense=[]
for seed in range(100):
    req={'seed':seed,'sample_index':0,'difficulty':'easy',
         'overrides':{'grid_h':6,'grid_w':6,'top_marks':3,'texture':'dense_top'}}
    res=run(req)
    dense.append({'seed':seed,'status':res['status'],'upper_nonzero':res.get('upper_nonzero'),
                  'self_check':res.get('self_check'),'error':res.get('error')})
summary={
 'schema':'arcpuzzles-audit-probe-v1','task_id':TASK,
 'generator_source':str(source.relative_to(ROOT)),'generator_sha256':source_sha,
 'axis_declarations':gen.AXES,
 'requests':requests,'results':results,
 'dense_top_sample':{
   'seeds':'0..99','count':100,
   'accepted':sum(x['status']=='ok' for x in dense),
   'exactly_requested_three_upper_marks':sum(x.get('upper_nonzero')==3 for x in dense),
   'extra_mark_cases':sum((x.get('upper_nonzero') or 0)>3 for x in dense),
   'first_extra':next((x for x in dense if (x.get('upper_nonzero') or 0)>3),None),
 },
}
out=Path(__file__).resolve().parent
(out/'probe.json').write_text(json.dumps({'summary':summary,'dense_records':dense},indent=2,sort_keys=True)+'\n')
# Retain the concrete generated grid for public rule application.
(out/'input.json').write_text(json.dumps([results['odd_declared_height']['input'], results['dense_top_exact_three']['input']],indent=2)+'\n')
print(json.dumps(summary,sort_keys=True))
