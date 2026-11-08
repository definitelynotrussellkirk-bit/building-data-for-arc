"""Findings-only audits: no audit-target source is changed."""
from pathlib import Path
from collections import Counter
import copy, hashlib, importlib.util, json, os, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repo/src'))
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime
ids=['3b907ea971ea','16d18a416d57']
runtime=ROOT/'.review/runtime-audits'
if not runtime.exists(): prepare_runtime(Catalog(ROOT/'repo'),runtime,task_ids=ids)
sys.path.insert(0,str(runtime))
from puzzle_generators.base import set_ctx_observer
from puzzle_generators.rule_wrap import wrap_rule
from arc_repl.racket_bridge import RacketBridge
os.environ['RACKET_PATH']=str(ROOT/'.review/racket-runtime/racket/bin/racket')
mods={}
for tid in ids:
 p=ROOT/f'repo/generators/{tid}/generator.py'
 s=importlib.util.spec_from_file_location('audit_'+tid,p)
 m=importlib.util.module_from_spec(s); s.loader.exec_module(m); mods[tid]=m
rows={}
for l in (ROOT/'repo/shared/data/canonical/puzzles.jsonl').open():
 row=json.loads(l)
 if row['task_id'] in ids: rows[row['task_id']]=row
bridge=RacketBridge(timeout=30,max_calls_before_restart=48)
def literal(g): return "'("+' '.join('('+' '.join(map(str,r))+')' for r in g)+')'
def evaluate(tid,grids):
 wrapped=wrap_rule(rows[tid]['program_solution'])
 result=[]
 for i in range(0,len(grids),16):
  result.extend(bridge.eval_text('(let ([f '+wrapped+']) (list '+' '.join('(f '+literal(g)+')' for g in grids[i:i+16])+'))'))
 return result
def norm(g): return [[int(v) for v in row] for row in g]
def board(g):
 cols=[c for c in range(len(g[0])) if all(row[c]==9 for row in g)]
 return [row[max(cols)+1:] for row in g]
report={}
try:
 for tid in ids:
  gen=mods[tid]; counts=Counter(); cases=[]; witnesses=[]; contexts=[]
  set_ctx_observer(contexts.append)
  for band in ['easy','medium','hard']:
   for seed in range(100):
    g=gen.generate(seed,seed,difficulty=band)
    case={'band':band,'seed':seed,'sample_index':seed,'input':g}
    counts['generated']+=1
    if gen.self_check(g): counts['self_check_failures']+=1
    if tid==ids[0]:
     b=board(g)
     actual=sum([r[c:c+3] for r in b[r0:r0+3]]==gen.TEMPLATE for r0 in range(len(b)-2) for c in range(len(b[0])-2))
     requested=contexts[-1].axis_value('match_count')
     if actual!=requested:
      counts['match_count_shortfalls']+=1
      if len(witnesses)<4: witnesses.append({**case,'requested':requested,'actual':actual})
    cases.append(case)
  set_ctx_observer(None)
  outs=evaluate(tid,[case['input'] for case in cases])
  if tid==ids[0]:
   counts['crop_board_shortcut_exact']=sum(o==board(c['input']) for c,o in zip(cases,outs))
   g=copy.deepcopy(cases[0]['input']); cdiv=next(c for c in range(len(g[0])) if all(row[c]==9 for row in g))
   r,c=next((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if c>cdiv and v==0)
   g[r][c]=1
   mutated=evaluate(tid,[g])[0]
   counterexample={'base':{k:v for k,v in cases[0].items() if k!='input'},'added_cell':[r,c,1], 'input':g,'racket_output':mutated,'crop_board_output':board(g),'self_check':gen.self_check(g),'shortcut_fails':board(g)!=mutated}
  else:
   counterexample={}
   components=gen._components_4conn
   counts['rule_matches_largest_component']=sum(
       out==[[7 if (r,c) in set(max(components(case['input']),key=len)) else v
              for c,v in enumerate(row)] for r,row in enumerate(case['input'])]
       for case,out in zip(cases,outs))
   for name in gen.DEGENERATE_TEXTURES:
    g=gen.generate(0,0,texture=name)
    item={'input':g,'self_check':gen.self_check(g)}
    try: item['racket_output']=evaluate(tid,[g])[0]
    except Exception as e: item['racket_error']=str(e)[:1600]
    counterexample[name]=item
  canonical=[]
  pairs=[]
  for split in ['train', 'test']:
   value=rows[tid][split]
   pairs.extend(value if isinstance(value,list) else [value])
  inputs=[norm(p['input']) for p in pairs]
  outputs=evaluate(tid,inputs)
  for i,(p,g,out) in enumerate(zip(pairs,inputs,outputs)):
   item={'pair_index':i,'self_check':gen.self_check(g),'racket_matches_stored':out==norm(p['output'])}
   if tid==ids[0]: item['crop_board_shortcut_exact']=board(g)==out
   else: item['component_sizes']=sorted(map(len,gen._components_4conn(g)))
   canonical.append(item)
  report[tid]={'generator_sha256':hashlib.sha256((ROOT/f'repo/generators/{tid}/generator.py').read_bytes()).hexdigest(),
               'counts':dict(counts),'witnesses':witnesses,'counterexample':counterexample,'canonical':canonical,
               'first_generated':{**cases[0],'racket_output':outs[0]}}
finally:
 set_ctx_observer(None); bridge.close()
out=ROOT/'checks/audits/findings.json'; out.write_text(json.dumps(report,indent=2)+'\n')
for tid,r in report.items():
 print(tid,r['counts'],r['canonical'])
 print('witness summaries',[(w['band'],w['seed'],w['requested'],w['actual']) for w in r['witnesses']])
 if tid==ids[1]: print('no_motifs error:',r['counterexample']['no_motifs'].get('racket_error'))
