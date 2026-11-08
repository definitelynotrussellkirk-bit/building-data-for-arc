"""Findings-only proposal: midpoint-edge template shortcut, no source edits.
Run through review.py run python3 ../checks/audit/0e134ade0f09/probe.py.
Then public apply the resulting input.json; pass --summarize after apply.
"""
import argparse, hashlib, importlib.util, json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

HERE=Path(__file__).resolve().parent
TASK='0e134ade0f09'
CROSS=((0,0),(-1,0),(1,0),(0,-1),(0,1))

def rival(grid):
    """Infer outputs from component bounding-box midpoints; do not read rings."""
    h,w=len(grid),len(grid[0]);bg=grid[1][1]
    sides={'top':grid[0][1],'right':grid[1][-1],'bottom':grid[-1][1],'left':grid[1][0]}
    fg=next(iter({v for row in grid for v in row}-{0,bg,*sides.values()}))
    unseen={(r,c) for r in range(1,h-1) for c in range(1,w-1) if grid[r][c]==fg}
    out=[row[:] for row in grid]
    while unseen:
        p=unseen.pop();stack=[p];comp={p}
        while stack:
            r,c=stack.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen:unseen.remove(q);comp.add(q);stack.append(q)
        r0=min(r for r,c in comp);r1=max(r for r,c in comp)
        c0=min(c for r,c in comp);c1=max(c for r,c in comp)
        midr,midc=(r0+r1)//2,(c0+c1)//2
        centers={'top':(r0,midc),'right':(midr,c1),'bottom':(r1,midc),'left':(midr,c0)}
        for side,(r,c) in centers.items():
            if all(grid[r+dr][c+dc]==bg for dr,dc in CROSS):
                for dr,dc in CROSS:out[r+dr][c+dc]=sides[side]
    return out

def main():
    args=argparse.ArgumentParser();args.add_argument('--summarize',action='store_true');opts=args.parse_args()
    if opts.summarize:
        manifest=json.loads((HERE/'cases.json').read_text());applied=json.loads((HERE/'racket.json').read_text())
        cases=[]
        for case,result in zip(manifest['cases'],applied['results'],strict=True):
            out=result['output'];pred=case['rival_output']
            changes=[{'row':r,'col':c,'rival':pred[r][c],'reference':out[r][c]} for r in range(len(out)) for c in range(len(out[0])) if pred[r][c]!=out[r][c]]
            cases.append({k:v for k,v in case.items() if k!='rival_output'}|{'valid_output':result['valid_output'],'error':result['error'],'rival_equal_reference':not changes,'rival_reference_mismatched_cells':len(changes),'first_mismatches':changes[:12]})
        summary={'source':{k:applied[k] for k in ('generator_sha256','executed_rule_hash','rule_text_sha256','rule_hash_matches_catalog','catalog_approved')},'generated_total':sum(c['kind']=='generated' for c in cases),'generated_rival_matches':sum(c['kind']=='generated' and c['rival_equal_reference'] for c in cases),'canonical_total':sum(c['kind']=='canonical' for c in cases),'canonical_rival_matches':sum(c['kind']=='canonical' and c['rival_equal_reference'] for c in cases),'cases':cases}
        (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='cases'},indent=2));return
    spec=importlib.util.spec_from_file_location('audited',Path('generators')/TASK/'generator.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    catalog=Catalog();desc=catalog.describe(TASK);cases=[];grids=[]
    for index in range(24):
        difficulty=('easy','medium','hard')[index%3];seed=820000+index
        overrides={'n_notches':4 if index%2==0 else 8}
        grid=g.generate(seed,index,difficulty=difficulty,**overrides)
        cases.append({'kind':'generated','seed':seed,'sample_index':index,'difficulty':difficulty,'overrides':overrides,'self_check':g.self_check(grid),'strict_canonical_like':g.strict_canonical_like(grid),'observed':g.observe_overrides(grid),'rival_output':rival(grid)})
        grids.append(grid)
    seen=set()
    for pair in canonical_pairs(TASK,root=catalog.root):
        digest=hashlib.sha256(json.dumps(pair['input'],separators=(',',':')).encode()).hexdigest()
        if digest in seen:continue
        seen.add(digest);grid=pair['input']
        cases.append({'kind':'canonical','variant':pair['variant'],'split':pair['split'],'pair_index':pair['pair_index'],'self_check':g.self_check(grid),'strict_canonical_like':g.strict_canonical_like(grid),'observed':g.observe_overrides(grid),'rival_equals_stored_output':rival(grid)==pair['output'],'rival_output':rival(grid)})
        grids.append(grid)
    for i,c in enumerate(cases):c['input_index']=i
    (HERE/'input.json').write_text(json.dumps(grids)+'\n')
    (HERE/'cases.json').write_text(json.dumps({'generator_sha256':desc['generator_sha256'],'rule_hash':desc['rule_hash'],'cases':cases},indent=2)+'\n')
    print(json.dumps({'generator_sha256':desc['generator_sha256'],'rule_hash':desc['rule_hash'],'generated':24,'unique_canonical':len(seen),'inputs':len(grids)}))
if __name__=='__main__':main()
