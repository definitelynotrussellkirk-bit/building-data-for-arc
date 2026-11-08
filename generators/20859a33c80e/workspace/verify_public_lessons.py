#!/usr/bin/env python3
"""Exercise the real public generation sampler with Racket labels and all rivals.

Run from repo/ through the packet wrapper. Research opt-in is explicit: this
script does not upgrade training approval. Retains every episode and actual
accepted sample index, so rejected draws cannot silently change the lesson.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lesson_probe import load_generator, digest, LIBRARY, TASK
from arcpuzzles import Catalog


def verify(count: int, seed: int, out: Path) -> dict:
    module = load_generator()
    source_hash = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    catalog = Catalog(LIBRARY)
    competitors = {**module.CANONICAL_SHORTCUTS, **module.LESSON_COMPETITORS}
    out.mkdir(parents=True, exist_ok=False)
    report = {'task_id': TASK, 'generator_sha256': source_hash, 'rule_hash':module.RULE_HASH,
              'training_admitted':False, 'sampler':'Catalog.generate; canonical Racket labels; actual sample_indices retained',
              'count_per_band':count, 'seed_start':seed, 'seed_stop_exclusive':seed+count,
              'requested_start_index':0, 'n_train':module.EXAMPLES_NEEDED, 'n_test':1,
              'competitors':sorted(competitors), 'per_band':{}, 'failures':[]}
    all_unique=set()
    for band in ('easy','medium','hard'):
        episodes = catalog.generate(TASK, count=count, seed=seed, difficulty=band,
            n_train=module.EXAMPLES_NEEDED, n_test=1, sample_index=0,
            allow_unapproved=True, reference='canonical', timeout=600)
        path=out/f'{band}-episodes.jsonl'
        path.write_text(''.join(json.dumps(ep,separators=(',',':'))+'\n' for ep in episodes))
        metrics=Counter(); unique=set(); survived=Counter(); ambiguous=Counter()
        for ep in episodes:
            metrics['lessons']+=1
            metrics['rejections']+=len(ep['rejections'])
            metrics['nonconsecutive_lessons'] += ep['sample_indices'] != list(range(module.EXAMPLES_NEEDED+1))
            for pair in ep['train']+ep['test']:
                metrics['pairs']+=1
                metrics['mirror_mismatches'] += pair['output'] != module.rule_mirror(pair['input'])
                metrics['selfcheck_failures'] += bool(module.self_check(pair['input']))
                metrics['strict_failures'] += bool(module.strict_canonical_like(pair['input']))
                unique.add(digest(pair['input'])); all_unique.add(digest(pair['input']))
            for query in ep['test']:
                reasons=module.lesson_identifiable(ep['train'],query)
                metrics['hook_rejections']+=bool(reasons)
                for name,fn in competitors.items():
                    fits=all(fn(pair['input'])==pair['output'] for pair in ep['train'])
                    survived[name]+=fits
                    ambiguous[name]+=fits and fn(query['input'])!=query['output']
                if reasons: report['failures'].append({'band':band,'seed':ep['seed'],'reasons':reasons})
            assert ep['provenance']['generator_sha256']==source_hash
            assert ep['executed_rule_hash']==module.RULE_HASH
        report['per_band'][band]={**dict(metrics),'unique_inputs':len(unique),
            'rival_demo_survivors':dict(survived),'ambiguous_lessons':dict(ambiguous),
            'episode_file':path.name,'episode_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        for key in ('mirror_mismatches','selfcheck_failures','strict_failures'):
            if metrics[key]: report['failures'].append({'band':band,key:metrics[key]})
        if any(ambiguous.values()):report['failures'].append({'band':band,'ambiguous':dict(ambiguous)})
        print(band,dict(metrics),flush=True)
    report['unique_inputs_all_bands']=len(all_unique)
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True,type=Path);p.add_argument('--count',type=int,default=100)
    p.add_argument('--seed',type=int,default=1000)
    a=p.parse_args()
    if a.count<1:p.error('--count must be positive')
    r=verify(a.count,a.seed,a.out)
    raise SystemExit(bool(r['failures']))
