"""Bounded source-pinned overlap-precedence learnability witness.

Run from the packet root:
WORK/.venv/bin/python review.py run python3 ../checks/a1ece4864521/probe.py
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / 'repo'
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]
from reviewer_support import load_selected_generator
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator

TASK = 'a1ece4864521'
PIN = 'd8bbc51697a0c549a159bec7ff97c49f494c3e445280106e377d02d59cd1ae28'
COMMAND = 'WORK/.venv/bin/python review.py run python3 ../checks/a1ece4864521/probe.py'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def overlaps(module, grid):
    marks = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value != module._clean_value(r, c)]
    cells = []
    for r, c, value in marks:
        cells.append({(rr, cc) for rr in range(r + 1, min(r + 5, len(grid)))
                      for cc in range(c + 1, min(c + 5, len(grid[0])))
                      if module._clean_value(rr, cc) == 0})
    conflicts = []
    for i, left in enumerate(cells):
        for j in range(i + 1, len(cells)):
            shared = sorted(left & cells[j])
            if shared and marks[i][2] != marks[j][2]:
                conflicts.append({'markers': [marks[i], marks[j]], 'shared_clean_zero_cells': shared})
    return conflicts


def main():
    module, source, source_hash = load_selected_generator(TASK, root=ROOT)
    assert source_hash == PIN, (source_hash, PIN)
    variants = Catalog(ROOT)._variants()[TASK]
    assert len({v['program_solution'] for v in variants}) == 1
    canonical = variants[0]['program_solution']
    needle = '\n                     anoms)))))'
    assert canonical.count(needle) == 1
    rival = canonical.replace(needle, '\n                     (reverse anoms))))))')
    (OUT / 'canonical.rkt').write_text(canonical)
    (OUT / 'rival_reverse_precedence.rkt').write_text(rival)
    chosen = None
    examined = 0
    for seed in range(32):
        grids = [module.generate(seed, index) for index in range(4)]
        examined += 4
        overlap_rows = [overlaps(module, grid) for grid in grids]
        if not any(overlap_rows[:3]) and overlap_rows[3]:
            chosen = seed, grids, overlap_rows
            break
    result = {
        'schema': 'bounded-peer-learnability-v1', 'task_id': TASK,
        'generator_sha256': source_hash, 'generator_path': str(source.relative_to(ROOT)),
        'actual_command': COMMAND, 'payload_cwd': str(Path.cwd()),
        'rival': 'Earlier row-major anomaly wins on overlapping clean-zero cells; canonical later anomaly wins.',
        'search': {'seed_range': [0, 31], 'sample_indices': [0, 1, 2, 3],
                   'difficulty': None, 'overrides': {}, 'draws_examined': examined},
        'source_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [source, ROOT / 'shared/runtime/reviewer_support.py',
                                    ROOT / 'src/arcpuzzles/parametric_worker.py',
                                    ROOT / 'shared/runtime/arc_repl/racket_bridge.py']},
        'program_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
        'rival_program_sha256': hashlib.sha256(rival.encode()).hexdigest(),
        'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limits': 'One named overlap-order rival; at most 32 default seeds with four generated inputs each. No full battery or universal uniqueness claim. Structural witness selection is audit-only.'}
    if chosen is None:
        result.update(status='bounded_no_finding', reference_evaluations=0)
    else:
        seed, grids, overlap_rows = chosen
        apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
        evidence = []
        try:
            for index, grid in enumerate(grids):
                errors = module.self_check(grid)
                assert not errors, errors
                expected, observed = apply(canonical, grid), apply(rival, grid)
                differences = [[r, c, expected[r][c], observed[r][c]]
                               for r in range(len(grid)) for c in range(len(grid[0]))
                               if expected[r][c] != observed[r][c]]
                evidence.append({'split': 'train' if index < 3 else 'test',
                    'sample_index': index, 'input': grid, 'canonical_output': expected,
                    'rival_output': observed, 'input_sha256': digest(grid),
                    'canonical_output_sha256': digest(expected), 'rival_output_sha256': digest(observed),
                    'differences': differences, 'overlaps': overlap_rows[index],
                    'self_check_errors': errors})
                print(json.dumps({'sample_index': index, 'differing_cells': len(differences)}), flush=True)
        finally:
            bridge.close()
        assert all(not row['differences'] for row in evidence[:3])
        assert evidence[3]['differences']
        challenge = {'train': [{'input': x['input'], 'output': x['canonical_output']} for x in evidence[:3]],
                     'test': [{'input': evidence[3]['input']}]}
        (OUT / 'challenge.public.json').write_text(json.dumps(challenge, indent=2) + '\n')
        (OUT / 'labels.private.json').write_text(json.dumps(evidence, indent=2) + '\n')
        result.update(status='counterexample', seed=seed, all_visible_demos_match=True,
            query_differs=True, query_differing_cells=len(evidence[3]['differences']),
            racket=identity, reference_evaluations=8, challenge_sha256=digest(challenge),
            evidence_files=['challenge.public.json', 'labels.private.json', 'canonical.rkt', 'rival_reverse_precedence.rkt'])
    (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
