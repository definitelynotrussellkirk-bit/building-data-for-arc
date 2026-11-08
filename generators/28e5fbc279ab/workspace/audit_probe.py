#!/usr/bin/env python3
"""Findings-only audits for the two immutable review targets.

No target is edited. Uses an independent zero-region BFS and actual canonical
Racket outputs. Keeps source hashes, exact inputs, rivals and validator results.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

TASKS = ("988bc6e81731", "b28619e32f6f")


def zero_regions(g):
    h,w=len(g),len(g[0]); unseen={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==0}
    result=[]
    while unseen:
        start=min(unseen); unseen.remove(start); seen={start}; stack=[start]
        while stack:
            r,c=stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen:
                    unseen.remove(p);seen.add(p);stack.append(p)
        if not any(r in (0,h-1) or c in (0,w-1) for r,c in seen):result.append(seen)
    return result


def strict_threshold_rival(g):
    out=[r[:] for r in g]
    for region in zero_regions(g):
        color=8 if len(region)<8 else 4 if len(region)<24 else 3
        for r,c in region:out[r][c]=color
    return out


def largest_rival(g):
    from puzzle_generators.helpers.selfcheck import components
    comps=components(g)
    target=max(comps,key=lambda x:len(x['cells']))
    r0,c0,r1,c1=target['bbox']
    crop=[row[c0:c1+1] for row in g[r0:r1+1]]
    return [[v for v in row for _ in range(2)] for row in crop for _ in range(2)]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--per-band',type=int,default=200)
    ap.add_argument('--seed',type=int,default=211)
    args=ap.parse_args()
    runtime=args.runtime.resolve();sys.path.insert(0,str(runtime))
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs,normalized_rule_hash
    args.out.mkdir(parents=True,exist_ok=True)
    commands={'cwd':str(Path.cwd()),'argv':[sys.executable,*sys.argv]}
    for task in TASKS:
        bundle=runner._load_bundle(task);gen=bundle.generator_module
        source_sha=hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
        identity={'task_id':task,'generator_sha256':source_sha,
                  'rule_sha256':hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
                  'rule_hash':normalized_rule_hash(bundle.rule_source)}
        bridge,fn=runner._open_bridge_with_rule(bundle.rule_callable_text)
        rival=strict_threshold_rival if task==TASKS[1] else largest_rival
        rival_name='strict_less_than_8_and_24' if task==TASKS[1] else 'largest_component_2x'
        counts=Counter();sizes=Counter();canonical=[];failures=[];example=None;seen=set()
        try:
            for i,pair in enumerate(canonical_pairs(task)):
                g=pair['input'];actual=runner._apply_rule(bridge,fn,g)
                errors=gen.self_check(g);other=rival(g)
                canonical.append({'pair_index':i,'validator_messages':errors,
                                  'racket_matches_stored':actual==pair['output'],
                                  'rival_matches_racket':other==actual})
                target_issue=bool(errors) if task==TASKS[0] else other!=actual
                if target_issue and example is None:
                    example={**identity,'origin':'canonical_pair','canonical_pair_index':i,
                             'seed':None,'sample_index':None,'overrides':None,'input':g,
                             'actual_racket_output':actual,'stored_output':pair['output'],
                             'rival':rival_name,'rival_output':other,'validator_messages':errors,
                             'belongs_to_documented_generator_domain':not bool(errors),'command':commands}
            for band in ('easy','medium','hard'):
                for i in range(args.per_band):
                    counts['attempts']+=1
                    try:
                        g=gen.generate(args.seed,i,difficulty=band)
                        actual=runner._apply_rule(bridge,fn,g)
                        errors=gen.self_check(g)
                        counts['validator_rejects']+=bool(errors)
                        counts['rival_matches_racket']+=rival(g)==actual
                        if task==TASKS[1]:sizes.update(len(region) for region in zero_regions(g))
                        counts['completed']+=1
                        seen.add(json.dumps(g,separators=(',',':')))
                        if errors:
                            failures.append({'seed':args.seed,'sample_index':i,'difficulty':band,
                                             'validator_messages':errors,'input':g,'actual_racket_output':actual})
                    except Exception as exc:
                        counts['errors']+=1
                        failures.append({'seed':args.seed,'sample_index':i,'difficulty':band,
                                         'error':f'{type(exc).__name__}: {exc}'})
        finally:bridge.shutdown()
        report={**identity,'schema':'adversarial-audit-v1','sampling':{'seed':args.seed,
                 'sample_index_inclusive':[0,args.per_band-1],'bands':['easy','medium','hard']},
                'counts':dict(counts),'unique_inputs':len(seen),'canonical':canonical,
                'rival':rival_name,'enclosed_area_counts':dict(sorted(sizes.items())),
                'failures':failures,'command':commands,'status':'audit_only_unmodified'}
        (args.out/f'{task}.json').write_text(json.dumps(report,indent=2)+'\n')
        if example:
            (args.out/f'{task}.counterexample.json').write_text(json.dumps(example,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('task_id','generator_sha256','counts','unique_inputs','canonical','enclosed_area_counts')},indent=2),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
