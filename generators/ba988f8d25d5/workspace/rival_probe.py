#!/usr/bin/env python3
"""Source-bound, reusable rival audit with real canonical Racket outputs.

Run from any working directory. Example from the packet root:
  python3 repo/generators/ba988f8d25d5/workspace/rival_probe.py \
      --per-band 200 --out checks/focused/rivals-after.json

Any per-puzzle generator exposing SEMANTIC_RIVALS can be selected with --task-id.
--generator-file and --rivals-file support comparisons to a frozen baseline.
The tool prepares an independent disposable runtime and never edits the library.
JSON retains exact first counterexamples; an adjacent HTML file visualizes them.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def score_rivals(grid, expected, rivals):
    """Compare outputs without confusing exceptions with refuting examples."""
    scores = {}
    for name, rival in sorted(rivals.items()):
        try:
            output = rival(copy.deepcopy(grid))
            scores[name] = {"status": "agrees" if output == expected else "disagrees", "output": output}
        except Exception as exc:
            scores[name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return scores


def _grid_html(grid):
    colors = ('#111111', '#0074D9', '#FF4136', '#2ECC40', '#FFDC00', '#AAAAAA', '#F012BE', '#FF851B', '#7FDBFF', '#870C25')
    if not isinstance(grid, list) or not grid:
        return '<pre>' + html.escape(repr(grid)) + '</pre>'
    rows = []
    for row in grid:
        cells = []
        for value in row:
            color = colors[value] if type(value) is int and 0 <= value < 10 else '#555555'
            cells.append(f'<td style="background:{color}" title="{html.escape(str(value))}">{html.escape(str(value))}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    return '<table class="grid">' + ''.join(rows) + '</table>'


def render_html(report):
    escape = lambda value: html.escape(str(value))
    rows = []
    for band, data in report.get('bands', {}).items():
        for name, count in data.get('rivals', {}).items():
            rows.append('<tr>' + ''.join(f'<td>{escape(v)}</td>' for v in
                (band, name, count.get('disagrees', 0), count.get('agrees', 0), count.get('error', 0))) + '</tr>')
    examples = []
    for name, case in report.get('first_counterexamples', {}).items():
        examples.append(f'<section><h2>{escape(name)}</h2><p>seed={escape(case["seed"])}; '
                        f'index={escape(case["sample_index"])}; band={escape(case["difficulty"])}</p>'
                        '<div class="example">' + ''.join(
                            f'<div><h3>{title}</h3>{_grid_html(case[key])}</div>'
                            for title, key in [('Input', 'input'), ('Canonical Racket', 'output'), ('Rival', 'rival_output')])
                        + '</div></section>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Rival audit</title>'
            '<style>body{font:16px system-ui;max-width:1120px;margin:40px auto;padding:0 24px;background:#f5f6f8;color:#16212b}'
            'h1{font-size:32px}.summary td,.summary th{padding:8px 15px;border-bottom:1px solid #ccd0d5;text-align:left}'
            '.summary{border-collapse:collapse}section{background:white;border-radius:12px;padding:20px;margin:24px 0}'
            '.example{display:flex;gap:36px;flex-wrap:wrap}.grid{border-collapse:collapse}.grid td{width:22px;height:22px;'
            'border:1px solid #666;font:10px monospace;text-align:center;color:white;text-shadow:0 1px 2px black}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e9edf2;padding:14px}</style>'
            f'<h1>Rival audit: {escape(report["task_id"])}</h1>'
            '<p>Disagreements are measured against the actual canonical Racket program, not a Python label surrogate. '
            'Zero disagreements is evidence only about this sampled cohort.</p>'
            '<table class="summary"><tr><th>Band</th><th>Rival</th><th>Refuted</th><th>Agrees</th><th>Errors</th></tr>'
            + ''.join(rows) + '</table>' + ''.join(examples)
            + '<h2>Source identity and limitations</h2><pre>'
            + escape(json.dumps({k: report.get(k) for k in ('source', 'canonical', 'errors')}, indent=2))
            + '</pre></html>')


def _load_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _worker(args):
    sys.path.insert(0, str(Path(args.worker_runtime).resolve()))
    from puzzle_generators.runner import _load_generator_module
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
    from scripts.generator_semantic_gate import _RuleOracle
    gen = _load_file(args.generator_file, 'probe_generator') if args.generator_file else _load_generator_module(args.task_id)
    provider = _load_file(args.rivals_file, 'probe_rivals') if args.rivals_file else gen
    rivals = getattr(provider, 'SEMANTIC_RIVALS', {})
    if not rivals:
        raise ValueError('No SEMANTIC_RIVALS found; provide --rivals-file with a callable mapping')
    source = canonical_rule_source(args.task_id)
    report = {
        'schema': 'arcpuzzles-rival-probe-v1', 'task_id': args.task_id,
        'source': {'generator_sha256': _digest(gen.__file__), 'generator_version': getattr(gen, 'VERSION', None),
                   'rivals_sha256': _digest(provider.__file__), 'rule_hash': normalized_rule_hash(source),
                   'rule_sha256': hashlib.sha256(source.encode()).hexdigest(),
                   'seed': args.seed, 'start_index': args.start_index, 'per_band': args.per_band,
                   'labels': 'canonical Racket via existing _RuleOracle; no Python label substitution'},
        'canonical': {}, 'bands': {}, 'first_counterexamples': {}, 'errors': [],
    }
    oracle = _RuleOracle(args.task_id)
    try:
        if not oracle.ready:
            raise RuntimeError(oracle.error)
        pairs = canonical_pairs(args.task_id)
        fits = Counter()
        for i, pair in enumerate(pairs):
            output, error = oracle.apply(pair['input'])
            if error or output != pair['output']:
                report['errors'].append({'canonical_index': i, 'error': error or 'canonical output mismatch'})
            check = getattr(gen, 'self_check', lambda grid: [])(copy.deepcopy(pair['input']))
            if check:
                report['errors'].append({'canonical_index': i, 'self_check': check})
            for name, result in score_rivals(pair['input'], pair['output'], rivals).items():
                fits[name] += int(result['status'] == 'agrees')
                if result['status'] == 'error':
                    report['errors'].append({'canonical_index': i, 'rival': name, 'error': result['error']})
        report['canonical'] = {'pairs': len(pairs), 'rival_matches': dict(fits),
                               'rivals_fitting_all': sorted(name for name in rivals if pairs and fits[name] == len(pairs))}
        for band in ('easy', 'medium', 'hard'):
            counts = {name: Counter() for name in rivals}
            inputs, outputs, sizes = set(), set(), Counter()
            successes = 0
            for index in range(args.start_index, args.start_index + args.per_band):
                replay = {'seed': args.seed, 'sample_index': index, 'difficulty': band}
                try:
                    grid = gen.generate(args.seed, index, difficulty=band)
                    before = copy.deepcopy(grid)
                    rejection = getattr(gen, 'self_check', lambda grid: [])(grid)
                    if rejection:
                        raise ValueError('self_check: ' + repr(rejection))
                    output, error = oracle.apply(grid)
                    if error:
                        raise RuntimeError(error)
                    mirror = getattr(gen, 'rule_mirror', None)
                    if callable(mirror) and mirror(grid) != output:
                        raise AssertionError('diagnostic mirror disagrees with actual Racket output')
                    results = score_rivals(grid, output, rivals)
                    if grid != before:
                        raise AssertionError('self_check, oracle or mirror mutated input')
                    for name, result in results.items():
                        counts[name][result['status']] += 1
                        if result['status'] == 'error':
                            report['errors'].append({**replay, 'rival': name, 'error': result['error']})
                        elif result['status'] == 'disagrees' and name not in report['first_counterexamples']:
                            report['first_counterexamples'][name] = {**replay, 'input': grid,
                                'output': output, 'rival_output': result['output']}
                    inputs.add(json.dumps(grid))
                    outputs.add(json.dumps(output))
                    observer = getattr(gen, 'observe_overrides', None)
                    if callable(observer):
                        values = observer(grid)
                        if 'small_size' in values:
                            sizes[values['small_size']] += 1
                    successes += 1
                except Exception as exc:
                    report['errors'].append({**replay, 'error': f'{type(exc).__name__}: {exc}'})
            report['bands'][band] = {'requested': args.per_band, 'checked': successes,
                'unique_inputs': len(inputs), 'unique_outputs': len(outputs), 'target_sizes': dict(sizes),
                'rivals': {name: {status: count[status] for status in ('agrees', 'disagrees', 'error')} for name, count in counts.items()}}
    finally:
        oracle.close()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    out.with_suffix('.html').write_text(render_html(report))
    print(json.dumps({'out': str(out), 'errors': len(report['errors']), 'bands': report['bands']}, indent=2))
    return 1 if report['errors'] else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id', default='ba988f8d25d5')
    parser.add_argument('--per-band', type=int, default=200)
    parser.add_argument('--seed', type=int, default=20260928)
    parser.add_argument('--start-index', type=int, default=0)
    parser.add_argument('--generator-file', type=Path)
    parser.add_argument('--rivals-file', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker-runtime', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.per_band < 1 or args.start_index < 0:
        parser.error('--per-band must be positive and --start-index nonnegative')
    if args.worker_runtime:
        return _worker(args)
    root = next((p for p in Path(__file__).resolve().parents if (p/'src/arcpuzzles').is_dir() and (p/'catalog/runtime_files.json').is_file()), None)
    if root is None:
        raise RuntimeError('Place this tool anywhere inside an ARCpuzzles repository')
    args.out = args.out.resolve()
    if args.out.exists() or args.out.with_suffix('.html').exists():
        raise FileExistsError('Evidence paths must be new; preserve the earlier run')
    sys.path.insert(0, str(root/'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    env = dict(os.environ)
    local_racket = root.parent/'.review/racket-runtime/racket/bin/racket'
    if not env.get('RACKET_PATH') and local_racket.is_file():
        env['RACKET_PATH'] = str(local_racket)
    if env.get('RACKET_PATH'):
        env['PATH'] = str(Path(env['RACKET_PATH']).resolve().parent) + os.pathsep + env.get('PATH', '')
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-rival-probe-') as temporary:
        prepare_runtime(Catalog(root), Path(temporary), args.task_id)
        command = [sys.executable, str(Path(__file__).resolve()), '--worker-runtime', temporary,
                   '--task-id', args.task_id, '--seed', str(args.seed), '--start-index', str(args.start_index),
                   '--per-band', str(args.per_band), '--out', str(args.out)]
        for flag, path in (('--generator-file', args.generator_file), ('--rivals-file', args.rivals_file)):
            if path:
                command.extend([flag, str(path.resolve())])
        result = subprocess.run(command, cwd=temporary, env=env, timeout=max(180, args.per_band * 3))
        return result.returncode


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f'rival probe failed: {exc}', file=sys.stderr)
        raise SystemExit(2)
