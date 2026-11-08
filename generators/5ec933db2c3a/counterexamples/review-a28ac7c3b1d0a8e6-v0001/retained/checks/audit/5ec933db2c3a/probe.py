"""Read-only source-bound audit. Python outputs; fresh Racket check pending."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / 'repo'
SOURCE = ROOT / 'generators/5ec933db2c3a/generator.py'
SHA = '32378ad32e0d4ab2500adf5792c024646274dd32b46364185e7521b7cd1d9315'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
spec = importlib.util.spec_from_file_location('audit_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
record = json.loads((HERE / 'canonical-record.json').read_text())


def canonical_pairs():
    for split in ('train', 'test'):
        pairs = record[split]
        if isinstance(pairs, str):
            pairs = json.loads(pairs)
        if isinstance(pairs, dict):
            pairs = [pairs]
        for index, pair in enumerate(pairs):
            yield split, index, pair


def scan(grid):
    divider, = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    board = [row[divider + 1:] for row in grid]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row[:divider]) if v not in (0, 9)]
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    template = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    matches = []
    for rotation in range(4):
        th, tw = len(template), len(template[0])
        for top in range(len(board) - th + 1):
            for left in range(len(board[0]) - tw + 1):
                missing, valid = [], True
                for r in range(th):
                    for c in range(tw):
                        actual, wanted = board[top + r][left + c], template[r][c]
                        if actual == wanted:
                            continue
                        if actual == 0 and wanted != 0:
                            missing.append((top + r, left + c, wanted))
                        else:
                            valid = False
                if valid and len(missing) == 2:
                    matches.append({'rotation': rotation, 'origin': (top, left), 'missing': missing})
        template = [list(row) for row in zip(*reversed(template))]
    return board, matches


def outputs(grid):
    board, matches = scan(grid)
    counts = Counter(tuple(m['origin']) for m in matches)
    corners = {(0, 0), (0, len(board[0]) - 3), (len(board) - 3, 0), (len(board) - 3, len(board[0]) - 3)}
    result = {}
    for name in ('reference', 'unique_orientation_only', 'corner_windows_only'):
        out = [row[:] for row in board]
        for match in matches:
            if name == 'unique_orientation_only' and counts[tuple(match['origin'])] != 1:
                continue
            if name == 'corner_windows_only' and tuple(match['origin']) not in corners:
                continue
            for r, c, value in match['missing']:
                out[r][c] = value
        result[name] = out
    return result, matches


begin = time.perf_counter()
canonical_results = []
for split, index, pair in canonical_pairs():
    actual, matches = outputs(pair['input'])
    assert actual['reference'] == pair['output'] == gen.rule_mirror(pair['input'])
    canonical_results.append({'split': split, 'pair_index': index,
                              'self_check': gen.self_check(pair['input']),
                              'strict_canonical_like': gen.strict_canonical_like(pair['input']),
                              'strong_generated_scene': gen._is_strong_generated_scene(pair['input']),
                              'exact_matches': matches,
                              'rival_agreement': {k: v == pair['output'] for k, v in actual.items() if k != 'reference'}})
    if (split, index) == ('train', 0):
        query = pair
        (HERE / 'input.json').write_text(json.dumps(pair['input'], indent=2) + '\n')
        (HERE / 'outputs.json').write_text(json.dumps({'status': 'Python-derived and equal to stored canonical output; fresh Racket execution pending',
            'canonical_source': 'shared/data/canonical/puzzles.jsonl', 'task_id': gen.TASK_ID,
            'split': split, 'pair_index': index, 'input': pair['input'], 'canonical_output': pair['output'],
            'python_outputs': actual, 'matches': matches}, indent=2) + '\n')

draw_log = []
for band in (None, 'easy', 'medium', 'hard'):
    for height in range(7, 11):
        for width in range(12, 17):
            seed, index = 17 * height + width, (height + width) % 4
            grid = gen.generate(seed, index, difficulty=band, grid_h=height, grid_w=width)
            actual, matches = outputs(grid)
            errors = gen.self_check(grid)
            assert not errors and (len(grid), len(grid[0])) == (height, width)
            assert actual['reference'] == gen.rule_mirror(grid)
            assert actual['unique_orientation_only'] == actual['reference']
            assert actual['corner_windows_only'] == actual['reference']
            draw_log.append({'seed': seed, 'sample_index': index, 'difficulty': band,
                             'overrides': {'grid_h': height, 'grid_w': width},
                             'actual_shape': [len(grid), len(grid[0])], 'self_check': errors,
                             'exact_match_origins': [m['origin'] for m in matches],
                             'new_rivals_match': True})

demos = []
for index in range(3):
    inp = gen.generate(0, index, difficulty='medium')
    actual, _ = outputs(inp)
    assert len({json.dumps(out) for out in actual.values()}) == 1
    demos.append({'input': inp, 'output': actual['reference']})
hook_result = gen.lesson_identifiable(demos, query)
assert hook_result == []
query_outputs, _ = outputs(query['input'])
assert query_outputs['unique_orientation_only'] != query['output']
assert query_outputs['corner_windows_only'] != query['output']
(HERE / 'lesson-counterexample.json').write_text(json.dumps({'status': 'Python-derived demonstration labels; fresh Racket execution pending',
    'generator_seed': 0, 'difficulty': 'medium', 'demo_sample_indices': [0, 1, 2],
    'train': demos, 'test': [query], 'lesson_identifiable_result': hook_result}, indent=2) + '\n')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
result = {'generator_id': gen.TASK_ID, 'generator_sha256': SHA,
    'declared_rule_hash': gen.RULE_HASH,
    'canonical_program_sha256': hashlib.sha256(record['program_solution'].encode()).hexdigest(),
    'classification': 'confirmed canonical coverage gaps; no generated-label mismatch found',
    'racket_status': 'pending root authority execution',
    'canonical_results': canonical_results, 'draws': draw_log,
    'generated_draw_count': len(draw_log), 'lesson_identifiable_result': hook_result,
    'elapsed_seconds': round(time.perf_counter() - begin, 6)}
(HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('draws', 'canonical_results')}, indent=2))
print(json.dumps({'canonical_results': canonical_results}, indent=2))
