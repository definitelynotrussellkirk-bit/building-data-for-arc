#!/usr/bin/env python3
"""Bounded, source-bound optional peer review; no acceptance inference."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_path, canonical_pairs, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = '80271cb9b303'
gen, source, digest = load_selected_generator(TASK, root=ROOT)
rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get('task_id') == TASK]
assert len(rows) == 1
program = rows[0]['program_solution']

def cropped_margin(grid):
    """Keep leading zeros as a margin; infer period only on the occupied span."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        nz = [c for c, v in enumerate(row) if v]
        if not nz:
            continue
        left, right = nz[0], nz[-1]
        segment = row[left:right + 1]
        p = gen._minimal_row_period(segment, len(segment) - 1)
        out[r] = row[:left] + [segment[(c-left) % p] for c in range(left, len(row))]
    return out

def longest_repeated_period(grid):
    """Prefer the longest compatible period that still exposes a repetition."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        nz = [c for c, v in enumerate(row) if v]
        if not nz:
            continue
        right = nz[-1]
        periods = [p for p in range(1, right + 1)
                   if all(row[c] == row[c % p] for c in range(right + 1))]
        p = max(periods) if periods else right + 1
        out[r] = [row[c % p] for c in range(len(row))]
    return out

rivals = {'cropped_margin': cropped_margin, 'longest_repeated_period': longest_repeated_period}
report = {'schema': 'bounded-peer-review-v1', 'assignment_id': 'review-7b6e9833ed831a81',
          'task_id': TASK, 'generator_sha256': digest,
          'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'rule_exact_sha256': hashlib.sha256(program.encode()).hexdigest(),
          'rule_normalized_hash': hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12],
          'scope': {'seeds': [0, 31], 'sample_indices': [0, 5], 'difficulty': 'medium',
                    'three_demo_cyclic_starts': [0, 1, 2]},
          'generated_grids': 0, 'lesson_windows': 0, 'grammar_failures': [],
          'declared_lesson_failures': [], 'harmful_survivals': {k: 0 for k in rivals},
          'demo_survivals': {k: 0 for k in rivals}, 'witnesses': {}}
sampled = []
for seed in range(32):
    pairs = []
    for i in range(6):
        grid = gen.generate(seed, i, difficulty='medium')
        errors = gen.self_check(grid)
        if errors:
            report['grammar_failures'].append({'seed': seed, 'sample_index': i, 'errors': errors})
        pairs.append({'input': grid, 'output': gen._solve_true(grid)})
        report['generated_grids'] += 1
    if not sampled:
        sampled = pairs
    for start in range(3):
        demos, query = pairs[start:start+3], pairs[start+3]
        report['lesson_windows'] += 1
        errors = gen.lesson_identifiable(demos, query)
        if errors:
            report['declared_lesson_failures'].append({'seed': seed, 'start': start, 'errors': errors})
        for name, rival in rivals.items():
            if not all(rival(pair['input']) == pair['output'] for pair in demos):
                continue
            report['demo_survivals'][name] += 1
            wrong = rival(query['input'])
            if wrong != query['output']:
                report['harmful_survivals'][name] += 1
                report['witnesses'].setdefault(name, {'seed': seed, 'start_sample_index': start,
                    'difficulty': 'medium', 'demos': demos, 'query': query, 'rival_query_output': wrong})

canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
report['canonical_rival_match_vectors'] = {
    name: [rival(pair['input']) == pair['output'] for pair in canonical] for name, rival in rivals.items()}
native_pairs = [('canonical', i, pair) for i, pair in enumerate(canonical)]
if report['witnesses']:
    for name, witness in report['witnesses'].items():
        native_pairs.extend((name, i, pair) for i, pair in enumerate([*witness['demos'], witness['query']]))
else:
    native_pairs.extend(('generated_seed_0_medium', i, pair) for i, pair in enumerate(sampled))
assert len(native_pairs) <= 20
report['native_checks'] = []
with RacketBridge(timeout=10) as bridge:
    report['runtime_identity'] = bridge.runtime_identity
    for context, index, pair in native_pairs:
        literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in pair['input']) + ')'
        actual = bridge.eval_text(f'({wrap_rule(program)} {literal})')
        report['native_checks'].append({'context': context, 'index': index,
            'matches_expected': actual == pair['output'],
            'input_sha256': hashlib.sha256(json.dumps(pair['input']).encode()).hexdigest(),
            'actual_output': actual})
report['native_execution_count'] = len(report['native_checks'])
report['native_parity_passed'] = all(r['matches_expected'] for r in report['native_checks'])
report['outcome'] = 'finding' if report['witnesses'] else 'no_findings_in_bounded_scope'
report['limitations'] = ['Finite 32-seed medium-band search over two undeclared rivals only.',
    'No broad battery, parametric qualification, or universal identifiability claim.',
    'Generator, rule, and evidence index were not edited.']
path = Path(__file__).with_name('result.json')
path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: report[k] for k in ['outcome', 'generated_grids', 'lesson_windows',
    'demo_survivals', 'harmful_survivals', 'native_execution_count', 'native_parity_passed']}, indent=2))
assert report['native_parity_passed']
