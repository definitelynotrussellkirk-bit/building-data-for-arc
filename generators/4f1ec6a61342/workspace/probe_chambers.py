#!/usr/bin/env python3
"""Independent chamber contract and declared-rival probe (Python proxy evidence)."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import platform
import re
import sys
import time

TASK = '4f1ec6a61342'
BANDS = ('easy', 'medium', 'hard')
EXPECTED_DOMAINS = {'grid_h': (7, 18), 'grid_w': (9, 20),
                    'n_chambers': (2, 6), 'target_count': (1, 6)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def locate(start):
    for root in (start, *start.parents):
        support = root / 'reviewer_support.py'
        if not support.is_file():
            support = root / 'shared/runtime/reviewer_support.py'
        if support.is_file():
            return root, support
    raise FileNotFoundError('No public reviewer_support.py in the selected tree')


def analyze(grid, pins=None):
    """Flood-fill observed cells only; no generator parsing or labeling helpers."""
    if not isinstance(grid, list) or not grid or any(not isinstance(r, list) or not r for r in grid):
        raise ValueError('empty or malformed grid')
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError('ragged grid')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('noninteger or out-of-palette cell')
    target = grid[0][0]
    errors = []
    if not 1 <= target <= 6:
        errors.append('control must be 1..6')
    for r in range(h):
        for c in range(w):
            if (r, c) == (0, 0):
                continue
            if grid[r][c] not in (0, 2, 5):
                errors.append(f'illegal interior/wall color at {r},{c}')
            if (r in (0, h-1) or c in (0, w-1)) and grid[r][c] != 5:
                errors.append(f'open exterior at {r},{c}')
    remaining = {(r, c) for r in range(h) for c in range(w)
                 if (r, c) != (0, 0) and grid[r][c] in (0, 2)}
    rooms = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        todo, cells = [first], {first}
        while todo:
            r, c = todo.pop()
            for rc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if rc in remaining:
                    remaining.remove(rc)
                    cells.add(rc)
                    todo.append(rc)
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        if len(cells) != (r1-r0+1)*(c1-c0+1):
            errors.append(f'nonrectangular chamber {len(rooms)}')
        rooms.append({'bounds': [r0, c0, r1, c1], 'area': len(cells),
                      'seeds': sum(grid[r][c] == 2 for r, c in cells), 'cells': cells})
    matches = [i for i, room in enumerate(rooms) if room['seeds'] == target]
    if not 2 <= len(rooms) <= 6:
        errors.append(f'chamber count out of domain: {len(rooms)}')
    if len(matches) != 1:
        errors.append(f'exactly one target chamber required; matches={matches}')
    observed = dict(grid_h=h, grid_w=w, n_chambers=len(rooms), target_count=target)
    for name, (lo, hi) in EXPECTED_DOMAINS.items():
        if not lo <= observed[name] <= hi:
            errors.append(f'{name} outside declared domain: {observed[name]}')
        if pins and observed[name] != pins[name]:
            errors.append(f'{name} pin {pins[name]} observed {observed[name]}')
    output = [[5 if value == 5 else 0 for value in row] for row in grid]
    for i in matches:
        for r, c in rooms[i]['cells']:
            output[r][c] = 8
    detail = {'observed': observed, 'target_rooms': matches,
              'rooms': [{k: v for k, v in room.items() if k != 'cells'} for room in rooms]}
    return errors, output, detail


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, help='Library or portable staged runtime root')
    ap.add_argument('--generator', type=Path, help='Selected generator path, default task in --root')
    ap.add_argument('--seeds', type=int, nargs='+', default=[17])
    ap.add_argument('--sample-index', type=int, default=0, help='Pinned Cartesian sample index')
    ap.add_argument('--windows', type=int, default=100, help='Consecutive starts per seed and band')
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--skip-cartesian', action='store_true', help='Small diagnostic runs only')
    ap.add_argument('--capexamples', type=int, default=20, help='Failure examples embedded in JSON')
    ap.add_argument('--failures-jsonl', type=Path, help='Retain every exact failure in a new file')
    ap.add_argument('--out', type=Path, required=True, help='New report path; never overwrites evidence')
    args = ap.parse_args()
    if args.windows < 1 or args.start < 0 or args.sample_index < 0 or args.capexamples < 0:
        ap.error('windows must be positive; starts, sample index and cap must be nonnegative')
    if args.out.exists() or (args.failures_jsonl and args.failures_jsonl.exists()):
        ap.error('output paths must be new')
    if args.failures_jsonl and args.out.resolve() == args.failures_jsonl.resolve():
        ap.error('report and JSONL paths must differ')
    started = time.time()
    root, helper = locate((args.root or Path(__file__).parent).resolve())
    support = load(helper, '_chamber_public_support')
    root = support.find_root(root)
    runtime = helper.parent
    sys.path.insert(0, str(runtime))
    source = args.generator or root / 'generators' / TASK / 'generator.py'
    if not source.is_file() and not args.generator:
        source = root / 'puzzle_generators/per_puzzle' / TASK / 'generator.py'
    source = source.resolve()
    source_hash = sha(source)
    gen = load(source, '_chamber_selected_generator')
    report = {'schema': 'independent-chambers-v1', 'task_id': TASK,
              'evidence_kind': 'direct-generator Python-oracle proxy; not Racket-labelled production materialization',
              'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
              'python': platform.python_version(), 'executable': sys.executable,
              'source': str(source), 'source_sha256': source_hash, 'root': str(root),
              'seeds': args.seeds, 'bands': list(BANDS), 'cartesian_sample_index': args.sample_index,
              'window_starts': list(range(args.start, args.start+args.windows)),
              'lesson_scope': '3train+1query; all four holdout rotations',
              'full_requested_coverage': not args.skip_cartesian and args.windows >= 100,
              'failure_counts': Counter(), 'failure_examples': [], 'canonical': [], 'bands_summary': {}}
    stream = None
    if args.failures_jsonl:
        args.failures_jsonl.parent.mkdir(parents=True, exist_ok=True)
        stream = args.failures_jsonl.open('x', encoding='utf-8')
    def failure(kind, context, **detail):
        event = {'kind': kind, **context, **detail}
        report['failure_counts'][kind] += 1
        if len(report['failure_examples']) < args.capexamples:
            report['failure_examples'].append(event)
        if stream:
            stream.write(json.dumps(event, separators=(',', ':'))+'\n')
    domains = {}
    for name, required in EXPECTED_DOMAINS.items():
        declared = gen.AXES.get(name, {}).get('valid', '')
        match = re.fullmatch(r'(\d+)\.\.(\d+)', declared)
        if not match or tuple(map(int, match.groups())) != required:
            failure('axis_contract', {'axis': name}, declared=declared, expected=list(required))
            domains[name] = range(required[0], required[1]+1)
        else:
            lo, hi = map(int, match.groups())
            domains[name] = range(lo, hi+1)
    report['axis_domains'] = {k: list(v) for k, v in domains.items()}
    rivals = {}
    for attribute in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS'):
        declaration = getattr(gen, attribute, None)
        if not isinstance(declaration, dict) or not declaration:
            failure('rival_declaration', {'attribute': attribute}, error='expected nonempty dict')
            continue
        for name, fn in declaration.items():
            if not isinstance(name, str) or not callable(fn):
                failure('rival_declaration', {'attribute': attribute, 'name': str(name)}, error='invalid entry')
            else:
                rivals[f'{attribute}:{name}'] = fn
    report['declared_rivals'] = sorted(rivals)
    def predictions(grid, output, context, outputs=None):
        exact = {}
        for name, fn in rivals.items():
            try:
                given = deepcopy(grid)
                value = support.normalize_grid(fn(given))
                if outputs is not None:
                    outputs[name] = value
                if given != grid:
                    failure('rival_mutation', context, rival=name, input=grid)
                exact[name] = value == output
            except Exception as exc:
                failure('rival_error', context, rival=name, input=grid, error=repr(exc))
                exact[name] = False
        return exact
    for pair in support.canonical_pairs(TASK, root=root):
        context = {k: pair[k] for k in ('variant', 'split', 'pair_index')}
        errors, output, detail = analyze(pair['input'])
        if errors or output != pair['output']:
            failure('canonical_oracle', context, errors=errors, input=pair['input'], oracle=output, output=pair['output'])
        rival_outputs = {}
        exact = predictions(pair['input'], pair['output'], context, rival_outputs)
        for name, fits in exact.items():
            if name.startswith('CANONICAL_SHORTCUTS:') and not fits:
                failure('canonical_shortcut_refuted', context, rival=name, input=pair['input'],
                        output=pair['output'], rival_output=rival_outputs.get(name))
        report['canonical'].append({**context, **detail, 'rival_exact': exact})
    for band in BANDS:
        stats = {'cartesian_cases': 0, 'window_cases': 0, 'rotations': 0, 'unique_inputs': 0,
                 'rival_status_counts': {n: Counter() for n in rivals}, 'room_seed_counts': Counter()}
        seen = {'cartesian': set(), 'window': set()}
        def generate(seed, index, pins=None, phase='window'):
            context = {'phase': phase, 'band': band, 'seed': seed, 'sample_index': index, 'pins': pins}
            stats[phase+'_cases'] += 1
            try:
                grid = gen.generate(seed, index, difficulty=band, **(pins or {}))
                seen[phase].add(digest(grid))
                errors, output, detail = analyze(grid, pins)
                stats['room_seed_counts'].update(str(room['seeds']) for room in detail['rooms'])
                if errors:
                    failure('grid_contract', context, errors=errors, input=grid, **detail)
                return {'input': grid, 'output': output, 'context': context,
                        'valid': not errors, 'rival_outputs': {}}
            except Exception as exc:
                failure('generation_or_oracle_error', context, error=repr(exc))
                return None
        for seed in args.seeds:
            if not args.skip_cartesian:
                for values in itertools.product(*domains.values()):
                    generate(seed, args.sample_index, dict(zip(domains, values)), 'cartesian')
            pairs = [generate(seed, i) for i in range(args.start, args.start+args.windows+3)]
            matches = [predictions(p['input'], p['output'], p['context'], p['rival_outputs'])
                       if p and p['valid'] else None for p in pairs]
            for offset in range(args.windows):
                window = pairs[offset:offset+4]
                truth = matches[offset:offset+4]
                if any(value is None for value in truth):
                    continue
                for query in range(4):
                    stats['rotations'] += 1
                    for name in rivals:
                        fits = all(truth[i][name] for i in range(4) if i != query)
                        status = 'refuted' if not fits else ('survived_all' if truth[query][name] else 'ambiguous')
                        stats['rival_status_counts'][name][status] += 1
                        if status == 'ambiguous':
                            failure('lesson_ambiguity', {'band': band, 'seed': seed, 'start': args.start+offset,
                                    'query_index': query}, rival=name, pairs=window)
        stats['unique_inputs'] = len(seen['cartesian'] | seen['window'])
        stats['cartesian_unique_inputs'] = len(seen['cartesian'])
        stats['window_unique_inputs'] = len(seen['window'])
        report['bands_summary'][band] = stats
    report['runtime_sha256'] = {str(Path(m.__file__).resolve().relative_to(root)): sha(m.__file__)
        for m in list(sys.modules.values()) if getattr(m, '__file__', None)
        and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(root)}
    report['probe_sha256'] = sha(__file__)
    report['canonical_ledger_sha256'] = sha(support.canonical_path(root))
    if sha(source) != source_hash:
        failure('source_changed_during_run', {}, after_sha256=sha(source))
    report['elapsed_seconds'] = round(time.time()-started, 3)
    report['failure_jsonl'] = str(args.failures_jsonl.resolve()) if stream else None
    report['failure_total'] = sum(report['failure_counts'].values())
    report['status'] = 'FAIL' if report['failure_total'] else 'PASS'
    if stream:
        stream.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'status': report['status'], 'source_sha256': source_hash,
                      'failure_counts': report['failure_counts'], 'bands': report['bands_summary'],
                      'full_requested_coverage': report['full_requested_coverage'], 'out': str(args.out)}))
    return 1 if report['failure_total'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
