"""Bounded, source-bound MAIN checks using only the live protected Racket runtime.

From the packet root:
  WORK/.venv/bin/python review.py run python3 \
    generators/c2cd365ed4fa/workspace/parametric/verify.py \
    --out ../checks/c2cd365ed4fa/focused

The report, programs, and complete executed episodes are private authoring
evidence. This checker neither qualifies nor accepts a native family.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.parametric_worker import _grid, _real_evaluator
from reviewer_support import canonical_path, find_root, public_challenge_bytes

sys.dont_write_bytecode = True
TASK_ID = 'c2cd365ed4fa'
HOME = Path(__file__).resolve().parent
ROOT = find_root(__file__)
MODES = ('fixed', 'count_ascending')
QUERY_SHAPES = [(10, 10), (30, 30), (10, 30), (30, 10)]


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else json_bytes(value)).hexdigest()


def load_adapter():
    path = HOME / 'adapter.py'
    name = '_c2cd_focused_' + digest(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _matrix(value):
    """Rival outputs may exceed 30 rows (for example a pixel histogram)."""
    if (type(value) is not list or not value or type(value[0]) is not list
            or not value[0] or any(type(row) is not list or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value)):
        raise ValueError('Racket must return a rectangular exact-integer color matrix')
    return value


def require_exact_label(claim, actual, context):
    _grid(claim)
    _grid(actual)
    if claim != actual:
        raise ValueError(f'{context}: claimed label {claim!r} differs from protected Racket {actual!r}')


class ProtectedExecutor:
    """No injected evaluator or test backend; cache only completed real executions."""
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.bridge = None
        self.identity = None
        self.executions = 0
        self.cache_hits = 0
        self.cache = {}

    def __enter__(self):
        self.apply, self.identity, self.bridge = _real_evaluator(self.root / 'shared/runtime')
        if self.identity.get('backend') != 'racket' or self.identity.get('protected') is not True:
            self.bridge.close()
            raise ValueError('A live protected Racket runtime is required')
        return self

    def __call__(self, program, grid):
        _grid(grid)
        key = (digest(program.encode()), digest(grid))
        if key not in self.cache:
            self.executions += 1
            self.cache[key] = _matrix(self.apply(program, grid))
        else:
            self.cache_hits += 1
        return deepcopy(self.cache[key])

    def __exit__(self, *_):
        if self.bridge is not None:
            self.bridge.close()


def check_labels(episode, execute):
    rows = []
    for split in ('train', 'test'):
        for index, pair in enumerate(episode[split]):
            actual = execute(episode['program_solution'], pair['input'])
            require_exact_label(pair['output'], actual, f'{split}/{index}')
            rows.append({'split': split, 'index': index,
                         'input_sha256': digest(pair['input']), 'output_sha256': digest(actual)})
    return rows


def rival_programs(adapter, mode):
    """Translate the declared finite rivals into complete executable Racket rules."""
    ordinary_order = 'records' if mode == 'fixed' else '(sort-by records second)'
    specs = {
        'four_connected': ('(third e)', 'records' if mode == 'fixed' else '(sort-by records third)'),
        'pixel_count': ('(fourth e)', 'records' if mode == 'fixed' else '(sort-by records fourth)'),
        'presence': ('(if (> (second e) 0) 1 0)', ordinary_order),
        'descending': ('(second e)', '(sort-by records (lambda (e) (- (second e))))'),
        'drop_absent': ('(second e)', ordinary_order),
        'compact_pad_right': ('(second e)', ordinary_order),
        'top_aligned': ('(second e)', ordinary_order),
    }
    for cap in range(1, 6):
        field = f'(min {cap} (second e))'
        specs[f'count_cap_{cap}'] = (field, 'records' if mode == 'fixed'
                                   else f'(sort-by records (lambda (e) {field}))')
    if mode == 'count_ascending':
        specs.update({
            'tie_numeric': ('(second e)', '(sort-by records (lambda (e) (+ (* 10 (second e)) (first e))))'),
            'tie_reverse': ('(second e)', '(sort-by records (lambda (e) (+ (* 10 (second e)) (- 4 (list-ref e 5)))))'),
            'tie_encounter': ('(second e)', '(sort-by records (lambda (e) (+ (* 1000 (second e)) (list-ref e 4))))'),
            'pixel_order': ('(second e)', '(sort-by records fourth)'),
            'four_connected_order': ('(second e)', '(sort-by records third)'),
        })
    else:
        specs['numeric_columns'] = ('(second e)', '(sort-by records first)')
    programs = {'other_setting': adapter.program({'column_order': MODES[mode == 'fixed']})}
    for name, (field, order) in specs.items():
        if name in ('drop_absent', 'compact_pad_right'):
            order = f'(filter (lambda (e) (> (second e) 0)) {order})'
        width = '(length ordered)' if name == 'drop_absent' else '5'
        row = 'i' if name == 'top_aligned' else '(- (- height 1) i)'
        programs[name] = f'''(rule! (lambda (g)
  (let* ((colors (list 5 2 8 9 6))
         (records (map (lambda (c)
           (let ((masked (cellmap g (r cc v) (if (= v c) c 7)))
                 (positions (find-color g c)))
             (list c (length (objects-8 masked 7)) (length (objects masked 7))
                   (length positions)
                   (if (empty? positions) (* (rows g) (cols g))
                     (+ (* (first (first positions)) (cols g)) (second (first positions))))
                   (- 5 (length (member c colors)))))) colors))
         (ordered {order})
         (height (max-of (lambda (e) {field}) records)))
    (reduce (lambda (out col)
      (let* ((e (list-ref ordered col)) (color (first e)) (n {field}))
        (reduce (lambda (acc i) (set-cell acc {row} col color)) out (range 0 n))))
      (empty-grid height {width} 7) (range 0 (length ordered))))))'''
    return programs


def audit_rivals(episode, programs, execute, python_predictions=None):
    """Fit demos first. Query labels cannot determine the survivor set."""
    rows = {}
    survivors = []
    for name, program in sorted(programs.items()):
        outputs = [execute(program, pair['input']) for pair in episode['train']]
        if python_predictions is not None:
            for index, output in enumerate(outputs):
                expected = _matrix(python_predictions[index][name])
                if output != expected:
                    raise ValueError(f'{name}/train/{index}: Racket rival differs from its declared Python meaning')
        mismatches = [i for i, (pair, output) in enumerate(zip(episode['train'], outputs))
                      if pair['output'] != output]
        row = {'program_sha256': digest(program.encode()), 'demo_mismatches': mismatches,
               'demo_output_sha256': [digest(output) for output in outputs],
               'query_execution': 'not_run_demo_refuted', 'query_mismatches': []}
        if mismatches:
            row['first_refutation'] = {'demo_index': mismatches[0], 'rival_output': outputs[mismatches[0]]}
        else:
            survivors.append(name)
        rows[name] = row
    harmful = []
    for name in survivors:
        outputs = [execute(programs[name], pair['input']) for pair in episode['test']]
        mismatches = [i for i, (pair, output) in enumerate(zip(episode['test'], outputs))
                      if pair['output'] != output]
        rows[name].update(query_execution='executed', query_mismatches=mismatches,
                          query_predictions=outputs)
        if mismatches:
            harmful.append(name)
    return {'passed': not harmful, 'demo_survivors': survivors,
            'query_changing_survivors': harmful, 'rivals': rows,
            'scope': 'Only these finite rivals and sampled demonstrations; no universal uniqueness claim.'}


def check_episode_shape(episode, demos, queries):
    if len(episode['train']) != demos or len(episode['test']) != queries:
        raise ValueError('Requested independent demonstration/query counts were not returned')
    pairs = episode['train'] + episode['test']
    for pair in pairs:
        _grid(pair['input'])
        _grid(pair['output'])
        if not 10 <= len(pair['input']) <= 30 or not 10 <= len(pair['input'][0]) <= 30:
            raise ValueError('An input is outside the declared 10..30 grammar')
    hashes = [digest(pair['input']) for pair in pairs]
    if len(set(hashes)) != len(hashes):
        raise ValueError('Repeated demonstration/query input')
    shapes = [(len(p['input']), len(p['input'][0])) for p in episode['test']]
    if shapes[:4] != QUERY_SHAPES[:min(queries, 4)]:
        raise ValueError(f'Four-query size profiles drifted: {shapes!r}')
    dense = None
    if queries >= 2:
        grid = episode['test'][1]['input']
        cells = sum(v != 7 for row in grid for v in row)
        borders = [grid[0], grid[-1], [r[0] for r in grid], [r[-1] for r in grid]]
        touched = [any(v != 7 for v in edge) for edge in borders]
        if cells < 150 or not all(touched):
            raise ValueError('30x30 profile lacks substantive foreground or four-border coverage')
        dense = {'shape': [30, 30], 'foreground_cells': cells, 'all_four_borders': True}
    return {'input_sha256': hashes, 'query_shapes': shapes, 'dense_query': dense}


def source_rows():
    relative = [f'generators/{TASK_ID}/generator.py',
                f'generators/{TASK_ID}/tests/test_parametric.py',
                f'generators/{TASK_ID}/tests/test_parametric_verifier.py',
                'src/arcpuzzles/parametric_worker.py', 'shared/runtime/reviewer_support.py',
                'shared/runtime/puzzle_generators/rule_wrap.py']
    paths = [ROOT / path for path in relative]
    paths.extend(HOME / name for name in ('adapter.py', 'prototype.py', 'canonical.rkt',
                                         'promotion.json', 'verify.py'))
    paths.append(canonical_path(ROOT))
    return [{'path': str(path.relative_to(ROOT)), 'sha256': digest(path.read_bytes()),
             'bytes': path.stat().st_size} for path in sorted(paths)]


def build_report(destination):
    destination = Path(destination)
    (destination / 'private').mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {'task_id': TASK_ID, 'status': 'failed', 'passed': False,
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
              'sources': source_rows(), 'python_sampler': [], 'executed_episodes': [],
              'limitations': [
                  'Bounded evidence: 16 Python sampler requests and four real-label episodes.',
                  'Rivals are fitted using demonstrations only; refuted rivals are not run on queries.',
                  'Pixel-count rival outputs may exceed 30 rows; runtime errors never count as refutations.',
                  'Writer privacy and negative cases are separate focused tests, not silently claimed here.',
                  'No native qualification, owner acceptance, peer audit, or training admission is granted.']}
    report['source_sha256'] = digest(report['sources'])
    execute = None
    try:
        adapter = load_adapter()
        programs = {mode: adapter.program({'column_order': mode}) for mode in MODES}
        canonical = {v['program_solution'] for line in canonical_path(ROOT).open()
                     if (v := json.loads(line)).get('task_id') == TASK_ID}
        if canonical != {programs['fixed']}:
            raise ValueError('Default is not byte-for-byte identical to the selected canonical authority')
        report['canonical_default_exact'] = True
        rivals = {mode: rival_programs(adapter, mode) for mode in MODES}
        report['programs'] = {mode: {'program': programs[mode],
                                    'sha256': digest(programs[mode].encode()),
                                    'rivals': {name: {'program': program, 'sha256': digest(program.encode())}
                                               for name, program in sorted(rivals[mode].items())}}
                              for mode in MODES}
        samples = {}
        count_profiles = [(2, 1), (2, 8), (6, 1), (6, 8)]
        for seed in range(8):
            demos, queries = count_profiles[seed % len(count_profiles)]
            matched = None
            for mode in MODES:
                episode = adapter.generate(seed, {'column_order': mode}, demos, queries)
                shape = check_episode_shape(episode, demos, queries)
                if matched is not None and shape['input_sha256'] != matched:
                    raise ValueError(f'Seed {seed}: private setting changed sampled inputs')
                matched = shape['input_sha256']
                teaching = adapter.prototype.teaching_check(episode, mode)
                if teaching['setting_survivors'] != [mode] or teaching['query_changing_survivors']:
                    raise ValueError(f'Seed {seed}/{mode}: Python bounded sampler teaching failure {teaching!r}')
                samples[(seed, mode)] = episode
                report['python_sampler'].append({'seed': seed, 'settings': episode['settings'],
                    'demos': demos, 'queries': queries, 'shape_checks': shape,
                    'sampling': episode['sampling'], 'teaching': teaching,
                    'label_status': 'python_claims_only'})
        with ProtectedExecutor(ROOT) as execute:
            report['racket'] = execute.identity
            for seed in (0, 17):
                for mode in MODES:
                    episode = adapter.generate(seed, {'column_order': mode}, 2, 4)
                    row = {'seed': seed, 'settings': episode['settings'], 'demos': 2, 'queries': 4,
                           'episode': episode, 'shape_checks': check_episode_shape(episode, 2, 4)}
                    report['executed_episodes'].append(row)
                    row['labels'] = check_labels(episode, execute)
                    predictions = [adapter.prototype.rival_predictions(p['input'], mode)
                                   for p in episode['train']]
                    if any(set(p) != set(rivals[mode]) for p in predictions):
                        raise ValueError('Declared Python/Racket rival sets differ')
                    row['racket_teaching'] = audit_rivals(episode, rivals[mode], execute, predictions)
                    if not row['racket_teaching']['passed']:
                        raise ValueError(f'Seed {seed}/{mode}: a real Racket rival fits all demos and changes a query')
                    visible = public_challenge_bytes(episode)
                    private_change = deepcopy(episode)
                    private_change.update(seed='private', settings={'private': True}, program_solution='private')
                    for pair in private_change['test']:
                        pair['output'] = [[True]]
                    if (public_challenge_bytes(private_change) != visible
                            or adapter.prototype.public_id(private_change) != digest(visible)):
                        raise ValueError('Private metadata or answer changed public bytes/identifier')
                    for i in range(4):
                        turn = json.loads(adapter.prototype.turn_bytes(episode, i))
                        if (set(turn) != {'train', 'test'} or turn['train'] != episode['train']
                                or turn['test'] != [{'input': episode['test'][i]['input']}]):
                            raise ValueError('Single-query projection leaks metadata or exposes extra queries')
                    row['public_projection'] = {'private_invariant': True, 'single_query_turns': 4,
                                                'public_id': digest(visible)}
                    if seed == 0:
                        one = samples[(seed, mode)]
                        if (one['train'] != episode['train'] or one['test'][0] != episode['test'][0]
                                or adapter.prototype.turn_bytes(one, 0) != adapter.prototype.turn_bytes(episode, 0)):
                            raise ValueError('Single-query evaluation changed the four-query first turn')
                        row['public_projection']['one_vs_four_prefix_exact'] = True
        if source_rows() != report['sources']:
            raise ValueError('Checked source bytes changed during verification; rerun into a fresh directory')
        report.update(status='passed', passed=True, canonical_repair='not_applicable',
                      native_acceptance='not_performed', training_admitted=False)
    except Exception as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        if execute is not None:
            report['real_racket_evaluations'] = execute.executions
            report['cached_real_execution_reuses'] = execute.cache_hits
    path = destination / 'private/report.json'
    path.write_bytes(json_bytes(report) + b'\n')
    return report, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    report, path = build_report(args.out)
    print(json.dumps({'status': report['status'], 'report': str(path),
                      'python_sampler_episodes': len(report['python_sampler']),
                      'executed_episodes': len(report['executed_episodes']),
                      'real_racket_evaluations': report.get('real_racket_evaluations', 0),
                      'elapsed_seconds': report['elapsed_seconds'],
                      'error': report.get('error')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
