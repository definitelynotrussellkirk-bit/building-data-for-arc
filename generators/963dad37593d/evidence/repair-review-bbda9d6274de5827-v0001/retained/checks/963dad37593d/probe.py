"""Bounded peer check: four visible examples versus one query, bbox-area rival."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
TASK = '963dad37593d'
OUT = ROOT.parent / 'checks' / TASK
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

def sha(value):
    return hashlib.sha256(value).hexdigest()

def crop(cells):
    rows = [r for r, c in cells]
    cols = [c for r, c in cells]
    points = set(cells)
    return [[8 if (r, c) in points else 0 for c in range(min(cols), max(cols)+1)]
            for r in range(min(rows), max(rows)+1)]

def bbox_area(cells):
    return ((max(r for r, c in cells)-min(r for r, c in cells)+1)
            * (max(c for r, c in cells)-min(c for r, c in cells)+1))

with _local_imports(ROOT / 'shared/runtime', ROOT / 'generators' / TASK):
    gen, source, source_hash = load_selected_generator(TASK, root=ROOT)
    program = Catalog(ROOT)._variants()[TASK][0]['program_solution']
    def prediction(grid, bbox=False):
        comps = [cells for color, cells in gen._body_components(grid)]
        comps.sort(key=lambda cells: (-(bbox_area(cells) if bbox else len(cells)), min(cells)))
        return crop(comps[sum(v == 1 for v in grid[0])-1])
    winner = None
    scanned = []
    for seed in range(16):
        grids = [gen.generate(seed, i, difficulty='medium') for i in range(5)]
        matches = [prediction(g, True) == prediction(g) for g in grids]
        scanned.append({'seed': seed, 'bbox_matches_area': matches})
        if all(matches[:4]) and not matches[4]:
            winner = (seed, grids)
            break
    report = {
        'task_id': TASK, 'generator_sha256': source_hash,
        'rule_text_sha256': sha(program.encode()), 'probe_sha256': sha(Path(__file__).read_bytes()),
        'rival': 'Count blue header cells k, rank body objects by descending bounding-box area (ties top-left), select kth and crop/recolor occupied cells to 8.',
        'search_bound': {'medium_seeds': list(range(16)), 'sample_indices': list(range(5)), 'demos': 4, 'query': 1},
        'scanned': scanned, 'found': winner is not None,
        'limits': 'Bounded reviewer-assembled sequential episode check; not a production lesson census, canonical-fitting rival, source approval, or parametric qualification.',
    }
    if winner:
        seed, grids = winner
        apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
        try:
            outputs = [apply(program, g) for g in grids]
        finally:
            bridge.close()
        pairs = []
        for i, (g, output) in enumerate(zip(grids, outputs)):
            assert not gen.self_check(g, difficulty='medium')
            assert output == prediction(g)
            assert g != output
            pairs.append({'sample_index': i, 'input': g, 'output': output,
                          'rival_output': prediction(g, True), 'self_check': [],
                          'components': [{'color': color, 'area': len(cells), 'bbox_area': bbox_area(cells), 'top_left': list(min(cells))}
                                         for color, cells in gen._body_components(g)]})
        assert len({json.dumps(p['input']) for p in pairs}) == 5
        assert all(p['output'] == p['rival_output'] for p in pairs[:4])
        assert pairs[4]['output'] != pairs[4]['rival_output']
        report['witness'] = {'seed': seed, 'difficulty': 'medium', 'sample_index': 0, 'train': pairs[:4], 'test': pairs[4:]}
        report['protected_runtime_identity'] = identity
        report['racket_labels_checked'] = 5
    (OUT / 'peer-evidence.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('task_id', 'generator_sha256', 'rule_text_sha256', 'found')}))
    print(json.dumps({'episodes_checked': len(scanned), 'witness_seed': winner[0] if winner else None}))
