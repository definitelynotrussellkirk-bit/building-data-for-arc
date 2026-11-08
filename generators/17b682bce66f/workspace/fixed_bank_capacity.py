"""Enumerate exact input support of the retained translated witness bank.

Run from packet root; pass --runtime .review/baseline_runtime to reproduce the
v3.0.0 bottleneck. In v3.1.0 this measures only the fixed branch, not the whole
procedural distribution. No labels or private solve artifacts are consulted.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    sys.path.insert(0,str(args.runtime.resolve()))
    g=importlib.import_module('puzzle_generators.per_puzzle.17b682bce66f.generator')
    all_hashes=set(); profiles={}; failures=[]
    for name,spec in g._SCENES.items():
        rr,cc=next((r,c) for r,c,v in spec.cells if v==9)
        offsets=tuple((r-rr,c-cc) for r,c,v in spec.cells if v==8)
        foot={(r,c) for r,c,v in spec.cells}
        for anchor in spec.cells:
            if anchor[2] in (2,3,4,5): foot.update(g._stamp_cells(anchor,offsets))
        rs=range(-min(r for r,c in foot),spec.height-max(r for r,c in foot))
        cs=range(-min(c for r,c in foot),spec.width-max(c for r,c in foot))
        shifts=[(r,c) for r in rs for c in cs] if spec.allow_translation else [(0,0)]
        hashes=[]
        for dr,dc in shifts:
            grid=[[0]*spec.width for _ in range(spec.height)]
            for r,c,v in spec.cells: grid[r+dr][c+dc]=v
            errs=g.self_check(grid)
            if errs: failures.append({'profile':name,'shift':[dr,dc],'errors':errs,'input':grid})
            h=hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()
            hashes.append(h);all_hashes.add(h)
        profiles[name]={'translation_count':len(shifts),'distinct_inputs':len(set(hashes)),
                        'input_hashes':hashes}
    r={'schema':'exact-fixed-bank-support-v1','task_id':g.TASK_ID,
       'generator_sha256':hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest(),
       'scope':'fixed bank only; whole support only when no procedural branch exists',
       'fixed_profiles':len(profiles),'distinct_inputs':len(all_hashes),
       'profiles':profiles,'failures':failures}
    with args.out.open('x') as f: json.dump(r,f,indent=2);f.write('\n')
    print(args.out)
    return int(bool(failures))

if __name__=='__main__':
    raise SystemExit(main())
