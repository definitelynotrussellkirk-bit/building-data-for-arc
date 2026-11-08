from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))
GENERATOR = REPO / 'generators' / '8dd7ace7de9a' / 'generator.py'
REF = GENERATOR.parent / 'workspace' / 'reference_probe.py'

def load(path, name):
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

gen = load(GENERATOR, 'generator_current')
ref = load(REF, 'reference_probe_current')

def top_left_tile_shortcut(grid):
    observed = gen.observe_overrides(grid)
    pr, pc = observed['period_r'], observed['period_c']
    tile = [row[:pc] for row in grid[:pr]]
    return [[tile[r % pr][c % pc] for c in range(len(grid[0]))] for r in range(len(grid))]

seed = 213_974_615_879_964
start = 66
difficulty = 'easy'
rows = []
for offset in range(4):
    grid = gen.generate(seed, start + offset, difficulty=difficulty)
    expected = gen.rule_mirror(deepcopy(grid))
    predicted = top_left_tile_shortcut(deepcopy(grid))
    diffs = [(r,c,expected[r][c],predicted[r][c]) for r in range(len(grid)) for c in range(len(grid[0])) if expected[r][c] != predicted[r][c]]
    rows.append({
        'offset': offset,
        'role': 'demo' if offset < 3 else 'query',
        'sample_index': start + offset,
        'observed_axes': gen.observe_overrides(grid),
        'shortcut_matches': not diffs,
        'difference_count': len(diffs),
        'first_differences': diffs[:10],
    })
canonical_rows=[]
for i,pair in enumerate(ref.canonical_pairs()):
    predicted=top_left_tile_shortcut(deepcopy(pair['input']))
    canonical_rows.append({'pair':i,'fits':predicted==pair['output']})
result={
    'schema':'8dd7ace7de9a-top-left-replay-v1',
    'generator_sha256':sha256(GENERATOR.read_bytes()).hexdigest(),
    'seed':seed,'start':start,'difficulty':difficulty,
    'pairs':rows,
    'demos_all_fit':all(row['shortcut_matches'] for row in rows[:3]),
    'query_differs':not rows[3]['shortcut_matches'],
    'canonical_fit':canonical_rows,
}
print(json.dumps(result, indent=2, sort_keys=True))
