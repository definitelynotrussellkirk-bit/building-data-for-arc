"""Source-bound canonical/rival/lesson census using the public reference API.

From the packet root:
  python3 run_with_racket.py python3 generators/b6592c220670/workspace/review_probe.py \
    --oracle --phase final --out ../checks/census-final

Thirteen seeds x eight cyclic starts = 104 overlapping four-demo/one-query
lessons per band, materialized from 156 draws per band. Never counts these as
520 independent inputs. The registries come from the loaded source, not a copied
list. An additional deduplication diagnostic allows an honest baseline comparison.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def load(path):
    spec = importlib.util.spec_from_file_location('reviewed_task', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def diagnostic_deduplicate(module, grid):
    state = module._crop_motif(grid)
    states = []
    for code in dict.fromkeys(module._script(grid)):
        state = module._step(state, code)
        states.append(state)
    return module._gallery(states)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--generator', type=Path, default=Path(__file__).resolve().parents[1] / 'generator.py')
    parser.add_argument('--phase', default='final')
    parser.add_argument('--oracle', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output must be a new directory; preserve previous evidence')
    args.out.mkdir(parents=True)
    mod = load(args.generator)
    sha = hashlib.sha256(args.generator.read_bytes()).hexdigest()
    cat = Catalog()
    canonical = None
    for line in (cat.root / 'shared/data/canonical/puzzles.jsonl').open():
        row = json.loads(line)
        if row.get('task_id') == mod.TASK_ID:
            canonical = row
            break
    if canonical is None:
        raise RuntimeError('canonical task not found')
    pairs = canonical['train'] + canonical['test']
    all_rivals = dict(mod.LESSON_COMPETITORS)
    all_rivals.update(mod.CANONICAL_SHORTCUTS)
    report = {
        'task_id': mod.TASK_ID, 'phase': args.phase, 'generator_sha256': sha,
        'generator_path': str(args.generator), 'rule_hash': mod.RULE_HASH,
        'argv': sys.argv, 'cwd': str(Path.cwd()), 'reference_api': 'Catalog.apply' if args.oracle else None,
        'sampling': {'seed_first': 23000, 'seed_last_inclusive': 23012,
                     'sample_indices_per_seed': list(range(12)), 'cyclic_starts': list(range(8)),
                     'demo_count': 4, 'query_offset': 4, 'assembly': 'consecutive draws, no filtering or replacement',
                     'lessons_per_band': 104, 'draws_per_band': 156,
                     'note': 'Lessons overlap; pooled draw frequencies are not independent lesson probabilities.'},
        'declared_canonical_shortcuts': sorted(mod.CANONICAL_SHORTCUTS),
        'declared_lesson_competitors': sorted(mod.LESSON_COMPETITORS),
        'canonical_fit': {name: {'passed': sum(fn(p['input']) == p['output'] for p in pairs), 'total': len(pairs)}
                          for name, fn in mod.CANONICAL_SHORTCUTS.items()},
        'diagnostic_deduplicate_canonical_fit': sum(diagnostic_deduplicate(mod, p['input']) == p['output'] for p in pairs),
        'bands': {}, 'failures': [], 'oracle_receipts': [],
    }
    if not all(x['passed'] == x['total'] for x in report['canonical_fit'].values()):
        report['failures'].append('one or more declared canonical shortcuts do not fit all canonical pairs')
    if 'deduplicate_script' not in mod.CANONICAL_SHORTCUTS:
        report['failures'].append('canonical-compatible deduplication rival is undeclared')
    all_records, lookup = [], {}
    for band in ('easy', 'medium', 'hard'):
        for seed in range(23000, 23013):
            for index in range(12):
                grid = mod.generate(seed, index, difficulty=band)
                record = {'band': band, 'seed': seed, 'sample_index': index, 'input': grid,
                          'input_sha256': digest(grid), 'output': mod.rule_mirror(grid)}
                all_records.append(record)
                lookup[(band, seed, index)] = record
    if args.oracle:
        if cat.describe(mod.TASK_ID)['generator_sha256'] != sha:
            raise RuntimeError('oracle mode requires the current selected source, not a different snapshot')
        for offset in range(0, len(all_records), 64):
            chunk = all_records[offset:offset + 64]
            receipt = cat.apply(mod.TASK_ID, [r['input'] for r in chunk], timeout=180)
            receipt['probe_coordinates'] = [{k: r[k] for k in ('band', 'seed', 'sample_index')} for r in chunk]
            path = args.out / 'oracle' / f'batch-{offset // 64:02d}.json'
            write(path, receipt)
            report['oracle_receipts'].append(str(path.relative_to(args.out)))
            if receipt['generator_sha256'] != sha or not receipt['rule_hash_matches_catalog']:
                report['failures'].append(f'source/authority mismatch in batch {offset // 64}')
            for record, actual in zip(chunk, receipt['results'], strict=True):
                if actual['error'] or actual['output'] != record['output']:
                    report['failures'].append({'kind': 'oracle_mismatch', 'band': record['band'], 'seed': record['seed'], 'sample_index': record['sample_index'], 'error': actual['error']})
                record['output'] = actual['output']
            print(f'oracle checked {offset + len(chunk)}/{len(all_records)} inputs', flush=True)
    witness_written = False
    for band in ('easy', 'medium', 'hard'):
        records = [r for r in all_records if r['band'] == band]
        stats = {'draws': len(records), 'unique_inputs': len({r['input_sha256'] for r in records}),
                 'strict': 0, 'selfcheck_failures': 0, 'repeated_script_draws': 0,
                 'deduplicate_disagreements': 0, 'repeated_codes': Counter(),
                 'lessons': 104, 'identifiable': 0, 'lessons_with_repeat_demo': 0,
                 'competitors': {name: Counter() for name in all_rivals}}
        for record in records:
            grid, output = record['input'], record['output']
            codes = mod._script(grid)
            stats['strict'] += not bool(mod.strict_canonical_like(grid))
            stats['selfcheck_failures'] += bool(mod.self_check(grid))
            repeated = {c for c in codes if codes.count(c) > 1}
            stats['repeated_script_draws'] += bool(repeated)
            stats['repeated_codes'].update(repeated)
            rival = diagnostic_deduplicate(mod, grid)
            if output != rival:
                stats['deduplicate_disagreements'] += 1
                if not witness_written:
                    write(args.out / 'deduplicate-witness.json', {
                        'task_id': mod.TASK_ID, 'generator_sha256': sha, 'rule_hash': mod.RULE_HASH,
                        'seed': record['seed'], 'sample_index': record['sample_index'], 'difficulty': band,
                        'overrides': {}, 'input': grid, 'script': codes, 'actual_output': output,
                        'output_source': 'canonical Racket via Catalog.apply' if args.oracle else 'Python mirror, not independently verified',
                        'rival_output': rival, 'validator_errors': mod.self_check(grid),
                    })
                    write(args.out / 'witness-input.json', grid)
                    witness_written = True
        for seed in range(23000, 23013):
            for start in range(8):
                window = [lookup[(band, seed, i)] for i in range(start, start + 5)]
                demos, query = window[:4], window[4]
                errors = mod.lesson_identifiable(demos, query)
                stats['identifiable'] += not bool(errors)
                if errors:
                    report['failures'].append({'kind': 'lesson', 'band': band, 'seed': seed, 'start': start, 'errors': errors})
                has_repeat = any(len(mod._script(d['input'])) > len(set(mod._script(d['input']))) for d in demos)
                stats['lessons_with_repeat_demo'] += has_repeat
                for name, fn in all_rivals.items():
                    survives = all(fn(d['input']) == d['output'] for d in demos)
                    agrees = fn(query['input']) == query['output']
                    state = 'refuted' if not survives else ('survived_all' if agrees else 'query_discriminates')
                    stats['competitors'][name][state] += 1
        if stats['lessons_with_repeat_demo'] != stats['lessons']:
            report['failures'].append(f'{band}: some four-demo windows lack a repetition witness')
        if stats['selfcheck_failures']:
            report['failures'].append(f'{band}: generated input rejected by self_check')
        report['bands'][band] = stats
    report['total_draws'] = len(all_records)
    report['unique_inputs_all_bands'] = len({r['input_sha256'] for r in all_records})
    report['source_unchanged_at_finish'] = hashlib.sha256(args.generator.read_bytes()).hexdigest() == sha
    report['passed'] = not report['failures'] and report['source_unchanged_at_finish']
    report['limitations'] = ['Tests only declared competitors plus the named baseline diagnostic, not all possible rules.',
                            'Compact fixed motif masks remain; disconnected and larger shapes are not added by this repair.',
                            'One-instruction overrides cannot contain repeats and do not promise four-demo teaching coverage.']
    write(args.out / 'report.json', report)
    print(json.dumps({k: report[k] for k in ('phase', 'generator_sha256', 'total_draws', 'unique_inputs_all_bands', 'bands', 'failures', 'passed')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
