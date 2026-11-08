#!/usr/bin/env python3
"""Source-bound Racket lesson probe using the actual repository runner.

Default: 100 pinned 3-demo/1-query lessons per band, plus every 3-cycle start
for ten independently seeded windows per band. No private solve files are read.
A surviving named rival is a nonzero teaching result even if query-equivalent.
--baseline replays retained old generator bytes against CURRENT declared rivals;
both source hashes are recorded rather than pretending old hooks existed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

TASK_ID = '1ea6c72cb7e3'
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
BANDS = ('easy', 'medium', 'hard')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_key(grid) -> str:
    return digest(json.dumps(grid, separators=(',', ':')).encode())


def classify_rival(rival, demos, query) -> str:
    """Keep demo refutation, harmless survival and query ambiguity distinct."""
    if any(rival(copy.deepcopy(pair['input'])) != pair['output'] for pair in demos):
        return 'refuted'
    return ('survived_all' if rival(copy.deepcopy(query['input'])) == query['output']
            else 'query_discriminates')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--lessons-per-band', type=int, default=100)
    parser.add_argument('--cyclic-seeds', type=int, default=10)
    parser.add_argument('--demos', type=int, default=3)
    args = parser.parse_args(argv)
    if args.lessons_per_band < 1 or args.cyclic_seeds < 0 or args.demos < 1:
        parser.error('positive lessons/demos and nonnegative cyclic-seeds required')
    out = args.out.resolve()
    baseline = args.baseline.resolve() if args.baseline else None
    archive = out.with_suffix('.lessons.jsonl.gz')
    example_path = out.with_suffix('.counterexample.json')
    for path in (out, archive, example_path):
        if path.exists():
            parser.error(f'refusing to overwrite retained evidence: {path}')
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    report = {
        'schema': 'visibility-lesson-probe-v1', 'task_id': TASK_ID,
        'mode': 'baseline_replayed_against_current_declared_rivals' if baseline else 'final',
        'invocation': {'argv': sys.argv, 'cwd': str(Path.cwd())},
        'generator_sha256': digest((baseline or HOME/'generator.py').read_bytes()),
        'rival_source_sha256': digest((HOME/'generator.py').read_bytes()),
        'probe_sha256': digest(Path(__file__).read_bytes()),
        'policy': {'pinned_sampler': 'generator_semantic_gate.materialize_lessons -> runner.run_one',
                   'pinned_seed': 'canonical_profile_gate._pinned_seed(task_id, lesson:BAND, k)',
                   'pinned_sample_index': '11*k', 'pinned_k_range': [0, args.lessons_per_band-1],
                   'cyclic_seed': 'int(sha256(TASK_ID:cycle:BAND:k)[:12],16)',
                   'cyclic_k_range': [0, args.cyclic_seeds-1], 'cyclic_starts': [0, 1, 2],
                   'n_demos': args.demos, 'n_queries': 1,
                   'scope': 'Named rivals only. Default three consecutive demonstrations; no universal induction claim.'},
        'errors': [], 'canonical': {}, 'cohorts': {}, 'examples': [],
    }
    sys.path.insert(0, str(ROOT/'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    old_cwd = Path.cwd()
    try:
        with tempfile.TemporaryDirectory(prefix='visibility-lesson-probe-') as directory:
            runtime = Path(directory)
            prepare_runtime(Catalog(ROOT), runtime, TASK_ID)
            report['actual_runtime_directory'] = str(runtime)
            sys.path.insert(0, str(runtime))
            spec = importlib.util.spec_from_file_location('visibility_rival_definitions', HOME/'generator.py')
            contract = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(contract)
            if baseline:
                shutil.copyfile(baseline, runtime/f'puzzle_generators/per_puzzle/{TASK_ID}/generator.py')
            os.chdir(runtime)
            gen = importlib.import_module(f'puzzle_generators.per_puzzle.{TASK_ID}.generator')
            from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
            from scripts.generator_semantic_gate import _RuleOracle, materialize_lessons
            from puzzle_generators import runner
            source = canonical_rule_source(TASK_ID)
            report['rule_hash'] = normalized_rule_hash(source)
            report['rule_source_sha256'] = digest(source.encode())
            report['canonical_shortcuts'] = sorted(contract.CANONICAL_SHORTCUTS)
            rivals = {**contract.CANONICAL_SHORTCUTS, **contract.LESSON_COMPETITORS}
            report['rivals'] = sorted(rivals)
            oracle = _RuleOracle(TASK_ID)
            try:
                if not oracle.ready:
                    raise RuntimeError(oracle.error)
                canonical = canonical_pairs(TASK_ID)
                report['canonical'] = {'pairs': len(canonical), 'racket_matches': 0,
                                       'shortcut_matches': {name: 0 for name in contract.CANONICAL_SHORTCUTS}}
                for pair in canonical:
                    actual, error = oracle.apply(pair['input'])
                    if error:
                        raise RuntimeError(error)
                    report['canonical']['racket_matches'] += actual == pair['output']
                    for name, rival in contract.CANONICAL_SHORTCUTS.items():
                        report['canonical']['shortcut_matches'][name] += rival(copy.deepcopy(pair['input'])) == actual
                if not canonical or report['canonical']['racket_matches'] != len(canonical):
                    report['errors'].append('canonical/Racket parity failure or missing usable canonical pairs')
                for name, count in report['canonical']['shortcut_matches'].items():
                    if count != len(canonical):
                        report['errors'].append(f'declared canonical shortcut {name} fits only {count}/{len(canonical)}')
                lessons, errors = materialize_lessons(TASK_ID, 3*args.lessons_per_band,
                    n_demos=args.demos, oracle_factory=lambda: oracle)
                report['errors'].extend(errors)
                for lesson in lessons:
                    lesson['cohort'] = 'pinned'
                for band in BANDS:
                    for k in range(args.cyclic_seeds):
                        seed = int(digest(f'{TASK_ID}:cycle:{band}:{k}'.encode())[:12], 16)
                        for start in (0, 1, 2):
                            try:
                                instance = runner.run_one(TASK_ID, seed=seed, sample_index=start,
                                    n_train=args.demos, n_test=1, difficulty=band,
                                    bundle=oracle.bundle, bridge=oracle.bridge, fn_name=oracle.fn_name)
                                lessons.append({'cohort': 'cyclic', 'band': band, 'seed': seed,
                                    'sample_index': start, 'demos': instance['train'], 'query': instance['test'][0]})
                            except Exception as exc:
                                report['errors'].append(f'cyclic {band}/{k}/{start}: {type(exc).__name__}: {exc}')
            finally:
                oracle.close()
            unique = {}
            per_band_unique = {band: set() for band in BANDS}
            witness_hits = Counter()
            total_pairs = 0
            bad_lessons = 0
            raw_hash = hashlib.sha256()
            raw_size = 0
            first_counterexample = None
            with archive.open('wb') as raw:
                with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as stream:
                    for index, lesson in enumerate(lessons):
                        band = lesson['band']
                        group = report['cohorts'].setdefault(lesson['cohort'], {}).setdefault(band, {
                            'lessons': 0, 'all_rivals_refuted': 0,
                            'rivals': {name: {'refuted': 0, 'survived_all': 0, 'query_discriminates': 0} for name in rivals}})
                        group['lessons'] += 1
                        pairs = [*lesson['demos'], lesson['query']]
                        for pair in pairs:
                            total_pairs += 1
                            key = grid_key(pair['input'])
                            per_band_unique[band].add(key)
                            if key not in unique:
                                unique[key] = grid_key(pair['output'])
                                findings = gen.self_check(copy.deepcopy(pair['input']))
                                if findings:
                                    report['errors'].append({'index': index, 'self_check': findings})
                                if contract._diagnostic_prediction(pair['input']) != pair['output']:
                                    report['errors'].append({'index': index, 'diagnostic_racket_mismatch': key})
                                for name, witness in contract.SEMANTIC_WITNESSES.items():
                                    witness_hits[name] += bool(witness(pair['input']))
                            elif unique[key] != grid_key(pair['output']):
                                report['errors'].append({'index': index, 'same_input_different_output': key})
                        scores = {name: classify_rival(rival, lesson['demos'], lesson['query']) for name, rival in rivals.items()}
                        for name, outcome in scores.items():
                            group['rivals'][name][outcome] += 1
                        good = all(outcome == 'refuted' for outcome in scores.values())
                        group['all_rivals_refuted'] += good
                        bad_lessons += not good
                        record = {k: lesson[k] for k in ('cohort', 'band', 'seed', 'sample_index', 'demos', 'query')}
                        record.update({'index': index, 'scores': scores})
                        encoded = (json.dumps(record, separators=(',', ':'), sort_keys=True)+'\n').encode()
                        stream.write(encoded); raw_hash.update(encoded); raw_size += len(encoded)
                        if not good and len(report['examples']) < 8:
                            report['examples'].append({k: record[k] for k in ('index', 'cohort', 'band', 'seed', 'sample_index', 'scores')})
                        if first_counterexample is None and 'query_discriminates' in scores.values():
                            first_counterexample = record
            if first_counterexample:
                first_counterexample.update({'generator_sha256': report['generator_sha256'],
                    'rule_hash': report['rule_hash'], 'rule_source_sha256': report['rule_source_sha256'],
                    'rival_source_sha256': report['rival_source_sha256'],
                    'note': 'All demonstrations fit the named surviving rival, but the Racket query answer differs.'})
                example_path.write_text(json.dumps(first_counterexample, indent=2)+'\n')
                report['counterexample_file'] = example_path.name
            report.update({'lessons': len(lessons), 'lessons_with_surviving_rivals': bad_lessons,
                           'pair_occurrences': total_pairs, 'unique_inputs': len(unique),
                           'unique_inputs_per_band': {b: len(v) for b, v in per_band_unique.items()},
                           'diagnostic_racket_comparisons': len(unique),
                           'witness_hits_over_unique_inputs': dict(witness_hits),
                           'archive': {'path': archive.name, 'sha256': digest(archive.read_bytes()),
                                       'uncompressed_path': archive.name[:-3],
                                       'uncompressed_bytes': raw_size, 'uncompressed_sha256': raw_hash.hexdigest(),
                                       'restore': 'gzip -dc '+archive.name+' > '+archive.name[:-3]}})
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    finally:
        os.chdir(old_cwd)
    report['seconds'] = time.monotonic()-started
    report['passed'] = not report['errors'] and report.get('lessons_with_surviving_rivals') == 0
    out.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: report.get(k) for k in ('mode','passed','lessons','lessons_with_surviving_rivals','unique_inputs','seconds','errors')}, indent=2))
    return 2 if report['errors'] else 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
