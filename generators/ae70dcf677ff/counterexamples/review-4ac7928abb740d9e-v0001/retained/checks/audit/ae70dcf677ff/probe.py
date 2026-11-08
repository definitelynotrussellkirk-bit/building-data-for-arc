import hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
p=REPO/'generators/ae70dcf677ff/generator.py'
spec=importlib.util.spec_from_file_location('audit_generator',p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
c=REPO/'shared/data/base/solutions/training/9841fdad__ae70dcf677ff.json'; canonical=json.loads(c.read_text())
rule=canonical['racket_target']['target_code']
out=Path(__file__).resolve().parent
rows=[]; corner=None
for index in range(64):
 g=mod.generate(0,index); h=len(g);w=len(g[0]);sep=(w-1)//2
 bg=max(set(g[r][c] for r in range(1,h-1) for c in range(1,sep)),key=lambda x:sum(g[r][c]==x for r in range(1,h-1) for c in range(1,sep)))
 row={'seed':0,'sample_index':index,'shape':[h,w],'left_width':sep-1,'right_width':w-sep-2,'intended_left_bg':bg,'oracle_left_bg':g[1][1],'self_check':mod.self_check(g)}
 rows.append(row)
 if corner is None and bg!=g[1][1]:corner=(index,g,row)
print('samples',len(rows),'equal_panel_width',sum(r['left_width']==r['right_width'] for r in rows),'corner_occupied',sum(r['intended_left_bg']!=r['oracle_left_bg'] for r in rows),'validator_accepts',sum(not r['self_check'] for r in rows))
cs=canonical['visible_context']['train']+canonical['visible_context']['test_inputs']
canon=[]
for i,pair in enumerate(cs):
 g=pair['input'];h=len(g);w=len(g[0]);frame=g[0][0];sep=next(c for c in range(1,w-1) if all(g[r][c]==frame for r in range(h)))
 canon.append({'pair':i,'shape':[h,w],'left_width':sep-1,'right_width':w-sep-2})
if corner is None: raise RuntimeError('no corner witness')
index,g,row=corner
(out/'input.json').write_text(json.dumps([g]))
identity={'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rule_target_code_sha256':hashlib.sha256(rule.encode()).hexdigest(),'canonical_record_sha256':hashlib.sha256(c.read_bytes()).hexdigest()}
res={'task_id':'ae70dcf677ff','version':mod.VERSION,'source_identity':identity,'generated_sample_range':{'seed':0,'sample_indices':[0,63],'denominator':64},'samples':rows,'canonical_geometry':canon,'generated_corner_witness':dict(row,input=g),'declared_competitors':{'CANONICAL_SHORTCUTS':getattr(mod,'CANONICAL_SHORTCUTS',None),'LESSON_COMPETITORS':getattr(mod,'LESSON_COMPETITORS',None)},'commands':[{'cwd':'packet_root','argv':['env','PYTHONDONTWRITEBYTECODE=1','python3','checks/audit/ae70dcf677ff/probe.py'],'exit_code':0}]}
(out/'probe-results.json').write_text(json.dumps(res,indent=2)+'\n')
print('corner witness',index,'canonical',canon,'source',identity)
