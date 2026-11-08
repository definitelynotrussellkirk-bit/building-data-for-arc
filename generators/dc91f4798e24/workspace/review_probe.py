"""Reproducible, source-hashed reference census and findings-only audit probes.

Run through the packet's run_with_racket.py. No private solve artifacts are read.
All labels are executed by the canonical Racket rule; Python supplies rivals.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / 'shared/runtime').is_dir() or (p / 'arc_repl').is_dir())
SOURCE_LAYOUT = (ROOT / 'shared/runtime').is_dir()
DATA = ROOT / ('shared/data' if SOURCE_LAYOUT else 'data')
GENERATORS = ROOT / ('generators' if SOURCE_LAYOUT else 'puzzle_generators/per_puzzle')
# Source tools expect their conventional scripts/ package. Stage through the
# shipped API rather than aliasing imports or borrowing a neighboring checkout.
if SOURCE_LAYOUT:
    import tempfile
    sys.path.insert(0, str(ROOT / 'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    _runtime_tmp = tempfile.TemporaryDirectory(prefix='arcpuzzles-review-probe-')
    RUNTIME = Path(_runtime_tmp.name)
    # Rotating packets need not contain this historical review's optional peers.
    # Importing the main task's independent flood fill must still work. Explicit
    # audits continue to fail visibly if their requested source is unavailable.
    runtime_tasks = [task for task in ('dc91f4798e24', '26f313fdf812', '9b028298192f')
                     if (GENERATORS / task / 'generator.py').is_file()]
    prepare_runtime(Catalog(ROOT), RUNTIME, task_ids=runtime_tasks)
else:
    RUNTIME = ROOT
sys.path.insert(0, str(RUNTIME))
# Clear source-layout modules a caller (e.g. pytest) may already have imported.
# They are compatible, but the CLI starts clean and loads entirely from RUNTIME.
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(task, path=None):
    path = path or GENERATORS / task / 'generator.py'
    spec = importlib.util.spec_from_file_location('probe_' + task, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def norm(grid):
    return [list(map(int, row)) for row in grid]


def canonical(task):
    rows = [json.loads(line) for line in (DATA / 'canonical/puzzles.jsonl').read_text().splitlines()]
    return [row for row in rows if row.get('task_id') == task]


def pairs(rows):
    output = []
    for row_index, row in enumerate(rows):
        for split in ('train', 'test'):
            values = row.get(split, [])
            values = [values] if isinstance(values, dict) else values
            for index, pair in enumerate(values):
                if 'output' in pair:
                    output.append({'row': row_index, 'split': split, 'index': index,
                                   'input': norm(pair['input']), 'output': norm(pair['output'])})
    return output


def components(grid, *, connectivity=4, binary=False):
    """Independent flood fill, retaining row-major encounter and bbox orders."""
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    moves = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (connectivity == 8 or abs(dr) + abs(dc) == 1)]
    while pending:
        start = min(pending)
        pending.remove(start)
        seen, queue = [start], deque([start])
        color = grid[start[0]][start[1]]
        while queue:
            r, c = queue.popleft()
            for dr, dc in moves:
                q = (r + dr, c + dc)
                if q in pending and (binary or grid[q[0]][q[1]] == color):
                    pending.remove(q); queue.append(q); seen.append(q)
        result.append({'color': color, 'cells': seen, 'size': len(seen), 'first': start,
                       'bbox': (min(r for r, c in seen), min(c for r, c in seen))})
    return result


def bars(counts):
    return [[color if i < n else 0 for i in range(max(1, *counts))]
            for color, n in zip((1, 2, 3), counts)]


def histogram(grid, connectivity=4):
    cc = components(grid, connectivity=connectivity)
    return bars([sum(x['color'] == color for x in cc) for color in (1, 2, 3)])


def pixel_rival(grid):
    return bars([sum(row.count(color) for row in grid) for color in (1, 2, 3)])


def binary_rival(grid):
    cc = components(grid, binary=True)
    return bars([sum(any(grid[r][c] == color for r, c in x['cells']) for x in cc)
                 for color in (1, 2, 3)])


class Reference:
    def __init__(self, task):
        self.rows = canonical(task)
        self.program = self.rows[0]['program_solution']
        programs = {row['program_solution'] for row in self.rows}
        if len(programs) != 1:
            raise ValueError(f'{task}: ambiguous rule programs ({len(programs)})')
        self.rule_sha256 = hashlib.sha256(self.program.encode()).hexdigest()
        self.bridge = RacketBridge(timeout=15)
        self.bridge.eval_text('(define probe_rule ' + wrap_rule(self.program) + ')')

    def __call__(self, grid):
        self.bridge.define_grid('probe_grid', grid)
        return self.bridge.eval_text('(probe_rule probe_grid)')

    def close(self):
        self.bridge.close()


def census(args):
    task = 'dc91f4798e24'
    source = args.generator_source or GENERATORS / task / 'generator.py'
    gen, ref = load(task, source), Reference(task)
    rivals = {'pixel_count': pixel_rival, 'eight_connected': lambda g: histogram(g, 8),
              'binary_foreground': binary_rival}
    report = {'phase': args.phase, 'task_id': task, 'generator_sha256': digest(source),
              'rule_sha256': ref.rule_sha256, 'seed_range': [0, args.per_band - 1],
              'sample_index': 'seed % 16', 'per_band': args.per_band,
              'bands': {}, 'canonical': [], 'failures': [], 'examples': {},
              'runtime_directory': str(RUNTIME), 'runtime_manifest_sha256': digest(RUNTIME / 'RUNTIME_MANIFEST.json')}
    try:
        for pair in pairs(ref.rows):
            actual = ref(pair['input'])
            report['canonical'].append({**pair, 'actual_output': actual,
                'validator_errors': gen.self_check(pair['input']),
                'rival_matches': {name: fn(pair['input']) == actual for name, fn in rivals.items()}})
            if actual != pair['output']:
                report['failures'].append({'kind': 'canonical_reference_mismatch', **pair})
        rows_path = args.out.with_suffix('.rows.jsonl')
        with rows_path.open('w') as handle:
            for band in (None, 'easy', 'medium', 'hard'):
                counts = Counter()
                unique = set()
                for seed in range(args.per_band):
                    grid = gen.generate(seed, seed % 16, difficulty=band)
                    actual = ref(grid)
                    errors = gen.self_check(grid)
                    rival_outputs = {name: fn(grid) for name, fn in rivals.items()}
                    mismatches = {name: value != actual for name, value in rival_outputs.items()}
                    record = {'seed': seed, 'sample_index': seed % 16, 'difficulty': band,
                              'overrides': {}, 'input': grid, 'actual_output': actual,
                              'validator_errors': errors, 'rival_mismatches': mismatches}
                    handle.write(json.dumps(record, separators=(',', ':')) + '\n')
                    unique.add(json.dumps(grid))
                    counts['inputs'] += 1
                    counts['validator_failures'] += bool(errors)
                    counts['python_reference_mismatches'] += histogram(grid) != actual
                    counts['noise'] += any(v >= 4 for row in grid for v in row)
                    counts['target_border'] += any(grid[r][c] in (1, 2, 3)
                        for r in range(len(grid)) for c in range(len(grid[0]))
                        if r in (0, len(grid)-1) or c in (0, len(grid[0])-1))
                    for name, differs in mismatches.items():
                        counts[name + '_refuted'] += differs
                        if differs and name not in report['examples']:
                            report['examples'][name] = {**record, 'rival_name': name,
                                                       'rival_output': rival_outputs[name]}
                    if errors or histogram(grid) != actual:
                        report['failures'].append(record)
                report['bands'][str(band)] = {**counts, 'unique_inputs': len(unique)}
        report['rows_sha256'] = digest(rows_path)
        report['unique_inputs_across_bands'] = len({json.dumps(json.loads(s)['input']) for s in rows_path.read_text().splitlines()})
        report['total_inputs'] = 4 * args.per_band
    finally:
        ref.close()
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('canonical', 'failures', 'examples')}, indent=2))
    return int(bool(report['failures']))


def matrix(grid, encounter=False):
    objects = components(grid)
    objects.sort(key=lambda x: x['first'] if encounter else x['bbox'])
    return [[1 if a['size'] == b['size'] else 2 if a['size'] > b['size'] else 3
             for b in objects] for a in objects]


def snake(grid, vertical_dedupe=False):
    cells = [(c, r, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v
             and not (vertical_dedupe and r > 0 and grid[r-1][c] == v)]
    colors = [v for c, r, v in sorted(cells)]
    output = [[0] * 3 for _ in range(3)]
    for i, v in enumerate(colors[:9]):
        r, c = divmod(i, 3)
        output[r][c if r != 1 else 2-c] = v
    return output


def audits(args):
    report = {'phase': 'audit_unchanged_sources', 'targets': {}, 'failures': [],
              'runtime_directory': str(RUNTIME), 'runtime_manifest_sha256': digest(RUNTIME / 'RUNTIME_MANIFEST.json')}
    for task in ('26f313fdf812', '9b028298192f'):
        source = GENERATORS / task / 'generator.py'
        gen, ref = load(task), Reference(task)
        mirror = matrix if task == '26f313fdf812' else snake
        rival = (lambda g: matrix(g, True)) if task == '26f313fdf812' else (lambda g: snake(g, True))
        target = {'generator_sha256': digest(source), 'rule_sha256': ref.rule_sha256,
                  'seed_range': [0, args.per_band - 1], 'sample_indices': list(range(8)),
                  'bands': ['easy', 'medium', 'hard'], 'canonical': [], 'counts': {}, 'counterexample': None}
        try:
            for pair in pairs(ref.rows):
                actual = ref(pair['input'])
                target['canonical'].append({**pair, 'actual_output': actual,
                    'rival_matches': rival(pair['input']) == actual,
                    'validator_errors': gen.self_check(pair['input'])})
            count = Counter()
            unique = set()
            for band in ('easy', 'medium', 'hard'):
                for seed in range(args.per_band):
                    for index in range(8):
                        g = gen.generate(seed, index, difficulty=band)
                        actual = ref(g)
                        unique.add(json.dumps(g))
                        count['inputs'] += 1
                        count['validator_failures'] += bool(gen.self_check(g))
                        count['reference_mismatches'] += mirror(g) != actual
                        count['rival_matches'] += rival(g) == actual
            target['counts'] = {**count, 'unique_inputs': len(unique)}
            if task == '26f313fdf812':
                g = [[0]*9 for _ in range(9)]
                for color, cells in ((2, [(1,5),(2,5),(3,5),(3,4),(3,3),(3,2),(3,1)]),
                                     (3, [(1,3),(1,4)]), (4, [(6,1),(6,2),(7,1),(7,2)])):
                    for r,c in cells: g[r][c] = color
                domain = 'Passes self_check and strict_canonical_like; outside disjoint 3x3 envelope sampler.'
                name = 'scan_encounter_order_not_bbox_top_left'
            else:
                # Nine answer-bearing cells; a vertical domino gives an exact
                # rival disagreement. This is intentionally outside the narrow
                # horizontal-domino linked profile, not claimed as emitted.
                g = [[0]*10 for _ in range(10)]
                for r,c,v in ((1,0,2),(2,0,2),(7,2,3),(1,3,4),(5,4,5),(8,5,6),(2,6,7),(4,7,8),(6,8,9)):
                    g[r][c] = v
                domain = 'Lawful per-cell rule input, but outside documented profile grammar; self_check rejects.'
                name = 'deduplicate_vertical_same_color_runs'
            target['counterexample'] = {'task_id': task, 'generator_sha256': digest(source),
                'rule_sha256': ref.rule_sha256, 'source': 'hand_constructed', 'seed': None,
                'sample_index': None, 'overrides': None, 'input': g, 'actual_output': ref(g),
                'rival_name': name, 'rival_output': rival(g), 'validator_errors': gen.self_check(g),
                'strict_errors': gen.strict_canonical_like(g), 'domain': domain,
                'command': ['python3', 'run_with_racket.py', 'python3',
                            'generators/dc91f4798e24/workspace/review_probe.py', 'audits',
                            '--per-band', str(args.per_band), '--out', str(args.out)],
                'cwd': 'packet_root', 'runtime_cwd': 'repo'}
            if target['counterexample']['actual_output'] == target['counterexample']['rival_output']:
                raise AssertionError('audit counterexample does not refute its rival')
            if count['validator_failures'] or count['reference_mismatches']:
                report['failures'].append(task)
        finally:
            ref.close()
        report['targets'][task] = target
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({task: {'counts': row['counts'], 'canonical_pairs': len(row['canonical']),
                             'counterexample': row['counterexample']} for task,row in report['targets'].items()}, indent=2))
    return int(bool(report['failures']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('census', 'audits'))
    parser.add_argument('--per-band', type=int, default=100)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--generator-source', type=Path)
    parser.add_argument('--phase', default='final')
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error('--per-band must be positive')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    return census(args) if args.mode == 'census' else audits(args)

if __name__ == '__main__':
    raise SystemExit(main())
