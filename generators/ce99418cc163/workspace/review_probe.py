"""Source-bound lesson census, independent rectangle oracle, and Racket receipts.

Run from repo via the packet wrapper. This is review evidence, not a label
exporter. It reads actual CANONICAL_SHORTCUTS/LESSON_COMPETITORS declarations.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime

TASK = 'ce99418cc163'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def rectangle_oracle(grid):
    """Independent exhaustive rectangle enumeration, never used to emit labels."""
    out = [row[:] for row in grid]
    for a, b in itertools.combinations(range(len(grid)), 2):
        for x, y in itertools.combinations(range(len(grid[0])), 2):
            points = [(a,x),(a,y),(b,x),(b,y)]
            if sum(grid[r][c] == 2 for r,c in points) == 3:
                for r,c in points:
                    if grid[r][c] == 0:
                        out[r][c] = 3
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds-per-band', type=int, default=34)
    args = parser.parse_args()
    if args.seeds_per_band < 1:
        parser.error('--seeds-per-band must be positive')
    args.out.mkdir(parents=True, exist_ok=False)
    catalog = Catalog(Path.cwd())
    source = Path(__file__).resolve().parents[1] / 'generator.py'
    spec = importlib.util.spec_from_file_location('reviewed_generator', source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    meta = catalog.describe(TASK)
    assert source_hash == meta['generator_sha256']
    with tempfile.TemporaryDirectory(prefix='review-canonical-reader-') as temp:
        prepare_runtime(catalog, Path(temp), TASK)
        sys.path.insert(0, temp)
        from scripts.canonical_profile_gate import canonical_pairs
        canonical = canonical_pairs(TASK)
        sys.path.remove(temp)
    assert canonical and all(p['output'] for p in canonical)
    summary = {
        'task_id':TASK, 'generator_sha256':source_hash, 'rule_hash':gen.RULE_HASH,
        'source_kind':'reviewer-measured', 'training_admitted':False,
        'sampler':'Direct generate(seed, start+i, difficulty=band); three demos then one query; no rejection/resampling',
        'seed_formula':'1000000*(band_index+1) + 104729*k; k=0..seeds_per_band-1',
        'seeds_per_band':args.seeds_per_band, 'cyclic_starts':[0,1,2],
        'indices_per_seed':[0,1,2,3,4,5],
        'canonical_pairs':len(canonical), 'canonical_shortcuts':{}, 'bands':{},
        'failures':[], 'domain_limits':'Four red-graph families only. Two declared rivals only. Three consecutive demos required; arbitrary resampling/shorter lessons have no coverage guarantee.',
    }
    for index,pair in enumerate(canonical):
        if gen.strict_canonical_like(pair['input']):
            summary['failures'].append(['canonical_rejected',index])
    for name,fn in gen.CANONICAL_SHORTCUTS.items():
        fits = sum(fn(p['input']) == p['output'] for p in canonical)
        summary['canonical_shortcuts'][name] = {'passed':fits,'total':len(canonical)}
        if fits != len(canonical):
            summary['failures'].append(['not_canonical_shortcut',name])
    all_rows = []
    for b,band in enumerate(('easy','medium','hard')):
        rows=[]
        for k in range(args.seeds_per_band):
            seed=1000000*(b+1)+104729*k
            for index in range(6):
                grid=gen.generate(seed,index,difficulty=band)
                rows.append({'band':band,'seed':seed,'sample_index':index,'input':grid,'input_sha256':digest(grid)})
        all_rows.extend(rows)
    # Include the canonical pairs in the same fresh reference execution.
    inputs=[p['input'] for p in canonical]+[r['input'] for r in all_rows]
    answers=[]
    for offset in range(0,len(inputs),64):
        receipt=catalog.apply(TASK,inputs[offset:offset+64],reference='canonical',timeout=180)
        assert receipt['generator_sha256']==source_hash
        assert receipt['rule_hash_matches_catalog'] is True
        (args.out/f'racket-{offset:04d}.json').write_text(json.dumps(receipt,separators=(',',':'))+'\n')
        for row in receipt['results']:
            if row['error'] is not None:
                raise RuntimeError(row['error'])
            answers.append(row['output'])
        print('Reference-labelled',min(offset+64,len(inputs)),'/',len(inputs),flush=True)
    for i,pair in enumerate(canonical):
        if answers[i] != pair['output']:
            summary['failures'].append(['canonical_authority',i])
    witnesses_saved=set()
    for item,answer in zip(all_rows,answers[len(canonical):],strict=True):
        item['output']=answer
        if gen.self_check(item['input']):
            summary['failures'].append(['self_check',item['band'],item['seed'],item['sample_index']])
        if rectangle_oracle(item['input']) != answer:
            summary['failures'].append(['independent_oracle',item['band'],item['seed'],item['sample_index']])
        if gen._diagnostic_one_pass(item['input']) != answer:
            summary['failures'].append(['diagnostic_oracle',item['band'],item['seed'],item['sample_index']])
        for name,fn in gen.LESSON_COMPETITORS.items():
            prediction=fn(item['input'])
            if prediction != answer and name not in witnesses_saved:
                witness={**item,'generator_sha256':source_hash,'rule_hash':gen.RULE_HASH,'rival':name,'rival_output':prediction}
                (args.out/f'witness-{name}.json').write_text(json.dumps(witness,indent=2)+'\n')
                witnesses_saved.add(name)
    for band in ('easy','medium','hard'):
        rows=[r for r in all_rows if r['band']==band]
        by_key={(r['seed'],r['sample_index']):r for r in rows}
        seeds=sorted({r['seed'] for r in rows})
        lesson_stats={n:Counter() for n in gen.LESSON_COMPETITORS}
        lesson_records=[]
        for seed in seeds:
            for start in (0,1,2):
                demos=[by_key[(seed,start+i)] for i in range(3)]
                query=by_key[(seed,start+3)]
                record={'seed':seed,'start':start,'rivals':{}}
                for name,fn in gen.LESSON_COMPETITORS.items():
                    fits=all(fn(d['input'])==d['output'] for d in demos)
                    agrees=fn(query['input'])==query['output']
                    label='query_discriminates' if fits and not agrees else 'survived_all' if fits else 'refuted'
                    lesson_stats[name][label]+=1
                    record['rivals'][name]=label
                    if fits:
                        summary['failures'].append(['surviving_rival',band,seed,start,name,label])
                lesson_records.append(record)
        witness_counts={name:sum(bool(fn(r['input'])) for r in rows) for name,fn in gen.SEMANTIC_WITNESSES.items()}
        summary['bands'][band]={
            'draws':len(rows),'unique_inputs':len({r['input_sha256'] for r in rows}),
            'strict_passed':sum(not gen.strict_canonical_like(r['input']) for r in rows),
            'independent_oracle_passed':sum(rectangle_oracle(r['input'])==r['output'] for r in rows),
            'lesson_count':len(lesson_records),'witness_counts':witness_counts,
            'layout_counts':dict(Counter(gen.observe_overrides(r['input'])['layout'] for r in rows)),
            'rivals':{n:dict(v) for n,v in lesson_stats.items()},
        }
        (args.out/f'lessons-{band}.json').write_text(json.dumps(lesson_records,separators=(',',':'))+'\n')
    (args.out/'draws.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in all_rows))
    # Confirm the direct sampler agrees with the public episode materializer.
    summary['public_generate_parity']={}
    for band in ('easy','medium','hard'):
        episode=catalog.generate(TASK,count=1,seed=17,difficulty=band,n_train=3,n_test=1,allow_unapproved=True,timeout=180)[0]
        actual=episode['train']+episode['test']
        passed=len(actual)==4 and all(p['input']==gen.generate(17,i,difficulty=band) for i,p in enumerate(actual))
        summary['public_generate_parity'][band]=passed
        if not passed:
            summary['failures'].append(['public_generate_parity',band])
        (args.out/f'public-episode-{band}.json').write_text(json.dumps(episode,separators=(',',':'))+'\n')
    summary['total_generated_draws']=len(all_rows)
    summary['total_unique_generated_inputs']=len({r['input_sha256'] for r in all_rows})
    summary['total_lessons']=sum(b['lesson_count'] for b in summary['bands'].values())
    summary['status']='PASS' if not summary['failures'] else 'FAIL'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash,'source changed during census'
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)
    return bool(summary['failures'])


if __name__=='__main__':
    raise SystemExit(main())
