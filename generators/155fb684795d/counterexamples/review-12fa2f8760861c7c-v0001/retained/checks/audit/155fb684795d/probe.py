#!/usr/bin/env python3
"""Reproduce a raw-shape tie-break lesson ambiguity without changing the target.

All cohort labels are Python diagnostics. The separate supported public apply
command labels input.json through the selected Racket authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
OUT = HERE.parent
for ancestor in HERE.parents:
    located = next(((tree, path) for tree in (ancestor / 'repo', ancestor)
                    for path in (tree / 'shared/runtime/reviewer_support.py', tree / 'reviewer_support.py')
                    if path.is_file()), None)
    if located is not None:
        tree, support = located
        sys.path.insert(0, str(support.parent))
        break
else:
    raise RuntimeError('Cannot find the local reviewer support runtime')

from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(tree)
TASK_ID = '155fb684795d'
SOURCE = ROOT / 'generators' / TASK_ID / 'generator.py'
if not SOURCE.is_file():
    SOURCE = ROOT / 'puzzle_generators/per_puzzle' / TASK_ID / 'generator.py'


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def normalize(cells):
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return tuple(sorted((r-r0, c-c0) for r, c in cells))


def raw_key(cells):
    forms = []
    for swap in (False, True):
        for sr in (-1, 1):
            for sc in (-1, 1):
                forms.append(normalize([(sr * (c if swap else r), sc * (r if swap else c))
                                        for r, c in cells]))
    return min(forms)


def panel_cells(grid):
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = [-1] + separators + [w]
    return [[(r, c-left-1) for r in range(h) for c in range(left+1, right) if grid[r][c]]
            for left, right in zip(bounds, bounds[1:]) if right > left+1]


def crop_eight(cells):
    cells = normalize(cells)
    out = [[0] * (max(c for r, c in cells)+1) for _ in range(max(r for r, c in cells)+1)]
    for r, c in cells:
        out[r][c] = 8
    return out


def rightmost_raw_unique(grid):
    """No dilation: among raw dihedral singleton shapes, choose the rightmost."""
    panels = panel_cells(grid)
    keys = [raw_key(cells) for cells in panels]
    counts = Counter(keys)
    candidates = [i for i, key in enumerate(keys) if counts[key] == 1]
    if not candidates:
        raise ValueError('No raw-unique candidate in this input')
    chosen = candidates[-1]
    return crop_eight(panels[chosen]), candidates, chosen


def load():
    spec = importlib.util.spec_from_file_location('audited_155fb684795d', SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=10)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds must be positive')
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    gen = load()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_fits = [rightmost_raw_unique(pair['input'])[0] == pair['output'] for pair in pairs]
    assert all(canonical_fits)
    rule_hashes = set()
    for line in canonical_path(ROOT).open():
        row = json.loads(line)
        if row.get('task_id') == TASK_ID:
            rule_hashes.add(hashlib.sha256(' '.join(row['program_solution'].split()).encode()).hexdigest()[:12])
    assert rule_hashes == {gen.RULE_HASH}

    seed, band, indices = 0, 'easy', [2, 3, 4, 5]
    inputs = [gen.generate(seed, i, difficulty=band) for i in indices]
    outputs = [gen.rule_mirror(grid) for grid in inputs]
    rival_details = [rightmost_raw_unique(grid) for grid in inputs]
    rivals = [value[0] for value in rival_details]
    validator_errors = [gen.self_check(grid) for grid in inputs]
    matches = [truth == rival for truth, rival in zip(outputs, rivals)]
    assert validator_errors == [[], [], [], []]
    assert matches == [True, True, True, False]
    assert len({grid_hash(grid) for grid in inputs}) == 4
    lesson = [{'input': grid, 'output': out} for grid, out in zip(inputs, outputs)]
    hook_reasons = gen.lesson_identifiable(lesson[:3], lesson[3])
    assert hook_reasons == []

    counts = Counter()
    per_band = {}
    seen = set()
    for difficulty in ('easy', 'medium', 'hard'):
        local = Counter()
        for cohort_seed in range(args.seeds):
            grids = [gen.generate(cohort_seed, i, difficulty=difficulty) for i in range(7)]
            truth = [gen.rule_mirror(grid) for grid in grids]
            rival = [rightmost_raw_unique(grid)[0] for grid in grids]
            for i, grid in enumerate(grids):
                assert gen.self_check(grid) == []
                assert (rival[i] == truth[i]) == (i % 4 != 1)
                seen.add(grid_hash(grid))
            local['generated_pairs'] += len(grids)
            for start in range(4):
                flags = [rival[i] == truth[i] for i in range(start, start+4)]
                local['windows'] += 1
                local['ordered_ambiguities'] += int(flags == [True, True, True, False])
                for query in range(4):
                    local['rotations'] += 1
                    local['ambiguous_rotations'] += int(not flags[query] and all(v for i, v in enumerate(flags) if i != query))
        counts.update(local)
        per_band[difficulty] = dict(local)
    assert counts['ambiguous_rotations'] == counts['windows']
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha

    write('input.json', inputs)
    write('rival.json', rivals)
    write('query_input.json', inputs[-1])
    write('query_rival.json', rivals[-1])
    write('diagnostic_outputs.json', outputs)
    write('lesson.json', {'train': lesson[:3], 'test': [lesson[3]]})
    report = {
        'task_id': TASK_ID, 'source_path': str(SOURCE), 'generator_sha256': source_sha,
        'rule_hash': gen.RULE_HASH, 'source_version': gen.VERSION,
        'finding': 'Canonical-fit rightmost-raw-unique tie breaker survives three generated demos and disagrees on their query',
        'rival': 'Compare original raw dihedral shapes; choose the rightmost panel whose raw shape occurs exactly once; crop that original object in 8',
        'uses_plus_growth': False, 'canonical_labeled_pairs': len(pairs),
        'canonical_rival_matches': canonical_fits,
        'canonical_pair_ids': [{k: pair[k] for k in ('variant', 'split', 'pair_index')} for pair in pairs],
        'witness': {'seed': seed, 'difficulty': band, 'overrides': {},
                    'sample_indices': indices, 'demo_indices': indices[:3], 'query_index': indices[3],
                    'query_pair_position': 3, 'input_hashes': [grid_hash(g) for g in inputs],
                    'validator_errors': validator_errors, 'native_lesson_hook_reasons': hook_reasons,
                    'raw_unique_candidates': [detail[1] for detail in rival_details],
                    'rival_chosen_panels': [detail[2] for detail in rival_details],
                    'true_odd_panels': [gen.observe_overrides(grid)['odd_index'] for grid in inputs],
                    'diagnostic_agreements': matches,
                    'domain_status': 'All four inputs are direct ordinary generate outputs with no overrides, pass self_check, are distinct and inside the documented four-panel manifold'},
        'bounded_cohort': {'seeds': [0, args.seeds-1], 'bands': list(per_band), 'window_starts': [0,1,2,3],
                           'actual_pair_indices': list(range(7)), 'counts': dict(counts),
                           'per_band': per_band, 'unique_inputs': len(seen),
                           'labels': 'Python generator rule_mirror diagnostics; only input.json receives separate actual Racket labels',
                           'scope': 'Direct generator calls and exact holdouts, no production materializer or learned-model behavior'},
        'prior_audit': {'return_id': 'review-90dc3740fbd981e5:v0001', 'same_source': True,
                        'relationship': 'Adds direct 3-demo/query disagreement from a simple total tie breaker to the retained vocabulary-support finding'},
    }
    write('probe.json', report)
    print(json.dumps({'generator_sha256': source_sha, 'rule_hash': gen.RULE_HASH,
                      'canonical_fit': f'{sum(canonical_fits)}/{len(canonical_fits)}',
                      'witness_agreements': matches, 'native_hook': hook_reasons,
                      'cohort': dict(counts), 'unique_inputs': len(seen)}, sort_keys=True))


if __name__ == '__main__':
    main()
