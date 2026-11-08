#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
from reviewer_support import canonical_pairs

REPO=Path(__file__).resolve().parents[2]/'repo'
SEARCH=json.loads((REPO.parent/'checks/audit/semantic-search.json').read_text())
CENSUS=json.loads((REPO.parent/'checks/audit/failure-census.json').read_text())

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(tid):
 p=REPO/'generators'/tid/'generator.py'; s=importlib.util.spec_from_file_location('audit_record_'+tid,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def anchor_rival(g):
 h,w=len(g),len(g[0]); src=next((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==3); dst=next((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==4); cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==2]
 dr,dc=dst[0]-src[0],dst[1]-src[1]; tr=[(r+dr,c+dc) for r,c in cells]
 rr=[r for r,c in tr]; cc=[c for r,c in tr]
 shift_r=max(0,-min(rr))+min(0,h-1-max(rr)); shift_c=max(0,-min(cc))+min(0,w-1-max(cc))
 out=[[0]*w for _ in range(h)]
 for r,c in tr: out[r+shift_r][c+shift_c]=8
 out[dst[0]][dst[1]]=4
 return out

def split(g):
 h,w=len(g),len(g[0]); sr=next(r for r,row in enumerate(g) if all(v==1 for v in row)); sc=next(c for c in range(w) if all(g[r][c]==1 for r in range(h)))
 return [[(g[r][c],g[r][sc+1+c],g[sr+1+r][c],g[sr+1+r][sc+1+c]) for c in range(sc)] for r in range(sr)]
def priority(g,order): return [[next((cell[i] for i in order if cell[i]),0) for cell in row] for row in split(g)]
def size_gated(g): return priority(g,(0,1,2,3) if (len(g),len(g[0]))==(9,9) else (0,2,1,3))

# 327
for tid in ['327c3478236b','a23328d45092']:
 d=REPO.parent/'checks/audit'/tid; racket=json.loads((d/'racket.json').read_text()); gen=load(tid); found=SEARCH[tid]['first']
 if tid=='327c3478236b':
  g=found['input']; actual=racket['results'][0]['output']; rival=anchor_rival(g)
  cp=canonical_pairs(tid,root=REPO)
  fit=sum(anchor_rival(p['input'])==p['output'] for p in cp)
  rec={
   'schema':'arc-generator-audit-counterexample-v1','task_id':tid,
   'generator_path':'generators/327c3478236b/generator.py','generator_version':gen.VERSION,
   'generator_sha256':sha(REPO/'generators'/tid/'generator.py'),
   'rule_hash':racket['executed_rule_hash'],'rule_text_sha256':racket['rule_text_sha256'],
   'source_unchanged':racket['generator_sha256']==sha(REPO/'generators'/tid/'generator.py'),
   'generated_case':{'seed':found['seed'],'sample_index':found['sample_index'],'difficulty':found['difficulty'],'overrides':{}},
   'validator':{'passes':gen.self_check(g,difficulty=found['difficulty'])==[],'errors':gen.self_check(g,difficulty=found['difficulty'])},
   'documented_generator_domain':{'ordinary_generator_output':True,'violates_declared_invariant':'translated cells are in-bounds'},
   'geometry':{k:found[k] for k in ['src','dst','vector','template_cells','translated_cells','out_of_bounds']},
   'input':g,'actual_racket_output':actual,
   'rival':{'name':'minimal_shift_full_copy','description':'Apply the documented anchor vector, then minimally shift the translated bbox back in-bounds so every template cell survives; this agrees whenever raw translation is already in-bounds.','output':rival,'fits_usable_canonical_pairs':fit,'usable_canonical_pairs':len(cp)},
   'difference':{'input_template_cell_count':sum(v==2 for row in g for v in row),'actual_color8_count':sum(v==8 for row in actual for v in row),'rival_color8_count':sum(v==8 for row in rival for v in row)},
   'census':CENSUS[tid],
   'racket_evidence':'checks/audit/327c3478236b/racket.json',
   'command':racket['command'],'cwd':racket['cwd']
  }
 else:
  gs=found['inputs']; actual=[x['output'] for x in racket['results']]; rival=[size_gated(g) for g in gs]
  cp=canonical_pairs(tid,root=REPO); fit=sum(size_gated(p['input'])==p['output'] for p in cp)
  rec={
   'schema':'arc-generator-audit-counterexample-v1','task_id':tid,
   'generator_path':'generators/a23328d45092/generator.py','generator_version':gen.VERSION,
   'generator_sha256':sha(REPO/'generators'/tid/'generator.py'),
   'rule_hash':racket['executed_rule_hash'],'rule_text_sha256':racket['rule_text_sha256'],
   'source_unchanged':racket['generator_sha256']==sha(REPO/'generators'/tid/'generator.py'),
   'generated_lesson':{'seed':found['seed'],'sample_indices':found['sample_indices'],'demo_indices':found['demo_indices'],'query_index':found['query_index'],'difficulty':found['difficulty'],'overrides':{},'examples_needed':gen.EXAMPLES_NEEDED,'assembly_tested':'three consecutive demonstrations followed by the next consecutive sample as query'},
   'validator':{'all_pass':all(gen.self_check(g,difficulty=found['difficulty'])==[] for g in gs),'errors':[gen.self_check(g,difficulty=found['difficulty']) for g in gs]},
   'documented_generator_domain':{'all_ordinary_generator_outputs':True,'all_follow_documented_separator/quadrant grammar':True},
   'input':gs,'actual_racket_output':actual,
   'rival':{'name':'canonical_size_else_swap_TR_BL','description':'Use canonical TL>TR>BL>BR priority on 9x9 inputs (the only canonical size); on every other size use TL>BL>TR>BR.','output':rival,'fits_usable_canonical_pairs':fit,'usable_canonical_pairs':len(cp),'fits_demonstrations':all(rival[i]==actual[i] for i in range(3)),'differs_on_query':rival[3]!=actual[3]},
   'query_difference_cells':[{'row':r,'col':c,'actual':actual[3][r][c],'rival':rival[3][r][c]} for r in range(len(actual[3])) for c in range(len(actual[3][0])) if actual[3][r][c]!=rival[3][r][c]],
   'overlap_constraints':found['overlap_constraints'],
   'census':CENSUS[tid],
   'racket_evidence':'checks/audit/a23328d45092/racket.json',
   'command':racket['command'],'cwd':racket['cwd']
  }
 (d/'counterexample.json').write_text(json.dumps(rec,indent=2)+'\n')
 print(tid, 'wrote', d/'counterexample.json')
 print(' canonical fit',rec['rival']['fits_usable_canonical_pairs'],'/',rec['rival']['usable_canonical_pairs'])
