"""Replay one finite assembled-lesson ambiguity through protected Racket."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PACKET_WORK = next(parent for parent in Path(__file__).resolve().parents
                   if (parent / 'repo/shared/runtime/reviewer_support.py').is_file())
ROOT = PACKET_WORK / 'repo'
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]
sys.dont_write_bytecode = True
from arcpuzzles.parametric_worker import _grid, _real_evaluator
from reviewer_support import canonical_path, load_selected_generator, public_challenge_bytes, public_challenge_id

TASK_ID = 'c9b2eae14052'
EXPECTED_SOURCE = 'eabe4c07ccc507e4e27d90a43d735aef25c2b07bb0b63899926ade0ca92615ea'
RIVAL = '''(rule!
  (for/fold ((out (empty-grid (rows g) (cols g) 0)))
            ((obj (in-list (objects g 0))))
    (let* ((cells (obj-cells obj))
           (edge (for/or ((p (in-list cells)))
                   (or (= (first p) 0) (= (first p) (- (rows g) 1))
                       (= (second p) 0) (= (second p) (- (cols g) 1)))))
           (corner (for/or ((p (in-list cells)))
                     (and (or (= (first p) 0) (= (first p) (- (rows g) 1)))
                          (or (= (second p) 0) (= (second p) (- (cols g) 1)))))))
      (if (and edge (not corner))
          (paint-cells out cells (obj-color obj)) out))))'''


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise ValueError('evidence destination must be new')
    out.mkdir(parents=True)
    module, source, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    if source_hash != EXPECTED_SOURCE:
        raise ValueError('the source has changed; this witness needs fresh review')
    authorities = {json.loads(line)['program_solution']
                   for line in canonical_path(ROOT).read_text().splitlines()
                   if json.loads(line).get('task_id') == TASK_ID}
    if len(authorities) != 1:
        raise ValueError('selected canonical authority is ambiguous')
    program, = authorities
    grids = [module.generate(14, i, difficulty='medium') for i in range(4)]
    validators = [module.self_check(grid) for grid in grids]
    if any(validators):
        raise ValueError(f'generated inputs are not lawful: {validators}')
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        truth = [_grid(apply(program, grid)) for grid in grids]
        rival = [_grid(apply(RIVAL, grid)) for grid in grids]
    finally:
        bridge.close()
    mirrors = [module.rule_mirror(grid) for grid in grids]
    pairs = [{'input': grid, 'output': output} for grid, output in zip(grids, truth)]
    matches = [a == b for a, b in zip(truth, rival)]
    hook = module.lesson_identifiable(pairs[:3], pairs[3])
    changed = [[r,c] for r in range(len(grids[3])) for c in range(len(grids[3][0]))
               if truth[3][r][c] != rival[3][r][c]]
    features = []
    for grid in grids:
        corners = {(0,0), (0,len(grid[0])-1), (len(grid)-1,0), (len(grid)-1,len(grid[0])-1)}
        features.append([{'color': obj['color'], 'cells': obj['cells'],
                          'border_count': obj['border_count'],
                          'contains_literal_corner': bool(corners & set(obj['cells']))}
                         for obj in module._analysis(grid)['records']])
    successful = (matches == [True,True,True,False] and truth == mirrors and hook == []
                  and sha(source.read_bytes()) == EXPECTED_SOURCE)
    report = {'schema': 'arcpuzzles-bounded-peer-lesson-audit-v1',
              'status': 'verified_finding' if successful else 'failed_reproduction',
              'task_id': TASK_ID, 'source_sha256': source_hash, 'declared_rule_hash': module.RULE_HASH,
              'canonical_program_sha256': sha(program.encode()), 'rival_program_sha256': sha(RIVAL.encode()),
              'probe_sha256': sha(Path(__file__).read_bytes()),
              'recipe': {'seed': 14, 'difficulty': 'medium', 'demo_indices': [0,1,2], 'query_index': 3},
              'racket': identity, 'racket_evaluations': 8, 'validator_results': validators,
              'python_mirror_matches_racket': truth == mirrors, 'rival_matches_truth': matches,
              'existing_lesson_identifiable': hook, 'differing_query_cells': changed,
              'scope': 'One three-demo generated lesson and one generated query; one additional finite rival.',
              'finding': 'Keeping border objects without literal corner pixels fits all demos but retains a two-border L on the query.',
              'remaining': ['The generator and its declared lesson rivals remain unchanged.',
                            'No prevalence, learner performance, complete rival search, battery, or approval assessment was run.']}
    witness = {'train': pairs[:3], 'test': [pairs[3]], 'canonical_program': program,
               'rival_program': RIVAL, 'rival_outputs': rival, 'features': features,
               'source_sha256': source_hash, 'recipe': report['recipe']}
    (out / 'report.json').write_bytes(raw(report))
    (out / 'witness.private.json').write_bytes(raw(witness))
    (out / 'canonical.rkt').write_text(program)
    (out / 'rival.rkt').write_text(RIVAL)
    challenge = {'train': pairs[:3], 'test': [{'input': grids[3]}]}
    public = out / 'public'
    public.mkdir()
    (public / (public_challenge_id(challenge)+'.json')).write_bytes(public_challenge_bytes(challenge))
    print(json.dumps({'status': report['status'], 'matches': matches, 'differing_query_cells': changed,
                      'existing_lesson_identifiable': hook, 'source_sha256': source_hash,
                      'canonical_program_sha256': report['canonical_program_sha256'],
                      'report': str(out/'report.json')}, sort_keys=True))
    return 0 if successful else 1


if __name__ == '__main__':
    raise SystemExit(main())
