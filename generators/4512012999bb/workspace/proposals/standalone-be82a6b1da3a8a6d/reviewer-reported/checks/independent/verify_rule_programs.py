#!/usr/bin/env python3
"""Independent, Racket-backed acceptance checks for the proposed tie policy."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--direct', required=True, type=Path)
    parser.add_argument('--mirror', required=True, type=Path)
    parser.add_argument('--canonical', default='shared/data/canonical/puzzles.jsonl', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Use a new evidence output path')
    task = next(json.loads(line) for line in args.canonical.read_text().splitlines()
                if json.loads(line).get('task_id') == '4512012999bb')
    programs = {'direct': args.direct.read_text(), 'mirror': args.mirror.read_text()}
    original = task['program_solution']
    selector = '(let ((flip? (> (score #t) (score #f))))'
    assert original.count(selector) == 1
    assert programs['direct'] == original, 'Default must preserve exact canonical text'
    assert programs['mirror'] == original.replace(selector, selector.replace('> ', '>= ')), 'Only the tie comparator may change'
    from arc_repl.racket_bridge import RacketBridge
    records = []
    with RacketBridge(timeout=30.0) as bridge:
        def execute(setting, grid):
            literal = '(' + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
            return bridge.eval_text('((let ((rule! (lambda (f) f))) ' + programs[setting] + ") '" + literal + ')')
        for index, pair in enumerate(task['train'] + task['test']):
            if 'output' not in pair:
                continue
            actual = execute('direct', pair['input'])
            assert actual == pair['output'], ('canonical', index)
            records.append({'case': 'canonical', 'index': index, 'passed': True})
        # These expected outputs are hand-constructed, without calling the
        # prototype's sampler, score function, or Python implementation.
        cases = [
            ('positive_score_tie', [[2, 1, 0, 0], [3, 0, 0, 5]], False, True),
            ('zero_score_tie', [[3, 0, 5, 0], [0, 5, 0, 3]], False, True),
            ('strict_direct', [[2, 2, 1, 0], [3, 0, 0, 5]], False, False),
            ('strict_mirror', [[1, 1, 2, 0], [3, 0, 0, 5]], True, True),
            ('symmetric_tie_is_uninformative', [[2, 0, 0, 2], [3, 5, 5, 3]], False, True),
        ]
        for name, crop, direct_flip, mirror_flip in cases:
            grid = [[0] * 15 for _ in range(7)]
            for offset, (left, right) in enumerate(zip([4, 2, 2, 4], [4, 1, 1, 4])):
                grid[offset + 1][1] = left
                grid[offset + 1][6] = right
            for r, row in enumerate(crop):
                grid[r + 2][9:13] = row
            outputs = {}
            for setting, flip in [('direct', direct_flip), ('mirror', mirror_flip)]:
                expected = [[4, 0, 0, 0, 0, 4]]
                expected += [[2, *(row[::-1] if flip else row), 1] for row in crop]
                expected += [[4, 0, 0, 0, 0, 4]]
                actual = execute(setting, grid)
                assert actual == expected, (name, setting, actual, expected)
                outputs[setting] = actual
            distinguishable = outputs['direct'] != outputs['mirror']
            assert distinguishable == (name in {'positive_score_tie', 'zero_score_tie'})
            records.append({'case': name, 'input': grid, 'outputs': outputs,
                            'policies_disagree': distinguishable, 'passed': True})
        identity = bridge.runtime_identity
    result = {'schema': 'independent-tie-policy-check-v1', 'task_id': '4512012999bb',
              'canonical_file_sha256': sha(args.canonical.read_bytes()),
              'program_sha256': {k: sha(v.encode()) for k, v in programs.items()},
              'runtime': identity, 'checks_passed': len(records), 'records': records,
              'scope': 'Five canonical pairs and five hand-built cases; not a production battery or a complete rival search.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': len(records), 'canonical_pairs': 5, 'independent_cases': 5}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
