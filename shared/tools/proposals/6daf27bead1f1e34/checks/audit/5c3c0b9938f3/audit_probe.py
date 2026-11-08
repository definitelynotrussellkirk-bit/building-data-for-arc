"""Read-only source-bound Python audit. No production labels or sources changed."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = '5c3c0b9938f3'
ROOT = find_root(__file__)
WORK = ROOT.parent
OUT = Path(__file__).resolve().parent
contract = json.loads((WORK / 'AUDIT_ASSIGNMENT.json').read_bytes())
assigned = next(row for row in contract['targets'] if row['task_id'] == TASK)
source = ROOT / f'generators/{TASK}/generator.py'
sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert sha == assigned['generator_sha256'], 'Assignment source binding differs'
GEN, loaded_source, loaded_sha = load_selected_generator(TASK, root=ROOT)
assert loaded_sha == sha and loaded_source == source


def reference(grid, *, only_six_blocks=False, vertical_only=False):
    """Literal Python translation of this task's canonical beam walks."""
    h, w = len(grid), len(grid[0])
    horiz, vert = set(), set()
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            directions = [(0, -1), (0, 1)] if color == 2 and not vertical_only else [(-1, 0), (1, 0)] if color == 3 else []
            target = horiz if color == 2 else vert
            for dr, dc in directions:
                rr, cc = r + dr, c + dc
                while 0 <= rr < h and 0 <= cc < w:
                    if grid[rr][cc] != 0:
                        if not only_six_blocks or grid[rr][cc] == 6:
                            break
                    else:
                        target.add((rr, cc))
                    rr, cc = rr + dr, cc + dc
    output = deepcopy(grid)
    for r, c in horiz | vert:
        output[r][c] = 4 if (r, c) in horiz and (r, c) in vert else 2 if (r, c) in horiz else 3
    return output


def emit(name, value):
    path = OUT / name
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    if path.exists() and path.read_bytes() != raw:
        raise ValueError('Refusing to replace different audit evidence: ' + name)
    if not path.exists():
        path.write_bytes(raw)


canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
assert len(canonical) == 4
assert all(reference(pair['input']) == pair['output'] for pair in canonical)
canonical_rival_fits = all(reference(pair['input'], only_six_blocks=True) == pair['output'] for pair in canonical)
assert canonical_rival_fits
population = {}
for band in ('easy', 'medium', 'hard'):
    counts = Counter()
    for i in range(200):
        grid = GEN.generate(7, i, difficulty=band)
        assert GEN.self_check(grid) == []
        colors = Counter(v for row in grid for v in row)
        output = reference(grid)
        counts['draws'] += 1
        counts['no_horizontal_emitter_2'] += colors[2] == 0
        counts['no_blocker_6'] += colors[6] == 0
        counts['no_crossing_label_4'] += not any(4 in row for row in output)
        counts['realized_color_count_' + str(len(colors))] += 1
        counts['only_six_rival_disagrees'] += reference(grid, only_six_blocks=True) != output
    population[band] = dict(counts)

lessons = {}
for rival_name, kwargs in [('only_color6_blocks', {'only_six_blocks': True}), ('vertical_only', {'vertical_only': True})]:
    found = None
    for seed in range(100):
        if found:
            break
        for start in range(20):
            pairs = []
            for index in range(start, start + 4):
                grid = GEN.generate(seed, index, difficulty='easy')
                pairs.append({'sample_index': index, 'input': grid, 'output': reference(grid),
                              'rival_output': reference(grid, **kwargs)})
            if all(p['output'] == p['rival_output'] for p in pairs[:3]) and pairs[3]['output'] != pairs[3]['rival_output']:
                found = {'seed': seed, 'difficulty': 'easy', 'start': start, 'n_train': 3,
                         'label_source': 'Python canonical translation; validated on all four canonical labels; not an authoritative generated Racket execution',
                         'rival': rival_name, 'rival_fits_all_canonical_labels': canonical_rival_fits if rival_name == 'only_color6_blocks' else False,
                         'pairs': pairs}
                break
    assert found is not None, rival_name
    emit('lesson-' + rival_name + '.json', {'task_id': TASK, 'generator_sha256': sha, **found})
    lessons[rival_name] = {'seed': found['seed'], 'start': found['start'], 'difficulty': 'easy',
                          'demo_fit_count': 3, 'query_disagreement': True,
                          'canonical_labeled_fit_count': 4 if rival_name == 'only_color6_blocks' else 0}

controls = []
for overrides in ({'grid_h': 14}, {'n_emitters': 1}):
    try:
        result = GEN.generate(0, 0, difficulty='easy', **overrides)
        controls.append({'overrides': overrides, 'unexpected_success': True})
    except Exception as error:
        controls.append({'overrides': overrides, 'exception_type': type(error).__name__, 'message': str(error)})
base = GEN.generate(0, 0, difficulty='easy')
controls.append({'unknown_key': '__audit_typo__', 'accepted_and_ignored': GEN.generate(0, 0, difficulty='easy', __audit_typo__=123) == base})
malformed = []
for name, grid in [('ragged_ignored_extra_cell', [[3, 0], [0, 0, 7]]),
                   ('ragged_short_row', [[3, 0], [0]]),
                   ('float_emitter', [[3.0, 0], [0, 0]])]:
    before = deepcopy(grid)
    try:
        result = GEN.self_check(grid)
        malformed.append({'name': name, 'input': grid, 'returned_reasons': result, 'accepted': result == []})
    except Exception as error:
        malformed.append({'name': name, 'input': grid, 'exception_type': type(error).__name__, 'message': str(error)})
    assert grid == before
emit('override-and-validator-counterexamples.json', {'task_id': TASK, 'generator_sha256': sha,
                                                    'controls': controls, 'malformed': malformed})
summary = {'schema': 'arcpuzzles-source-bound-audit-v1', 'task_id': TASK, 'generator_sha256': sha,
           'audit_assignment_sha256': hashlib.sha256((WORK / 'AUDIT_ASSIGNMENT.json').read_bytes()).hexdigest(),
           'canonical_ledger_sha256': hashlib.sha256((ROOT / 'shared/data/canonical/puzzles.jsonl').read_bytes()).hexdigest(),
           'canonical_mirror_checked_pairs': len(canonical), 'canonical_mirror_mismatches': 0,
           'only_color6_blocks_rival_canonical_fit_count': 4,
           'generated_label_execution': 'Python mirror only; no generated Racket execution',
           'population_seed': 7, 'population_indices': [0, 199], 'population': population,
           'consecutive_lesson_counterexamples': lessons, 'controls': controls, 'malformed': malformed,
           'command': {'argv': [sys.executable, str(Path(__file__).resolve())], 'cwd': os.getcwd(),
                       'PYTHONPATH': os.environ.get('PYTHONPATH'), 'exit_code_on_success': 0},
           'prior_audit_evidence_read': False, 'target_sources_modified': False}
emit('summary.json', summary)
print(json.dumps({k: v for k, v in summary.items() if k not in {'malformed'}}, sort_keys=True, indent=2))
