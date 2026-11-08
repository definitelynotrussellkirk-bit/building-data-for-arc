"""Source-bound authoring probe using the public Racket API, not private runners.

Run from the packet with:
 python3 run_with_racket.py python3 generators/cdb267535df8/workspace/probe_voronoi.py --out ../checks/voronoi-probe.json
Keep this tool closed during a visible-only solve: it reads canonical answers.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK='cdb267535df8'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--per-band', type=int, default=100)
    args=parser.parse_args()
    if not 1<=args.per_band<=1000:parser.error('--per-band must be 1..1000')
    if args.out.exists():parser.error('output already exists; preserve prior evidence')
    root=find_root(__file__)
    candidates=[root/'generators'/TASK/'generator.py',root/'puzzle_generators/per_puzzle'/TASK/'generator.py']
    source=next(p for p in candidates if p.is_file())
    spec=importlib.util.spec_from_file_location('reviewed',source)
    gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    pairs=canonical_pairs(TASK, root=root)
    report={'task_id':TASK,'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'rule_hash':gen.RULE_HASH,'argv':sys.argv,'cwd':str(Path.cwd()),
            'canonical_rival_fit':{name:{'matched':sum(fn(p['input'])==p['output'] for p in pairs),
                                             'total':len(pairs)} for name,fn in gen.CANONICAL_SHORTCUTS.items()},
            'bands':{},'scope':'finite default draws; no universal identifiability claim'}
    reference_inputs=[p['input'] for p in pairs]
    reference_meta=[{'canonical_pair':i} for i in range(len(pairs))]
    exact_example=None
    for band in ('easy','medium','hard'):
        hist=Counter();palette=set();unique=set();unreachable=0
        witnesses=Counter(); failures=[]
        for i in range(args.per_band):
            g=gen.generate(99100+i,i,difficulty=band)
            obs=gen.observe_overrides(g)
            hist.update([f"{obs['grid_h']}x{obs['grid_w']}/seeds={obs['n_seeds']}/colors={obs['n_seed_colors']}"])
            palette.update(v for row in g for v in row if v not in (0,5))
            unique.add(json.dumps(g,separators=(',',':')))
            errors=gen.self_check(g)
            if errors:failures.append({'seed':99100+i,'sample_index':i,'errors':errors})
            for name,predicate in gen.SEMANTIC_WITNESSES.items():witnesses[name]+=bool(predicate(g))
            prediction=gen._prediction(g)
            records=gen._distance_maps(tuple(tuple(row) for row in g))
            w=len(g[0])
            unreachable+=any(v==0 and all(ds[r*w+c]<0 for _,ds in records)
                             for r,row in enumerate(g) for c,v in enumerate(row))
            if i<12:
                reference_inputs.append(g);reference_meta.append({'band':band,'seed':99100+i,'sample_index':i})
            if exact_example is None and gen._tie_by_seed(g)!=prediction:
                rival=gen._tie_by_seed(g)
                difference=next((r,c) for r in range(len(g)) for c in range(w) if rival[r][c]!=prediction[r][c])
                exact_example={'input':g,'rival_output':rival,'difference_cell':list(difference),
                               'seed':99100+i,'sample_index':i,'difficulty':band,'overrides':{},
                               'validator_errors':errors,'reference_result_index':len(pairs)+i}
        report['bands'][band]={'draws':args.per_band,'seed_start':99100,'seed_end':99100+args.per_band-1,
                               'sample_index_start':0,'sample_index_end':args.per_band-1,
                               'unique_inputs':len(unique),'histogram':dict(hist),'seed_palette':sorted(palette),
                               'unreachable_blank_examples':unreachable,'witness_counts':dict(witnesses),'failures':failures}
    applied=Catalog(root).apply(TASK,reference_inputs,timeout=300)
    mismatches=[]
    for i,result in enumerate(applied['results']):
        if result['output']!=gen._prediction(result['input']):mismatches.append(i)
    if exact_example is not None:
        exact_example['actual_racket_output']=applied['results'][exact_example['reference_result_index']]['output']
    report.update({'racket_evidence':applied,'reference_case_metadata':reference_meta,
                   'racket_compared':len(reference_inputs),'racket_mismatch_indices':mismatches,
                   'generated_counterexample':exact_example})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'out':str(args.out),'generator_sha256':report['generator_sha256'],
                     'racket_compared':len(reference_inputs),'mismatches':mismatches,
                     'canonical_rival_fit':report['canonical_rival_fit']}))
    return int(bool(mismatches) or any(v['failures'] for v in report['bands'].values()))


if __name__=='__main__':raise SystemExit(main())
