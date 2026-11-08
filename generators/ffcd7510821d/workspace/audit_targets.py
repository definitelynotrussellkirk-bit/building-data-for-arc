#!/usr/bin/env python3
"""Replay the unchanged packet's two audit targets against canonical Racket.

No audit target is edited. Retains all generated pairs, every discovered lesson
failure, source hashes and an independently executable counterexample.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
TARGETS = ('32a376372541', '033db13a9d37')


def copy_left(grid):
    output = [row[:] for row in grid]
    width = len(grid[0])
    for r,row in enumerate(grid):
        for c in range(width//2):
            if row[c]:
                output[r][width-1-c] = row[c]
    return output


def parity_pattern(grid, *, last=False):
    cells = [(r,c,value) for r,row in enumerate(grid) for c,value in enumerate(row) if value]
    if not cells:
        raise ValueError('the parity rule requires a seed')
    sr,sc,value = cells[-1] if last else cells[0]
    return [[value if (r,c)==(sr+1,sc) else 4 if r<=sr and c%2==sc%2 else 0
             for c in range(len(grid[0]))] for r in range(len(grid))]


def _load(path):
    spec = importlib.util.spec_from_file_location('audit_'+path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--per-band', type=int, default=100)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 4:
        parser.error('--per-band must be at least four')
    if args.out.exists():
        parser.error('refusing to overwrite retained evidence')
    args.out.mkdir(parents=True)
    contract = json.loads((REPO.parent/'AUDIT_ASSIGNMENT.json').read_text())
    expected = {target['task_id']:target['generator_sha256'] for target in contract['targets']}
    if set(expected) != set(TARGETS):
        raise ValueError('this replay belongs to a different audit assignment')
    sys.path.insert(0,str(REPO/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-audit-replay-') as temp:
        runtime = Path(temp)
        manifest = prepare_runtime(Catalog(REPO), runtime, task_ids=list(TARGETS))
        (args.out/'runtime-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        sys.path.insert(0,str(runtime))
        from puzzle_generators.runner import _open_bridge_with_rule, _apply_rule, wrap_rule
        canonical = {row['task_id']:row for row in map(json.loads,(REPO/'shared/data/canonical/puzzles.jsonl').open())
                     if row.get('task_id') in TARGETS}
        report = {'schema':'assigned-adversarial-audit-v1','seed':args.seed,
                  'sample_index_range':[0,args.per_band-1], 'bands':['easy','medium','hard'],
                  'runtime_directory':str(runtime), 'targets':{}}
        command = {'cwd':'packet_root','argv':['python3','run_with_racket.py','python3',
                   'generators/ffcd7510821d/workspace/audit_targets.py','--seed',str(args.seed),
                   '--per-band',str(args.per_band),'--out','../checks/'+args.out.name]}
        for task in TARGETS:
            path = REPO/'generators'/task/'generator.py'
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected[task]:
                raise ValueError(f'audit target drift: {task}')
            module = _load(path)
            rule = canonical[task]['program_solution']
            identity = {'task_id':task,'generator_sha256':digest,
                        'rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
                        'rule_hash':hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12]}
            target = {**identity,'counts':{},'by_band':{},'counterexample':None,'override_findings':[]}
            bridge,function = _open_bridge_with_rule(wrap_rule(rule))
            sample_path = args.out/(task+'-samples.jsonl')
            failure_path = args.out/(task+'-lesson-failures.jsonl')
            unique = set()
            counters = Counter()
            try:
                with sample_path.open('w') as samples_out, failure_path.open('w') as failures:
                    for band in report['bands']:
                        records = []
                        band_counts = Counter()
                        for index in range(args.per_band):
                            grid = module.generate(args.seed,index,difficulty=band)
                            output = _apply_rule(bridge,function,grid)
                            mirror = copy_left(grid) if task==TARGETS[0] else parity_pattern(grid)
                            errors = module.self_check(grid,difficulty=band)
                            input_sha = hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()
                            unique.add(input_sha)
                            record = {'seed':args.seed,'sample_index':index,'difficulty':band,'overrides':{},
                                      'input':grid,'actual_racket_output':output,'validator_errors':errors,
                                      'input_sha256':input_sha}
                            samples_out.write(json.dumps(record,separators=(',',':'))+'\n')
                            records.append({'input':grid,'output':output})
                            band_counts['generated'] += 1
                            band_counts['python_racket_mismatches'] += mirror != output
                            band_counts['validator_rejections'] += bool(errors)
                            if task==TARGETS[1]:
                                band_counts['decoy_inputs'] += sum(bool(v) for row in grid for v in row)>1
                        n_demos = module.EXAMPLES_NEEDED
                        for start in range(args.per_band-n_demos):
                            demos,query = records[start:start+n_demos],records[start+n_demos]
                            band_counts['lesson_windows'] += 1
                            if task==TARGETS[0]:
                                errors = module.lesson_identifiable(demos,query)
                                bad = bool(errors)
                                rival_name, rival_output = 'declared_competitors', None
                            else:
                                bad = (all(parity_pattern(d['input'],last=True)==d['output'] for d in demos)
                                       and parity_pattern(query['input'],last=True)!=query['output'])
                                errors = ['last-nonzero rival fits every demo and changes the query answer'] if bad else []
                                rival_name, rival_output = 'last_nonzero_seed', parity_pattern(query['input'],last=True)
                            band_counts['ambiguous_or_rejected_lessons'] += bad
                            if bad:
                                failure = {**identity,'seed':args.seed,'sample_index':start+n_demos,'difficulty':band,
                                           'overrides':{},'demo_start_index':start,'demos':demos,
                                           'input':query['input'],'actual_racket_output':query['output'],
                                           'rival_name':rival_name,'rival_output':rival_output,
                                           'validator_errors':module.self_check(query['input']),
                                           'in_documented_generator_domain':True,'reasons':errors,'command':command}
                                failures.write(json.dumps(failure,separators=(',',':'))+'\n')
                                if target['counterexample'] is None:
                                    name = task+'-counterexample.json'
                                    (args.out/name).write_text(json.dumps(failure,indent=2)+'\n')
                                    target['counterexample'] = name
                        target['by_band'][band] = dict(band_counts)
                        counters.update(band_counts)
                    # Audit's original canonical pairs, not the later fresh solve.
                    original_pairs = list(canonical[task].get('train',[]))
                    test = canonical[task].get('test',[])
                    original_pairs += test if isinstance(test,list) else [test]
                    for pair in original_pairs:
                        output = _apply_rule(bridge,function,pair['input'])
                        counters['canonical_pairs'] += 1
                        counters['canonical_mismatches'] += output != pair['output']
                        counters['canonical_validator_rejections'] += bool(module.self_check(pair['input']))
                if task==TARGETS[1]:
                    # Boundary honesty: record, do not repair audit-only source.
                    for overrides in ({'seed_row':-10},{'seed_col':999},{'unknown_option':7}):
                        grid = module.generate(args.seed,0,difficulty='medium',**overrides)
                        seed_cell = next((r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v)
                        target['override_findings'].append({'seed':args.seed,'sample_index':0,'difficulty':'medium',
                            'overrides':overrides,'returned_seed_cell':seed_cell,'input':grid,
                            'actual_racket_output':_apply_rule(bridge,function,grid),
                            'validator_errors':module.self_check(grid),
                            'classification':'out-of-domain override silently accepted or clamped'})
            finally:
                bridge.shutdown()
            target['counts'] = {**dict(counters),'unique_generated_inputs':len(unique)}
            target['evidence_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in (sample_path,failure_path)}
            report['targets'][task] = target
        (args.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    # Successful replay can contain findings; semantic verdict is in the report.
    return 0


if __name__=='__main__':
    raise SystemExit(main())
