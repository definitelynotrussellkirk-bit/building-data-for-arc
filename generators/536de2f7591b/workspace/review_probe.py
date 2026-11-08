#!/usr/bin/env python3
"""Source-bound lesson qualification using the REAL runner and canonical Racket.

Run from repo via packet run_with_racket.py. No Python-label fallback. A fresh
portable runtime is prepared, the same pinned lesson plan as the semantic gate
is used, and all declared competitors/shortcuts are discovered from the module.
The independent stepwise Python oracle is parity evidence, never label authority.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

TASK = '536de2f7591b'


def sha(data):
    if not isinstance(data, bytes):
        data = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(data).hexdigest()


def stepwise_output(grid):
    """Slide a whole block one column at a time, consulting ORIGINAL cyan cells."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        cells = [c for c, value in enumerate(row) if value == 3]
        if not cells:
            continue
        left = cells[0]
        while left > 0 and row[left - 1] != 8:
            left -= 1
        for c in cells:
            out[r][c] = 0
        for c in range(left, left + len(cells)):
            out[r][c] = 3
    return out


def worker(count):
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, _pinned_seed
    bundle = runner._load_bundle(TASK)
    gen = bundle.generator_module
    generator_path = Path(gen.__file__)
    canonical = next(json.loads(line) for line in Path('data/canonical/puzzles.jsonl').read_text().splitlines()
                     if json.loads(line).get('task_id') == TASK)
    rule = canonical['program_solution']
    source = {'task_id': TASK, 'generator_sha256': sha(generator_path.read_bytes()),
              'rule_sha256': hashlib.sha256(rule.encode()).hexdigest(), 'rule_hash': gen.RULE_HASH,
              'probe_sha256': sha(Path(__file__).read_bytes())}
    bridge, fn_name = runner._open_bridge_with_rule(runner.wrap_rule(rule))
    reports, evidence, ledger, failures = {}, {}, [], []
    all_inputs = set()
    try:
        pairs = canonical_pairs(TASK)
        canonical_report = {}
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            canonical_report[name] = {'matches': sum(rival(p['input']) == p['output'] for p in pairs),
                                      'denominator': len(pairs)}
            if canonical_report[name]['matches'] != len(pairs):
                failures.append({'kind': 'noncanonical_shortcut', 'name': name})
        canonical_parity = sum(runner._apply_rule(bridge, fn_name, p['input']) == p['output'] == stepwise_output(p['input']) for p in pairs)
        if canonical_parity != len(pairs):
            failures.append({'kind': 'canonical_parity', 'matches': canonical_parity})
        for band in ('easy', 'medium', 'hard'):
            totals, starts, profiles, disagreements, witness_hits = Counter(), Counter(), Counter(), Counter(), Counter()
            unique = set()
            for i in range(count):
                seed, start = _pinned_seed(TASK, f'lesson:{band}', i), i * 11
                inst = runner.run_one(TASK, seed, start, n_train=gen.EXAMPLES_NEEDED, n_test=1,
                                      bundle=bundle, bridge=bridge, fn_name=fn_name, difficulty=band)
                totals['lessons'] += 1
                starts[start % len(gen.SCHEDULE_PROFILES)] += 1
                survivors = [name for name, rival in gen.LESSON_COMPETITORS.items()
                             if all(rival(p['input']) == p['output'] for p in inst['train'])]
                totals['lessons_eliminating_all_declared_competitors'] += not survivors
                if survivors:
                    failures.append({'kind': 'surviving_competitors', 'band': band, 'seed': seed,
                                     'sample_index': start, 'survivors': survivors, 'instance': inst})
                pair_hashes, accepted = [], []
                next_si = start
                for pair in inst['train'] + inst['test']:
                    grid, output = pair['input'], pair['output']
                    # Audit runner retries against the actual accepted grid sequence.
                    while next_si < start + (gen.EXAMPLES_NEEDED + 1) * 5:
                        emitted = gen.generate(seed, next_si, difficulty=band)
                        if emitted == grid:
                            break
                        totals['skipped_sample_indexes'] += 1
                        next_si += 1
                    actual_si = next_si
                    if emitted != grid:
                        raise RuntimeError('could not reconstruct runner sample index')
                    next_si += 1
                    accepted.append(actual_si)
                    digest = sha(grid)
                    unique.add(digest); all_inputs.add(digest); pair_hashes.append(sha(pair))
                    totals['pairs'] += 1
                    totals['strict_canonical_like'] += not gen.strict_canonical_like(grid)
                    totals['python_racket_matches'] += stepwise_output(grid) == output
                    totals['changed_pairs'] += grid != output
                    profiles[gen.schedule_profile(seed, actual_si, band)] += 1
                    issues = gen.self_check(grid)
                    if issues or stepwise_output(grid) != output:
                        failures.append({'kind': 'pair_failure', 'band': band, 'seed': seed,
                                         'sample_index': actual_si, 'issues': issues, 'pair': pair,
                                         'independent_python': stepwise_output(grid)})
                    for name, witness in gen.SEMANTIC_WITNESSES.items():
                        if witness(grid):
                            witness_hits[name] += 1
                            if not any(gen.SEMANTIC_RIVALS[r](grid) != output for r in gen.WITNESS_RIVALS[name]):
                                failures.append({'kind': 'false_witness', 'name': name, 'pair': pair})
                    for name, rival in gen.CANONICAL_SHORTCUTS.items():
                        rival_output = rival(grid)
                        if rival_output != output:
                            disagreements[name] += 1
                            evidence.setdefault(name, dict(source, band=band, seed=seed,
                                sample_index=actual_si, overrides={}, input=grid,
                                actual_racket_output=output, rival_output=rival_output,
                                self_check_errors=issues, documented_domain=True))
                ledger.append({'band': band, 'lesson_index': i, 'seed': seed,
                               'start_sample_index': start, 'accepted_sample_indexes': accepted,
                               'pair_sha256': pair_hashes, 'surviving_competitors': survivors})
            reports[band] = dict(totals, unique_inputs=len(unique), start_residue_counts=dict(starts),
                                 schedule_profiles=dict(profiles), witness_pair_hits=dict(witness_hits),
                                 canonical_shortcut_disagreements=dict(disagreements))
    finally:
        bridge.close()
    report = {'schema': '536de2f7591b-qualification-v1', 'phase': 'final', **source,
              'runtime_directory': str(Path.cwd()), 'lessons_requested_per_band': count,
              'sampler': 'puzzle_generators.runner.run_one; n_train=4,n_test=1, difficulty passed through',
              'seed_policy': '_pinned_seed(task_id, lesson:<band>, k), k=0..count-1; start=k*11',
              'cyclic_starts': 'all four residues counted per band; no overlapping windows for one seed',
              'canonical_racket_python_matches': canonical_parity, 'canonical_pair_denominator': len(pairs),
              'canonical_shortcuts': canonical_report, 'bands': reports,
              'unique_inputs_all_bands': len(all_inputs), 'counterexamples': evidence,
              'lessons': ledger, 'failures': failures,
              'limitation': 'Finite sample and declared rival set only; not universal identifiability or approval.'}
    print(json.dumps(report, indent=2))
    return int(bool(failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--lessons-per-band', type=int, default=100)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.lessons_per_band < 1:
        parser.error('--lessons-per-band must be positive')
    if args.worker:
        return worker(args.lessons_per_band)
    if args.out is None or args.out.exists():
        parser.error('--out must name a new file')
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix=TASK+'-qualification-') as folder:
        stage = Path(folder)
        prepare_runtime(Catalog(root), stage, TASK)
        shutil.copy2(__file__, stage/'review_probe.py')
        result = run_process([sys.executable, '-B', 'review_probe.py', '--worker',
                              '--lessons-per-band', str(args.lessons_per_band)], stage, timeout=300)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if result['timed_out'] or result['exit_code'] not in (0, 1):
        args.out.write_text(json.dumps({'status': 'worker_failed', **result}, indent=2)+'\n')
        return 2
    try:
        report = json.loads(result['stdout'])
    except json.JSONDecodeError:
        args.out.write_text(json.dumps({'status': 'worker_invalid_json', **result}, indent=2)+'\n')
        return 2
    report['worker_stderr'] = result['stderr']
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('generator_sha256', 'bands', 'unique_inputs_all_bands')}, indent=2))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
