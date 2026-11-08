"""Source-bound, independent crop-selection audit for f9099d7c7e31.

Run through the packet's run_with_racket.py wrapper. --self-tests stages an
ordinary standalone runtime and all task-local tests, including newly added
files absent from the inherited runtime map. No approval or source is edited.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import html
import importlib.util
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

TASK_ID = 'f9099d7c7e31'
RIVALS = ('largest_by_area', 'winner_pixels_only', 'smallest_of_widest',
          'leftmost_object', 'largest_bbox_area', 'widest_then_tallest',
          'widest_then_shortest', 'border_only')
BANDS = ('easy', 'medium', 'hard')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def components(grid):
    """Independent same-color FOUR-connected components, not imported from gen."""
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(r, list) or len(r) != len(grid[0]) for r in grid)
            or any(type(c) is not int or not 0 <= c <= 9 for r in grid for c in r)):
        raise ValueError('expected a nonempty rectangular integer ARC grid')
    h, w, seen, result = len(grid), len(grid[0]), set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            todo, cells = [(r, c)], set()
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                cells.add((y, x))
                for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                    if (0 <= yy < h and 0 <= xx < w and (yy, xx) not in seen
                            and grid[yy][xx] == color):
                        seen.add((yy, xx))
                        todo.append((yy, xx))
            r0, r1 = min(y for y, _ in cells), max(y for y, _ in cells)
            c0, c1 = min(x for _, x in cells), max(x for _, x in cells)
            result.append(dict(color=color, cells=cells, size=len(cells),
                               height=r1-r0+1, width=c1-c0+1, bbox=(r0, c0, r1, c1)))
    return result


def crop(grid, obj):
    r0, c0, r1, c1 = obj['bbox']
    return [row[c0:c1+1] for row in grid[r0:r1+1]]


def predictions(grid):
    obs = components(grid)
    if not obs:
        return {name: [] for name in ('width_then_size', *RIVALS)}
    chosen = max(obs, key=lambda o: (o['width'], o['size']))
    widest = [o for o in obs if o['width'] == chosen['width']]
    border = [o for o in obs if o['bbox'][0] == 0 or o['bbox'][1] == 0
              or o['bbox'][2] == len(grid)-1 or o['bbox'][3] == len(grid[0])-1]
    r0, c0, r1, c1 = chosen['bbox']
    return {
        'width_then_size': crop(grid, chosen),
        'largest_by_area': crop(grid, max(obs, key=lambda o: (o['size'], o['width']))),
        'winner_pixels_only': [[grid[r][c] if (r, c) in chosen['cells'] else 0
                               for c in range(c0, c1+1)] for r in range(r0, r1+1)],
        'smallest_of_widest': crop(grid, min(widest, key=lambda o: o['size'])),
        'leftmost_object': crop(grid, min(obs, key=lambda o: (o['bbox'][1], o['bbox'][0]))),
        'largest_bbox_area': crop(grid, max(obs, key=lambda o:
                                           (o['height']*o['width'], o['width'], o['size']))),
        'widest_then_tallest': crop(grid, max(obs, key=lambda o:
                                             (o['width'], o['height'], o['size']))),
        'widest_then_shortest': crop(grid, max(obs, key=lambda o:
                                              (o['width'], -o['height'], o['size']))),
        'border_only': crop(grid, max(border, key=lambda o: (o['width'], o['size']))) if border else [],
    }


def summarize(rows):
    counts = Counter({name: 0 for name in RIVALS})
    witnesses, groups, errors, mismatch = {}, defaultdict(dict), [], 0
    n_default = 0
    for n, row in enumerate(rows):
        if row.get('errors'):
            errors.append({'row': n, 'errors': row['errors']})
        if 'input' not in row or 'output' not in row:
            errors.append({'row': n, 'errors': ['missing input or reference output']})
            continue
        pred = predictions(row['input'])
        mismatch += pred['width_then_size'] != row['output']
        if row['kind'] != 'default':
            continue
        n_default += 1
        wrong = {name for name in RIVALS if pred[name] != row['output']}
        for name in wrong:
            counts[name] += 1
            witnesses.setdefault(name, {'row': n, 'input': row['input'], 'output': row['output'],
                                         'rival_output': pred[name], 'seed': row['seed'],
                                         'sample_index': row['sample_index'], 'difficulty': row['difficulty']})
        groups[(row['seed'], row['difficulty'])][row['sample_index']] = wrong
    window_failures, missing_phases, windows = [], [], 0
    for (seed, band), samples in groups.items():
        for start in range(4):
            if any(i not in samples for i in range(start, start+5)):
                missing_phases.append({'seed': seed, 'difficulty': band, 'start': start})
                continue
            windows += 1
            refuted = set().union(*(samples[i] for i in range(start, start+4)))
            survivors = sorted(set(RIVALS) - refuted)
            if survivors:
                window_failures.append({'seed': seed, 'difficulty': band, 'start': start,
                                        'survivors': survivors,
                                        'query_disagreements': sorted(set(survivors) & samples[start+4])})
    missing = [name for name in RIVALS if not counts[name]]
    return {'passed': bool(n_default and windows and not (errors or mismatch or missing
                                                          or window_failures or missing_phases)),
            'rows': len(rows), 'default_rows': n_default, 'mirror_mismatches': mismatch,
            'errors': errors, 'default_disagreements': dict(counts),
            'missing_default_counterexamples': missing, 'windows_checked': windows,
            'window_failures': window_failures, 'missing_window_phases': missing_phases,
            'first_counterexamples': witnesses}


def write_gallery(path, report):
    # Offline table cells, not embedded scripts or external assets.
    colors = ('#000000', '#0074d9', '#ff4136', '#2ecc40', '#ffdc00',
              '#aaaaaa', '#f012be', '#ff851b', '#7fdbff', '#870c25')
    def table(grid):
        return '<table>' + ''.join('<tr>' + ''.join(
            f'<td style="background:{colors[c]}" title="{c}">{c}</td>' for c in row
        ) + '</tr>' for row in grid) + '</table>' if grid else '<p>No output</p>'
    content = ['<!doctype html><meta charset="utf-8"><title>Crop-selection counterexamples</title>',
               '<style>body{font:16px system-ui;margin:2rem;max-width:1200px}',
               'table{border-collapse:collapse}td{width:24px;height:24px;border:1px solid #666;',
               'text-align:center;font-size:11px;color:white;text-shadow:0 0 3px black}',
               'article{border-top:1px solid #aaa;margin:2rem 0}.grids{display:flex;gap:2rem;flex-wrap:wrap}</style>',
               '<h1>Independent, Racket-labeled counterexamples</h1>',
               '<p>These are review evidence, not fresh-solve query labels.</p>']
    for name, witness in report['first_counterexamples'].items():
        content += [f'<article><h2>{html.escape(name)}</h2><p>Seed {witness["seed"]}; '
                    f'index {witness["sample_index"]}; {html.escape(witness["difficulty"])}</p><div class="grids">']
        for title, key in [('Input', 'input'), ('Racket output', 'output'), ('Wrong rule', 'rival_output')]:
            content.append(f'<section><h3>{title}</h3>{table(witness[key])}</section>')
        content.append('</div></article>')
    path.write_text(''.join(content), encoding='utf-8')


def load_generator(path):
    spec = importlib.util.spec_from_file_location('reviewed_generator', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_tests(repo, out):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    home = repo / 'generators' / TASK_ID
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-task-tests-') as tmp:
        stage = Path(tmp)
        prepare_runtime(Catalog(repo), stage, TASK_ID)
        for part in ('tests', 'workspace'):
            src = home / part
            dst = stage / 'tests' if part == 'tests' else stage / 'puzzle_generators/per_puzzle' / TASK_ID / part
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
        command = [sys.executable, '-m', 'pytest', '-q'] + [f'tests/{p.name}' for p in sorted((home/'tests').glob('test_*.py'))]
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        run = subprocess.run(command, cwd=stage, env=env, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=180)
        (out/'tests.log').write_text(run.stdout)
        report = {'passed': run.returncode == 0, 'exit_code': run.returncode, 'command': command,
                  'generator_sha256': sha256(home/'generator.py'),
                  'task_files': {str(p.relative_to(home)): sha256(p) for part in ('tests', 'workspace')
                                 for p in sorted((home/part).rglob('*.py')) if '__pycache__' not in p.parts}}
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(run.stdout, end='')
        return run.returncode


def run_audit(args, repo, out):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    source = (args.source or repo/'generators'/TASK_ID/'generator.py').resolve()
    gen = load_generator(source)
    canonical = repo/'shared/data/canonical/puzzles.jsonl'
    records = [json.loads(line) for line in canonical.open(encoding='utf-8')]
    authorities = [r for r in records if r.get('task_id') == TASK_ID]
    if len(authorities) != 1:
        raise ValueError(f'expected one canonical authority, found {len(authorities)}')
    rule = authorities[0]['program_solution']
    wrapped = wrap_rule(rule)
    rows, defaults = [], []
    started = time.perf_counter()
    with RacketBridge(timeout=10, max_calls_before_restart=256) as bridge:
        identity = bridge.runtime_identity
        def reference(grid):
            components(grid)  # Do not serialize unchecked values into executable text.
            literal = "'(" + ' '.join('('+' '.join(map(str, row))+')' for row in grid) + ')'
            return bridge.eval_text(f'({wrapped} {literal})')

        def record(grid, **meta):
            errors = list(meta.pop('errors', []))
            try:
                output = reference(grid)
                errors.extend(gen.self_check(copy.deepcopy(grid)))
                if predictions(grid)['width_then_size'] != output:
                    errors.append('independent width/count mirror differs from Racket')
            except Exception as exc:
                output = None
                errors.append(f'{type(exc).__name__}: {exc}')
            row = dict(meta, input=grid, output=output, errors=errors)
            rows.append(row)
            return row

        for split in ('train', 'test'):
            for i, pair in enumerate(authorities[0].get(split, [])):
                row = record(pair['input'], kind='canonical', split=split, sample_index=i)
                if row['output'] != pair['output']:
                    row['errors'].append('canonical recorded label differs from execution')
        for band in BANDS:
            for seed in range(args.seeds):
                for i in range(args.samples):
                    meta = dict(kind='default', difficulty=band, seed=seed, sample_index=i)
                    try:
                        grid = gen.generate(seed, i, difficulty=band)
                        errors = [] if grid == gen.generate(seed, i, difficulty=band) else ['nondeterministic grid']
                        row = record(grid, **meta, errors=errors)
                        row['strict_canonical_like'] = not bool(gen.strict_canonical_like(grid))
                        defaults.append(row)
                    except Exception as exc:
                        rows.append(dict(meta, errors=[f'{type(exc).__name__}: {exc}']))
        if args.matrix:
            keys = ('grid_h', 'grid_w', 'n_objects', 'target_width', 'target_height',
                    'selection_mode', 'intruder_in_crop', 'larger_narrow_decoy')
            domains = (range(9,12), range(9,12), (3,4), (4,5), (2,3),
                       ('unique_width','width_tie_size'), (False,True), (False,True))
            for band in BANDS:
                for values in itertools.product(*domains):
                    kw = dict(zip(keys, values))
                    meta = dict(kind='override', difficulty=band, seed=9917, sample_index=2, overrides=kw)
                    try:
                        grid = gen.generate(9917, 2, difficulty=band, **kw)
                        errors = [] if gen.observe_overrides(grid) == kw else ['exact override mismatch']
                        record(grid, **meta, errors=errors)
                    except Exception as exc:
                        rows.append(dict(meta, errors=[f'{type(exc).__name__}: {exc}']))
        if args.metamorphic:
            transforms = {
                'flip_lr': lambda g: [list(reversed(row)) for row in g],
                'flip_ud': lambda g: [list(row) for row in reversed(g)],
                'nonzero_palette_cycle': lambda g: [[0 if c == 0 else c % 9 + 1 for c in row] for row in g],
            }
            for row in [r for r in defaults if r['seed'] == 0 and r['sample_index'] < 4]:
                for name, fn in transforms.items():
                    transformed = record(fn(row['input']), kind='metamorphic', transform=name,
                                         difficulty=row['difficulty'], seed=0, sample_index=row['sample_index'])
                    if transformed['output'] != fn(row['output']):
                        transformed['errors'].append('reflection/palette covariance failed')
    with (out/'pairs.jsonl').open('w') as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(',', ':'))+'\n')
    report = summarize(rows)
    report.update(schema='arcpuzzles-independent-selection-probe-v1', task_id=TASK_ID,
                  generator_sha256=sha256(source), generator_version=gen.VERSION,
                  generator_source=str(source), canonical_ledger_sha256=sha256(canonical),
                  rule_sha256=hashlib.sha256(rule.encode()).hexdigest(), tool_sha256=sha256(__file__),
                  pairs_sha256=sha256(out/'pairs.jsonl'), racket=identity,
                  case_counts=dict(Counter(r['kind'] for r in rows)),
                  strict_default_fraction=sum(r['strict_canonical_like'] for r in defaults)/max(1,len(defaults)),
                  elapsed_seconds=time.perf_counter()-started,
                  limits=['finite rival bank; not an exhaustive proof against all shortcuts',
                          'override Cartesian domains exhaustive; seeds are sampled',
                          'no fresh-solve private labels or approval changes'])
    if report['strict_default_fraction'] < gen.MIN_STRICT_FRAC:
        report['passed'] = False
        report['errors'].append({'errors': ['strict canonical-like fraction below declared floor']})
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    write_gallery(out/'counterexamples.html', report)
    print(json.dumps({k: v for k, v in report.items() if k not in {'first_counterexamples', 'window_failures', 'racket'}}, indent=2))
    return 0 if report['passed'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--source', type=Path, help='optional frozen baseline generator.py')
    parser.add_argument('--out', type=Path, required=True, help='must not already exist')
    parser.add_argument('--seeds', type=int, default=8)
    parser.add_argument('--samples', type=int, default=8)
    parser.add_argument('--matrix', action='store_true', help='1728 exact-control cases, each Racket-verified')
    parser.add_argument('--metamorphic', action='store_true')
    parser.add_argument('--self-tests', action='store_true')
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.samples < 8:
        parser.error('--seeds must be positive and --samples >= 8 to cover all four lesson phases')
    repo, out = args.repo.resolve(), args.out.resolve()
    if out.exists():
        parser.error('output exists; use a fresh directory to preserve evidence')
    if not (repo/'src/arcpuzzles').is_dir() or not (repo/'shared/runtime').is_dir():
        parser.error('--repo must identify the ARCpuzzles source repository')
    out.mkdir(parents=True)
    sys.path[:0] = [str(repo/'src'), str(repo/'shared/runtime')]
    try:
        if args.self_tests:
            return run_tests(repo, out)
        # RacketBridge also imports sibling `scripts` modules and prelude assets.
        # The raw shared/runtime/ directory is NOT a complete executable tree.
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import prepare_runtime
        with tempfile.TemporaryDirectory(prefix='arcpuzzles-independent-audit-') as tmp:
            stage = Path(tmp)
            receipt = prepare_runtime(Catalog(repo), stage, TASK_ID)
            (out/'runtime_manifest.json').write_text(json.dumps(receipt, indent=2)+'\n')
            sys.path.insert(0, str(stage))
            try:
                return run_audit(args, repo, out)
            finally:
                sys.path.remove(str(stage))
    except Exception as exc:
        (out/'failure.json').write_text(json.dumps({'passed': False, 'error': f'{type(exc).__name__}: {exc}'}, indent=2)+'\n')
        (out/'traceback.log').write_text(traceback.format_exc())
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
