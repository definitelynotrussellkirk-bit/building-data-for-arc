"""Bounded teaching probe of the single-component-color mobility condition."""
from pathlib import Path
import hashlib
import json

from arcpuzzles.catalog import Catalog
from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


TASK = '0b53f4dfc446'
ROOT = Path.cwd()
OUT = Path(__file__).resolve().with_name('peer-review.json')


def components(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        first = min(remaining); remaining.remove(first)
        cells, stack = [first], [first]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point); cells.append(point); stack.append(point)
        result.append(sorted(cells))
    return result


def norm(cells):
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def facts(grid):
    colors = sorted({v for row in grid for v in row} - {0, 5})
    by_color = {color: components(grid, color) for color in colors}
    holes = []
    for cells in components(grid, 5):
        r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
        hole = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if grid[r][c] == 0]
        if hole: holes.append(hole)
    return {'component_counts': {str(color): len(parts) for color, parts in by_color.items()},
            'matching_multicomponent_colors': [color for color, parts in by_color.items()
                if len(parts) > 1 and any(norm(parts[0]) == norm(hole) for hole in holes)]}


def run():
    if OUT.exists(): raise FileExistsError(OUT)
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    catalog = Catalog(ROOT); row = catalog.describe(TASK)
    canonical = next(iter({v['program_solution'] for v in catalog._variants()[row.get('rule_task_id', TASK)]}))
    edits = [('(if (= (length objs) 1)', '(if (> (length objs) 0)'),
             ('(lambda (ci) (= (second ci) 1))', '(lambda (ci) (> (second ci) 0))')]
    rival = canonical
    for before, after in edits:
        if rival.count(before) != 1: raise ValueError('Unexpected canonical mobility implementation')
        rival = rival.replace(before, after)
    report = {
        'schema': 'arcpuzzles-bounded-peer-review-v1', 'task_id': TASK,
        'status': 'no_finding_in_bounded_probe', 'outcome': 'unchanged',
        'source': {'path': source.relative_to(ROOT).as_posix(), 'sha256': digest,
                   'canonical_rule_hash': row['rule_hash'], 'approved': row['approved'],
                   'canonical_program_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
                   'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'commands': [{'cwd': str(ROOT.parent.parent), 'argv': [
            'WORK/.venv/bin/python', 'review.py', 'run', '../.venv/bin/python',
            '../checks/0b53f4dfc446/probe.py'], 'exit_status': 0}],
        'reviewed': ['generator.py', 'notes.md', 'SUMMARY.md', 'evidence/review_index.json'],
        'existing_audit': {'unresolved': row.get('audit_unresolved'),
                           'scope': 'Existing override/validation audit is unchanged and not resolved by this probe.'},
        'rival': 'Ignore color multiplicity: move the first component of any nonzero non-container color when its normalized shape matches a hole.',
        'scope': 'One mobility-condition rival, at most seeds 0..23, three unforced default-difficulty demonstrations plus one query. No full battery, source repair, or universal learnability claim.',
        'racket_run': False, 'racket_evaluations': 0, 'seeds_examined': [], 'observations': [],
        'production_source_changed': False, 'training_admitted': False,
    }
    bridge = None
    try:
        for seed in range(24):
            grids = [gen.generate(seed, index) for index in range(4)]
            observations = [facts(grid) for grid in grids]
            report['seeds_examined'].append(seed)
            if any(any(count != 1 for count in f['component_counts'].values()) for f in observations[:3]):
                continue
            if not observations[3]['matching_multicomponent_colors']:
                continue
            checks = [gen.self_check(grid) for grid in grids]
            if any(checks): raise ValueError('Generated witness violates current self_check')
            if bridge is None:
                bridge = RacketBridge(); identity = bridge.runtime_identity
                if identity.get('backend') != 'racket' or identity.get('protected') is not True:
                    raise ValueError('Protected Racket backend required')
                report.update(racket_run=True, racket=identity)
            def apply(program, grid):
                literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
                report['racket_evaluations'] += 1
                return bridge.eval_text(f'({wrap_rule(program)} {literal})')
            truth = [apply(canonical, grid) for grid in grids]
            predictions = [apply(rival, grid) for grid in grids]
            if truth != [gen._mirror(grid) for grid in grids]:
                raise ValueError('Canonical Racket differs from the selected source mirror')
            if truth[:3] != predictions[:3] or truth[3] == predictions[3]:
                continue
            differences = [(r, c) for r in range(len(grids[3])) for c in range(len(grids[3][0]))
                           if truth[3][r][c] != predictions[3][r][c]]
            report.update(status='finding', seed=seed, sample_indices=[0, 1, 2, 3],
                          component_observations=observations, self_check=checks,
                          program=canonical, rival_program=rival,
                          witness={'train': [{'input': grid, 'output': output}
                                             for grid, output in zip(grids[:3], truth[:3])],
                                   'query': {'input': grids[3], 'output': truth[3],
                                             'rival_output': predictions[3], 'differing_cells': differences}},
                          observations=['The multiplicity-ignoring rival fits all three Racket-labeled demonstrations but changes the query.',
                                        'Every demo color has one component; the query has a multi-component color whose first component matches a container hole.',
                                        'Source comments request a multi_decoy teaching example, but default texture draws are independent and no lesson-identifiability hook enforces it.'],
                          proposed_next_action='Select a multi_decoy demonstration whenever a query exercises color multiplicity; check the chosen finite rival on demonstrations before releasing the query. This comment does not change or resolve the existing scalar-contract audit.')
            break
    finally:
        if bridge is not None: bridge.close()
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('Selected source changed during bounded probe')
    with OUT.open('x') as stream:
        json.dump(report, stream, sort_keys=True, separators=(',', ':')); stream.write('\n')
    print(json.dumps({'status': report['status'], 'seed': report.get('seed'),
                      'racket_run': report['racket_run'], 'racket_evaluations': report['racket_evaluations'],
                      'receipt': '../checks/0b53f4dfc446/peer-review.json',
                      'seeds_examined': len(report['seeds_examined'])}, sort_keys=True))


if __name__ == '__main__': run()
