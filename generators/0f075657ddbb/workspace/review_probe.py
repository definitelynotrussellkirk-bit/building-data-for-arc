"""Portable, source-bound Racket differential probe for any per-puzzle generator.

Run from a review packet through run_with_racket.py. It stages an independent
runtime, never labels through a Python mirror, and retains every sampled input,
reference output, failure, and first named-rival counterexample. This is a
correctness/coverage probe, not a model benchmark or admission decision.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def normalize_pairs(value):
    """Normalize the library's list/single-pair and digit-row representations.

    Does not reinterpret invalid shapes or silently drop malformed records.
    """
    if isinstance(value,dict):
        value=[value]
    if not isinstance(value,list):
        raise ValueError('canonical pairs must be a list or one pair object')
    result=copy.deepcopy(value)
    for pair in result:
        if not isinstance(pair,dict) or 'input' not in pair:
            raise ValueError('canonical pair is missing input')
        for key in ('input','output'):
            if key not in pair:
                continue
            grid=pair[key]
            if isinstance(grid,list) and grid and all(isinstance(row,str) for row in grid):
                pair[key]=[[int(color) for color in row] for row in grid]
    return result


def run_worker(request_path: Path) -> int:
    request = json.loads(request_path.read_text())
    sys.path.insert(0, str(Path.cwd()))
    from puzzle_generators import runner
    module = importlib.import_module(request['module'])
    task = request['canonical']
    out = Path(request['out'])
    bridge, fn = runner._open_bridge_with_rule(runner.wrap_rule(task['program_solution']))
    counters, failures, witnesses, bands = Counter(), [], {}, {}
    latencies, seen = [], set()
    rival_functions = getattr(module, 'SEMANTIC_RIVALS', {})
    rival_counts = Counter()
    canonical_rival_fits = Counter()
    canonical_file = out / 'canonical.jsonl'
    samples_file = out / 'samples.jsonl'
    fixtures_file = out / 'fixtures.jsonl'

    def apply(grid):
        snapshot = copy.deepcopy(grid)
        started = time.perf_counter()
        answer = runner._apply_rule(bridge, fn, grid)
        latencies.append(time.perf_counter() - started)
        if grid != snapshot:
            raise AssertionError('Racket application mutated its Python input')
        if not runner.is_well_formed(answer):
            raise AssertionError('Racket output is not a well-formed ARC grid')
        return answer

    def check(name, grid, expected=None):
        result = {'name': name, 'input': grid}
        try:
            before = copy.deepcopy(grid)
            checker = getattr(module, 'self_check', None)
            reasons = checker(grid) if callable(checker) else None
            result['self_check'] = reasons
            if grid != before:
                raise AssertionError('self_check mutated its input')
            if reasons:
                failures.append({'name': name, 'kind': 'self_check', 'reasons': reasons})
            answer = apply(grid)
            result['output'] = answer
            if expected is not None and answer != expected:
                failures.append({'name': name, 'kind': 'canonical_label_mismatch'})
            mirror = getattr(module, 'rule_mirror', None)
            if callable(mirror):
                actual = mirror(grid)
                if actual != answer:
                    failures.append({'name': name, 'kind': 'python_mirror_mismatch'})
                if grid != before:
                    raise AssertionError('rule_mirror mutated its input')
            return result
        except Exception as exc:
            error = {'name': name, 'kind': 'exception', 'error': f'{type(exc).__name__}: {exc}'}
            failures.append(error)
            return {**result, **error}

    try:
        with canonical_file.open('w') as stream:
            for split in ('train', 'test'):
                for index, pair in enumerate(normalize_pairs(task.get(split, []))):
                    name = f'canonical:{split}:{index}'
                    row = check(name, copy.deepcopy(pair['input']), pair.get('output'))
                    counters['canonical_pairs'] += 1
                    for rival, func in rival_functions.items():
                        if func(copy.deepcopy(pair['input'])) == pair.get('output'):
                            canonical_rival_fits[rival] += 1
                    stream.write(json.dumps(row) + '\n')
        with samples_file.open('w') as stream:
            for band in ('easy','medium','hard'):
                stats = Counter()
                for i in range(request['count']):
                    seed = request['seed_start'] + i
                    params = {'seed': seed, 'sample_index': 0, 'difficulty': band}
                    name = f'{band}:{seed}:0'
                    try:
                        raw = module.generate(**params)
                        grid = raw.get('input') if isinstance(raw,dict) else raw
                        again = module.generate(**params)
                        again = again.get('input') if isinstance(again,dict) else again
                        if grid != again:
                            raise AssertionError('repeat generation differs')
                        row = check(name,grid)
                        row['parameters'] = params
                        if 'output' in row:
                            answer = row['output']
                            stats['samples'] += 1
                            stats['identity'] += int(answer == grid)
                            stats['no_top_row_red'] += int(2 not in grid[0])
                            stats[f'shape_{len(grid)}x{len(grid[0])}'] += 1
                            seen.add(digest(json.dumps(grid).encode()))
                            observer = getattr(module,'observe_overrides',None)
                            if callable(observer): row['observed'] = observer(grid)
                            for rival, func in rival_functions.items():
                                alternative = func(copy.deepcopy(grid))
                                if alternative != answer:
                                    rival_counts[rival] += 1
                                    stats['refutes_' + rival] += 1
                                    if rival not in witnesses:
                                        witnesses[rival] = {**row, 'rival':rival,'rival_output':alternative,
                                            'differing_cells':[[r,c,answer[r][c],alternative[r][c]]
                                                for r in range(len(grid)) for c in range(len(grid[0]))
                                                if answer[r][c] != alternative[r][c]]}
                        stream.write(json.dumps(row) + '\n')
                    except Exception as exc:
                        error = {'name':name,'parameters':params,'kind':'generation_exception',
                                 'error':f'{type(exc).__name__}: {exc}'}
                        failures.append(error)
                        stream.write(json.dumps(error) + '\n')
                bands[band] = dict(stats)
        with fixtures_file.open('w') as stream:
            for index, fixture in enumerate(request.get('fixtures',[])):
                name = fixture.get('name',f'fixture:{index}')
                try:
                    if 'input' in fixture:
                        grid = copy.deepcopy(fixture['input'])
                    else:
                        raw = module.generate(**fixture['parameters'])
                        grid = raw.get('input') if isinstance(raw,dict) else raw
                except (ValueError,TypeError) as exc:
                    if fixture.get('expect_rejection'):
                        stream.write(json.dumps({'name':name,'expected_rejection':str(exc)})+'\n')
                        counters['expected_rejections'] += 1
                        continue
                    error={'name':name,'kind':'fixture_generation_exception','error':f'{type(exc).__name__}: {exc}'}
                    failures.append(error)
                    stream.write(json.dumps(error)+'\n')
                    continue
                if fixture.get('expect_rejection'):
                    failures.append({'name':name,'kind':'expected_rejection_not_raised'})
                row = check(name,grid,fixture.get('output'))
                stream.write(json.dumps(row)+'\n')
                counters['fixtures'] += 1
    finally:
        bridge.shutdown()
    ordered = sorted(latencies)
    summary = {'schema':'source-bound-generator-probe-v1', 'task_id':task['task_id'],
               'generator_sha256':request['generator_sha256'],
               'canonical_program_sha256':digest(task['program_solution'].encode()),
               'canonical_ledger_sha256':request['canonical_ledger_sha256'],
               'generator_version':getattr(module,'VERSION',None),
               'sample_count_per_band':request['count'],'seed_start':request['seed_start'],
               'bands':bands,'unique_inputs':len(seen),**dict(counters),
               'racket_calls':len(latencies),'latency_includes_startup':False,
               'latency_p50_seconds':ordered[len(ordered)//2] if ordered else None,
               'latency_p95_seconds':ordered[min(len(ordered)-1,int(len(ordered)*0.95))] if ordered else None,
               'canonical_rival_fits':dict(canonical_rival_fits),
               'sample_rival_disagreements':dict(rival_counts),'failure_count':len(failures),
               'passed':not failures,'scope':'Executed samples only; no safety-label change or model benchmark.'}
    write_json(out/'summary.json',summary)
    write_json(out/'failures.json',failures)
    write_json(out/'rival_witnesses.json',witnesses)
    print(json.dumps({k:v for k,v in summary.items() if k!='bands'},sort_keys=True))
    return int(bool(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path)
    parser.add_argument('--task',default='0f075657ddbb')
    parser.add_argument('--generator',type=Path,help='Optional baseline generator copy to stage, without editing source.')
    parser.add_argument('--out',type=Path)
    parser.add_argument('--count',type=int,default=120,help='Seeds per band, sample_index=0, three bands.')
    parser.add_argument('--seed-start',type=int,default=0)
    parser.add_argument('--fixtures',type=Path,help='JSON list of exact inputs or generator parameters.')
    parser.add_argument('--timeout',type=float,default=300)
    parser.add_argument('--worker',type=Path,help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return run_worker(args.worker)
    if args.out is None or args.count < 1 or args.timeout <= 0:
        parser.error('--out, positive --count and positive --timeout are required')
    root = (args.root or Path(__file__).resolve().parents[3]).resolve()
    out = args.out.resolve()
    if out.exists():
        parser.error(f'output path already exists: {out}')
    sys.path.insert(0,str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    catalog = Catalog(root)
    record = catalog.describe(args.task)
    canonical_path = root/'shared/data/canonical/puzzles.jsonl'
    canonical_rows = [json.loads(line) for line in canonical_path.open()]
    matches = [row for row in canonical_rows if row['task_id'] == record['rule_task_id']]
    if len(matches) != 1:
        raise ValueError('probe requires an unambiguous canonical task row')
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-review-probe-') as temporary:
        stage = Path(temporary)
        prepare_runtime(catalog,stage,record['id'])
        generator = stage/record['runtime_generator']
        if args.generator:
            shutil.copyfile(args.generator.resolve(),generator)
        request = {'out':str(out),'count':args.count,'seed_start':args.seed_start,
                   'module':record['runtime_generator'].replace('/','.')[:-3],
                   'canonical':matches[0], 'generator_sha256':digest(generator.read_bytes()),
                   'canonical_ledger_sha256':digest(canonical_path.read_bytes()),
                   'fixtures':json.loads(args.fixtures.read_text()) if args.fixtures else []}
        request_path = stage/'review_probe_request.json'
        write_json(request_path,request)
        worker = stage/'review_probe_worker.py'
        shutil.copyfile(Path(__file__),worker)
        result = run_process([sys.executable,'-E','-s',str(worker),'--worker',str(request_path)],
                             stage,timeout=args.timeout)
        write_json(out/'process.json',result)
        print(result['stdout'],end='')
        print(result['stderr'],end='',file=sys.stderr)
        if result['timed_out']:
            print('Probe process timed out; retain process.json, not a passing verdict.',file=sys.stderr)
        return 1 if result['timed_out'] else result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
