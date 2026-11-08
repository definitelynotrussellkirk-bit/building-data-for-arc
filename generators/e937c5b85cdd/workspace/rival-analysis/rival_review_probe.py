"""Bounded, task-local baseline rival review; no generated Python label is called Racket.

Run from the packet repository (the wrapper supplies the protected Racket runtime):
  python ../run_with_racket.py python generators/e937c5b85cdd/workspace/rival-analysis/rival_review_probe.py

The generated census uses the existing Python reimplementation diagnostically.
An independently retained Catalog.apply receipt verifies explicit witnesses,
canonical scenes, D4 transforms, and selected ambiguous lessons through Racket.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]
from reviewer_support import canonical_pairs
from arcpuzzles import Catalog

TASK = 'e937c5b85cdd'
OUT = ROOT.parent / 'checks/rival-analysis'
SOURCE = (Path(__file__).parent / 'baseline_generator_snapshot.py')
SOURCE_HASH = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('rival_review_baseline_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
DIRS = {'up': (-1, 0), 'dn': (1, 0), 'lt': (0, -1), 'rt': (0, 1)}


def objects(grid):
    """Independent input-derived cross parser (distinct color is a task invariant)."""
    h, w = len(grid), len(grid[0])
    by_color = {}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] not in (6, 7):
                by_color.setdefault(grid[r][c], set()).add((r, c))
    result = []
    for color, cells in sorted(by_color.items()):
        centers = [(r, c) for r, c in cells
                   if all((r + dr, c + dc) in cells for dr, dc in DIRS.values())]
        assert len(centers) == 1, (color, centers)
        r, c = centers[0]
        arms = {}
        for direction, (dr, dc) in DIRS.items():
            length = 0
            while (r + dr * (length + 1), c + dc * (length + 1)) in cells:
                length += 1
            arms[direction] = length
        direction = max(arms, key=arms.get)
        assert list(arms.values()).count(arms[direction]) == 1
        result.append({'color': color, 'center': (r, c), 'arms': arms,
                       'direction': direction, 'cells': len(cells)})
    return result


def project(grid, variant='intended'):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for obj in objects(grid):
        if variant == 'six_cell_template' and obj['cells'] != 6:
            continue
        r, c = obj['center']
        direction = obj['direction']
        if direction in ('up', 'dn'):
            ends = ((0, c), (h - 1, c))
            paint = 1 if direction == 'up' else 0
            if variant == 'nearer_axis_border':
                paint = 0 if r <= h - 1 - r else 1
        else:
            ends = ((r, 0), (r, w - 1))
            paint = 1 if direction == 'lt' else 0
            if variant == 'nearer_axis_border':
                paint = 0 if c <= w - 1 - c else 1
        pr, pc = ends[paint]
        zr, zc = ends[1 - paint]
        out[pr][pc] = obj['color']
        out[zr][zc] = 0
    return out


RIVALS = ('nearer_axis_border', 'six_cell_template')


def wrong(grid, rival):
    return project(grid, rival) != gen._rule_output(grid)


def d4(grid, which):
    result = deepcopy(grid)
    if which >= 4:
        result = [list(reversed(row)) for row in result]
    for _ in range(which % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def hand_cross(longest=2):
    grid = [[6 if r in (0, 10) or c in (0, 10) else 7 for c in range(11)]
            for r in range(11)]
    r, c = 5, 6
    cells = {(r, c), (r - 1, c), (r + 1, c), (r, c - 1)}
    cells.update((r, c + x) for x in range(1, longest + 1))
    for rr, cc in cells:
        grid[rr][cc] = 2
    return grid


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = canonical_pairs(TASK, root=ROOT)
    distinct = list({json.dumps([p['input'], p['output']]): p for p in pairs}.values())
    report = {
        'task_id': TASK, 'source_sha256': SOURCE_HASH, 'version': gen.VERSION,
        'canonical_pair_occurrences': len(pairs), 'canonical_distinct_pairs': len(distinct),
        'canonical_fits': {name: sum(project(p['input'], name) == p['output'] for p in pairs)
                           for name in ('intended', *RIVALS)},
        'canonical_features': [{'identity': {k: p[k] for k in ('variant', 'split', 'pair_index')},
                                'objects': objects(p['input'])} for p in distinct],
        'diagnostic_label_source': 'existing generator._rule_output Python reimplementation; not Racket',
        'census_plan': '200 inputs per band: seed=0..199; sample_index=17*seed+1',
        'lesson_plan': '128 lessons per band: seed=0..127; indices=11*seed+[0,1,2,3]; first three demos, last query; all four query rotations also scored',
        'bands': {}, 'lessons': {},
    }
    ambiguous = []
    for band in ('easy', 'medium', 'hard'):
        counts = Counter()
        dirs = Counter()
        for seed in range(200):
            grid = gen.generate(seed, 17 * seed + 1, difficulty=band)
            assert not gen.self_check(grid)
            assert project(grid) == gen._rule_output(grid)
            counts['inputs'] += 1
            counts['strict_profile'] += gen.canonical_profile_signature(grid) in gen._CANONICAL_SIGNATURES
            counts['length3_present'] += any(o['cells'] == 7 for o in objects(grid))
            for rival in RIVALS:
                counts[f'{rival}_refuted'] += wrong(grid, rival)
            dirs.update(obj['direction'] for obj in objects(grid))
        report['bands'][band] = {'counts': dict(counts), 'object_direction_counts': dict(dirs)}
        lesson_counts = Counter()
        for seed in range(128):
            items = [gen.generate(seed, 11 * seed + offset, difficulty=band) for offset in range(4)]
            lesson_counts['lessons'] += 1
            for rival in RIVALS:
                wrongness = [wrong(grid, rival) for grid in items]
                lesson_counts[f'{rival}_original_ambiguous'] += not any(wrongness[:3]) and wrongness[3]
                lesson_counts[f'{rival}_rotated_ambiguous'] += sum(
                    wrongness[q] and not any(wrongness[j] for j in range(4) if j != q)
                    for q in range(4))
                lesson_counts[f'{rival}_survived_all'] += not any(wrongness)
                if sum(wrongness) == 1 and not any(a['rival'] == rival and a['band'] == band for a in ambiguous):
                    q = wrongness.index(True)
                    ambiguous.append({'rival': rival, 'band': band, 'seed': seed,
                                      'indices': [11 * seed + offset for offset in range(4)],
                                      'query_position': q, 'grids': items})
        report['lessons'][band] = dict(lesson_counts)
    # One public apply batch labels 5 bases x 8 transforms plus <=6 lessons x 4 pairs.
    bases = [{'name': f'canonical_distinct_{i}', 'grid': p['input'], 'expected': p['output']}
             for i, p in enumerate(distinct)]
    bases += [{'name': f'rightward_nearer_edge_arm{length}', 'grid': hand_cross(length)}
              for length in (2, 3)]
    apply_inputs = []
    identities = []
    for base in bases:
        assert not gen.self_check(base['grid'])
        for which in range(8):
            apply_inputs.append(d4(base['grid'], which))
            identities.append({'kind': 'd4', 'base': base['name'], 'transform': which})
    for item in ambiguous:
        for pos, grid in enumerate(item['grids']):
            apply_inputs.append(grid)
            identities.append({'kind': 'lesson', 'rival': item['rival'], 'band': item['band'],
                               'seed': item['seed'], 'sample_index': item['indices'][pos],
                               'is_query': pos == item['query_position']})
    assert len(apply_inputs) <= 64, len(apply_inputs)
    (OUT / 'python_diagnostics.json').write_text(json.dumps(report, indent=2) + '\n')
    receipt = Catalog(ROOT).apply(TASK, apply_inputs, reference='canonical', timeout=180)
    (OUT / 'public_apply_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (OUT / 'public_apply_input_identities.json').write_text(json.dumps(identities, indent=2) + '\n')
    errors = [r.get('error') for r in receipt['results'] if r.get('error') or r['output'] is None]
    assert not errors, errors
    report['racket'] = {
        'executed_rule_hash': receipt['executed_rule_hash'],
        'source_sha256_at_apply': receipt['generator_sha256'],
        'labeled_inputs': len(receipt['results']),
        'errors': errors,
        'python_agreement': sum(gen._rule_output(r['input']) == r['output'] for r in receipt['results']),
        'independent_python_agreement': sum(project(r['input']) == r['output'] for r in receipt['results']),
        'd4_commutation': [], 'witnesses': [], 'ambiguous_lessons': [],
    }
    for i, base in enumerate(bases):
        records = receipt['results'][8 * i:8 * i + 8]
        base_output = records[0]['output']
        report['racket']['d4_commutation'].append({
            'base': base['name'], 'transforms': 8,
            'commuting': sum(records[which]['output'] == d4(base_output, which) for which in range(8)),
        })
        if i >= len(distinct):
            report['racket']['witnesses'].append({
                'base': base['name'], 'apply_result_index': 8 * i,
                'self_check': gen.self_check(base['grid']),
                'rivals_refuted': [name for name in RIVALS if project(base['grid'], name) != base_output],
                'input': base['grid'], 'output_racket': base_output,
                'rival_outputs': {name: project(base['grid'], name) for name in RIVALS},
            })
    offset = len(bases) * 8
    for i, item in enumerate(ambiguous):
        records = receipt['results'][offset + 4 * i:offset + 4 * i + 4]
        fits = [project(r['input'], item['rival']) == r['output'] for r in records]
        q = item['query_position']
        report['racket']['ambiguous_lessons'].append({
            **{key: value for key, value in item.items() if key != 'grids'},
            'rival_fits': fits, 'demo_fits': sum(fits[j] for j in range(4) if j != q),
            'query_differs': not fits[q], 'apply_result_indices': list(range(offset + 4 * i, offset + 4 * i + 4)),
        })
    report['source_unchanged_through_probe'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
    (OUT / 'rival_review_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('task_id', 'source_sha256', 'version',
        'canonical_pair_occurrences', 'canonical_distinct_pairs', 'canonical_fits',
        'bands', 'lessons', 'source_unchanged_through_probe')}, indent=2))
    print(json.dumps({k: v for k, v in report['racket'].items() if k != 'witnesses'}, indent=2))


if __name__ == '__main__':
    main()
