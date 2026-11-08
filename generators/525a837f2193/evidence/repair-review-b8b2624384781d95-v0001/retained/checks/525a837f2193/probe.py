"""Bounded peer replay: existing override defect and exact rival scope."""
from pathlib import Path
import hashlib
import importlib.util
import json

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

ROOT = Path.cwd()
HOME = ROOT / 'generators/525a837f2193'
OUT = ROOT.parent / 'checks/525a837f2193/probe.json'

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

generator = load(HOME / 'generator.py', 'peer_525_current')
helper_path = HOME / 'counterexamples/review-cce39a7758c1eb1c-v0001/retained/checks/audit/assigned_audit_probe.py'
helpers = load(helper_path, 'peer_525_retained_helpers')
record = Catalog('.').get('525a837f2193')
programs = {v['program_solution'] for v in record['variants']}
assert len(programs) == 1
canonical = next(iter(programs))
rival = '''(rule! (lambda (g)
  (let* ((spots (for*/list ((r (range 0 (rows g))) (c (range 0 (cols g)))
                  #:when (and (!= (at g r c) 0) (!= (at g r c) 1))) (list r c))))
    (if (empty? spots) g
      (let* ((first-spot (first spots))
             (color (at g (first first-spot) (second first-spot)))
             (selected (filter (lambda (p) (= (at g (first p) (second p)) color)) spots))
             (rr (map first selected)) (cc (map second selected)))
        (build-grid (rows g) (cols g) (r c)
          (if (and (= (at g r c) 1) (or (member r rr) (member c cc)))
              color (at g r c))))))))'''

a = generator.generate('assigned-audit-override', 0, difficulty='medium', anomaly=9)
b = generator.generate('assigned-audit-override', 0, difficulty='medium', anomaly=2)
observed = sorted({v for row in a for v in row if v not in (0, 1)})
assert a == b and observed != [9] and observed != [2]

canonical_pairs = record['variants'][0]['train'] + record['variants'][0]['test']
grids = [('canonical', i, p['input'], p['output']) for i, p in enumerate(canonical_pairs)]
grids += [('generated', i, generator.generate('review-b8b2624384781d95-peer', i, difficulty='medium'), None) for i in range(3)]
grids += [('outside_declared_support', 0, helpers.make_three_by_three_lattice(), None)]
rows = []
runtime = ROOT / 'shared/runtime'
with _local_imports(runtime, HOME):
    apply, identity, bridge = _real_evaluator(runtime)
    try:
        for origin, index, grid, saved in grids:
            actual = apply(canonical, grid)
            alternative = apply(rival, grid)
            assert alternative == helpers.pixel_line_rival_525(grid)
            if saved is not None:
                assert actual == saved
            if origin != 'outside_declared_support':
                assert actual == alternative
            else:
                assert actual != alternative and generator.self_check(grid)
            rows.append({'origin': origin, 'index': index, 'input': grid,
                         'reference_output': actual, 'rival_output': alternative,
                         'same_output': actual == alternative,
                         'self_check_errors': generator.self_check(grid),
                         'different_cells': [[r,c] for r in range(len(grid)) for c in range(len(grid[0])) if actual[r][c] != alternative[r][c]]})
    finally:
        bridge.close()

report = {
    'task_id': '525a837f2193', 'status': 'reproduced_unresolved_findings',
    'generator_sha256': sha(HOME / 'generator.py'),
    'probe_sha256': sha(Path(__file__)), 'reused_helper_sha256': sha(helper_path),
    'rule_hash': record['rule_hash'], 'canonical_program_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
    'racket': identity, 'racket_evaluations': 14,
    'program': canonical, 'rival_program': rival,
    'override': {'seed': 'assigned-audit-override', 'sample_index': 0, 'difficulty': 'medium',
                 'requests': [{'anomaly':9}, {'anomaly':2}], 'same_input': a==b,
                 'observed_anomaly_colors': observed, 'input': a,
                 'self_check_errors': generator.self_check(a)},
    'cases': rows,
    'findings': [
        f'The exact anomaly axis is still ignored: both requests produce anomaly colors {observed}.',
        'The raw-pixel rival matches three canonical and three ordinary generated inputs in this bounded replay; no within-support query counterexample was found.',
        'The 3x3-block witness is rejected by current self_check. Canonical Racket paints only the first anomaly row/column and their immediate unseparated neighbors; it does not implement full 3x3 block propagation. Merely widening cell_size would therefore be an unsafe abstraction repair.'
    ],
    'limits': 'One named rival, three current generated cases, three distinct canonical cases and one outside-support probe. No full battery, production repair, native acceptance, or training admission.'
}
assert report['generator_sha256'] == 'e5ff9a4894638da756d18d8b394fe1e1eb8cdee8e92f089b2c332465ed03182a'
OUT.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': report['status'], 'racket_evaluations':14, 'ordinary_and_canonical_matches':sum(x['same_output'] for x in rows), 'outside_support_difference_cells':len(rows[-1]['different_cells']), 'observed_anomaly_colors':observed}))
