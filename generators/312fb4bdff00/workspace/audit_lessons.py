"""Audit all cyclic query rotations of a saved public lesson census.

Usage (from repo via packet wrapper):
  python3 generators/312fb4bdff00/workspace/audit_lessons.py \
    --census ../checks/lesson-census.json --out ../checks/cyclic-lessons.json

Reads retained Racket-derived pairs and dynamically discovers every declared
rival, rather than copying names. Also cross-checks the independent grid-rotation
oracle against those labels. No generation and no hidden solve labels are read.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from review_probe import cyclic_rivals,load_generator,oracle,matches


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        raise SystemExit('Output must be a new path')
    raw=args.census.read_bytes();data=json.loads(raw);gen=load_generator()
    source_sha=hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    if data['generator_sha256'] != source_sha:
        raise SystemExit('Census generator bytes do not match the selected source')
    if data['status'] != 'no_declared_ambiguity' or data['errors']:
        raise SystemExit('Expected a complete error-free census; inspect it before auditing')
    report={'generator_sha256':source_sha,'census_sha256':hashlib.sha256(raw).hexdigest(),
            'bands':{},'racket_agreement':{'tested':0,'mismatches':[]},
            'winning_transform_counts':{},'winning_candidate_counts':{},
            'match_count_counts':{},'limitations':'Finite declared rivals; rotations reuse inputs and are not independent samples.'}
    transforms=Counter();candidates=Counter();counts=Counter()
    for band in ('easy','medium','hard'):
        instances=[row['instance'] for row in data['lessons'] if row['band']==band]
        report['bands'][band]=cyclic_rivals(gen,instances)
        for instance in instances:
            for split in ('train','test'):
                for pair in instance[split]:
                    row=report['racket_agreement'];row['tested']+=1
                    if oracle(pair['input']) != pair['output']:
                        row['mismatches'].append({'band':band,'pair':pair})
                    hits=matches(pair['input']);counts[len(hits)]+=1
                    if hits:
                        candidates[hits[0][0]]+=1;transforms[hits[0][1]]+=1
    report['winning_transform_counts']=dict(sorted(transforms.items()))
    report['winning_candidate_counts']=dict(sorted(candidates.items()))
    report['match_count_counts']=dict(sorted(counts.items()))
    report['passed']=not report['racket_agreement']['mismatches'] and all(
        not band['ambiguities'] for band in report['bands'].values())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='bands'},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
