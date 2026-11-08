"""Reproduce findings-only audits from the repo root, using untouched sources."""
import importlib.util
import hashlib
import json
from pathlib import Path

ROOT=Path.cwd()
OUT=ROOT.parent/'checks/audit'

def load(tid):
    path=ROOT/'generators'/tid/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+tid,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod,hashlib.sha256(path.read_bytes()).hexdigest()

def exactly_two(grid):
    out=[row[:] for row in grid]
    for r,row in enumerate(grid):
        for color in dict.fromkeys(x for x in row if x):
            cs=[c for c,x in enumerate(row) if x==color]
            if len(cs)==2:
                for c in range(min(cs),max(cs)+1):out[r][c]=color
    return out

def at_least_two(grid):
    out=[row[:] for row in grid]
    for r,row in enumerate(grid):
        for color in dict.fromkeys(x for x in row if x):
            cs=[c for c,x in enumerate(row) if x==color]
            if len(cs)>=2:
                for c in range(min(cs),max(cs)+1):out[r][c]=color
    return out

def corners(grid,loose=False):
    out=[row[:] for row in grid]
    for color in dict.fromkeys(x for row in grid for x in row if x):
        points=[(r,c) for r,row in enumerate(grid) for c,x in enumerate(row) if x==color]
        rs=sorted({r for r,c in points});cs=sorted({c for r,c in points})
        if len(points)==3 and ((len(rs)>1 and len(cs)>1) if loose else (len(rs)==len(cs)==2)):
            for r in (min(rs),max(rs)):
                for c in (min(cs),max(cs)):out[r][c]=color
    return out

canonical={}
for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open():
    d=json.loads(line)
    if d.get('task_id') in ('8f221c2b552e','f0f02eb1d2e0'):
        canonical[d['task_id']]=d

for tid in ('8f221c2b552e','f0f02eb1d2e0'):
    mod,sha=load(tid);home=OUT/tid;home.mkdir(parents=True,exist_ok=True)
    source=canonical[tid];test=source.get('test',[])
    pairs=source['train']+([test] if isinstance(test,dict) else test)
    if tid=='8f221c2b552e':
        g=[[0]*8 for _ in range(4)]
        for c in (1,3,6):g[1][c]=2
        rival=exactly_two;reference=at_least_two
        domain='Outside documented two-endpoint sampler; accepted by self_check and lawful under >=2 Racket branch.'
    else:
        g=[[0]*7 for _ in range(7)]
        for r,c in ((0,0),(0,2),(2,0)):g[r][c]=2
        for r,c in ((3,3),(4,4),(5,3)):g[r][c]=3
        rival=lambda x:corners(x,True);reference=corners
        domain='Outside sampler and rejected by self_check: extra 3-color motif spans three rows and two columns. Racket leaves it unchanged.'
    default=mod.generate(0,0,difficulty='hard')
    overridden=mod.generate(0,0,difficulty='hard',palette_size=1,n_distinct_colors=1)
    stats={'samples':0,'validator_rejected':0,'rival_disagrees_with_independent_oracle':0}
    for band in ('easy','medium','hard'):
        for seed in range(64):
            sample=mod.generate(seed,100+seed,difficulty=band)
            stats['samples']+=1
            stats['validator_rejected']+=bool(mod.self_check(sample))
            stats['rival_disagrees_with_independent_oracle']+=rival(sample)!=reference(sample)
    report={'task_id':tid,'generator_sha256':sha,
            'rule_hash':hashlib.sha256(' '.join(source['program_solution'].split()).encode()).hexdigest()[:12],
            'witness_origin':'handcrafted; no generation seed','input':g,'rival_output':rival(g),
            'independent_reference_prediction':reference(g),'self_check':mod.self_check(g),'domain':domain,
            'canonical_rival_fit':[rival(p['input'])==p['output'] for p in pairs],
            'ordinary_sample_census':stats,'sampler':{'seeds':'0..63 inclusive','sample_index':'100+seed','bands':['easy','medium','hard']},
            'override_defect':{'seed':0,'sample_index':0,'difficulty':'hard',
                               'overrides':{'palette_size':1,'n_distinct_colors':1},
                               'same_grid_as_default':overridden==default,
                               'observed_nonzero_colors':len({x for row in overridden for x in row if x}),
                               'input':overridden},
            'command':['python3','../checks/audit/reproduce.py'],'cwd':'repo',
            'census_authority_note':'Sample census uses an independent Python interpretation; the separate public apply receipt verifies the exact witness.'}
    (home/'input.json').write_text(json.dumps(g)+'\n')
    (home/'finding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(tid,stats,'canonical',report['canonical_rival_fit'],'override colors',report['override_defect']['observed_nonzero_colors'])
