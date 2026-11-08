from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('task', choices=('5f8abe24cffe','c0aac14eef4d'))
ap.add_argument('outdir', type=Path)
ap.add_argument('--finalize', type=Path)
args=ap.parse_args()
args.outdir.mkdir(parents=True, exist_ok=True)
source=Path('generators')/args.task/'generator.py'
spec=importlib.util.spec_from_file_location('audit_target_'+args.task, source)
mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)
seed=5 if args.task=='5f8abe24cffe' else 0
inputs=[mod.generate(seed,i,difficulty='medium') for i in range(4)]
validators=[list(mod.self_check(grid) or []) for grid in inputs]
(args.outdir/'lesson_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')

ORTH=((-1,0),(1,0),(0,-1),(0,1))
def frames(grid):
    h,w=len(grid),len(grid[0]); unseen={(r,c) for r in range(h) for c in range(w) if grid[r][c]==1}; out=[]
    while unseen:
        start=unseen.pop(); cells={start}; q=[start]
        while q:
            r,c=q.pop()
            for dr,dc in ORTH:
                p=(r+dr,c+dc)
                if p in unseen: unseen.remove(p); cells.add(p); q.append(p)
        r0=min(r for r,_ in cells); r1=max(r for r,_ in cells); c0=min(c for _,c in cells); c1=max(c for _,c in cells)
        border={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if r in (r0,r1) or c in (c0,c1)}
        if cells==border and r1-r0>=2 and c1-c0>=2: out.append((r0,c0,r1,c1))
    return sorted(out)
def crop(grid):
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    if not cells:return []
    r0=min(r for r,_ in cells); r1=max(r for r,_ in cells); c0=min(c for _,c in cells); c1=max(c for _,c in cells)
    return [row[c0:c1+1] for row in grid[r0:r1+1]]
def panels(grid):
    return [crop([row[c0+1:c1] for row in grid[r0+1:r1]]) for r0,c0,r1,c1 in frames(grid)[:3]]
def transform(g,code):
    if code==1:return [row[:] for row in g]
    if code==2:return [list(row) for row in zip(*g[::-1])]
    if code==3:return [row[::-1] for row in g[::-1]]
    if code==4:return [list(row) for row in zip(*g)]
    if code==5:return [row[::-1] for row in g]
    if code==6:return g[::-1]
    raise ValueError(code)
def first_code(a,b):return next(code for code in range(1,7) if transform(a,code)==b)

if args.task=='5f8abe24cffe':
    parsed=[panels(grid) for grid in inputs]
    codes=[first_code(ps[0],ps[1]) for ps in parsed]
    fixed=codes[0]
    rival_outputs=[transform(ps[2],fixed) for ps in parsed]
    detail={'profiles':[mod.observe_overrides(grid) for grid in inputs],
            'transform_codes':codes,
            'shortcut':f'always apply transform code {fixed} (up-down reflection) to C and ignore A/B'}
else:
    def rival(grid):
        row=grid[0]; width=len(row); color=next(v for v in row if v); count=sum(v!=0 for v in row); out=[]
        for r in range(width//2):
            new=row[:]
            for c in range(min(width,count+r)):new[c]=color
            out.append(new)
        return out
    rival_outputs=[rival(grid) for grid in inputs]
    detail={'profiles':[mod.observe_overrides(grid) for grid in inputs],
            'shortcut':'copy all existing markers into every output row, then fill the count+r left prefix'}

base={'schema':'arcpuzzles-audit-counterexample-v1','task_id':args.task,
      'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'seed':seed,'sample_indices':[0,1,2,3],'difficulty':'medium',
      'demonstration_indices':[0,1,2],'query_index':3,
      'validator_findings':validators,'all_inputs_in_documented_domain':not any(validators),
      'detail':detail,'rival_outputs':rival_outputs,
      'generation_command':{'cwd':'repo','argv':['python3','../checks/audit/reproduce_counterexample.py',args.task,f'../checks/audit/{args.task}']},
      'apply_command':{'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply',args.task,'--input',f'../checks/audit/{args.task}/lesson_inputs.json','--out',f'../checks/audit/{args.task}/lesson_racket.json']}}
if args.finalize:
    racket=json.loads(args.finalize.read_text())
    outputs=[row['output'] for row in racket['results']]
    base.update({'executed_rule_hash':racket['executed_rule_hash'],
                 'rule_text_sha256':racket['rule_text_sha256'],
                 'racket_outputs':outputs,
                 'shortcut_fits_all_demonstrations':all(rival_outputs[i]==outputs[i] for i in range(3)),
                 'shortcut_disagrees_on_query':rival_outputs[3]!=outputs[3],
                 'query_input':inputs[3],
                 'rival_query_output':rival_outputs[3],
                 'racket_query_output':outputs[3]})
    (args.outdir/'counterexample.json').write_text(json.dumps(base,indent=2)+'\n')
    print(json.dumps({'task_id':args.task,'fits':base['shortcut_fits_all_demonstrations'],'differs':base['shortcut_disagrees_on_query']},sort_keys=True))
else:
    (args.outdir/'metadata.json').write_text(json.dumps(base,indent=2)+'\n')
    print(json.dumps({'task_id':args.task,'inputs':4,'valid':not any(validators)},sort_keys=True))
