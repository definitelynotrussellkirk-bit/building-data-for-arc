#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(tid):
    path=REPO/'generators'/tid/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+tid, path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod,path

def components(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
      for c in range(w):
        if grid[r][c]==0 or (r,c) in seen: continue
        color=grid[r][c]; stack=[(r,c)]; seen.add((r,c)); cells=[]
        while stack:
          rr,cc=stack.pop(); cells.append((rr,cc))
          for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            p=(rr+dr,cc+dc)
            if 0<=p[0]<h and 0<=p[1]<w and p not in seen and grid[p[0]][p[1]]==color:
              seen.add(p); stack.append(p)
        out.append({'color':color,'cells':cells})
    return out

def largest_rival(grid):
    comps=components(grid)
    chosen=min(comps,key=lambda x:(-len(x['cells']), min(x['cells'])))
    rs=[p[0] for p in chosen['cells']]; cs=[p[1] for p in chosen['cells']]
    r0,r1,c0,c1=min(rs),max(rs),min(cs),max(cs)
    cells=set(chosen['cells'])
    return [[8 if (r,c) in cells else 0 for c in range(c0,c1+1)] for r in range(r0,r1+1)]

def canonical_pairs(tid):
    for line in (REPO/'shared/data/canonical/puzzles.jsonl').open():
      row=json.loads(line)
      if row.get('task_id')==tid:
        test=row.get('test') or []
        if isinstance(test,dict): test=[test]
        return [*(row.get('train') or []),*test]
    raise KeyError(tid)

# 2f: exact invalid-but-accepted no-bank counterexample.
gen,path=load('2f16117deb0f')
grid=gen.generate(0,0,texture='no_bank')
adir=ROOT/'checks/audit/2f16117deb0f'; adir.mkdir(parents=True,exist_ok=True)
(adir/'input.json').write_text(json.dumps(grid,indent=2)+'\n')
(adir/'no_bank_counterexample.json').write_text(json.dumps({
  'schema':'audit-counterexample-v1','task_id':'2f16117deb0f',
  'generator_sha256':sha(path),'seed':0,'sample_index':0,
  'overrides':{'texture':'no_bank'},'input':grid,
  'self_check':gen.self_check(grid),
  'violated_declared_invariants':['row 3 holds keys 1..K','rows 4-5 hold 2x2 bank entries'],
  'finding':'The advertised no_bank degenerate has no bank keys or entries, but self_check returns no errors.'
},indent=2)+'\n')

# f3: 60 lawful generated inputs, plus largest-component shortcut census.
gen,path=load('f3ecc20ad2d1')
adir=ROOT/'checks/audit/f3ecc20ad2d1'; adir.mkdir(parents=True,exist_ok=True)
inputs=[]; sample_rows=[]
for i in range(60):
  band=('easy','medium','hard')[i%3]
  grid=gen.generate(9000+i,i,difficulty=band)
  errs=gen.self_check(grid)
  if errs: raise AssertionError((i,errs))
  comps=components(grid); sizes=sorted((len(c['cells']) for c in comps),reverse=True)
  inputs.append(grid)
  sample_rows.append({'seed':9000+i,'sample_index':i,'difficulty':band,
                      'component_sizes_desc':sizes,'largest_margin':sizes[0]-sizes[1],
                      'rival_output':largest_rival(grid)})
(adir/'input.json').write_text(json.dumps({'inputs':inputs},indent=2)+'\n')
canon=canonical_pairs('f3ecc20ad2d1')
canon_fit=[largest_rival(p['input'])==p['output'] for p in canon]
(adir/'largest_component_probe.pre_racket.json').write_text(json.dumps({
  'schema':'audit-shortcut-probe-v1','task_id':'f3ecc20ad2d1',
  'generator_sha256':sha(path),'rule_hash_expected':'84736dfacc09',
  'canonical_pairs_fit':sum(canon_fit),'canonical_pairs_total':len(canon_fit),
  'canonical_fit_vector':canon_fit,'generated_count':len(inputs),
  'seed_range':[9000,9059],'bands':{'easy':20,'medium':20,'hard':20},
  'minimum_largest_component_margin':min(r['largest_margin'] for r in sample_rows),
  'samples':sample_rows,
  'finding':'Selecting the largest monochrome component, cropping it, and recoloring it 8 fits every canonical pair and is structurally forced by generated target sizes versus distractors.'
},indent=2)+'\n')
