"""Reusable bounded demonstration-only protected-Racket shortcut audit.

Run from the repository through review.py. The adjacent adapter, family.rivals,
and promotion contract define the task; no other task's source is imported.
Outputs contain private programs and answers and must not be model prompts.
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def difference(left, right):
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        return {'different': True, 'shape_changed': True}
    cells = [[r, c] for r in range(len(left)) for c in range(len(left[0])) if left[r][c] != right[r][c]]
    return {'different': bool(cells), 'shape_changed': False, 'changed_cells': len(cells), 'positions': cells}


def snapshot(home, root):
    paths = [home / 'generator.py']
    paths += [p for p in (home / 'workspace/parametric').rglob('*')
              if p.suffix in ('.py', '.rkt', '.json') and 'evidence' not in p.parts and 'examples' not in p.parts]
    paths += list((home / 'tests').glob('test_native_*.py'))
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in sorted(paths)}


def run(out, seeds, demos=None, queries=4):
    from arcpuzzles import Catalog
    from arcpuzzles.parametric_worker import _grid, _real_evaluator
    here = Path(__file__).resolve().parent
    home, root = here.parents[1], here.parents[3]
    contract = json.loads((here / 'promotion.json').read_text())
    if demos is None:
        demos = contract.get('qualification_demos', contract['limits']['demos'][0])
    adapter = load(here / 'adapter.py', '_bounded_audit_adapter_' + home.name)
    family = load(here / 'native_family.py', '_bounded_audit_family_' + home.name)
    binding = snapshot(home, root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    apply, identity, bridge = _real_evaluator(root / 'shared/runtime')
    cache, programs = {}, {}
    requests = 0
    def execute(program, grid):
        nonlocal requests
        requests += 1
        ps = sha(program.encode()); gs = sha(raw(grid))
        programs[ps] = program
        key = (ps, gs)
        if key not in cache:
            cache[key] = _grid(apply(program, grid))
        return cache[key]
    settings = [dict(zip(contract['parameters'], values))
                for values in itertools.product(*contract['parameters'].values())]
    result = {'schema': 'arcpuzzles-bounded-private-rival-audit-v1', 'task_id': home.name,
              'source_sha256': binding, 'racket': identity,
              'scope': 'Finite declared settings and authored shortcuts; demonstrations only select rules. '
                       'No universal identifiability or training admission claim.',
              'seeds': seeds, 'demos': demos, 'queries': queries,
              'episodes': [], 'comparisons': [], 'errors': [], 'canonical_pairs': 0}
    try:
        default = adapter.program(contract['default'])
        def canonical_grid(value):
            # Catalog preserves both official string rows and integer matrices.
            # Decode only the former; keep the runtime's strict types otherwise.
            if type(value) is list and all(type(row) is str for row in value):
                value = [[int(cell) for cell in row] for row in value]
            return _grid(value)
        for variant in Catalog(root).get(home.name)['variants']:
            tests = variant.get('test', [])
            if type(tests) is dict:
                tests = [tests]
            for pair in variant.get('train', []) + tests:
                if 'output' in pair:
                    actual = execute(default, canonical_grid(pair['input']))
                    if actual != canonical_grid(pair['output']):
                        raise ValueError('Exact canonical label disagrees with supplied pair')
                    result['canonical_pairs'] += 1
        for setting in settings:
            for seed in seeds:
                episode = adapter.generate(seed, setting, demos, queries)
                program = adapter.program(setting)
                for split in ('train', 'test'):
                    for pair in episode[split]:
                        actual = execute(program, pair['input'])
                        if actual != _grid(pair['output']):
                            raise ValueError('Python claim disagrees with protected label')
                index = len(result['episodes'])
                result['episodes'].append({'seed': seed, 'settings': setting, **episode})
                menu = {'setting:' + json.dumps(s, sort_keys=True): adapter.program(s)
                        for s in settings if s != setting}
                menu.update(family.rivals(setting))
                for name, rival in menu.items():
                    row = {'episode_index': index, 'rival': name, 'program_sha256': sha(rival.encode())}
                    try:
                        for i, pair in enumerate(episode['train']):
                            prediction = execute(rival, pair['input'])
                            delta = difference(pair['output'], prediction)
                            if delta['different']:
                                row.update(status='demo_refuted', demo_index=i,
                                           prediction=prediction, difference=delta)
                                break
                        else:
                            conflicts = []
                            for i, pair in enumerate(episode['test']):
                                prediction = execute(rival, pair['input'])
                                delta = difference(pair['output'], prediction)
                                if delta['different']:
                                    conflicts.append({'query_index': i, 'prediction': prediction, 'difference': delta})
                            row.update(status='query_conflict' if conflicts else 'finite_consistent', query_conflicts=conflicts)
                    except Exception as exc:
                        row.update(status='execution_error', error=str(exc))
                        result['errors'].append({'episode_index': index, 'rival': name, 'error': str(exc)})
                    result['comparisons'].append(row)
    except Exception as exc:
        result['errors'].append({'stage': 'intended_labels', 'error': str(exc)})
    finally:
        bridge.close()
    result['source_unchanged'] = binding == snapshot(home, root)
    counts = {state: sum(c['status'] == state for c in result['comparisons'])
              for state in ('demo_refuted', 'query_conflict', 'finite_consistent', 'execution_error')}
    result['summary'] = {'episodes': len(result['episodes']), 'comparisons': len(result['comparisons']),
                         **counts, 'protected_executions': len(cache), 'requests': requests,
                         'cache_hits': requests - len(cache), 'canonical_pairs': result['canonical_pairs']}
    result['status'] = 'passed' if not result['errors'] and not counts['query_conflict'] and result['source_unchanged'] else 'failed'
    result['programs'] = programs
    (out / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], **result['summary'], 'path': str(out / 'audit.json')}, indent=2))
    return result['status'] == 'passed'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=int, action='append')
    parser.add_argument('--demos', type=int)
    parser.add_argument('--queries', type=int, default=4)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.out, args.seed or [0, 17], args.demos, args.queries) else 1)
