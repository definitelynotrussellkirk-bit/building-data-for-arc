#!/usr/bin/env python3
"""Source-bound, task-independent Racket witness runner for future reviewers.

Run from a source checkout or a relocated runtime. Cases are a JSON list (or
{"cases": [...]}); each case provides either input or seed/sample_index plus
optional difficulty/overrides. Optional expected_output and rival_output are
compared to actual Racket execution. This is a review tool, NOT a solve tool.
Never use it during the masked Python-solve phase.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def source_paths(root: Path, task: str):
    """Resolve explicit source/runtime layouts; never import a sibling tree."""
    root = root.resolve()
    if not task or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in task):
        raise ValueError('unsafe task ID')
    if (root/'shared/runtime').is_dir():
        return (root/'generators'/task/'generator.py',
                root/'shared/data/canonical/puzzles.jsonl', root/'shared/runtime')
    if (root/'puzzle_generators').is_dir():
        return (root/'puzzle_generators/per_puzzle'/task/'generator.py',
                root/'data/canonical/puzzles.jsonl', root)
    raise ValueError(f'not an ARCpuzzles source checkout or runtime: {root}')


def grid_literal(grid):
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int for row in grid for v in row)):
        raise ValueError('expected a nonempty rectangular integer grid')
    # Deliberately allow out-of-range integers to reproduce validator defects.
    return "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'


def load_source(root, task):
    generator, canonical, import_root = source_paths(root, task)
    sys.path.insert(0, str(import_root))
    spec = importlib.util.spec_from_file_location('witness_generator_'+task, generator)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    rows = []
    for line in canonical.open():
        row = json.loads(line)
        if row.get('task_id') == task:
            rows.append(row)
    rules = {row['program_solution'] for row in rows if row.get('program_solution')}
    if len(rules) != 1:
        raise ValueError(f'expected one unambiguous canonical rule, got {len(rules)}')
    rule = rules.pop()
    sha = lambda value: hashlib.sha256(value).hexdigest()
    identity = {
        'task_id': task,
        'generator_sha256': sha(generator.read_bytes()),
        'rule_sha256': sha(rule.encode()),
        'canonical_file_sha256': sha(canonical.read_bytes()),
        'generator_path': str(generator.relative_to(root.resolve())),
        'layout_root': str(root.resolve()),
    }
    return module, rule, rows, identity


def canonical_pairs(row):
    """Canonical history includes bare pair dicts and digit-string grid rows."""
    result = []
    for split in ("train", "test"):
        pairs = row.get(split, [])
        if isinstance(pairs, dict):
            pairs = [pairs]
        for index, pair in enumerate(pairs):
            converted = {}
            for key in ("input", "output"):
                grid = pair[key]
                if isinstance(grid, list) and grid and isinstance(grid[0], str):
                    grid = [[int(v) for v in line] for line in grid]
                grid_literal(grid)
                converted[key] = grid
            result.append((split, index, converted))
    return result


def run_cases(root, task, cases, include_canonical=False):
    root = root.resolve()
    if (root / "shared/runtime").is_dir():
        # Shared helpers still import their historical scripts/ package. Use the
        # official portable layout instead of inventing source-tree import aliases.
        import tempfile
        sys.path.insert(0, str(root / "src"))
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import prepare_runtime
        with tempfile.TemporaryDirectory(prefix="arcpuzzles-reference-probe-") as directory:
            staged = Path(directory)
            prepare_runtime(Catalog(root), staged, task)
            result = run_cases(staged, task, cases, include_canonical)
            result["identity"]["source_checkout"] = str(root)
            return result
    module, rule, rows, identity = load_source(root, task)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    source = wrap_rule(rule)
    cases = list(cases)
    if include_canonical:
        for row_index, row in enumerate(rows):
            for split, i, pair in canonical_pairs(row):
                cases.append({'id': f'canonical-{row_index}-{split}-{i}',
                              'input': pair['input'], 'expected_output': pair['output'],
                              'origin': 'canonical', 'documented_domain': True})
    results = []
    with RacketBridge() as bridge:
        identity['runtime'] = bridge.runtime_identity
        for i, original in enumerate(cases):
            case = dict(original)
            result = {'id': case.get('id', str(i)), 'request': case}
            try:
                grid = case.get('input')
                if grid is None:
                    grid = module.generate(case.get('seed', 0), case.get('sample_index', 0),
                                           difficulty=case.get('difficulty'), **case.get('overrides', {}))
                result['input'] = grid
                try:
                    result['validator_errors'] = module.self_check(grid)
                except Exception as exc:
                    result['validator_error'] = f'{type(exc).__name__}: {exc}'
                result['actual_racket_output'] = bridge.eval_text(f'({source} {grid_literal(grid)})')
                if 'expected_output' in case:
                    result['expected_matches'] = result['actual_racket_output'] == case['expected_output']
                if 'rival_output' in case:
                    result['rival_output'] = case['rival_output']
                    result['rival_disagrees'] = result['actual_racket_output'] != case['rival_output']
            except Exception as exc:
                result['execution_error'] = f'{type(exc).__name__}: {exc}'
            results.append(result)
    failures = [r['id'] for r in results if 'execution_error' in r or r.get('expected_matches') is False]
    return {'schema': 'arcpuzzles-reference-witness-v1', 'identity': identity,
            'case_count': len(results), 'failures': failures, 'cases': results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--task', required=True)
    p.add_argument('--cases', type=Path)
    p.add_argument('--canonical', action='store_true')
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        p.error('output already exists; retain old evidence and choose a new path')
    raw = json.loads(args.cases.read_text()) if args.cases else []
    cases = raw['cases'] if isinstance(raw, dict) else raw
    if not isinstance(cases, list) or any(not isinstance(c, dict) for c in cases):
        p.error('cases must be a list of objects')
    if not cases and not args.canonical:
        p.error('provide at least one case or --canonical')
    report = run_cases(args.root, args.task, cases, args.canonical)
    report['command'] = {'cwd': str(Path.cwd()), 'argv': [sys.executable] + sys.argv}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'cases': report['case_count'], 'failures': report['failures'], 'out': str(args.out)}))
    return int(bool(report['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
