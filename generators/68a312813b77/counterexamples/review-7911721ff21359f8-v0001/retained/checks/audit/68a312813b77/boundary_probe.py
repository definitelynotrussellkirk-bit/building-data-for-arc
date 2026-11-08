from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
GEN_PATH = PACKET / 'repo/generators/68a312813b77/generator.py'
APPLY_PATH = PACKET / 'checks/audit/68a312813b77/racket.json'
OUT_PATH = PACKET / 'checks/audit/68a312813b77/boundary-shortcut.json'

spec = importlib.util.spec_from_file_location('audit_target_68a312813b77', GEN_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

apply = json.loads(APPLY_PATH.read_text())
input_grid = apply['results'][0]['input']
authority = apply['results'][0]['output']


def components8(grid):
    H, W = len(grid), len(grid[0])
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v != 0}
    out=[]
    while remaining:
        start=remaining.pop(); comp={start}; stack=[start]
        while stack:
            r,c=stack.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr==dc==0: continue
                    q=(r+dr,c+dc)
                    if q in remaining:
                        remaining.remove(q); comp.add(q); stack.append(q)
        out.append(comp)
    return out


def boundary_restricted_rival(grid):
    out=[row[:] for row in grid]
    H,W=len(grid),len(grid[0])
    for comp in components8(grid):
        r0=min(r for r,_ in comp); r1=max(r for r,_ in comp)
        c0=min(c for _,c in comp); c1=max(c for _,c in comp)
        # Shortcut: incorrectly applies the rule only to objects wholly interior.
        if r0 == 0 or c0 == 0 or r1 == H-1 or c1 == W-1:
            continue
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):
                if out[r][c] == 0:
                    out[r][c] = 7
    return out

rival = boundary_restricted_rival(input_grid)
ordinary = {'draws': 0, 'draws_with_boundary_component': 0, 'self_check_failures': 0}
examples=[]
for difficulty in ('easy','medium','hard'):
    for sample_index in range(200):
        grid=mod.generate(20261004, sample_index, difficulty=difficulty)
        ordinary['draws'] += 1
        errs=mod.self_check(grid, difficulty=difficulty)
        ordinary['self_check_failures'] += bool(errs)
        H,W=len(grid),len(grid[0])
        touches=any(
            min(r for r,_ in comp)==0 or min(c for _,c in comp)==0
            or max(r for r,_ in comp)==H-1 or max(c for _,c in comp)==W-1
            for comp in components8(grid)
        )
        ordinary['draws_with_boundary_component'] += touches
        if touches and len(examples)<3:
            examples.append({'difficulty':difficulty,'sample_index':sample_index,'grid':grid})

report={
    'schema':'arcpuzzles-audit-counterexample-v1',
    'task_id':'68a312813b77',
    'finding':'boundary-object shortcut survives ordinary generation',
    'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'rule_hash':apply['executed_rule_hash'],
    'canonical_input_passes_self_check':mod.self_check(input_grid),
    'input_source':'first canonical training input',
    'input':input_grid,
    'actual_racket_output':authority,
    'rival_output':rival,
    'outputs_differ':rival != authority,
    'differing_cells':[
        [r,c,authority[r][c],rival[r][c]]
        for r in range(len(authority)) for c in range(len(authority[0]))
        if authority[r][c] != rival[r][c]
    ],
    'rival':'fill each 8-connected component bbox only when the bbox does not touch a grid edge',
    'ordinary_sampling':ordinary,
    'ordinary_boundary_examples':examples,
    'generator_fact':'ordinary placement clamps every bbox origin to >=1 and every bbox end to <=size-2',
    'apply_evidence':'checks/audit/68a312813b77/racket.json',
    'commands':[
        ['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','68a312813b77','--input','../checks/audit/68a312813b77/input.json','--out','../checks/audit/68a312813b77/racket.json'],
        ['python3','run_with_racket.py','python3','../checks/audit/68a312813b77/boundary_probe.py'],
    ],
    'cwd':'packet_root for wrapper; payload cwd repo',
}
OUT_PATH.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('generator_sha256','rule_hash','canonical_input_passes_self_check','outputs_differ','differing_cells','ordinary_sampling')}, indent=2))
