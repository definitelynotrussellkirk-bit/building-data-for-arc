"""Read-only generator boundary review. No Racket labels or source mutations."""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse
import hashlib
import importlib.util
import re
import itertools
import json
from pathlib import Path
import sys
import time

WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_pairs, load_selected_generator


def sha(value):
    if not isinstance(value, bytes):
        value=json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def inspect(grid):
    assert isinstance(grid,list) and grid and all(isinstance(row,list) for row in grid)
    h,w=len(grid),len(grid[0])
    assert 1<=h<=30 and 1<=w<=30 and all(len(row)==w for row in grid)
    assert all(type(v) is int and 0<=v<=9 for row in grid for v in row)
    seen=set(); frames=[]; counts=Counter()
    for r in range(h):
        for c in range(w):
            col=grid[r][c]
            if not col or (r,c) in seen: continue
            cells=[]; queue=[(r,c)];seen.add((r,c))
            while queue:
                y,x=queue.pop();cells.append((y,x))
                for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0<=yy<h and 0<=xx<w and (yy,xx) not in seen and grid[yy][xx]==col:
                        seen.add((yy,xx));queue.append((yy,xx))
            if len(cells)==1:
                counts[col]+=1
                continue
            top,left=min(y for y,x in cells),min(x for y,x in cells)
            bottom,right=max(y for y,x in cells),max(x for y,x in cells)
            assert bottom-top>=2 and right-left>=2
            border={(y,x) for y in range(top,bottom+1) for x in range(left,right+1)
                    if y in (top,bottom) or x in (left,right)}
            assert set(cells)==border
            assert all(grid[y][x]==0 for y in range(top+1,bottom) for x in range(left+1,right))
            frames.append({'color':col,'height':bottom-top+1,'width':right-left+1,
                           'origin_parity':(top+left)%2,'capacity':((bottom-top-1)*(right-left-1)+1)//2})
    capacities=[f['capacity'] for f in frames]
    assert frames and len(capacities)==len(set(capacities))
    assert len(counts)==len(set(counts.values()))
    matched=sum(cap in counts.values() for cap in capacities)
    mode='all' if matched==len(frames) else 'partial' if matched else 'none'
    return {'height':h,'width':w,'frames':frames,'singleton_counts':dict(counts),'match_mode':mode}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='checks/code-review/independent-probe.json')
    parser.add_argument('--source')
    cli=parser.parse_args()
    if cli.source:
        path=WORK/cli.source
        body=path.read_bytes();source_sha=sha(body)
        spec=importlib.util.spec_from_file_location('reviewed_snapshot',path)
        mod=importlib.util.module_from_spec(spec)
        exec(compile(body,str(path),'exec'),mod.__dict__)
    else:
        mod,path,source_sha=load_selected_generator('18bd3cd2985e',root=ROOT)
    denominator=int(re.search(r'h \* w // \((\d+) \* k\)',path.read_text()).group(1))
    baseline=WORK/'.review/baseline/repo/generators/18bd3cd2985e/generator.py'
    report={'schema':'arc-readonly-canonical-code-review-v1','source_path':str(path),
            'source_sha256':source_sha,'baseline_sha256':sha(baseline.read_bytes()),
            'python':sys.executable,'command':sys.argv,'status':'running',
            'scope':'Independent Python geometry, joint override boundaries, and conditional distribution; no Racket sweeps'}
    cases=[];failures=[];timings=[]
    started=time.monotonic()
    for band,h,w,k,mode,seed_index in itertools.product(
            (None,'easy','medium','hard'),(12,13,30),(12,13,30),(1,2,3),
            ('all','partial','none'),((0,0),(1,5),(17,3),(29,2))):
        if k==1 and mode=='partial':continue
        seed,index=seed_index
        args={'grid_h':h,'grid_w':w,'n_frames':k,'match_mode':mode}
        case={'difficulty':band,'seed':seed,'sample_index':index,'overrides':args}
        before=time.monotonic()
        try:
            grid=mod.generate(seed,index,difficulty=band,**args)
            actual=inspect(grid)
            assert not mod.self_check(grid)
            assert actual['height']==h and actual['width']==w and len(actual['frames'])==k
            assert actual['match_mode']==mode
            assert len(actual['singleton_counts'])==k
            assert not ({f['color'] for f in actual['frames']} & set(actual['singleton_counts']))
            if len(cases)<12:
                assert mod.generate(seed,index,difficulty=band,**args)==grid
            case.update(status='passed',input_sha256=sha(grid))
        except Exception as exc:
            case.update(status='failed',error=repr(exc))
            if 'grid' in locals():case['grid']=grid
            failures.append(case.copy())
        elapsed=time.monotonic()-before
        timings.append((elapsed,case.copy()))
        cases.append(case)
    rejects=[]
    invalid=[{'grid_h':v} for v in (11,31,True,12.0,'12')]
    invalid += [{'grid_w':v} for v in (11,31,False,12.0,'12')]
    invalid += [{'n_frames':v} for v in (0,4,True,2.0,'2')]
    invalid += [{'n_frames':1,'match_mode':'partial'}]
    for args in invalid:
        try:
            mod.generate(0,0,**args)
            rejects.append({'overrides':args,'status':'unexpected_acceptance'})
        except (TypeError,ValueError) as exc:
            rejects.append({'overrides':args,'status':'rejected','exception':type(exc).__name__,'message':str(exc)})
    profiles={(20,20,2),(18,23,2),(12,20,2),(22,26,3)}
    conditional=defaultdict(Counter); max_cap=defaultdict(int); dist_cases=[]
    for seed,index in itertools.product((0,7,17,29),range(24)):
        grid=mod.generate(seed,index,difficulty='hard')
        actual=inspect(grid)
        mode=actual['match_mode']; profile=(len(grid),len(grid[0]),len(actual['frames']))
        is_canonical=profile in profiles
        conditional[mode]['canonical_profile' if is_canonical else 'broad_profile']+=1
        max_cap[mode]=max(max_cap[mode],max(f['capacity'] for f in actual['frames']))
        dist_cases.append({'seed':seed,'sample_index':index,'mode':mode,'profile':profile,
                           'canonical_profile':is_canonical,'max_capacity':max(f['capacity'] for f in actual['frames']),
                           'input_sha256':sha(grid)})
    possible=[]
    for h,w,k in sorted(profiles):
        budget=max(20,h*w//(denominator*k))
        caps=[((fh-2)*(fw-2)+1)//2 for fh in range(3,12) for fw in range(3,12)
              if fh*fw<=budget and ((fh-2)*(fw-2)+1)//2<=27]
        possible.append({'profile':[h,w,k],'frame_area_budget':budget,'hard_max_possible_capacity':max(caps)})
    canonical=[]
    for pair in canonical_pairs('18bd3cd2985e',root=ROOT,labeled_only=True):
        actual=inspect(pair['input'])
        canonical.append({'variant':pair['variant'],'split':pair['split'],'pair_index':pair['pair_index'],
                          'accepted_by_self_check':not mod.self_check(pair['input']),
                          'accepted_by_strict_canonical_like':not mod.strict_canonical_like(pair['input']),
                          'frames':actual['frames']})
    report.update(status='passed' if not failures and all(x['status']=='rejected' for x in rejects) else 'failed',
                  joint_boundary_cases=len(cases),failed_cases=failures,case_digest=sha(cases),
                  successful_case_matrix=cases,invalid_override_probes=rejects,
                  elapsed_seconds=round(time.monotonic()-started,3),
                  slowest_cases=[{'seconds':round(t,6),**case} for t,case in sorted(timings,key=lambda x:-x[0])[:5]],
                  conditional_distribution={mode:dict(counts) for mode,counts in conditional.items()},
                  observed_max_capacity=dict(max_cap),distribution_cases=dist_cases,
                  mathematically_possible_canonical_profile_capacities=possible,
                  canonical_input_acceptance=canonical,
                  unchanged_source_after_run=sha(path.read_bytes())==source_sha)
    out=WORK/cli.out
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('status','source_sha256','joint_boundary_cases','failed_cases','elapsed_seconds','conditional_distribution','observed_max_capacity','mathematically_possible_canonical_profile_capacities','unchanged_source_after_run')},indent=2))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
