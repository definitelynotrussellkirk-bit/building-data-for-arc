"""Bounded n_markers/label probe; authoring data, not a blind solver."""
from pathlib import Path
import hashlib
import json

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = '7a5df359d0c5'
ROOT = find_root(__file__)
OUT = ROOT.parent / 'checks' / TASK / 'probe.json'
module, source, source_hash = load_selected_generator(TASK, root=ROOT)
rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
row, = [row for row in rows if row.get('task_id') == TASK]
rule = row['program_solution']

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def expected_ring(grid):
    h, w = len(grid), len(grid[0])
    result = [[0] * w for _ in range(h)]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            color = grid[r][c]
            if color:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            result[r + dr][c + dc] = color
    return result

report = {
    'schema': 'bounded-marker-count-probe-v1',
    'task_id': TASK,
    'generator_path': str(source.relative_to(ROOT)),
    'generator_sha256': source_hash,
    'canonical_rule_sha256': hashlib.sha256(rule.encode()).hexdigest(),
    'canonical_ledger_sha256': hashlib.sha256(canonical_path(ROOT).read_bytes()).hexdigest(),
    'scope': 'n_markers=4 at minimum default medium grid 8x8; seeds 0..15, sample_index=0; canonical label calibration',
    'generated': [], 'canonical': [], 'failures': [],
}
with RacketBridge(timeout=20) as bridge:
    report['racket_identity'] = bridge.runtime_identity
    bridge.eval_text('(define review-rule ' + wrap_rule(rule) + ')')
    def execute(grid):
        bridge.define_grid('review-input', grid)
        return bridge.eval_text('(review-rule review-input)')
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        actual = execute(pair['input'])
        ok = actual == pair['output']
        record = {key: pair[key] for key in ('variant', 'split', 'pair_index')}
        record['matches_canonical_label'] = ok
        report['canonical'].append(record)
        if not ok:
            report['failures'].append({'canonical': record, 'actual': actual, 'expected': pair['output']})
    for seed in range(16):
        grid = module.generate(seed, 0, difficulty='medium', grid_h=8, grid_w=8, n_markers=4)
        repeated = module.generate(seed, 0, difficulty='medium', grid_h=8, grid_w=8, n_markers=4)
        markers = [(r, c, v) for r, line in enumerate(grid) for c, v in enumerate(line) if v]
        expected = expected_ring(grid)
        actual = execute(grid)
        checks = {
            'count_exact': len(markers) == 4,
            'deterministic': repeated == grid,
            'self_check': not module.self_check(grid),
            'interior_distinct_spaced': len({v for _, _, v in markers}) == 4
                and all(1 <= r < 7 and 1 <= c < 7 for r, c, _ in markers)
                and all(abs(a[0]-b[0]) > 2 or abs(a[1]-b[1]) > 2
                        for i, a in enumerate(markers) for b in markers[i+1:]),
            'racket_ring_label': actual == expected,
        }
        record = {'seed': seed, 'sample_index': 0, 'checks': checks,
                  'input_sha256': digest(grid), 'output_sha256': digest(actual)}
        report['generated'].append(record)
        if seed == 0:
            report['minimal_witness'] = {'seed': seed, 'input': grid, 'racket_output': actual}
        if not all(checks.values()):
            report['failures'].append({'generated': record, 'input': grid, 'actual': actual, 'expected': expected})
report['outcome'] = 'unchanged' if not report['failures'] else 'finding'
report['limits'] = ['Only one existing control at one default grid boundary and 16 seeds was probed.',
                    'Declared AXES beyond the exercised default band, degenerate textures, lesson identifiability, and exhaustive placement coverage were not assessed.']
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'outcome': report['outcome'], 'generated_cases': len(report['generated']),
                  'canonical_labels': len(report['canonical']), 'failures': len(report['failures']),
                  'generator_sha256': source_hash, 'rule_sha256': report['canonical_rule_sha256'],
                  'evidence': str(OUT.relative_to(ROOT.parent))}, sort_keys=True))
raise SystemExit(bool(report['failures']))
