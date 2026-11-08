#!/usr/bin/env python3
"""Bounded source-bound peer probe for row/column-only nesting-depth rivals.
Run from packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/df74e338b4f5/probe.py
"""
from pathlib import Path
import copy
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2] / 'repo'
sys.path[:0] = [str(ROOT / 'shared/runtime'), str(ROOT / 'src')]
from reviewer_support import load_selected_generator
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator

TASK = 'df74e338b4f5'
EXPECTED = 'c464c7b69ddbca31d8f58c27be9beeb4d4c15bf0f9ea0a70db3bb245bca429e9'
OUT = Path(__file__).resolve().parent

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def axis_rival(grid, axis, gen):
    # Preserve frame detection, but ignore one coordinate in containment.
    analysis = gen._analyze(grid)
    assert not analysis['errors']
    output = copy.deepcopy(grid)
    for marker in analysis['markers']:
        r, c = marker['r'], marker['c']
        if axis == 'row':
            output[r][c] = sum(r0 < r < r1 for r0, c0, r1, c1 in analysis['boxes'])
        else:
            output[r][c] = sum(c0 < c < c1 for r0, c0, r1, c1 in analysis['boxes'])
    return output

def main():
    gen, source, sha = load_selected_generator(TASK, root=ROOT)
    assert sha == EXPECTED, f'Source changed: {sha}'
    record = Catalog(ROOT).get(TASK)
    programs = {v['program_solution'] for v in record['variants']}
    assert len(programs) == 1
    program = programs.pop()
    normalized = ' '.join(program.split())
    rule_sha = hashlib.sha256(normalized.encode()).hexdigest()
    assert rule_sha[:12] == gen.RULE_HASH == record['rule_hash']
    rows, candidate, representatives = [], None, []
    # At most 72 ordinary five-pair windows, 360 source-produced inputs.
    for band in ('easy', 'medium', 'hard'):
        for seed in range(24):
            inputs = [gen.generate(seed, i, difficulty=band) for i in range(5)]
            outputs = [gen.rule_mirror(grid) for grid in inputs]
            assert all(not gen.self_check(grid) for grid in inputs)
            outcomes = {}
            for axis in ('row', 'column'):
                predicted = [axis_rival(grid, axis, gen) for grid in inputs]
                matches = [a == b for a, b in zip(predicted, outputs)]
                outcomes[axis] = matches
                if all(matches[:4]) and not matches[4] and candidate is None:
                    candidate = {'difficulty': band, 'seed': seed, 'sample_indices': list(range(5)),
                                 'rival': axis, 'inputs': inputs, 'predicted': predicted,
                                 'mirror_outputs': outputs}
            rows.append({'difficulty': band, 'seed': seed, 'indices': list(range(5)),
                         'input_sha256': [digest(x) for x in inputs], 'matches_mirror': outcomes})
            if seed == 0:
                representatives.append({'difficulty': band, 'seed': seed, 'inputs': inputs,
                                        'mirror_outputs': outputs})
            if candidate:
                break
        if candidate:
            break
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    checks = []
    try:
        targets = [candidate] if candidate else representatives
        for target in targets:
            outputs = [apply(program, grid) for grid in target['inputs']]
            assert outputs == target['mirror_outputs'], 'Racket/mirror mismatch'
            checks.append({'difficulty': target['difficulty'], 'seed': target['seed'],
                           'pairs': [{'input': grid, 'output': output} for grid, output in zip(target['inputs'], outputs)]})
            if candidate:
                assert all(candidate['predicted'][i] == outputs[i] for i in range(4))
                assert candidate['predicted'][4] != outputs[4]
                assert not gen.lesson_identifiable(checks[-1]['pairs'][:4], checks[-1]['pairs'][4])
    finally:
        bridge.close()
    case = None
    if candidate:
        case = {'task_id': TASK, 'source_sha256': sha, 'rule_sha256_normalized': rule_sha,
                'difficulty': candidate['difficulty'], 'seed': candidate['seed'],
                'sample_indices': candidate['sample_indices'], 'rival': candidate['rival'],
                'rival_definition': 'Count frames containing the marker coordinate on this axis; ignore the other coordinate.',
                'train': checks[0]['pairs'][:4], 'test': checks[0]['pairs'][4:],
                'rival_query_output': candidate['predicted'][4],
                'canonical_query_output': checks[0]['pairs'][4]['output'],
                'lesson_identifiable_reasons': []}
        (OUT / 'minimal-case.json').write_text(json.dumps(case, indent=2) + '\n')
    evidence = {'schema': 'bounded-peer-probe-v1', 'task_id': TASK,
                'source_path': str(source.relative_to(ROOT)), 'source_sha256': sha,
                'rule_hash': record['rule_hash'], 'rule_sha256_normalized': rule_sha,
                'rule_sha256_raw': hashlib.sha256(program.encode()).hexdigest(),
                'rivals': ['row_span_only', 'column_span_only'],
                'windows_checked': len(rows), 'python_mirror_pairs_checked': len(rows) * 5,
                'racket_pairs_checked': sum(len(x['pairs']) for x in checks),
                'runtime_identity': identity, 'finding': bool(candidate),
                'windows': rows, 'racket_evidence': checks,
                'limits': ['Finite seed range 0..23, four demos and query indices 0..4, three difficulty bands; stop at first witness.',
                           'Search labels use the selected Python mirror; only retained case or seed-zero representatives are checked in protected Racket.',
                           'Only two undeclared rivals checked. No battery, qualification, repair, approval, or parametric duty.']}
    (OUT / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({k: evidence[k] for k in ('task_id','source_sha256','rule_hash','windows_checked',
                       'python_mirror_pairs_checked','racket_pairs_checked','finding')}))

if __name__ == '__main__':
    main()
