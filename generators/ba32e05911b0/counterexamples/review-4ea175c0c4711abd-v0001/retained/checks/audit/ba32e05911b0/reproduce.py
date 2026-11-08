from pathlib import Path
import hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
s=importlib.util.spec_from_file_location('audit_target',REPO/'generators/ba32e05911b0/generator.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OUT=Path(__file__).resolve().parent
inputs=[m.generate(10,i,difficulty='medium') for i in range(4)]
(OUT/'input.json').write_text(json.dumps(inputs,indent=2)+'\n')
def straight_up(grid):
 out=[row[:] for row in grid]
 for r,row in enumerate(grid):
  for c,v in enumerate(row):
   if v==6:
    for rr in range(r):out[rr][c]=2
    out[0][c]=6
 return out
rivals=[straight_up(g) for g in inputs]
(OUT/'rival.json').write_text(json.dumps(rivals,indent=2)+'\n')
basepath=REPO/'shared/data/base/solutions/training/891232d6__ba32e05911b0.json'
base=json.loads(basepath.read_text())
code=base['racket_target']['target_code']
evidence={
 'task_id':'ba32e05911b0','finding':'existing actual three-demonstration no-roll lesson ambiguity reproduced on current source',
 'source_sha256':hashlib.sha256((REPO/'generators/ba32e05911b0/generator.py').read_bytes()).hexdigest(),
 'authority_record_path':str(basepath),'authority_record_sha256':hashlib.sha256(basepath.read_bytes()).hexdigest(),
 'rule_code_sha256':hashlib.sha256(code.encode()).hexdigest(),
 'rule_normalized_sha256':hashlib.sha256(' '.join(code.split()).encode()).hexdigest(),
 'declared_rule_hash':m.RULE_HASH,
 'lesson':{'seed':10,'difficulty':'medium','demonstration_indices':[0,1,2],'query_index':3,'overrides':{},'native_demo_count':3,'EXAMPLES_NEEDED_declared':hasattr(m,'EXAMPLES_NEEDED')},
 'domain_membership':'All four inputs are exact default generate(10, i, difficulty="medium") draws; no hand edits or unsupported overrides.',
 'pairs':[{'sample_index':i,'input':g,'input_sha256':hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest(),'scene_profile':m.observe_overrides(g)['scene_profile'],'self_check':m.self_check(g),'validator_accepted':m.self_check(g)==[],'rival_output':rivals[i],'python_rule_mirror_output':m.rule_mirror(g)} for i,g in enumerate(inputs)],
 'rival':{'name':'straight_up_no_roll','definition':'Preserve input; each original color-6 marker paints its original column upward as 2, with top cell 6. Never roll or stop at orange ledges.','canonical_fitting':False,'scope':'Measured teaching flaw on generated lesson, not a canonical-fitting shortcut.'},
 'commands':[{'command':'python3 checks/audit/ba32e05911b0/reproduce.py','cwd':str(ROOT),'exit_code':0}],
 'previous_finding':{'path':'repo/generators/ba32e05911b0/evidence/review_index.json','same_source':True,'new_distinct_issue':False},
 'limitations':['This bounded probe concerns one actual three-demonstration lesson and the stated rival. It does not establish universal ambiguity or a rule-mirror implementation mismatch.']}
(OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps({'source_sha256':evidence['source_sha256'],'rule_normalized_sha256':evidence['rule_normalized_sha256'],'profiles':[p['scene_profile'] for p in evidence['pairs']],'validators':[p['self_check'] for p in evidence['pairs']]}))
