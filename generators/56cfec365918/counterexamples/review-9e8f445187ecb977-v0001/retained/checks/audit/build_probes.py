from __future__ import annotations
from copy import deepcopy
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

ROOT=Path.cwd()
OUT=ROOT.parent/'checks'/'audit'

def load(t):
 p=ROOT/'generators'/t/'generator.py'
 s=importlib.util.spec_from_file_location('audit_'+t,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
 return m,p

def write(t, obj):
 d=OUT/t; d.mkdir(parents=True,exist_ok=True); (d/'probe.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n'); (d/'input.json').write_text(json.dumps(obj['input'],indent=2)+'\n')

# 235: shortcut uses row 1, column 1 as background instead of the actual (2,1) anchor.
t='235a1d06b9d3'; m,p=load(t)
def rival235(g):
 bg=g[1][1]
 return [list(g[0]),list(g[1]),[bg if x==bg else 6 for x in g[0]]]
canon=canonical_pairs(t,root=ROOT)
input235=[[3,0,3,0,0],[7,0,0,0,0],[0,3,3,3,3]]
write(t,{
 'task_id':t,'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rule_hash':getattr(m,'RULE_HASH',None),
 'shortcut':'use input[1][1] as background anchor instead of input[2][1]',
 'canonical_pairs':len(canon),'shortcut_fits_all_canonical':all(rival235(x['input'])==x['output'] for x in canon),
 'generated_probe_count':100,'shortcut_fits_generated':all(rival235(m.generate(i,i*7+3))==m.rule_mirror(m.generate(i,i*7+3)) for i in range(100)),
 'input':input235,'self_check':m.self_check(input235),'intended_python':m.rule_mirror(deepcopy(input235)),'rival_output':rival235(input235),
 'generator_emits_discriminator':False,
 'reason_not_emitted':'generator and validator force every lower-row non-cue cell, including [1][1] and [2][1], to equal the same background',
})

# 56: shortcut treats each color as one global 2x2 object.
t='56cfec365918'; m,p=load(t)
def rival56(g):
 out=[[0 for _ in row] for row in g]
 colors=sorted({v for row in g for v in row if v!=0})
 for color in colors:
  cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color]
  r0=min(r for r,_ in cells); r1=max(r for r,_ in cells)
  c0=min(c for _,c in cells); c1=max(c for _,c in cells)
  out[r0][c0]=color
  out[r1][c1]=color
 return out
def intended56(g):
 out=[list(r) for r in g]; h=len(g); w=len(g[0])
 for r in range(h-1):
  for c in range(w-1):
   v=g[r][c]
   if v!=0 and g[r+1][c]==v and g[r][c+1]==v and g[r+1][c+1]==v:
    out[r][c+1]=0; out[r+1][c]=0
 return out
canon=canonical_pairs(t,root=ROOT)
input56=[[0]*8 for _ in range(4)]
for r,c in ((1,1),(1,2),(2,1),(2,2),(1,5),(1,6),(2,5),(2,6)): input56[r][c]=4
write(t,{
 'task_id':t,'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rule_hash':getattr(m,'RULE_HASH',None),
 'shortcut':'treat all cells of each color as one global object and keep only the global bounding-box top-left and bottom-right',
 'canonical_pairs':len(canon),'shortcut_fits_all_canonical':all(rival56(x['input'])==x['output'] for x in canon),
 'generated_probe_count':100,'shortcut_fits_generated':all(rival56(m.generate(i,i*7+3))==intended56(m.generate(i,i*7+3)) for i in range(100)),
 'input':input56,'self_check':m.self_check(input56),'intended_python':intended56(input56),'rival_output':rival56(input56),
 'generator_emits_discriminator':False,
 'reason_not_emitted':'ordinary generation assigns a distinct color to every block, so no color ever names two separated 2x2 objects',
})
