"""Findings-only audit reproducers; edits neither random audit target."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys

# Isolated Python (-I) intentionally omits the script directory. Import only
# the sibling helper copied into this private runtime, never the source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_worker import HERE, bridge_for, canonical_checks, grid_hash, sha


def frame_components(grid):
    seen = set()
    components = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 5 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            for x, y in todo:
                for a, b in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                    if (0 <= a < len(grid) and 0 <= b < len(grid[0])
                            and grid[a][b] == 5 and (a,b) not in seen):
                        todo.append((a,b)); seen.add((a,b))
            r1, r2 = min(x for x,y in todo), max(x for x,y in todo)
            c1, c2 = min(y for x,y in todo), max(y for x,y in todo)
            complete = (r2-r1 >= 2 and c2-c1 >= 2
                        and all(grid[x][y] == 5 for x in (r1,r2) for y in range(c1,c2+1))
                        and all(grid[x][y] == 5 for y in (c1,c2) for x in range(r1,r2+1)))
            components.append({'bbox': [r1,c1,r2,c2], 'complete_border': complete,
                               'cell_count': len(todo)})
    return components


def fill_bbox_rival(grid):
    """Incorrectly treats every gray component's bounding box as a full frame."""
    out = deepcopy(grid)
    for item in frame_components(grid):
        r1,c1,r2,c2 = item['bbox']
        values = {grid[r][c] for r in range(r1+1,r2) for c in range(c1+1,c2)
                  if grid[r][c] not in (0,5)}
        if len(values) == 1:
            value = next(iter(values))
            for r in range(r1+1,r2):
                for c in range(c1+1,c2):
                    out[r][c] = value
    return out


def rightmost_only(grid):
    """Incorrectly extends only the rightmost eligible domino of each row."""
    out = deepcopy(grid)
    for r,row in enumerate(grid):
        ends = [(c+2,row[c]) for c in range(len(row)-2)
                if row[c] != 0 and row[c] == row[c+1] and row[c+2] == 0
                and (c == 0 or row[c-1] != row[c])]
        if ends:
            c,value = max(ends)
            out[r][c] = value
    return out


def source_fields(task, module, bundle):
    return {'task_id': task, 'generator_sha256': sha(module.__file__),
            'rule_sha256': hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
            'runtime_directory': str(HERE)}


def audit_frames(request):
    task = '79fa065ed7aa'
    module = importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
    runner,bundle,bridge,name,canonical = bridge_for(task)
    identity = source_fields(task,module,bundle)
    try:
        canonical_result = canonical_checks(runner,bundle,bridge,name,canonical,
                                             {'gray_component_bbox':fill_bbox_rival})
        if canonical_result['failures']:
            raise AssertionError(canonical_result['failures'])
        samples, deficits, unique = [], [], set()
        overrides = {'grid_h':9, 'grid_w':12, 'n_frames':2}
        for index in range(90):
            grid = module.generate(request['seed'],index,difficulty='medium',**overrides)
            observed = len(frame_components(grid))
            actual = runner._apply_rule(bridge,name,grid)
            predicted = fill_bbox_rival(deepcopy(grid))
            unique.add(grid_hash(grid))
            row = {'seed':request['seed'],'sample_index':index,'difficulty':'medium',
                   'overrides':overrides, 'requested_frames':2,'observed_frames':observed,
                   'self_check_errors':module.self_check(grid), 'input_sha256':grid_hash(grid),
                   'bbox_rival_matches':predicted == actual}
            samples.append(row)
            if observed != 2:
                deficits.append({**identity, **row, 'input':grid, 'actual_racket_output':actual,
                                 'rival_output':predicted, 'rival_relation':'label-equivalent here; defect is requested count loss',
                                 'in_documented_generator_domain':True,
                                 'satisfies_requested_override':False})
        broken = deepcopy(canonical[0]['input'])
        broken[1][2] = 0
        actual = runner._apply_rule(bridge,name,broken)
        predicted = fill_bbox_rival(deepcopy(broken))
        if actual == predicted or module.self_check(broken):
            raise AssertionError('broken-frame validator counterexample no longer reproduces')
        boundary = {'difficulty':'easy','overrides':{'n_frames':3}}
        try:
            module.generate(request['seed'],0,**boundary['overrides'],difficulty='easy')
            boundary['outcome'] = 'accepted'
        except ValueError as exc:
            boundary['outcome'] = 'rejected'
            boundary['error'] = str(exc)
        return {**identity, 'classification':'reproduced exact-count loss and validator false acceptance',
                'canonical':canonical_result, 'sampling':{'seed':request['seed'], 'sample_index_range_inclusive':[0,89],
                'difficulty':'medium','overrides':overrides,'draws':90,'unique_inputs':len(unique)},
                'deficit_count':len(deficits),'all_deficits':deficits,'sample_records':samples,
                'boundary_control':boundary,
                'broken_border_counterexample':{**identity,'construction':'canonical train[0], remove gray at [1][2]',
                    'input':broken,'actual_racket_output':actual,'rival_output':predicted,
                    'self_check_errors':module.self_check(broken),'in_documented_generator_domain':False,
                    'domain_note':'Intentionally malformed frame; exposes validator weakness, not a required training branch.'}}
    finally:
        bridge.close()


def audit_dominoes(request):
    task = 'd1e7fb6c23d0'
    module = importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
    runner,bundle,bridge,name,canonical = bridge_for(task)
    identity = source_fields(task,module,bundle)
    try:
        canonical_result = canonical_checks(runner,bundle,bridge,name,canonical,
                                             {'rightmost_domino_only':rightmost_only})
        if canonical_result['failures']:
            raise AssertionError(canonical_result['failures'])
        stats,unique,records = Counter(),set(),[]
        for index in range(90):
            band = ('easy','medium','hard')[index % 3]
            grid = module.generate(request['seed'],index,difficulty=band)
            actual = runner._apply_rule(bridge,name,grid)
            predicted = rightmost_only(deepcopy(grid))
            stats['draws'] += 1; stats['rival_matches'] += actual == predicted
            stats['self_check_passes'] += not bool(module.self_check(grid))
            unique.add(grid_hash(grid))
            records.append({'seed':request['seed'],'sample_index':index,'difficulty':band,
                            'input_sha256':grid_hash(grid),'rival_matches':actual == predicted,
                            'self_check_errors':module.self_check(grid)})
        grid = deepcopy(canonical[0]['input'])
        grid[1][4] = grid[1][5] = 6
        actual = runner._apply_rule(bridge,name,grid)
        predicted = rightmost_only(deepcopy(grid))
        if actual == predicted or module.self_check(grid):
            raise AssertionError('two-domino same-row counterexample no longer reproduces')
        return {**identity,'classification':'reproduced support gap / canonical-perfect shortcut',
                'canonical':canonical_result, 'sampling':{'seed':request['seed'],
                  'sample_index_range_inclusive':[0,89], 'bands':'easy/medium/hard cyclic; 30 draws each',
                  **dict(stats),'unique_inputs':len(unique)}, 'sample_records':records,
                'counterexample':{**identity,'construction':'canonical train[0], set row 1 columns 4 and 5 to 6',
                  'input':grid,'actual_racket_output':actual,'rival_output':predicted,
                  'self_check_errors':module.self_check(grid),
                  'in_documented_semantic_domain':True,'in_current_generator_support':False,
                  'domain_note':'Two separate eligible dominoes in one row; current generator emits at most one per row. '
                                'The validator accepts and the canonical rule extends both. Scope is a distribution gap, not wrong generated labels.'}}
    finally:
        bridge.close()


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    expected = {'79fa065ed7aa','d1e7fb6c23d0'}
    if set(request['audit_targets']) != expected:
        raise ValueError('This findings-only probe is bound to the unchanged drawn audit targets.')
    results = {'79fa065ed7aa':audit_frames(request),'d1e7fb6c23d0':audit_dominoes(request)}
    report = {'schema':'arcpuzzles-findings-only-audit-v1','status':'completed_with_findings',
              'passed':True,'passed_means':'Reproducers executed successfully, NOT generator approval or a clean audit.',
              'worker_sha256':sha(__file__), 'shared_worker_sha256':sha(HERE/'probe_worker.py'),
              'runtime_directory':str(HERE),'targets':results}
    Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'targets':sorted(results),'report':sys.argv[2]}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
