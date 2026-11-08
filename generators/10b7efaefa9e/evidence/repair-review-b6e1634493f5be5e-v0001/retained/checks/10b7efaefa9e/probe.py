"""One bounded threshold-three teaching-rival probe; no generator edits."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


TASK = '10b7efaefa9e'
ROOT = Path.cwd()
OUT = Path(__file__).resolve().with_name('peer-review.json')


def sizes(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    result = []
    while unseen:
        first = unseen.pop()
        component, todo = [first], [first]
        while todo:
            r, c = todo.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen and grid[nr][nc] == grid[r][c]:
                    unseen.remove((nr, nc)); todo.append((nr, nc)); component.append((nr, nc))
        result.append(len(component))
    return sorted(result)


def run():
    if OUT.exists():
        raise FileExistsError(OUT)
    module, source, digest = load_selected_generator(TASK, root=ROOT)
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK)
    canonical = next(iter({v['program_solution'] for v in catalog._variants()[row.get('rule_task_id', TASK)]}))
    needle = '(>= (obj-size obj) 4)'
    if canonical.count(needle) != 1:
        raise ValueError('Selected rule does not have the expected unique threshold literal')
    rival = canonical.replace(needle, '(>= (obj-size obj) 3)')
    report = {
        'schema': 'arcpuzzles-bounded-peer-review-v1', 'task_id': TASK,
        'status': 'no_issue_found_in_bounded_probe', 'outcome': 'unchanged',
        'source': {'path': source.relative_to(ROOT).as_posix(), 'sha256': digest,
                   'canonical_rule_hash': row['rule_hash'], 'approved': row['approved'],
                   'canonical_program_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
                   'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'commands': [{'cwd': str(ROOT.parent.parent), 'argv': [
            'WORK/.venv/bin/python', 'review.py', 'run', '../.venv/bin/python',
            '../checks/10b7efaefa9e/probe.py'], 'exit_status': 0}],
        'reviewed': ['generator.py', 'notes.md', 'SUMMARY.md', 'evidence/associated_notes.jsonl'],
        'rival': 'Recolor four-connected non-background components of size >=3 instead of >=4.',
        'scope': 'One threshold rival; seeds 0..23 at most; three default-difficulty demonstrations and one query; no production battery, repair, or universal learnability claim.',
        'racket_run': False, 'seeds_examined': [], 'observations': [],
        'production_source_changed': False, 'training_admitted': False,
    }
    for seed in range(24):
        grids = [module.generate(seed, i) for i in range(4)]
        counts = [sizes(grid) for grid in grids]
        report['seeds_examined'].append(seed)
        if any(3 in values for values in counts[:3]) or 3 not in counts[3]:
            continue
        checks = [module.self_check(grid) for grid in grids]
        if any(checks):
            raise ValueError('Candidate lesson is outside the generator self-check domain')
        bridge = RacketBridge()
        try:
            identity = bridge.runtime_identity
            if identity.get('backend') != 'racket' or identity.get('protected') is not True:
                raise ValueError('Protected Racket backend is required')
            def apply(program, grid):
                literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
                return bridge.eval_text(f'({wrap_rule(program)} {literal})')
            truth = [apply(canonical, grid) for grid in grids]
            predictions = [apply(rival, grid) for grid in grids]
        finally:
            bridge.close()
        if truth[:3] != predictions[:3] or truth[3] == predictions[3]:
            raise ValueError('Racket did not confirm the hypothesized teaching gap')
        report.update(status='finding', racket_run=True, racket=identity, racket_evaluations=8,
                      seed=seed, sample_indices=[0, 1, 2, 3], component_sizes=counts,
                      program=canonical, rival_program=rival, self_check=checks,
                      witness={'train': [{'input': grid, 'output': output}
                                         for grid, output in zip(grids[:3], truth[:3])],
                               'query': {'input': grids[3], 'output': truth[3], 'rival_output': predictions[3]}},
                      observations=['The >=3 rival fits all three executed demonstration labels but changes the executed query answer.',
                                    'The demonstrations omit size-three components, while the query includes at least one.',
                                    'The generator has no lesson-identifiability hook selecting a size-three boundary witness.'],
                      proposed_next_action='Add a size-three kept component to at least one demonstration whenever a query can contain size three; retain exact size-four positive examples. This is a comment-only teaching finding, not an implemented repair.')
        break
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('Selected source changed during the bounded probe')
    with OUT.open('x') as stream:
        json.dump(report, stream, sort_keys=True, indent=2); stream.write('\n')
    print(json.dumps({'status': report['status'], 'seed': report.get('seed'),
                      'racket_run': report['racket_run'], 'receipt': str(OUT),
                      'seeds_examined': len(report['seeds_examined'])}, sort_keys=True))


if __name__ == '__main__':
    run()
