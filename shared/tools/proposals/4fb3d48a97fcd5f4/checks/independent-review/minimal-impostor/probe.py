import ast,hashlib,json,pathlib,sys
from collections import Counter
from reviewer_support import canonical_pairs,find_root,load_selected_generator
from arcpuzzles import Catalog
ROOT=find_root(__file__);TASK='2c30a4753f6b';OUT=pathlib.Path(__file__).parent
m,source,sha=load_selected_generator(TASK,root=ROOT)
lint=ROOT/'shared/tools/generator_defect_lint.py';tree=ast.parse(lint.read_text())
names={'_is_grid','_dims','_palette','_majority','_minimal_impostors','_canonical_minimal_kinds','_norm','_call_self_check','probe_selfcheck_minimal_impostors'}
selected=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
ns={'Counter':Counter};exec(compile(selected,str(lint),'exec'),ns)
inputs=[m.generate(s,s,difficulty='easy') for s in range(1,7)]
canonical=[(p['input'],p['output']) for p in canonical_pairs(TASK,root=ROOT)]
warning=ns['probe_selfcheck_minimal_impostors'](m,inputs,['easy']*6,canonical)
rows=[];accepted=[]
for seed,g in enumerate(inputs,1):
 for name,mutation in ns['_minimal_impostors'](g):
  errs=m.self_check(mutation,difficulty='easy')
  row={'seed':seed,'sample_index':seed,'difficulty':'easy','kind':name,'input':mutation,'errors':errs,'observed_profile':m.observe_overrides(mutation)}
  rows.append(row)
  if not errs and name=='short_line':accepted.append(row)
assert len(accepted)==1
receipt=Catalog(ROOT).apply(TASK,[r['input'] for r in accepted],reference='canonical',timeout=120)
(OUT/'racket.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert all(r['error'] is None for r in receipt['results'])
assert all(r['output']==m.rule_mirror(a['input']) for a,r in zip(accepted,receipt['results'],strict=True))
teaching=[]
for seed in range(1000):
 g=m.generate(seed,seed*2,difficulty='easy');facts=m._analysis(g)
 teaching.append({'seed':seed,'errors':facts['errors'],'profile':facts['scene_profile'],'mismatches':facts['facts']['mismatch_pairs'],'width':len(g[0]),'colors':len({v for row in g for v in row if v}),'area':len(g)*len(g[0]),'all_six_refuted':all(fn(g)!=m.rule_mirror(g) for fn in m.LESSON_COMPETITORS.values())})
assert all(not r['errors'] and r['width']>3 and r['colors']==2 and r['area']<=36 and r['all_six_refuted'] for r in teaching)
report={'task_id':TASK,'generator_sha256':sha,'linter_sha256':hashlib.sha256(lint.read_bytes()).hexdigest(),'linter_probe':'Exact functions compiled from current linter AST; first six inputs generated in its band/seed/index order.','warning':warning,'probes':rows,'totals':dict(Counter(r['kind'] for r in rows)),'accepted':dict(Counter(r['kind'] for r in rows if not r['errors'])),'accepted_short_line':accepted,'racket_receipt':'racket.json','teaching_probe':{'seed_range':[0,999],'sample_index':'2*seed','difficulty':'easy','count':len(teaching),'invalid':sum(bool(r['errors']) for r in teaching),'not_all_rivals_refuted':sum(not r['all_six_refuted'] for r in teaching),'observed_profiles':dict(Counter(r['profile'] for r in teaching))},'conclusion':'The short line is lawful near_symmetric input and canonical Racket reflection executes correctly. Generic tiny-shape warning is not a task defect. Teaching draws remain valid and refute all declared rivals, though some classify as edge_asymmetry rather than the sampled multicolor_sparse axis label.','invocation':{'cwd':str(pathlib.Path.cwd()),'argv':[sys.executable,*sys.argv]}}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('generator_sha256','warning','accepted','teaching_probe','conclusion')}))
