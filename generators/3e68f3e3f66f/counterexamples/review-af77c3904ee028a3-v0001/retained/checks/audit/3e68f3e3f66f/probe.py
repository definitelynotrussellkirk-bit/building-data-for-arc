#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, importlib.util, json, sys
from pathlib import Path

TASK='3e68f3e3f66f'
work=Path(__file__).resolve().parents[3]; repo=work/'repo'
sys.path[:0]=[str(repo/'src'),str(repo/'shared/runtime')]
from reviewer_support import canonical_pairs, find_root
src=repo/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_3e',src)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def rival(grid):
    h,w=len(grid),len(grid[0]); legend=[v for v in grid[0] if v]
    source=next((r,c) for r in range(h) for c in range(w) if grid[r][c]==5)
    anchors=sorted((r,c) for r in range(h) for c in range(w) if grid[r][c]==6)
    motif=[(r,c) for r in range(1,h) for c in range(w) if grid[r][c] not in (0,5,6)][:3]
    out=copy.deepcopy(grid)
    for i,(ar,ac) in enumerate(anchors):
        for r,c in motif:
            rr=ar+r-source[0]; cc=ac+c-source[1]
            if 0<=rr<h and 0<=cc<w: out[rr][cc]=legend[i]
    return out

def first_diff(a,b):
    for r,(ra,rb) in enumerate(zip(a,b)):
        for c,(x,y) in enumerate(zip(ra,rb)):
            if x!=y:return [r,c,{'racket':x,'rival':y}]
    return None
pairs=canonical_pairs(TASK,root=find_root(repo)); canon=[rival(p['input'])==p['output'] for p in pairs]
receipt=json.loads((work/'checks/audit'/TASK/'racket.json').read_text())
inputs=[row['input'] for row in receipt['results']]; truths=[row['output'] for row in receipt['results']]
generated=[mod.generate(13,i,difficulty='medium') for i in range(4)]
profiles=[mod.observe_overrides(g)['scene_profile'] for g in generated]
matches=[rival(g)==truth for g,truth in zip(inputs,truths)]
report={
 'schema':'arcpuzzles-audit-counterexample-v1','task_id':TASK,
 'finding':'A three-demo lesson can teach “copy at most the first three row-major motif cells”; the query requires a fourth cell.',
 'generator_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'executed_rule_hash':receipt['executed_rule_hash'],
 'canonical_check':{'pairs':len(canon),'rival_matches':sum(canon),'fits_all':all(canon)},
 'generation':{'seed':13,'sample_indices':[0,1,2,3],'difficulty':'medium','profiles':profiles,'reproduced_inputs':generated==inputs},
 'pairs':[{'role':'demo' if i<3 else 'query','sample_index':i,'profile':profiles[i],'self_check':mod.self_check(g),'rival_matches_racket':matches[i]} for i,g in enumerate(inputs)],
 'first_query_difference':first_diff(truths[3],rival(inputs[3])),
 'domain_note':'All four grids are emitted by the current target generator. The first three demos contain no fourth-cell witness.',
 'apply_command':receipt['command'],'apply_cwd':receipt['cwd']}
out=work/'checks/audit'/TASK/'finding.json'; out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert all(canon) and generated==inputs and matches==[True,True,True,False] and all(not mod.self_check(g) for g in inputs)
