"""Source-bound, Racket-backed complete-lesson review for this task.

Run from the packet root through run_with_racket.py. No private runner imports.
Default: 100 seeds per band, all 3 cyclic starts, 3 demos + 1 query = 900 lessons,
but only 1,800 generated draws (overlapping windows are counted explicitly).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def evaluate_lesson(competitors, demos, query):
    result = {'refuted':[], 'survived_all':[], 'query_discriminates':[], 'errors':[]}
    for name,rival in sorted(competitors.items()):
        try:
            # Evaluate every demo, so a later exception cannot be hidden by all().
            fits = [rival(copy.deepcopy(p['input'])) == p['output'] for p in demos]
            query_matches = rival(copy.deepcopy(query['input'])) == query['output']
        except Exception as exc:
            result['errors'].append({'rival':name,'error':f'{type(exc).__name__}: {exc}'})
            continue
        key = 'refuted' if not all(fits) else 'survived_all' if query_matches else 'query_discriminates'
        result[key].append(name)
    return result


def canonical_pairs(catalog, task_id):
    pairs = []
    for variant in catalog.get(task_id)['variants']:
        for split in ('train','test'):
            items = variant.get(split,[])
            if isinstance(items,dict):
                items = [items]
            for item in items:
                if not isinstance(item,dict) or 'input' not in item or 'output' not in item:
                    continue
                pair = {}
                for field in ('input','output'):
                    pair[field] = [[int(c) for c in row] for row in item[field]]
                pairs.append(pair)
    return pairs


def run(args):
    from arcpuzzles import Catalog  # public API; also keeps unit tests standalone
    out = args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    source = HOME/'generator.py'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    gen = load_module('review_probe_generator',source)
    oracle = load_module('review_probe_oracle',HOME/'workspace/review_oracle.py')
    catalog = Catalog(args.repo_root)
    if catalog.describe(gen.TASK_ID)['generator_sha256'] != source_hash:
        raise RuntimeError('Probe module does not match the selected catalog generator')
    competitors = dict(gen.LESSON_COMPETITORS)
    shortcuts = dict(gen.CANONICAL_SHORTCUTS)
    if not competitors or not shortcuts:
        raise RuntimeError('Refusing an empty-rival success claim')
    canonical = canonical_pairs(catalog,gen.TASK_ID)
    if not canonical:
        raise RuntimeError('No usable canonical pairs; shortcut fit is unverified')
    report = {
        'schema':'routing-complete-lesson-probe-v1','task_id':gen.TASK_ID,
        'generator_sha256':source_hash,'version':gen.VERSION,'rule_hash':gen.RULE_HASH,
        'oracle_sha256':hashlib.sha256((HOME/'workspace/review_oracle.py').read_bytes()).hexdigest(),
        'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'phase':args.phase,'cwd':str(Path.cwd()),'argv':sys.argv,
        'seed_start':args.seed_start,'seeds_per_band':args.seeds,
        'cyclic_starts':[0,1,2],'sample_indexes_per_seed':list(range(6)),
        'sampler':'generate(seed, sample_index, difficulty=band); consecutive 3 demos + 1 query; all cyclic starts',
        'window_pair_appearances_per_band':args.seeds*3*4,
        'counting_note':'Windows overlap. Draw and unique-input counts are not lesson counts.',
        'canonical_pairs':len(canonical),'canonical_shortcut_fits':{},
        'canonical_validator_rejections':[], 'failures':[], 'bands':{},
        'reference_backend':'public Catalog.apply, canonical Racket, batches <=64',
    }
    for name,rival in shortcuts.items():
        matches = [rival(copy.deepcopy(p['input'])) == p['output'] for p in canonical]
        report['canonical_shortcut_fits'][name] = {'passed':sum(matches),'total':len(matches)}
        if not all(matches):
            report['failures'].append({'kind':'false_canonical_shortcut','rival':name})
    for i,pair in enumerate(canonical):
        errors = gen.self_check(pair['input'])
        if errors:
            report['canonical_validator_rejections'].append({'index':i,'errors':errors})
    metadata,grids = [],[p['input'] for p in canonical]
    for band in args.bands:
        for seed in range(args.seed_start,args.seed_start+args.seeds):
            for index in range(6):
                grid = gen.generate(seed,index,difficulty=band)
                errors = gen.self_check(grid)
                conflicts = oracle.path_conflicts(grid)
                if errors or conflicts:
                    report['failures'].append({'kind':'invalid_generated_input','band':band,
                        'seed':seed,'sample_index':index,'errors':errors,'conflicts':conflicts})
                metadata.append({'band':band,'seed':seed,'sample_index':index,'input_sha256':digest(grid)})
                grids.append(grid)
    (out/'draw-plan.json').write_text(json.dumps(metadata,separators=(',',':'))+'\n')
    outputs = []
    try:
        with (out/'racket-receipts.jsonl').open('w') as handle:
            for start in range(0,len(grids),args.batch_size):
                receipt = catalog.apply(gen.TASK_ID,grids[start:start+args.batch_size],reference='canonical',timeout=300)
                if receipt['generator_sha256'] != source_hash or not receipt['rule_hash_matches_catalog']:
                    raise RuntimeError('Source/authority changed while checking')
                handle.write(json.dumps({'start_index':start,'receipt':receipt},separators=(',',':'))+'\n')
                handle.flush()
                for row in receipt['results']:
                    if row['error'] is not None or not row['valid_output']:
                        raise RuntimeError(f'Reference execution failure at {start+row["index"]}: {row}')
                    outputs.append(row['output'])
                print(f'Racket checked {len(outputs)}/{len(grids)} inputs',flush=True)
        if len(outputs) != len(grids):
            raise RuntimeError('Short reference result batch')
        for i,(grid,actual) in enumerate(zip(grids,outputs)):
            predicted = oracle.solve_reference(grid)
            if actual != predicted:
                report['failures'].append({'kind':'python_racket_mismatch','index':i,'predicted':predicted})
            if i < len(canonical) and actual != canonical[i]['output']:
                report['failures'].append({'kind':'canonical_authority_mismatch','index':i})
        report['racket_comparisons'] = len(outputs)
        generated_outputs = outputs[len(canonical):]
        generated_grids = grids[len(canonical):]
        lookup = {(m['band'],m['seed'],m['sample_index']):{'input':g,'output':o}
                  for m,g,o in zip(metadata,generated_grids,generated_outputs)}
        all_lessons = []
        for band in args.bands:
            ids = [i for i,m in enumerate(metadata) if m['band'] == band]
            stats = {'draws':len(ids),'unique_inputs':len({digest(generated_grids[i]) for i in ids}),
                     'strict_hits':sum(not gen.strict_canonical_like(generated_grids[i]) for i in ids),
                     'identity_outputs':sum(generated_grids[i] == generated_outputs[i] for i in ids),
                     'lessons':0,'lesson_competitors':{},'witnesses':{},'witness_implication_failures':0}
            outcomes = {name:Counter() for name in competitors}
            for witness,predicate in gen.SEMANTIC_WITNESSES.items():
                hits = 0
                for i in ids:
                    grid,actual = generated_grids[i],generated_outputs[i]
                    if predicate(copy.deepcopy(grid)):
                        hits += 1
                        for name in gen.WITNESS_RIVALS.get(witness,[]):
                            if gen.SEMANTIC_RIVALS[name](copy.deepcopy(grid)) == actual:
                                stats['witness_implication_failures'] += 1
                                report['failures'].append({'kind':'false_witness','draw':metadata[i],
                                                          'witness':witness,'rival':name})
                stats['witnesses'][witness] = {'hits':hits,'draws':len(ids)}
            for seed in range(args.seed_start,args.seed_start+args.seeds):
                for start in range(3):
                    pairs = [lookup[band,seed,start+j] for j in range(4)]
                    if len({digest(p['input']) for p in pairs}) != 4:
                        report['failures'].append({'kind':'within_lesson_duplicate','band':band,'seed':seed,'start':start})
                    outcome = evaluate_lesson(competitors,pairs[:3],pairs[3])
                    if outcome['errors']:
                        report['failures'].append({'kind':'rival_error','band':band,'seed':seed,'start':start,'errors':outcome['errors']})
                    for state in ('refuted','survived_all','query_discriminates'):
                        for name in outcome[state]:
                            outcomes[name][state] += 1
                    if outcome['survived_all'] or outcome['query_discriminates']:
                        report['failures'].append({'kind':'unrefuted_lesson_rival','band':band,'seed':seed,'start':start,'outcome':outcome})
                    all_lessons.append({'band':band,'seed':seed,'start':start,**outcome})
                    stats['lessons'] += 1
            stats['lesson_competitors'] = {name:{key:count[key] for key in ('refuted','survived_all','query_discriminates')}
                                           for name,count in outcomes.items()}
            report['bands'][band] = stats
        report['total_generated_draws'] = len(metadata)
        report['unique_generated_inputs_all_bands'] = len({digest(g) for g in generated_grids})
        report['total_lessons'] = len(all_lessons)
        report['independent_reference_mismatches'] = sum(f['kind']=='python_racket_mismatch' for f in report['failures'])
        report['status'] = 'pass' if not report['failures'] and not report['canonical_validator_rejections'] else 'fail'
        (out/'lesson-outcomes.json').write_text(json.dumps(all_lessons,separators=(',',':'))+'\n')
    except Exception as exc:
        report['status'] = 'error'
        report['failures'].append({'kind':'probe_error','error':f'{type(exc).__name__}: {exc}'})
    finally:
        report['final_source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        if report['final_source_sha256'] != source_hash:
            report['status'] = 'fail'
            report['failures'].append({'kind':'source_changed_during_probe'})
        (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report.get(key) for key in ('status','racket_comparisons','total_lessons','failures')},indent=2))
    return 0 if report['status'] == 'pass' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--repo-root',type=Path,default=HOME.parents[1])
    parser.add_argument('--seeds',type=int,default=100)
    parser.add_argument('--seed-start',type=int,default=1000)
    parser.add_argument('--bands',nargs='+',choices=('easy','medium','hard'),default=['easy','medium','hard'])
    parser.add_argument('--batch-size',type=int,default=64)
    parser.add_argument('--phase',default='final')
    args = parser.parse_args()
    if args.seeds < 1 or not 1 <= args.batch_size <= 64 or len(set(args.bands)) != len(args.bands):
        parser.error('positive seed count, unique bands, and a batch size in 1..64 are required')
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
