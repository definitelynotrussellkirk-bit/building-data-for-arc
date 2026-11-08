"""Exhaust all count/orientation tuples on the smallest advertised canvas.

Then cross every canvas size with all orientations at maximum motif counts.
This tests generation + input validation + independent geometry, NOT Racket.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time
from reference_probe import load_generator, observed, geometry_output


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    gen=load_generator(); started=time.monotonic(); errors=[]; total=0
    def check(options):
        nonlocal total
        i=total; total+=1
        try:
            g=gen.generate(919,i,difficulty=('easy','medium','hard')[i%3],**options)
            issues=gen.self_check(g)
            actual=observed(g)
            if issues or actual != options or gen.observe_overrides(g) != options:
                raise AssertionError(f'counts/validation: {actual}, {issues}')
            out=geometry_output(g)
            changes=sum(a!=b for rowa,rowb in zip(g,out) for a,b in zip(rowa,rowb))
            if changes != 2*options['n_pairs']+options['n_axis']:
                raise AssertionError(f'wrong changed-cell count: {changes}')
        except Exception as exc:
            errors.append({'sample_index':i,'overrides':options,'error':f'{type(exc).__name__}: {exc}'})
    for so,to,pairs,noise,axis,distractors in itertools.product(range(8),range(8),range(1,7),range(5),range(6),range(5)):
        check(dict(grid_h=10,grid_w=14,source_orientation=so,target_orientation=to,
                   n_pairs=pairs,n_noise=noise,n_axis=axis,n_distractors=distractors))
    counts_cases=total
    for h,w,so,to in itertools.product(range(10,25),range(14,25),range(8),range(8)):
        check(dict(grid_h=h,grid_w=w,source_orientation=so,target_orientation=to,
                   n_pairs=6,n_noise=4,n_axis=5,n_distractors=4))
    report={'schema':'b90d4c3d5553-cartesian-stress-v1','generator_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
            'cases':total,'count_orientation_cases_on_10x14':counts_cases,
            'dimension_orientation_cases_at_max_counts':total-counts_cases,
            'seconds':time.monotonic()-started,'errors':errors,
            'racket_executed':False,'passed':not errors}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='errors'},indent=2))
    return int(bool(errors))


if __name__=='__main__': raise SystemExit(main())
