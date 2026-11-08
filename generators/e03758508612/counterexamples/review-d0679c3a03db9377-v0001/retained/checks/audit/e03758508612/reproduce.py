"""Focused fixed-geometry shortcut audit. Run via the supported packet wrapper.
prepare writes exact inputs; verify consumes public arcpuzzles apply labels.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
WORK = next(p for p in HERE.parents if (p / 'repo' / 'generators').is_dir())
SOURCE = WORK / 'repo/generators/e03758508612/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def midpoint_rival(grid):
    """Do not parse walls/connectivity: assign rooms by coordinate midpoints.
    Wall pixels are copied, but neither their arrangement nor connectivity
    contributes to grouping or winner selection.
    """
    h, w = len(grid), len(grid[0])
    rank = {v: i for i, v in enumerate(grid[0][:3])}
    out = [row[:] for row in grid]
    groups = {}
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] != 8:
                groups.setdefault((r >= h // 2, c >= w // 2), []).append((r, c))
    for cells in groups.values():
        colors = {grid[r][c] for r, c in cells if grid[r][c] in rank}
        if colors:
            winner = min(colors, key=rank.get)
            for r, c in cells:
                out[r][c] = winner
    return out


def prepare():
    canonical = json.loads((HERE / 'canonical.json').read_text())
    cases = []
    for difficulty in ('easy', 'medium', 'hard'):
        for index in range(4):
            grid = generator.generate(17, index, difficulty=difficulty)
            cases.append({'name': f'{difficulty}-17-{index}', 'seed': 17,
                          'sample_index': index, 'difficulty': difficulty,
                          'overrides': {}, 'input': grid,
                          'self_check_errors': generator.self_check(grid, difficulty=difficulty)})
    pair = canonical['variants'][0]['train'][3]
    cases.append({'name': 'canonical-variant-0-train-3', 'seed': None,
                  'sample_index': None, 'difficulty': None, 'overrides': {},
                  'origin': 'canonical variant 0, train pair index 3 (zero based)',
                  'input': pair['input'], 'canonical_output': pair['output'],
                  'self_check_errors': generator.self_check(pair['input'])})
    for case in cases:
        case['input_sha256'] = digest(case['input'])
        case['shape'] = [len(case['input']), len(case['input'][0])]
        case['rival_output'] = midpoint_rival(case['input'])
    record = {'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'canonical_rule_hash': canonical['rule_hash'], 'cases': cases}
    (HERE / 'cases.json').write_text(json.dumps(record, indent=2) + '\n')
    (HERE / 'input.json').write_text(json.dumps({'inputs': [c['input'] for c in cases]}, separators=(',', ':')) + '\n')
    assert all(not c['self_check_errors'] for c in cases[:-1])
    assert cases[-1]['self_check_errors'] == ['expected 4 chambers below legend, got 2']
    print('Prepared 12 accepted generated cases and 1 canonical two-room counterexample.')


def verify():
    cases = json.loads((HERE / 'cases.json').read_text())
    labels = json.loads((HERE / 'racket.json').read_text())
    assert labels['rule_hash_matches_catalog']
    assert labels['executed_rule_hash'] == cases['canonical_rule_hash']
    assert labels['generator_sha256'] == cases['generator_sha256']
    rows = []
    for case, result in zip(cases['cases'], labels['results'], strict=True):
        assert result['output'] is not None
        assert result['input'] == case['input']
        diff = [[r, c, case['rival_output'][r][c], result['output'][r][c]]
                for r in range(len(case['input']))
                for c in range(len(case['input'][0]))
                if case['rival_output'][r][c] != result['output'][r][c]]
        rows.append({'name': case['name'], 'self_check_errors': case['self_check_errors'],
                     'rival_matches_racket': not diff, 'difference_count': len(diff),
                     'first_difference': diff[0] if diff else None})
        if 'canonical_output' in case:
            assert result['output'] == case['canonical_output']
    assert all(r['rival_matches_racket'] for r in rows[:-1])
    assert not rows[-1]['rival_matches_racket']
    report = {'finding': 'Fixed 2x2 geometry permits a midpoint room rival that omits wall parsing.',
              'generator_sha256': cases['generator_sha256'],
              'canonical_rule_hash': cases['canonical_rule_hash'],
              'generated_authoritative_matches': 12, 'generated_domain_accepted': 12,
              'canonical_authoritative_mismatches': 1, 'checks': rows,
              'scope': 'Finite Racket check of 12 cases. Universal generated agreement follows from fixed source chamber construction; no claim of exhaustive runtime sampling.'}
    (HERE / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def shifted_prepare():
    grid = generator.generate(17, 3, difficulty='easy')
    original = [row[:] for row in grid]
    middle = len(grid[0]) // 2
    changes = []
    for r in range(2, len(grid) - 1):
        if all(v == 8 for v in grid[r]):
            continue
        assert grid[r][middle] == 8 and grid[r][middle + 1] == 0
        grid[r][middle] = 0
        grid[r][middle + 1] = 8
        changes.extend([[r, middle, 8, 0], [r, middle + 1, 0, 8]])
    errors = generator.self_check(grid, difficulty='easy')
    assert not errors
    record = {'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'canonical_rule_hash': json.loads((HERE / 'canonical.json').read_text())['rule_hash'],
              'seed': 17, 'sample_index': 3, 'difficulty': 'easy', 'overrides': {},
              'mutation': 'Move the internal vertical divider from col 5 to col 6 on rows 2,3,5,6; keep all seeds, legend and horizontal walls.',
              'changes': changes, 'input': grid, 'input_sha256': digest(grid),
              'original_input_sha256': digest(original), 'self_check_errors': errors,
              'rival_output': midpoint_rival(grid)}
    (HERE / 'shifted-case.json').write_text(json.dumps(record, indent=2) + '\n')
    (HERE / 'shifted-input.json').write_text(json.dumps(grid, separators=(',', ':')) + '\n')
    print('Shifted divider counterfactual is accepted by selected generator.self_check: [].')


def shifted_verify():
    case = json.loads((HERE / 'shifted-case.json').read_text())
    labels = json.loads((HERE / 'shifted-racket.json').read_text())
    assert labels['rule_hash_matches_catalog']
    assert labels['executed_rule_hash'] == case['canonical_rule_hash']
    assert labels['generator_sha256'] == case['generator_sha256']
    result = labels['results'][0]
    assert result['input'] == case['input'] and result['output'] is not None
    differences = [[r, c, case['rival_output'][r][c], result['output'][r][c]]
                   for r in range(len(case['input']))
                   for c in range(len(case['input'][0]))
                   if case['rival_output'][r][c] != result['output'][r][c]]
    assert differences == [[2, 5, 7, 6], [3, 5, 7, 6]]
    report = {'generator_sha256': case['generator_sha256'],
              'canonical_rule_hash': case['canonical_rule_hash'],
              'domain_acceptance': 'selected generator.self_check returned []',
              'reference_success': True, 'rival_matches_racket': False,
              'differences_row_col_rival_racket': differences,
              'input_sha256': case['input_sha256'],
              'qualification': 'Hand-made accepted counterfactual derived from seed 17/index 3/easy, not claimed to be reachable from unmodified generation.'}
    (HERE / 'shifted-summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'verify', 'shifted-prepare', 'shifted-verify'))
    args = parser.parse_args()
    {'prepare': prepare, 'verify': verify, 'shifted-prepare': shifted_prepare, 'shifted-verify': shifted_verify}[args.mode]()
