#!/usr/bin/env python3
"""Findings-only audit of the two immutable assigned targets.

Run from a runtime staged with task_ids=['96d2d525a266','13e4ae480f66'].
The target generators are never edited. Source hashes, seeds, exact grids,
validator outcomes and live Racket answers are retained in the report.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT=Path.cwd().resolve()
sys.path.insert(0,str(ROOT))
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash, canonical_rule_source
from scripts.generator_semantic_gate import _RuleOracle


def components(grid):
    pending={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==1}
    groups=[]
    while pending:
        first=min(pending);pending.remove(first);group={first};todo=[first]
        while todo:
            r,c=todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in pending:
                    pending.remove(p);group.add(p);todo.append(p)
        groups.append(group)
    return groups


def any_border_rival(grid):
    output=copy.deepcopy(grid);h,w=len(grid),len(grid[0])
    for group in components(grid):
        if any(r in (0,h-1) or c in (0,w-1) for r,c in group):
            for r,c in group:output[r][c]=4
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    summary={}
    for task in ('96d2d525a266','13e4ae480f66'):
        gen=importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
        report={'task_id':task,'generator_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                'rule_hash':canonical_rule_hash(task),
                'rule_source_sha256':hashlib.sha256(canonical_rule_source(task).encode()).hexdigest(),
                'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'command':{'cwd':str(ROOT),'argv':[sys.executable,'audit_probe.py',*sys.argv[1:]]}}
        oracle=_RuleOracle(task)
        if not oracle.ready:raise RuntimeError(oracle.error)
        def apply(grid):
            answer,error=oracle.apply(grid)
            if error:raise RuntimeError(error)
            return answer
        try:
            pairs=canonical_pairs(task)
            report['canonical_pairs']=len(pairs)
            report['canonical_racket_matches']=sum(apply(p['input'])==p['output'] for p in pairs)
            report['canonical_validator_errors']=[gen.self_check(p['input']) for p in pairs]
            if task=='96d2d525a266':
                requested={'grid_h':20,'grid_w':20,'n_pair_colors':4}
                grid=gen.generate(1,0,difficulty='easy',**requested)
                plain=gen.generate(1,0,difficulty='easy')
                bycolor={c:[(r,k) for r,row in enumerate(grid) for k,v in enumerate(row) if v==c]
                         for c in {v for row in grid for v in row}-{0}}
                n_pairs=sum(len(cells)==2 and cells[0][0]!=cells[1][0] and cells[0][1]!=cells[1][1]
                            for cells in bycolor.values())
                report['finding']='Advertised grid_h/grid_w/n_pair_colors overrides are silently ignored.'
                report['counterexample']={'seed':1,'sample_index':0,'difficulty':'easy','overrides':requested,
                    'input':grid,'actual_racket_output':apply(grid),'rival_output':None,
                    'rival_output_note':'This is an exact-override defect, not an output-rule rival claim.',
                    'observed':{'grid_h':len(grid),'grid_w':len(grid[0]),'n_pair_colors':n_pairs},
                    'byte_equal_to_no_overrides':grid==plain,'self_check':gen.self_check(grid),
                    'documented_domain':True,'domain_note':'Requested values all lie in the advertised AXES ranges.'}
                assert grid==plain and len(grid)!=20
                ignored=0;strict=0
                for band in ('easy','medium','hard'):
                    for i in range(30):
                        g=gen.generate(7000+i,i,difficulty=band,**requested)
                        ignored+=g==gen.generate(7000+i,i,difficulty=band)
                        strict+=not gen.self_check(g)
                report['census']={'bands':['easy','medium','hard'],'seed_range':[7000,7029],
                                  'sample_index_range':[0,29],'draws':90,'identical_with_and_without_overrides':ignored,
                                  'validator_accepted':strict}
            else:
                report['finding']='Any-border recoloring survives the sampled training distribution; non-left border controls are absent.'
                report['rival']='recolor any blue component touching any of the four borders'
                report['canonical_rival_fit_counts']=sum(any_border_rival(p['input'])==p['output'] for p in pairs)
                counts={};unique=set()
                for band in ('easy','medium','hard'):
                    matches=accepted=0
                    for i in range(30):
                        grid=gen.generate(7000+i,i,difficulty=band)
                        actual=apply(grid)
                        matches+=any_border_rival(grid)==actual
                        accepted+=not gen.self_check(grid)
                        unique.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
                    counts[band]={'draws':30,'rival_matches':matches,'validator_accepted':accepted}
                report['census']={'seed_range':[7000,7029],'sample_index_range':[0,29],
                                  'bands':counts,'draws':90,'unique_inputs':len(unique)}
                grid=[[0]*11 for _ in range(9)]
                for r,c in ((1,0),(2,0),(4,10),(5,10),(6,5),(6,6)):grid[r][c]=1
                actual=apply(grid);rival=any_border_rival(grid)
                assert actual!=rival
                report['counterexample']={'input':grid,'actual_racket_output':actual,'rival_output':rival,
                    'seed':None,'sample_index':None,'overrides':{},'construction':'hand-built exact scene, not an ordinary draw',
                    'self_check':gen.self_check(grid),
                    'documented_domain':'One left-touching and two non-left blue 4-components; generator padding excludes the right-edge control.',
                    'ordinary_generator_support':False,
                    'different_cells':[[r,c,actual[r][c],rival[r][c]] for r in range(9) for c in range(11) if actual[r][c]!=rival[r][c]]}
                requested=gen.generate(1,0,n_left=3,n_interior=3)
                groups=components(requested)
                report['secondary_override_probe']={'seed':1,'sample_index':0,'overrides':{'n_left':3,'n_interior':3},
                    'observed_left':sum(any(c==0 for _,c in group) for group in groups),
                    'observed_interior':sum(all(c>0 for _,c in group) for group in groups),
                    'input':requested,'self_check':gen.self_check(requested)}
            report['target_modified']=False
        finally:oracle.close()
        path=out/(task+'.json');path.write_text(json.dumps(report,indent=2)+'\n')
        summary[task]={'path':path.name,'finding':report['finding'],
                       'canonical_pairs':report['canonical_pairs'],
                       'canonical_racket_matches':report['canonical_racket_matches'],
                       'generator_sha256':report['generator_sha256'],'rule_hash':report['rule_hash']}
        print(task,report['finding'],flush=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
