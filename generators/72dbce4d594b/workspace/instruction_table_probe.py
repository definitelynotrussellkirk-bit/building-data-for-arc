"""Finite instruction-table identifiability probe; Python standard library only.

The generic ``factorized_gate`` works with a routing key and named predictors.
The CLI adapter supplies the component/rank/D4 hypotheses for this task. Labels
for sampled grids are the task's Python mirror; validate them independently with
Racket before treating this as reference-backed training evidence.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Callable, Mapping

Grid = list[list[int]]
Predictor = Callable[[Grid], Grid]


def freeze(grid):
    return tuple(tuple(row) for row in grid)


def factorized_gate(demos, queries, *, key: Callable, predictors: Mapping[str, Predictor]):
    """Intersect candidates per instruction, then check query-output consensus.

    Ambiguous *rules* are allowed when every survivor predicts the same answer.
    No reference query labels are used. Exceptions are reported, never silently
    discarded; zero compatible hypotheses is an explicit model-class failure.
    """
    buckets = {}
    errors = []
    for index, demo in enumerate(demos):
        control = key(demo['input'])
        remaining = buckets.setdefault(control, set(predictors))
        for name in tuple(remaining):
            try:
                prediction = predictors[name](demo['input'])
            except Exception as exc:
                errors.append({'demo': index, 'candidate': name, 'error': repr(exc)})
                remaining.remove(name)
                continue
            if prediction != demo['output']:
                remaining.remove(name)
    results = []
    for index, query in enumerate(queries):
        grid = query['input']
        control = key(grid)
        survivors = sorted(buckets.get(control, set(predictors)))
        groups = {}
        for name in survivors:
            try:
                out = predictors[name](grid)
                frozen = freeze(out)
            except Exception as exc:
                errors.append({'query': index, 'candidate': name, 'error': repr(exc)})
                continue
            groups.setdefault(frozen, []).append(name)
        results.append({'query': index, 'control': control, 'survivors': survivors,
                        'distinct_predictions': len(groups),
                        'prediction_classes': list(groups.values()),
                        'identifiable': bool(survivors) and len(groups) == 1})
    inconsistent = [str(k) for k,v in buckets.items() if not v]
    return {'passed': not errors and not inconsistent and bool(results) and all(r['identifiable'] for r in results),
            'inconsistent_controls': inconsistent,
            'queries': results, 'errors': errors,
            'candidate_sets': {str(k): sorted(v) for k, v in buckets.items()}}


def connected_blue(grid):
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 1}
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        stack = [first]
        component = []
        while stack:
            r,c = stack.pop()
            component.append((r,c))
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining:
                    remaining.remove(p)
                    stack.append(p)
        groups.append(component)
    return sorted(groups, key=len)


MATRICES = {
    'identity': (1,0,0,1), 'rot90': (0,1,-1,0),
    'rot180': (-1,0,0,-1), 'rot270': (0,-1,1,0),
    'flip_lr': (1,0,0,-1), 'flip_ud': (-1,0,0,1),
    'transpose': (0,1,1,0), 'anti_transpose': (0,-1,-1,0),
}


def predict(grid, matrix):
    rank = sum(v == 2 for row in grid for v in row)
    shapes = connected_blue(grid)
    if len(shapes) != 3 or not 1 <= rank <= 3:
        raise ValueError('expected three blue components and rank 1..3')
    a,b,c,d = matrix
    points = [(a*r+b*col,c*r+d*col) for r,col in shapes[rank-1]]
    min_r, min_c = min(r for r,col in points), min(col for r,col in points)
    targets = [(r,col) for r,row in enumerate(grid) for col,v in enumerate(row) if v == 8]
    if len(targets) != 1:
        raise ValueError('expected one cyan target')
    tr,tc = targets[0]
    result = [[0]*len(grid[0]) for _ in grid]
    for r,col in points:
        rr,cc = tr+r-min_r,tc+col-min_c
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            result[rr][cc] = 7
    return result


def instruction(grid):
    return sum(v == 3 for row in grid for v in row)


def analyze(demos, queries):
    predictors = {name: (lambda grid, m=matrix: predict(grid,m)) for name,matrix in MATRICES.items()}
    return factorized_gate(demos, queries, key=instruction, predictors=predictors)


def load_generator(path, support_root=None):
    if support_root:
        sys.path.insert(0,str(Path(support_root).resolve()))
    spec = importlib.util.spec_from_file_location('probe_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--generator', type=Path)
    parser.add_argument('--support-root', type=Path)
    parser.add_argument('--seeds', type=int, default=64)
    parser.add_argument('--starts', type=int, default=12)
    parser.add_argument('--bands', default='easy,medium,hard')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.case:
        case = json.loads(args.case.read_text())
        report = analyze(case['demos'], [case['query']])
        report['case_sha256'] = hashlib.sha256(args.case.read_bytes()).hexdigest()
    else:
        if not args.generator or args.seeds < 1 or args.starts < 1:
            parser.error('supply --case or --generator with positive --seeds and --starts')
        gen = load_generator(args.generator,args.support_root)
        count = failures = generated = 0
        first_failures = []
        profile_counts = Counter()
        cross = Counter()
        start_time = time.perf_counter()
        n = gen.EXAMPLES_NEEDED
        for band in args.bands.split(','):
            for seed in range(args.seeds):
                grids = [gen.generate(seed,i,difficulty=band) for i in range(args.starts+n)]
                pairs = [{'input':g,'output':gen.rule_mirror(g)} for g in grids]
                generated += len(grids)
                for i,g in enumerate(grids):
                    profile_counts[gen.schedule_profile(seed,i,band)] += 1
                    cross[f"{sum(v==2 for row in g for v in row)}:{instruction(g)}"] += 1
                for start in range(args.starts):
                    row = analyze(pairs[start:start+n], [pairs[start+n]])
                    count += 1
                    if not row['passed']:
                        failures += 1
                        if len(first_failures) < 12:
                            first_failures.append({'seed':seed,'start':start,'difficulty':band,**row})
        report = {'schema':'instruction-table-probe-v1', 'task_id':gen.TASK_ID,
                  'generator_sha256':hashlib.sha256(args.generator.read_bytes()).hexdigest(),
                  'labels':'Python rule_mirror; separate Racket parity is required',
                  'n_demos':n,'seeds':args.seeds,'starts':args.starts,'bands':args.bands.split(','),
                  'grids':generated,'lessons':count,'ambiguous_or_invalid_lessons':failures,
                  'passed':failures==0,'first_failures':first_failures,
                  'profile_counts':dict(profile_counts),'rank_transform_counts':dict(cross),
                  'elapsed_seconds':time.perf_counter()-start_time}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('first_failures','candidate_sets','queries')},sort_keys=True))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
