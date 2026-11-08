"""Verify whole lessons through the public Racket-backed Catalog.generate API.

The companion probe.py tests all cyclic starts with an independent oracle.
This tool checks the real materializer, including accepted indices/rejections.
No-contract is an error, never a vacuous semantic pass. No training approval is
changed. Run from repo via the packet's run_with_racket.py wrapper.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from probe import load_generator, oracle, digest
from arcpuzzles import Catalog


def score_episodes(gen, episodes):
    rivals=dict(getattr(gen,'CANONICAL_SHORTCUTS',{}))
    rivals.update(getattr(gen,'LESSON_COMPETITORS',{}))
    if not rivals:
        raise ValueError('NO_CONTRACT: declare at least one falsifiable lesson rival')
    survived={name:0 for name in rivals}
    query_errors={name:0 for name in rivals}
    unique=set(); mismatches=[]; rejections=[]; windows=[]
    for i,episode in enumerate(episodes):
        demos=episode['train']; queries=episode['test']
        windows.append({'seed':episode['seed'],'sample_indices':episode.get('sample_indices'),
                        'episode_index':episode.get('episode_index')})
        rejections.extend(episode.get('rejections',[]))
        for j,pair in enumerate(demos+queries):
            unique.add(digest(pair['input']))
            if oracle(pair['input'])!=pair['output']:
                mismatches.append({'episode':i,'pair_index':j})
        for name,rival in rivals.items():
            fits=all(rival(p['input'])==p['output'] for p in demos)
            survived[name]+=fits
            query_errors[name]+=fits and any(rival(p['input'])!=p['output'] for p in queries)
    return {'lessons':len(episodes),'pairs':sum(len(e['train'])+len(e['test']) for e in episodes),
            'unique_inputs':len(unique),'survived_demos':survived,
            'survived_demos_wrong_query':query_errors,'racket_oracle_mismatches':mismatches,
            'rejections':rejections,'accepted_windows':windows}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--count',type=int,default=100)
    ap.add_argument('--seed',type=int,default=20261003)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.count<1: ap.error('--count must be positive')
    args.out.mkdir(parents=True,exist_ok=True)
    gen=load_generator(); cat=Catalog()
    report={'task_id':gen.TASK_ID,'generator_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
            'rule_hash':gen.RULE_HASH,'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'sampler':'public Catalog.generate; count episodes, derived episode seeds, sample_index=0; accept/reject indices retained',
            'requested_seed':args.seed,'requested_count_per_band':args.count,
            'n_train':3,'n_test':1,'bands':{},'completed':False}
    target=args.out/'summary.json'
    for band in ('easy','medium','hard'):
        episodes=cat.generate(gen.TASK_ID,count=args.count,seed=args.seed,difficulty=band,
                              n_train=3,n_test=1,sample_index=0,allow_unapproved=True,timeout=900)
        path=args.out/f'{band}.jsonl'
        path.write_text(''.join(json.dumps(e,separators=(',',':'))+'\n' for e in episodes))
        assert all(e['provenance']['generator_sha256']==report['generator_sha256'] for e in episodes)
        result=score_episodes(gen,episodes)
        result.update(episodes_file=path.name,episodes_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        report['bands'][band]=result
        target.write_text(json.dumps(report,indent=2)+'\n')
        print(band,{k:v for k,v in result.items() if k!='accepted_windows'},flush=True)
    report['completed']=True
    target.write_text(json.dumps(report,indent=2)+'\n')
    return int(any(b['racket_oracle_mismatches'] or b['rejections'] or any(b['survived_demos'].values())
                   for b in report['bands'].values()))

if __name__=='__main__':
    raise SystemExit(main())
