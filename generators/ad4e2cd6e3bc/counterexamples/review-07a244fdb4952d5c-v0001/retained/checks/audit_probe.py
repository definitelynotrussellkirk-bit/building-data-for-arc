#!/usr/bin/env python3
"""Reproduce the two findings-only audits. Run through run_with_racket.py."""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
from collections import deque

TASKS = ('f898eb5adb5d', 'ad4e2cd6e3bc')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def largest_component_rival(grid):
    """Deliberately ignore the seed; paint the largest passable component."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (0, 2)}
    components = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        queue, component = deque([first]), {first}
        while queue:
            r, c = queue.popleft()
            for cell in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if cell in unseen:
                    unseen.remove(cell)
                    component.add(cell)
                    queue.append(cell)
        components.append(component)
    region = max(components, key=len)
    out = [row[:] for row in grid]
    for r, c in region:
        if out[r][c] == 0:
            out[r][c] = 8
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output exists')
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    catalog = Catalog()
    rules = {}
    with (catalog.root / 'shared/data/canonical/puzzles.jsonl').open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get('task_id') in TASKS:
                rules[row['task_id']] = row
    report = {'schema': 'review-07a244fdb4952d5c-audits-v1',
              'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()), 'tasks': {}}
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-audits-') as directory:
        stage = Path(directory)
        prepare_runtime(catalog, stage, task_ids=list(TASKS))
        sys.path.insert(0, str(stage))
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        sources = {task: wrap_rule(rules[task]['program_solution']) for task in TASKS}
        bridge = RacketBridge(max_calls_before_restart=64)
        def execute(task, grid):
            rows = ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid)
            return bridge.eval_text(f"({sources[task]} '({rows}))")
        try:
            for task in TASKS:
                module = importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
                report['tasks'][task] = {
                    'generator_sha256': sha(Path(module.__file__).read_bytes()),
                    'canonical_rule_sha256': sha(rules[task]['program_solution'].encode()),
                }
                result = report['tasks'][task]
                if task == TASKS[0]:
                    seed, index, band = 0, 0, 'easy'
                    overrides = dict(grid_h=8, grid_w=10, n_walls=0, n_waypoints=3)
                    grid = module.generate(seed, index, difficulty=band, **overrides)
                    baseline = module.generate(seed, index, difficulty=band)
                    actual = execute(task, grid)
                    result.update({
                        'kind': 'reproduced_ignored_overrides',
                        'seed': seed, 'sample_index': index, 'difficulty': band, 'overrides': overrides,
                        'input': grid, 'no_override_input': baseline,
                        'input_identical_to_no_override': grid == baseline,
                        'observed': {'grid_h':len(grid), 'grid_w':len(grid[0]),
                                     'n_walls':sum(v == 5 for row in grid for v in row),
                                     'n_waypoints':sum(v in (4,6,7,9) for row in grid for v in row)},
                        'racket_output': actual, 'rival_output': execute(task, baseline),
                        'rival_description': 'No-override control, not a competing semantic solver.',
                        'self_check': 'unavailable: generator defines no self_check',
                        'in_documented_domain': True, 'generated': True,
                    })
                else:
                    samples = []
                    for band in ('easy', 'medium', 'hard'):
                        for seed in range(100):
                            samples.append((dict(seed=seed, sample_index=seed, difficulty=band, overrides={}),
                                            module.generate(seed, seed, difficulty=band)))
                    generated = []
                    for meta, grid in samples:
                        actual = execute(task, grid)
                        rival = largest_component_rival(grid)
                        generated.append({**meta, 'input':grid, 'racket_output':actual,
                                          'rival_output':rival, 'rival_matches':rival == actual,
                                          'self_check':module.self_check(grid)})
                    canonical = []
                    for split in ('train','test'):
                        for i, pair in enumerate(rules[task][split]):
                            rival = largest_component_rival(pair['input'])
                            actual = execute(task, pair['input'])
                            canonical.append(dict(split=split,index=i,input=pair['input'],racket_output=actual,
                                                  rival_output=rival,rival_matches=rival==actual,
                                                  recorded_output_matches=actual==pair['output']))
                    frontier = [[5]*8,
                                [5,2,0,5,0,0,0,5],
                                [5,5,5,5,0,0,0,5],
                                [5,0,0,0,0,0,0,5],
                                [5,0,0,0,0,0,0,5],
                                [5,0,0,0,0,0,0,5],
                                [5]*8]
                    actual, rival = execute(task, frontier), largest_component_rival(frontier)
                    result.update({
                        'kind':'reproduced_sampling_shortcut_with_valid_frontier',
                        'rival_description':'Ignore seed position; flood zeros in the largest passable component.',
                        'seed_range_inclusive':[0,99], 'sample_index':'seed', 'bands':['easy','medium','hard'],
                        'generated_observations':len(generated),
                        'generated_unique_inputs':len({json.dumps(row['input']) for row in generated}),
                        'generated_rival_matches':sum(row['rival_matches'] for row in generated),
                        'generated_validator_failures':sum(bool(row['self_check']) for row in generated),
                        'generated_pairs':generated, 'canonical_pairs':canonical,
                        'frontier': {'input':frontier, 'racket_output':actual, 'rival_output':rival,
                                     'rival_matches':rival==actual, 'self_check':module.self_check(frontier),
                                     'observed_profile':module.observe_overrides(frontier),
                                     'in_documented_validator_domain':True, 'generated':False,
                                     'outside_sampler_support_reason':'Non-public scenes always put the seed in the largest component.'},
                    })
        finally:
            bridge.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        json.dump(report,handle,indent=2); handle.write('\n')
    for task, result in report['tasks'].items():
        print(task, result['kind'], result.get('observed', result.get('generated_rival_matches')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
