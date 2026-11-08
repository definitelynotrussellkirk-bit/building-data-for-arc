"""Targeted, bounded audit of marker-side placement; no source changes."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'repo/shared/runtime'))
source = ROOT / 'repo/generators/b49cc3ee0734/generator.py'
spec = importlib.util.spec_from_file_location('audit_generator', source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
rows = [json.loads(line) for line in (ROOT / 'repo/shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line).get('task_id') == 'b49cc3ee0734']
assert len(rows) == 1
canonical = rows[0]

def analyze(g):
    h, w = len(g), len(g[0])
    cols = [c for c in range(w) if all(g[r][c] == 5 for r in range(h))]
    rws = [r for r in range(h) if all(v == 5 for v in g[r])]
    vertical = bool(cols)
    divider = cols[0] if vertical else rws[0]
    markers = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 2]
    objects = [(r, c) for r in range(h) for c in range(w) if g[r][c] not in (0, 2, 5)]
    axis = 1 if vertical else 0
    return {'orientation': 'vertical' if vertical else 'horizontal', 'divider': divider,
            'markers': markers, 'objects': objects,
            'marker_on_object_side': all((x[axis] < divider) == (markers[0][axis] < divider) for x in objects)}

def ignore_marker(g):
    """Canonical-fitting rival: reflect every object cell regardless of marker."""
    info = analyze(g)
    out = [row[:] for row in g]
    d = info['divider']
    for r, c in info['markers']:
        out[r][c] = 0
    for r, c in info['objects']:
        nr, nc = (r, 2*d-c) if info['orientation'] == 'vertical' else (2*d-r, c)
        if 0 <= nr < len(g) and 0 <= nc < len(g[0]):
            out[nr][nc] = g[r][c]
    return out

fits = [{'split': split, 'index': i, 'matches': ignore_marker(pair['input']) == pair['output']}
        for split in ('train', 'test') for i, pair in enumerate(canonical[split])]
assert all(x['matches'] for x in fits)
scanned = []
witness = None
for seed in range(64):
    args = {'seed': seed, 'sample_index': 0, 'difficulty': 'easy', 'overrides': {'grid_h': 7, 'grid_w': 7}}
    g = mod.generate(seed, 0, difficulty='easy', grid_h=7, grid_w=7)
    info = analyze(g)
    scanned.append({'seed': seed, 'marker_on_object_side': info['marker_on_object_side']})
    if not info['marker_on_object_side']:
        witness = {'arguments': args, 'analysis': info, 'self_check_errors': mod.self_check(g)}
        (OUT / 'input.json').write_text(json.dumps(g) + '\n')
        (OUT / 'rival.json').write_text(json.dumps(ignore_marker(g)) + '\n')
        break
assert witness, 'No wrong-side marker in bounded targeted seed set'
sha = lambda b: hashlib.sha256(b).hexdigest()
result = {'generator_path': str(source.relative_to(ROOT)), 'generator_sha256': sha(source.read_bytes()),
          'canonical_path': 'repo/shared/data/canonical/puzzles.jsonl',
          'canonical_rule_sha256': sha(canonical['program_solution'].encode()),
          'canonical_row_sha256': sha(json.dumps(canonical, sort_keys=True).encode()),
          'canonical_rival_fits': fits, 'bounded_scanned_count': len(scanned), 'scanned': scanned,
          'witness': witness, 'documented_domain': 'Generated normally with easy difficulty and accepted 7x7 dimension overrides; violates stated marker-on-source-side invariant.'}
(OUT / 'probe.json').write_text(json.dumps(result, indent=2) + '\n')
(OUT / 'canonical.json').write_text(json.dumps(canonical, indent=2) + '\n')
print(json.dumps(result, indent=2))
