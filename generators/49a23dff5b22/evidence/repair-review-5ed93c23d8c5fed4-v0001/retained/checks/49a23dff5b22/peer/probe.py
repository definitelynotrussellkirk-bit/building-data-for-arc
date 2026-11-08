from pathlib import Path
import sys,json,time,hashlib
HERE=Path(__file__).resolve().parent
from reviewer_support import load_selected_generator,canonical_path,find_root
REPO=find_root(__file__)
from arcpuzzles.parametric_worker import _real_evaluator
start=time.monotonic()
task='49a23dff5b22'
mod,source,digest=load_selected_generator(task,root=REPO)
expected_source='a2cdbf2196beefcdff3decbcfa7340bbb1337c3de347381b189ba7a6b24b5ac9'
if digest != expected_source:
    raise ValueError('Peer source changed; review the new source before replaying this finding')
record=next(json.loads(line) for line in canonical_path(REPO).read_text().splitlines() if json.loads(line)['task_id']==task)
report={'schema':'bounded-peer-review-v1','task_id':task,'source_sha256':digest,'scope':'One finite adversarial probe: exact API reproducer and at most 100 generated easy inputs for a synthetic three-demo/query teaching witness; not native episode qualification.','canonical_program':record['program_solution']}
base=mod.generate(0,3,difficulty='easy')
controls=[]
for kwargs in ({'grid_h':10},{'grid_w':10},{'anchor_corner':True},{'__override_contract_unknown_axis__':True}):
    try:
        got=mod.generate(0,3,difficulty='easy',**kwargs)
        controls.append({'requested':kwargs,'shape':[len(got),len(got[0])],'identical_to_default':got==base,'accepted':True})
    except Exception as e: controls.append({'requested':kwargs,'exception':repr(e),'accepted':False})
report['control_reproducer']={'seed':0,'sample_index':3,'difficulty':'easy','default_shape':[len(base),len(base[0])],'results':controls}
def crop(g):
    pts=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v]
    rs,cs=zip(*pts)
    return [row[min(cs):max(cs)+1] for row in g[min(rs):max(rs)+1]]
def compress(g):
    rows=[row for row in g if any(row)]
    cols=[c for c in range(len(g[0])) if any(row[c] for row in rows)]
    return [[row[c] for c in cols] for row in rows]
# A predeclared competing rule deletes *all* blank rows and columns, including interior gaps.
# This is not a label implementation: final labels below come from protected Racket.
demos=[];query=None;n=0
for i in range(100):
    g=mod.generate(0,i,difficulty='easy');n+=1
    if crop(g)==compress(g) and len(demos)<3: demos.append((i,g))
    elif crop(g)!=compress(g) and query is None: query=(i,g)
    if len(demos)==3 and query is not None: break
report['searched_draws']=n
apply,identity,bridge=_real_evaluator((REPO/'shared/runtime').resolve())
try:
    report['runtime_identity']=identity
    # Confirm canonical visible labels and whether canonical demos rule out this competitor.
    report['canonical_demos']=[{'racket_matches_given':apply(record['program_solution'],p['input'])==p['output'],'competitor_matches_given':compress(p['input'])==p['output']} for p in record['train']]
    if len(demos)==3 and query is not None:
        pairs=[]
        for i,g in demos:
            label=apply(record['program_solution'],g)
            pairs.append({'seed':0,'sample_index':i,'difficulty':'easy','input':g,'output':label,'competitor_fits':compress(g)==label})
        i,g=query;label=apply(record['program_solution'],g)
        report['teaching_witness']={'scope':'Author-assembled generator-output episode, not an exported/native episode. Canonical demos are separately checked.','wrong_rule':'Remove every all-zero row and column, including interior gaps.','train':pairs,'query':{'seed':0,'sample_index':i,'difficulty':'easy','input':g,'racket_output':label,'wrong_output':compress(g)},'all_demos_fit':all(p['competitor_fits'] for p in pairs),'query_differs':compress(g)!=label,'suggested_repair':'If composing generated demos, require at least one visible output with an interior all-zero row or column whenever such a query is selected.'}
    else:report['teaching_witness']=None
finally:bridge.close()
report['status']='existing_control_blocker_reproduced'
assert all(row['accepted'] and row['identical_to_default'] for row in controls)
assert all(row['racket_matches_given'] and not row['competitor_matches_given'] for row in report['canonical_demos'])
assert report['teaching_witness']['all_demos_fit'] and report['teaching_witness']['query_differs']
report['probe_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
report['repair']='Implement or remove advertised exact override axes, validate unknown keys, and test requested dimensions/anchor semantics against generated output. This probe makes no production edits and does not resolve existing audit.'
report['elapsed_seconds']=round(time.monotonic()-start,3)
(HERE/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'source_sha256':digest,'searched_draws':n,'teaching_witness':report.get('teaching_witness') is not None,'elapsed_seconds':report['elapsed_seconds']}))
