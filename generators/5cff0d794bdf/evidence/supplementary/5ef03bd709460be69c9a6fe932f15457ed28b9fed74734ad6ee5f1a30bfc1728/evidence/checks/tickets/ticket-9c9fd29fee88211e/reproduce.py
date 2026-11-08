"""Read-only selected-source audit. Build inputs, then verify a public apply receipt.
Run through WORK/run_with_racket.py so imports and Racket stay packet-local.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = '5cff0d794bdf'
EXPECTED_SHA256 = 'b6ba414e0be2f73cd50ba150644a5039c190c831aba2339dcb03026182249493'
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def fill(grid, guarded=True):
    out = [row[:] for row in grid]
    for col in range(len(grid[0])):
        points = [(r, row[col]) for r, row in enumerate(grid) if row[col] != 0]
        if not points:
            continue
        if guarded and (len(points) != 2 or points[0][1] != points[-1][1]):
            continue
        first, last = points[0][0], points[-1][0]
        for row in range(first, last + 1):
            out[row][col] = points[0][1]
    return out


def source_identity(gen, source, sha):
    row = next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
               if json.loads(line).get('task_id') == TASK)
    text = row['program_solution']
    return {'task_id': TASK, 'generator_path': str(source), 'generator_sha256': sha,
            'generator_version': gen.VERSION,
            'canonical_source_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'canonical_normalized_rule_hash': hashlib.sha256(' '.join(text.split()).encode()).hexdigest()[:12],
            'declared_rule_hash': getattr(gen, 'RULE_HASH', None)}


def build(gen, source, sha):
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    records, inputs = [], []
    for p in pairs:
        assert fill(p['input']) == p['output']
        inputs.append(p['input'])
        records.append({'kind': 'canonical', 'variant': p['variant'], 'split': p['split'],
                        'pair_index': p['pair_index'], 'self_check': gen.self_check(p['input']),
                        'expected_output': p['output'], 'unguarded_output': fill(p['input'], False)})
    for difficulty in ('easy', 'medium', 'hard'):
        for seed in (0, 1, 17, 12345):
            grid = gen.generate(seed, 7, difficulty=difficulty)
            assert gen.self_check(grid, difficulty=difficulty) == []
            inputs.append(grid)
            records.append({'kind': 'generated', 'seed': seed, 'sample_index': 7,
                            'difficulty': difficulty, 'overrides': {},
                            'self_check': gen.self_check(grid, difficulty=difficulty),
                            'expected_output': fill(grid), 'unguarded_output': fill(grid, False)})
    for mutation in ('mismatched_endpoints', 'three_same_color_markers'):
        grid = [row[:] for row in pairs[0]['input']]
        if mutation == 'mismatched_endpoints':
            grid[6][1] = 9
        else:
            grid[2][1] = 2
        assert gen.self_check(grid)
        inputs.append(grid)
        records.append({'kind': 'outside_generator_domain_guard_probe', 'mutation': mutation,
                        'base_canonical': {'variant': 0, 'split': 'train', 'pair_index': 0},
                        'self_check': gen.self_check(grid), 'expected_output': fill(grid),
                        'unguarded_output': fill(grid, False)})
    for i, (record, grid) in enumerate(zip(records, inputs)):
        record['input_index'] = i
        record['input_sha256'] = digest(grid)
        record['shape'] = [len(grid), len(grid[0])]
        record['unguarded_matches_mirror'] = record['unguarded_output'] == record['expected_output']
    base = gen.generate(12345, 7, difficulty='medium')
    noop_cases = [
        ('palette_kind_warm', {'palette_kind': 'warm'}),
        ('invalid_palette_kind', {'palette_kind': 'not-a-declared-kind'}),
        ('palette_size_1', {'palette_size': 1}),
        ('palette_size_9', {'palette_size': 9}),
        ('n_distinct_colors_1', {'n_distinct_colors': 1}),
        ('n_distinct_colors_9', {'n_distinct_colors': 9}),
        ('invalid_density', {'density': 'dense'}),
        ('invalid_position_bias', {'position_bias': 'rows'}),
        ('texture_warm', {'texture': 'warm'}),
        ('unknown_axis', {'unknown_axis': 3}),
    ]
    noops = []
    for name, overrides in noop_cases:
        grid = gen.generate(12345, 7, difficulty='medium', **overrides)
        noops.append({'name': name, 'overrides': overrides, 'same_as_baseline': grid == base,
                      'grid_sha256': digest(grid), 'self_check': gen.self_check(grid, difficulty='medium'),
                      'nonzero_colors': sorted({v for row in grid for v in row if v != 0})})
    boundary_cases = [{'grid_h': 8, 'grid_w': 9}, {'grid_h': 4}, {'grid_h': 24},
                      {'grid_w': 3}, {'grid_w': 18}, {'cols': 1}, {'cols': 12}]
    rejected = []
    for overrides in boundary_cases:
        try:
            grid = gen.generate(12345, 7, difficulty='medium', **overrides)
        except Exception as exc:
            rejected.append({'overrides': overrides, 'status': 'rejected',
                             'exception': type(exc).__name__, 'error': str(exc)})
        else:
            rejected.append({'overrides': overrides, 'status': 'accepted', 'shape': [len(grid), len(grid[0])]})
    report = {**source_identity(gen, source, sha),
              'build_command': {'cwd': str(Path.cwd()), 'argv': sys.argv, 'exit_code': 0},
              'declared_axes': gen.AXES, 'records': records,
              'override_recipe': {'seed': 12345, 'sample_index': 7, 'difficulty': 'medium'},
              'baseline_grid_sha256': digest(base), 'baseline_self_check': gen.self_check(base, difficulty='medium'),
              'baseline_colors': sorted({v for row in base for v in row if v != 0}),
              'ignored_override_calls': noops, 'declared_valid_rejections': rejected,
              'summary': {'canonical_labeled_pairs': len(pairs), 'generated_inputs': 12,
                          'outside_domain_guard_inputs': 2, 'racket_batch_inputs': len(inputs),
                          'ignored_override_calls': len(noops), 'declared_valid_override_calls': len(rejected)}}
    (HERE / 'input.json').write_text(json.dumps({'inputs': inputs}, separators=(',', ':')) + '\n')
    (HERE / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'source': source_identity(gen, source, sha), 'summary': report['summary'],
                      'baseline_grid_sha256': report['baseline_grid_sha256'],
                      'all_ignored_controls_identical': all(p['same_as_baseline'] and not p['self_check'] for p in noops),
                      'declared_valid_rejections': rejected}, indent=2))


def verify(gen, source, sha):
    report = json.loads((HERE / 'probe.json').read_text())
    receipt = json.loads((HERE / 'racket.json').read_text())
    assert report['generator_sha256'] == receipt['generator_sha256'] == sha
    assert receipt['rule_hash_matches_catalog'] is True
    assert receipt['executed_rule_hash'] == report['canonical_normalized_rule_hash']
    assert len(receipt['results']) == len(report['records']) == 19
    for record, result in zip(report['records'], receipt['results']):
        assert result['error'] is None
        assert result['output'] == record['expected_output'], record['input_index']
    valid = report['records'][:17]
    guards = report['records'][17:]
    assert all(not record['self_check'] and record['unguarded_matches_mirror'] for record in valid)
    assert all(record['self_check'] and not record['unguarded_matches_mirror'] for record in guards)
    assert all(p['same_as_baseline'] and not p['self_check'] for p in report['ignored_override_calls'])
    assert all(p['status'] == 'rejected' for p in report['declared_valid_rejections'])
    validation = {**source_identity(gen, source, sha),
                  'verify_command': {'cwd': str(Path.cwd()), 'argv': sys.argv, 'exit_code': 0},
                  'apply_command': {'cwd': receipt['cwd'], 'argv': receipt['command'], 'exit_code': 0},
                  'executed_rule_hash': receipt['executed_rule_hash'],
                  'apply_rule_text_sha256': receipt['rule_text_sha256'],
                  'rule_hash_matches_catalog': receipt['rule_hash_matches_catalog'],
                  'racket_outputs_matching_independent_mirror': 19,
                  'racket_batch_inputs': 19, 'valid_domain_rule_disagreements': 0,
                  'unguarded_rival_canonical_matches': 5, 'unguarded_rival_generated_matches': 12,
                  'unguarded_rival_outside_domain_disagreements': 2,
                  'domain_statuses': [r.get('generator_domain') for r in receipt['results']],
                  'input_file_sha256': hashlib.sha256((HERE / 'input.json').read_bytes()).hexdigest(),
                  'racket_file_sha256': hashlib.sha256((HERE / 'racket.json').read_bytes()).hexdigest(),
                  'scope': 'Bounded checks; no semantic failure found among accepted inputs. API contract defects reproduced. Guard shortcut is untested by normal scenes and differs only on these outside-self_check-domain inputs.'}
    (HERE / 'verification.json').write_text(json.dumps(validation, indent=2) + '\n')
    print(json.dumps(validation, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['build', 'verify'])
    args = parser.parse_args()
    gen, source, sha = load_selected_generator(TASK, root=ROOT)
    assert sha == EXPECTED_SHA256, (sha, EXPECTED_SHA256)
    (build if args.mode == 'build' else verify)(gen, source, sha)

if __name__ == '__main__':
    main()
