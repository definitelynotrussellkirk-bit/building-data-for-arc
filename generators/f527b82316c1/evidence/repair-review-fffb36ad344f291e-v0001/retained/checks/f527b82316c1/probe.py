"""Two default lessons, four named rival rules, protected Racket labels.

From packet outer directory:
WORK/.venv/bin/python review.py run python3 ../checks/f527b82316c1/probe.py
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2] / 'repo'
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]
from reviewer_support import load_selected_generator
from arcpuzzles.parametric_worker import _real_evaluator

TASK = 'f527b82316c1'
SOURCE_SHA256 = '6e2eac45f2caa45b293ba90cccae1c495773848fe624c2b63932fe7e585d7c7e'
generator, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
assert source_hash == SOURCE_SHA256, 'Selected source changed; review must be rebound'
record = next(json.loads(line) for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
              if json.loads(line)['task_id'] == TASK)
program = record['program_solution']
rule_hash = hashlib.sha256(program.encode()).hexdigest()

DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

def tile(grid):
    h, w = len(grid), len(grid[0])
    return [[grid[r % h][c % w] for c in range(2 * w)] for r in range(2 * h)]

def halo(grid, offsets):
    h, w = len(grid), len(grid[0])
    return [[8 if grid[r][c] == 0 and any(
        0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0
        for dr, dc in offsets) else grid[r][c] for c in range(w)] for r in range(h)]

RIVALS = {
    'tile_only': tile,
    'diagonal_halo_then_tile': lambda g: tile(halo(g, DIAGONALS)),
    'tile_then_cardinal_halo': lambda g: halo(tile(g), CARDINALS),
    'tile_then_eight_neighbor_halo': lambda g: halo(tile(g), DIAGONALS + CARDINALS),
}

apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
episodes = []
try:
    for seed in (0, 1):
        grids = [generator.generate(seed, index) for index in range(4)]
        labels = [apply(program, grid) for grid in grids]
        for grid, label in zip(grids, labels):
            assert label == halo(tile(grid), DIAGONALS), 'Python canonical interpretation differs from Racket'
        rivals = []
        for name, predict in RIVALS.items():
            matches = [predict(grid) == label for grid, label in zip(grids, labels)]
            rivals.append({'name': name, 'demo_matches': matches[:3], 'query_matches': matches[3],
                           'counterexample': all(matches[:3]) and not matches[3]})
        episodes.append({'seed': seed, 'demo_sample_indices': [0, 1, 2], 'query_sample_index': 3,
                         'train': [{'input': grid, 'output': label} for grid, label in zip(grids[:3], labels[:3])],
                         'query': {'input': grids[3], 'output': labels[3]}, 'rivals': rivals})
finally:
    bridge.close()

found = any(r['counterexample'] for episode in episodes for r in episode['rivals'])
result = {'schema': 'bounded-peer-learnability-v1', 'task_id': TASK,
          'source_path': source_path.relative_to(ROOT).as_posix(), 'source_sha256': source_hash,
          'rule_sha256': rule_hash, 'runtime_identity': identity,
          'scope': 'Default seeds 0 and 1, indices 0..2 demos and 3 query; exactly four named rivals.',
          'outcome': 'counterexample' if found else 'bounded_no_issue', 'episodes': episodes,
          'limits': ['Finite named rivals only; no all-seed or general learnability claim.',
                     'Existing dead-axis and validation audit is unchanged and unresolved.']}
destination = Path(__file__).with_name('probe-result.json')
destination.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'outcome': result['outcome'], 'source_sha256': source_hash,
                  'rule_sha256': rule_hash, 'episodes': [{'seed': e['seed'], 'rivals': e['rivals']} for e in episodes]}, indent=2))
