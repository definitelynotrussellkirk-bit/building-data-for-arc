"""Bounded, source-bound checks using only the live protected Racket runtime.

From the packet root:
  WORK/.venv/bin/python review.py run python3 \
    generators/49fe4f572f8d/workspace/parametric/verify.py \
    --out ../checks/49fe4f572f8d/focused

The full executed episodes and rival programs are private authoring evidence.
This checker neither qualifies nor accepts a native family.
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
TASK_ID = '49fe4f572f8d'
HOME = Path(__file__).resolve().parent
ROOT = find_root(__file__)
MODES = ('down', 'settle_clear_once')
QUERY_SHAPES = [(6, 7), (30, 30), (6, 30), (30, 7)]


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else json_bytes(value)).hexdigest()


def load_adapter():
    path = HOME / 'adapter.py'
    name = '_49fe_focused_' + digest(str(path).encode())
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def require_exact_label(claim, actual, context):
    _grid(claim)
    _grid(actual)
    if claim != actual:
        raise ValueError(f'{context}: claimed label {claim!r} differs from protected Racket {actual!r}')


class ProtectedExecutor:
    """No injected evaluator; cache only completed real executions by exact input."""
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
            self.cache[key] = _grid(self.apply(program, grid))
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


def _single_pass(start='(gravity g "down")', predicate='(>= (obj-size o) 3)',
                 detector='objects', *, finish=True, whole_colors=False):
    cells = ('(flatmap (lambda (o) (find-color settled (obj-color o))) groups)'
             if whole_colors else '(flatmap obj-cells groups)')
    final = '(gravity cleared "down")' if finish else 'cleared'
    return f'''(rule! (lambda (g)
  (let* ((settled {start})
         (groups (filter (lambda (o) {predicate}) ({detector} settled 0)))
         (cleared (erase-cells settled {cells} 0)))
    {final})))'''


def _modified_gravity(name):
    picked = '(reverse values)' if name == 'reverse_column_order' else (
        '(take values (min 3 (length values)))' if name == 'cap_three_cells_per_column'
        else 'values')
    packed = '(append (make-list (- (rows g) (length picked)) 0) picked)'
    result = f'(if (not (= (last column) 0)) column {packed})' if (
        name == 'freeze_bottom_supported_columns') else packed
    return f'''(transpose (map (lambda (column)
      (let* ((values (filter (lambda (v) (not (= v 0))) column))
             (picked {picked})) {result})) (transpose g)))'''


def _repeated_clear(*, sequential=False):
    cells = '(obj-cells (first groups))' if sequential else '(flatmap obj-cells groups)'
    # Every pass removes at least three cells. Area is a conservative finite
    # budget, so the bound cannot stop an otherwise valid cascade prematurely.
    return f'''(rule! (lambda (g)
  (let loop ((state (gravity g "down")) (remaining (* (rows g) (cols g))))
    (let ((groups (filter (lambda (o) (>= (obj-size o) 3)) (objects state 0))))
      (if (or (empty? groups) (= remaining 0)) state
        (loop (gravity (erase-cells state {cells} 0) "down") (- remaining 1)))))))'''


def rival_programs(adapter, mode):
    """Complete executable meanings for the declared finite alternatives."""
    programs = {
        'other_setting': adapter.program({'mode': MODES[mode == 'down']}),
        'identity': '(rule! (lambda (g) g))',
    }
    for name in ('reverse_column_order', 'freeze_bottom_supported_columns',
                 'cap_three_cells_per_column'):
        modified = _modified_gravity(name)
        programs[name] = f'(rule! (lambda (g) {modified}))' if mode == 'down' else (
            _single_pass(modified))
    if mode == 'settle_clear_once':
        programs.update({
            'clear_before_gravity': _single_pass('g'),
            'omit_final_gravity': _single_pass(finish=False),
            'repeat_until_stable': _repeated_clear(),
            'threshold_two': _single_pass(predicate='(>= (obj-size o) 2)'),
            'threshold_four': _single_pass(predicate='(>= (obj-size o) 4)'),
            'exactly_three': _single_pass(predicate='(= (obj-size o) 3)'),
            'eight_connected': _single_pass(detector='objects-8'),
            'clear_whole_colors': _single_pass(whole_colors=True),
            'sequential_clearing': _repeated_clear(sequential=True),
            'vertical_only': _single_pass(predicate='(and (>= (obj-size o) 3) (= (obj-w o) 1))'),
            'horizontal_only': _single_pass(predicate='(and (>= (obj-size o) 3) (= (obj-h o) 1))'),
        })
    return programs


def audit_rivals(episode, programs, execute, python_predictions=None):
    """Fit demos first. Query labels cannot determine the survivor set."""
    rows, survivors = {}, []
    for name, program in sorted(programs.items()):
        outputs = [execute(program, pair['input']) for pair in episode['train']]
        if python_predictions is not None:
            for index, output in enumerate(outputs):
                expected = _grid(python_predictions[index][name])
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
        if not 6 <= len(pair['input']) <= 30 or not 7 <= len(pair['input'][0]) <= 30:
            raise ValueError('An input is outside the declared H6..30/W7..30 grammar')
        if (len(pair['output']), len(pair['output'][0])) != (
                len(pair['input']), len(pair['input'][0])):
            raise ValueError('Gravity rules must preserve grid dimensions')
    hashes = [digest(pair['input']) for pair in pairs]
    if len(set(hashes)) != len(hashes):
        raise ValueError('Repeated demonstration/query input')
    shapes = [(len(p['input']), len(p['input'][0])) for p in episode['test']]
    if shapes[:4] != QUERY_SHAPES[:min(queries, 4)]:
        raise ValueError(f'Four-query size profiles drifted: {shapes!r}')
    dense = None
    if queries >= 2:
        grid = episode['test'][1]['input']
        cells = sum(v != 0 for row in grid for v in row)
        occupied = [any(row[col] for row in grid) for col in range(30)]
        if cells < 300 or not all(occupied) or not any(grid[0]) or not any(grid[-1]):
            raise ValueError('30x30 profile lacks substantive foreground or full-canvas coverage')
        dense = {'shape': [30, 30], 'foreground_cells': cells,
                 'all_columns_occupied': True, 'top_and_bottom_touched': True}
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
                  'Runtime errors abort the report and never count as refutations.',
                  'Writer privacy and negative cases are separate focused tests, not silently claimed here.',
                  'No native qualification, owner acceptance, peer audit, or training admission is granted.']}
    report['source_sha256'] = digest(report['sources'])
    execute = None
    try:
        adapter = load_adapter()
        programs = {mode: adapter.program({'mode': mode}) for mode in MODES}
        canonical = {v['program_solution'] for line in canonical_path(ROOT).open()
                     if (v := json.loads(line)).get('task_id') == TASK_ID}
        if canonical != {programs['down']}:
            raise ValueError('Default is not byte-for-byte identical to the selected canonical authority')
        report['canonical_default_exact'] = True
        rivals = {mode: rival_programs(adapter, mode) for mode in MODES}
        report['programs'] = {mode: {'program': programs[mode],
                                    'sha256': digest(programs[mode].encode()),
                                    'rivals': {name: {'program': program, 'sha256': digest(program.encode())}
                                               for name, program in sorted(rivals[mode].items())}}
                              for mode in MODES}
        count_profiles = [(2, 1), (2, 8), (6, 1), (6, 8)]
        for seed in range(8):
            demos, queries = count_profiles[seed % len(count_profiles)]
            matched = None
            for mode in MODES:
                episode = adapter.generate(seed, {'mode': mode}, demos, queries)
                shape = check_episode_shape(episode, demos, queries)
                if matched is not None and shape['input_sha256'] != matched:
                    raise ValueError(f'Seed {seed}: private setting changed sampled inputs')
                matched = shape['input_sha256']
                teaching = adapter.prototype.teaching_check(episode, mode)
                if teaching['setting_survivors'] != [mode] or teaching['query_changing_survivors']:
                    raise ValueError(f'Seed {seed}/{mode}: Python bounded sampler teaching failure {teaching!r}')
                report['python_sampler'].append({'seed': seed, 'settings': episode['settings'],
                    'demos': demos, 'queries': queries, 'shape_checks': shape,
                    'sampling': episode['sampling'], 'teaching': teaching,
                    'label_status': 'python_claims_only'})
        with ProtectedExecutor(ROOT) as execute:
            report['racket'] = execute.identity
            for seed, demos, queries in ((0, 2, 1), (17, 3, 4)):
                for mode in MODES:
                    episode = adapter.generate(seed, {'mode': mode}, demos, queries)
                    row = {'seed': seed, 'settings': episode['settings'], 'demos': demos, 'queries': queries,
                           'episode': episode, 'shape_checks': check_episode_shape(episode, demos, queries)}
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
                    for i in range(queries):
                        turn = json.loads(adapter.prototype.turn_bytes(episode, i))
                        if (set(turn) != {'train', 'test'} or turn['train'] != episode['train']
                                or turn['test'] != [{'input': episode['test'][i]['input']}]):
                            raise ValueError('Single-query projection leaks metadata or exposes extra queries')
                    row['public_projection'] = {'private_invariant': True, 'single_query_turns': queries,
                                                'public_id': digest(visible)}
                    for requested_demos, requested_queries in ((2, 1), (6, 8)):
                        alternate = adapter.generate(seed, {'mode': mode}, requested_demos, requested_queries)
                        common_demos, common_queries = min(demos, requested_demos), min(queries, requested_queries)
                        if (episode['train'][:common_demos] != alternate['train'][:common_demos]
                                or episode['test'][:common_queries] != alternate['test'][:common_queries]):
                            raise ValueError('Independent requested counts changed an existing input/label prefix')
                    row['public_projection']['independent_count_prefix_exact'] = True
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
