"""Independently reconcile every saved Racket label and inspect sampler shortcuts."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--census',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    probe,contract=load('review_probe'),load('component_contract');gen,source=probe.load_generator()
    raw=a.census.read_bytes();data=json.loads(raw);sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert data['generator_sha256']==sha
    count=Counter();seed_hist=Counter();seed_counts=Counter();heights=Counter();widths=Counter();rivals=Counter();all_seen=set();bounds=[1.0,0.0]
    for lesson in data['lessons']:
        for pair in lesson['instance']['train']+lesson['instance']['test']:
            g,y=pair['input'],pair['output'];h,w=len(g),len(g[0]);count['pairs']+=1
            count['oracle_matches']+=probe.oracle(g)==y
            count['selfcheck_accepted']+=not gen.self_check(g)
            result=contract.analyze(g,background=0,wall_colors=[5],connectivity=4,max_seed_cells_per_component=1)
            count['ownership_contract_passes']+=not result['violations']
            all_seen.add(result['input_sha256']);seeds=[(r,c,v) for r,row in enumerate(g) for c,v in enumerate(row) if v not in (0,5)]
            count['grids_with_border_seed']+=any(r in (0,h-1) or c in (0,w-1) for r,c,v in seeds)
            count['grids_with_only_interior_seeds']+=all(r not in (0,h-1) and c not in (0,w-1) for r,c,v in seeds)
            seed_hist.update(v for r,c,v in seeds);seed_counts[len(seeds)]+=1;heights[h]+=1;widths[w]+=1
            density=sum(v==5 for row in g for v in row)/(h*w);bounds[0]=min(bounds[0],density);bounds[1]=max(bounds[1],density)
            for namespace in ('CANONICAL_SHORTCUTS','LESSON_COMPETITORS','SEMANTIC_RIVALS'):
                for name,rival in getattr(gen,namespace).items():
                    rivals[namespace+':'+name]+=rival(g)!=y
    ok=all(count[key]==count['pairs'] for key in ['oracle_matches','selfcheck_accepted','ownership_contract_passes']) and all(n==count['pairs'] for n in rivals.values())
    out={'schema':'independent-census-reconciliation-v1','task_id':probe.TASK,'phase':'final','generator_sha256':sha,'census_sha256':hashlib.sha256(raw).hexdigest(),'census_sampler':data['sampler'],'status':'pass' if ok else 'fail','counts':dict(count),'unique_inputs':len(all_seen),'seed_color_counts':dict(sorted(seed_hist.items())),'seed_count_histogram':dict(sorted(seed_counts.items())),'height_histogram':dict(sorted(heights.items())),'width_histogram':dict(sorted(widths.items())),'wall_fraction_min_max':bounds,'per_rival_refuted_pairs':dict(rivals),'limitations':['Finite five-rival family only; not universal induction.','Rejecting boards that fail a rival witness biases toward nontrivial region geometry.','At least one unseeded region and unique growing seeds are intentional declared-domain restrictions.','No model training or benchmark improvement measured.']}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['height_histogram','width_histogram']},indent=2));return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
