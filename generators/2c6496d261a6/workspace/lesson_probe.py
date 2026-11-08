#!/usr/bin/env python3
"""Source-bound, Racket-labelled finite-rival lesson probe for 2c6496d261a6.

From packet/: python3 run_with_racket.py python3 \
    generators/2c6496d261a6/workspace/lesson_probe.py \
    --lessons-per-band 100 --out ../checks/lesson-probe.json
Optional --generator PATH samples an alternate task generator (e.g. the packet's
preserved baseline); competitor/witness/strict definitions remain those of the
current selected generator and both sources are hashed. Paths resolve from the
wrapper's repo working directory. The source snapshot lives in a disposable
TemporaryDirectory, never in checks. JSON contains complete lesson provenance.

Next-agent limits: this is a finite declared-rival diagnostic, not unrestricted
identifiability or a draw audit. Three demos and two queries are fixed. Only the
selected canonical row is inspected; no solve artifacts or private labels are
consulted. Labels come from real Racket. Sampling uses existing runner.run_one
with a persistent bridge and therefore depends on the recorded runner version;
its internal bundle/bridge API may require adapting after runtime upgrades.
Canonical counterexample verification uses public arcpuzzles.runtime.apply_rule.
The repaired ordinary sampler uses 3..9 total colors and 2..5 keepers; exact
controls also permit 2 total colors or 1 keeper. This unoverridden probe does
not claim exhaustive coverage of those exact-control cases. Every declared
CANONICAL_SHORTCUTS entry is checked against all usable canonical train/test
pairs and receives its first actually sampled Racket-labelled disagreement.
passed/probe_completed indicate measurement execution only;
all_lessons_identifiable separately records the finite-rival semantic result.
Any generation, oracle, self-check, malformed contract, silent runner rejection,
or policy mismatch writes a failed receipt and exits nonzero. Nonzero rival
survival is reported faithfully rather than suppressed or turned into a failure.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

TASK_ID = '2c6496d261a6'
BANDS = (('default', None), ('easy', 'easy'), ('medium', 'medium'), ('hard', 'hard'))
COUNTEREXAMPLE = [[2,2,0,4,0,0,0], [0,0,2,0,0,0,0], [0,0,0,0,0,5,5],
                  [0,0,0,6,0,0,0], [0,6,0,0,0,0,0]]


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load generator: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def passes(result: Any, label: str) -> bool:
    if type(result) is bool:
        return result
    if isinstance(result, (list, tuple)):
        return not result
    raise TypeError(f'{label} must return bool or a list/tuple of errors, got {type(result).__name__}')


def canonical_row(repo: Path) -> dict:
    matches = []
    with (repo / 'shared/data/canonical/puzzles.jsonl').open() as handle:
        for line in handle:
            if f'"task_id": "{TASK_ID}"' in line or f'"task_id":"{TASK_ID}"' in line:
                row = json.loads(line)
                if row.get('task_id') == TASK_ID:
                    matches.append(row)
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one selected canonical row, got {len(matches)}')
    return matches[0]


def facts(grid):
    colors = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                colors[v].append((r, c))
    keepers = sum(len({r for r, _ in cells}) == 1 for cells in colors.values())
    return {'height': len(grid), 'width': len(grid[0]), 'nonzero_colors': len(colors),
            'keeper_colors': keepers, 'erased_colors': len(colors)-keepers,
            'nonzero_cells': sum(map(len, colors.values()))}


class TracedSampler:
    def __init__(self, module):
        self.module = module
        self.attempts = []

    def __getattr__(self, name):
        return getattr(self.module, name)

    def generate(self, *args, **kwargs):
        trace = {'seed': kwargs.get('seed'), 'sample_index': kwargs.get('sample_index'),
                 'difficulty': kwargs.get('difficulty')}
        self.attempts.append(trace)
        try:
            grid = self.module.generate(*args, **kwargs)
            trace['input_sha256'] = digest(grid)
            return grid
        except Exception as exc:
            trace['error'] = f'{type(exc).__name__}: {exc}'
            raise


def probe(args, report):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import apply_rule, prepare_runtime, validate_grid
    repo = Path(__file__).resolve().parents[3]
    selected = repo / f'generators/{TASK_ID}/generator.py'
    alternate = args.generator.resolve() if args.generator else selected
    canonical = canonical_row(repo)
    canonical_pairs = [pair for split in ('train', 'test') for pair in canonical.get(split, [])
                       if isinstance(pair, dict) and 'input' in pair and 'output' in pair]
    if not canonical_pairs:
        raise RuntimeError('No usable selected canonical pairs')
    for pair in canonical_pairs:
        validate_grid(pair['input']); validate_grid(pair['output'])
    rule = canonical['program_solution']
    rule_hash = digest_bytes(' '.join(rule.split()).encode())[:12]
    catalog = Catalog(repo)
    report['source'] = {'task_id': TASK_ID, 'canonical_rule_hash': rule_hash,
                        'canonical_row_sha256': digest(canonical),
                        'probe_sha256': digest_bytes(Path(__file__).read_bytes()),
                        'evaluator_generator_path': str(selected),
                        'evaluator_generator_sha256': digest_bytes(selected.read_bytes()),
                        'sampling_generator_path': str(alternate),
                        'sampling_generator_sha256': digest_bytes(alternate.read_bytes())}
    applied = apply_rule(catalog, TASK_ID, [COUNTEREXAMPLE], reference='canonical',
                         allow_unapproved=True, timeout=120)
    result = applied['results'][0]
    if not result['valid_output'] or result['error'] or applied['executed_rule_hash'] != rule_hash:
        raise RuntimeError('Public Racket counterexample application failed or executed a different authority')
    with tempfile.TemporaryDirectory(prefix='row-filter-lesson-probe-') as directory:
        stage = Path(directory)
        manifest = prepare_runtime(catalog, stage, TASK_ID)
        report['source']['runtime_manifest_sha256'] = digest(manifest)
        row = catalog.describe(TASK_ID)
        staged_generator = stage / row['runtime_generator']
        if digest_bytes(staged_generator.read_bytes()) != report['source']['evaluator_generator_sha256']:
            raise RuntimeError('Selected generator changed during snapshot preparation')
        sys.path.insert(0, str(stage))
        # No puzzle_generators imports precede this snapshot import.
        from puzzle_generators import runner
        if not Path(runner.__file__).resolve().is_relative_to(stage):
            raise RuntimeError('Runner imported outside the pinned portable runtime')
        evaluator = load_module(staged_generator, 'lesson_probe_evaluator')
        if args.generator:
            staged_alternate = stage / 'lesson_probe_sampling_generator.py'
            staged_alternate.write_bytes(alternate.read_bytes())
            if digest_bytes(staged_alternate.read_bytes()) != report['source']['sampling_generator_sha256']:
                raise RuntimeError('Alternate generator changed during snapshot preparation')
            sampler = load_module(staged_alternate, 'lesson_probe_sampler')
        else:
            sampler = evaluator
        for name in ('LESSON_COMPETITORS', 'SEMANTIC_RIVALS', 'SEMANTIC_WITNESSES', 'CANONICAL_SHORTCUTS'):
            values = getattr(evaluator, name)
            if not isinstance(values, dict) or not values or any(not callable(fn) for fn in values.values()):
                raise TypeError(f'{name} must be a nonempty dict of named callables')
        report['source'].update({'sampling_generator_version': getattr(sampler, 'VERSION', None),
                                'evaluator_generator_version': getattr(evaluator, 'VERSION', None),
                                'runtime_runner_sha256': digest_bytes(Path(runner.__file__).read_bytes()),
                                'runtime_bridge_sha256': digest_bytes((stage/'arc_repl/racket_bridge.py').read_bytes()),
                                'runtime_base_sha256': digest_bytes((stage/'puzzle_generators/base.py').read_bytes())})
        report['domain_limits'] = {'declared_sampling_axes': getattr(sampler, 'AXES', {}),
                                   'declared_evaluator_axes': getattr(evaluator, 'AXES', {}),
                                   'overrides': {}, 'bands': dict(BANDS),
                                   'repaired_ordinary_cardinalities': {'nonzero_colors': '3..9', 'keeper_colors': '2..5'},
                                   'repaired_exact_control_cardinalities': {'nonzero_colors': '2..9', 'keeper_colors': '1..5'},
                                   'scope': 'Ordinary unoverridden lessons only; exact controls also permit two total colors or one keeper. Alternate sampling uses its own recorded AXES and empirical ranges. Extremes and every override combination are not exhaustively sampled.'}
        rivals = evaluator.SEMANTIC_RIVALS
        shortcuts = evaluator.CANONICAL_SHORTCUTS
        report['canonical_shortcuts'] = {}
        for name, rival in shortcuts.items():
            fitted = [rival(deepcopy(pair['input'])) == pair['output'] for pair in canonical_pairs]
            report['canonical_shortcuts'][name] = {'canonical_pair_count': len(canonical_pairs),
                'canonical_fit_count': sum(fitted), 'fits_all_usable_canonical_pairs': all(fitted),
                'sampled_disagreement_count': 0, 'first_generated_counterexample': None}
            if not all(fitted):
                raise RuntimeError(f'Declared canonical shortcut {name} fails a usable canonical pair')
        report['counterexample'] = {'input': COUNTEREXAMPLE, 'racket_output': result['output'],
            'racket_authority': {key: applied[key] for key in ('reference', 'rule_file', 'executed_rule_hash',
                                'rule_text_sha256', 'rule_hash_matches_catalog')},
            'rivals': {name: {'output': fn(deepcopy(COUNTEREXAMPLE)),
                             'fits_all_canonical_demonstrations': all(fn(deepcopy(p['input'])) == p['output']
                                                                     for p in canonical['train']),
                             'usable_canonical_pair_count': len(canonical_pairs),
                             'fits_all_usable_canonical_pairs': all(fn(deepcopy(p['input'])) == p['output']
                                                                    for p in canonical_pairs)}
                       for name, fn in rivals.items()}}
        for value in report['counterexample']['rivals'].values():
            value['disagrees_with_racket'] = value['output'] != result['output']
        report['racket_authority'] = {'reference': 'canonical', 'rule_file': 'data/canonical/puzzles.jsonl',
                                     'executed_rule_hash': rule_hash,
                                     'wrapped_rule_sha256': digest_bytes(runner.wrap_rule(rule).encode()),
                                     'labels': 'persistent RacketBridge, existing runner.run_one'}
        traced = TracedSampler(sampler)
        bundle = runner.GeneratorBundle(TASK_ID, TASK_ID, rule, runner.wrap_rule(rule),
                                       'data/canonical/puzzles.jsonl', traced,
                                       bool(getattr(sampler, 'ALLOW_IDENTITY_OUTPUT', False)))
        competitors = evaluator.LESSON_COMPETITORS
        report['sampler'] = {'entrypoint': 'puzzle_generators.runner.run_one', 'n_train': 3, 'n_test': 2,
            'lessons_per_band': args.lessons_per_band, 'seed_base': args.seed,
            'seed_formula': 'seed_base + band_index * 1000000 + lesson_index',
            'sample_index_base': args.sample_index,
            'sample_index_formula': 'sample_index_base + lesson_index * 5; five sequential accepted calls',
            'silent_rejections_allowed': False, 'competitors': list(competitors)}
        bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
        all_hashes = set()
        report['bands'] = {}
        try:
            for band_index, (band, difficulty) in enumerate(BANDS):
                band_hashes = set()
                witness_counts = Counter({name: 0 for name in evaluator.SEMANTIC_WITNESSES})
                strict_counts = Counter({'pass': 0, 'fail': 0})
                competitor_counts = {name: Counter() for name in competitors}
                observations = defaultdict(list)
                band_report = {'lessons': [], 'competitors': {}}
                report['bands'][band] = band_report
                for lesson_index in range(args.lessons_per_band):
                    seed = args.seed + band_index * 1000000 + lesson_index
                    si = args.sample_index + lesson_index * 5
                    start = len(traced.attempts)
                    lesson = runner.run_one(TASK_ID, seed, si, n_train=3, n_test=2,
                        bundle=bundle, bridge=bridge, fn_name=fn_name, difficulty=difficulty)
                    attempts = traced.attempts[start:]
                    report['last_sampler_attempts'] = attempts
                    if len(attempts) != 5 or any('error' in a for a in attempts):
                        raise RuntimeError(f'{band} lesson {lesson_index}: runner retried or rejected a sample')
                    pairs = lesson['train'] + lesson['test']
                    entry = {'lesson_index': lesson_index, 'seed': seed, 'sample_index': si,
                             'samples': [], 'competitors': {}, 'queries': []}
                    for pair_index, (pair, attempt) in enumerate(zip(pairs, attempts, strict=True)):
                        grid = pair['input']
                        validate_grid(grid); validate_grid(pair['output'])
                        ih = digest(grid)
                        if attempt['sample_index'] != si + pair_index or attempt['input_sha256'] != ih:
                            raise RuntimeError('Actual sampling trace differs from accepted input order')
                        self_errors = evaluator.self_check(deepcopy(grid), difficulty=difficulty)
                        if not passes(self_errors, 'self_check'):
                            raise RuntimeError(f'Selected evaluator self_check failed: {self_errors}')
                        strict = passes(evaluator.strict_canonical_like(deepcopy(grid)), 'strict_canonical_like')
                        strict_counts['pass' if strict else 'fail'] += 1
                        witnesses = {name: passes(fn(deepcopy(grid)), f'witness {name}')
                                     for name, fn in evaluator.SEMANTIC_WITNESSES.items()}
                        witness_counts.update(name for name, present in witnesses.items() if present)
                        stats = facts(grid)
                        for name, value in stats.items(): observations[name].append(value)
                        entry['samples'].append({**attempt, 'split': 'demo' if pair_index < 3 else 'query',
                            'output_sha256': digest(pair['output']), 'strict_canonical_like': strict,
                            'witnesses': witnesses, 'grid_facts': stats})
                        band_hashes.add(ih); all_hashes.add(ih)
                        for name, rival in shortcuts.items():
                            rival_output = rival(deepcopy(grid))
                            shortcut_report = report['canonical_shortcuts'][name]
                            if rival_output != pair['output']:
                                shortcut_report['sampled_disagreement_count'] += 1
                                if shortcut_report['first_generated_counterexample'] is None:
                                    shortcut_report['first_generated_counterexample'] = {
                                        'band': band, 'lesson_index': lesson_index, 'pair_index': pair_index,
                                        'seed': seed, 'sample_index': attempt['sample_index'],
                                        'difficulty': difficulty, 'overrides': {}, 'input': grid,
                                        'racket_output': pair['output'], 'rival_output': rival_output,
                                        'input_sha256': ih, 'output_sha256': digest(pair['output']),
                                        'sampling_generator_sha256': report['source']['sampling_generator_sha256'],
                                        'canonical_rule_hash': rule_hash,
                                        'racket_authority': report['racket_authority']} 
                    for name, rival in competitors.items():
                        demo_survives = all(rival(deepcopy(p['input'])) == p['output'] for p in lesson['train'])
                        query_disagrees = [rival(deepcopy(p['input'])) != p['output'] for p in lesson['test']]
                        survived_all = demo_survives and not any(query_disagrees)
                        flags = {'survived_demos': demo_survives, 'query_discriminates': any(query_disagrees),
                                 'query_discriminates_given_demo_survival': demo_survives and any(query_disagrees),
                                 'query_disagrees': query_disagrees, 'survived_all': survived_all}
                        entry['competitors'][name] = flags
                        competitor_counts[name].update({key: int(value) for key, value in flags.items()
                                                       if type(value) is bool})
                    demo_survivors = [name for name, flags in entry['competitors'].items() if flags['survived_demos']]
                    for query_index, query in enumerate(lesson['test']):
                        identifiable = passes(evaluator.lesson_identifiable(deepcopy(lesson['train']), deepcopy(query)),
                                              'lesson_identifiable')
                        if identifiable != (not demo_survivors):
                            raise RuntimeError('lesson_identifiable disagrees with finite all-demo-survivors policy')
                        entry['queries'].append({'query_index': query_index, 'lesson_identifiable': identifiable,
                            'demo_survivors': demo_survivors,
                            'query_discriminating_survivors': [name for name in demo_survivors
                                if entry['competitors'][name]['query_disagrees'][query_index]],
                            'query_agreeing_survivors': [name for name in demo_survivors
                                if not entry['competitors'][name]['query_disagrees'][query_index]]})
                    entry['all_demos_refute_all_declared_competitors'] = not demo_survivors
                    band_report['lessons'].append(entry)
                band_report.update({'lesson_count': len(band_report['lessons']),
                    'sample_count': len(band_report['lessons'])*5, 'unique_input_count': len(band_hashes),
                    'unique_input_sha256': sorted(band_hashes), 'witness_counts': dict(witness_counts),
                    'strict_canonical_like_counts': dict(strict_counts),
                    'competitors': {name: dict(counts) for name, counts in competitor_counts.items()},
                    'identifiable_lesson_count': sum(x['all_demos_refute_all_declared_competitors'] for x in band_report['lessons']),
                    'observed_grid_fact_ranges': {name: {'min': min(vals), 'max': max(vals)} for name, vals in observations.items()}})
                print(f'{band}: {band_report["lesson_count"]} lessons, {len(band_hashes)} unique inputs, '
                      f'{band_report["identifiable_lesson_count"]} identifiable', flush=True)
        finally:
            bridge.shutdown()
        report.pop('last_sampler_attempts', None)
        report['total'] = {'lesson_count': sum(b['lesson_count'] for b in report['bands'].values()),
                           'sample_count': len(traced.attempts), 'unique_input_count': len(all_hashes),
                           'unique_input_sha256': sorted(all_hashes),
                           'witness_counts': {name: sum(b['witness_counts'][name] for b in report['bands'].values())
                                              for name in evaluator.SEMANTIC_WITNESSES},
                           'strict_canonical_like_counts': {name: sum(b['strict_canonical_like_counts'][name]
                                                                     for b in report['bands'].values())
                                                            for name in ('pass', 'fail')},
                           'identifiable_lesson_count': sum(b['identifiable_lesson_count'] for b in report['bands'].values()),
                           'competitors': {name: {flag: sum(b['competitors'][name][flag] for b in report['bands'].values())
                                                  for flag in ('survived_demos', 'query_discriminates',
                                                               'query_discriminates_given_demo_survival', 'survived_all')}
                                           for name in competitors}}
        report['all_lessons_identifiable'] = (report['total']['identifiable_lesson_count']
                                              == report['total']['lesson_count'])
        report['probe_completed'] = True
        report['passed'] = True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lessons-per-band', type=int, default=100)
    parser.add_argument('--seed', type=int, default=2701)
    parser.add_argument('--sample-index', type=int, default=0)
    parser.add_argument('--generator', type=Path)
    args = parser.parse_args()
    if args.lessons_per_band < 1 or args.lessons_per_band >= 1000000 or args.sample_index < 0:
        parser.error('lessons-per-band must be in 1..999999; sample-index must be nonnegative')
    if args.out.exists():
        parser.error(f'Output already exists: {args.out}')
    report = {'schema': 'arcpuzzles-task-local-lesson-probe-v1', 'task_id': TASK_ID, 'passed': False,
              'probe_completed': False,
              'pass_criterion': 'sampling/oracle/contract execution completed',
              'all_lessons_identifiable': None}
    started = time.monotonic()
    try:
        probe(args, report)
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        print(report['error'], file=sys.stderr)
    finally:
        report['elapsed_seconds'] = round(time.monotonic()-started, 3)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
