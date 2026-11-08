#!/usr/bin/env python3
"""Proposed border-color variant, separate from canonical generation/approval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

from reviewer_support import canonical_path, find_root
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper

TASK_ID = 'a5bda33d14a0'
DEFAULT = 8
TESTED_SETTINGS = (8, 3, 6)


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def validate_color(color):
    if type(color) is not int or not 1 <= color <= 9:
        raise ValueError('border_color must be an integer in 1..9')


def canonical_source(root):
    sources = []
    for line in canonical_path(root).read_text().splitlines():
        row = json.loads(line)
        if row.get('task_id') == TASK_ID:
            sources.append(row['program_solution'])
    if not sources or len(set(sources)) != 1:
        raise ValueError('Expected one unambiguous selected canonical rule')
    return sources[0]


def materialize(border_color=DEFAULT, *, root=None):
    validate_color(border_color)
    source = canonical_source(find_root(__file__) if root is None else root)
    needle = '(set-cell out (first p) (second p) 8)'
    if source.count(needle) != 1:
        raise ValueError('Canonical rule changed; review parameter substitution')
    # Only the fill literal changes: zero guard and every source cell remain exact.
    return source.replace(needle, f'(set-cell out (first p) (second p) {border_color})')


def execute(bridge, source, grid):
    literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    # This selected rule is already ordinary Racket and uses only explicit g.
    # Avoid wrap_rule's optional authoring-parser dependency in repository layout.
    return bridge.eval_text(f'(let ((g {literal})) {strip_rule_wrapper(source)})')


def inputs_for_episode(seed, border_color=DEFAULT):
    validate_color(border_color)
    rng = random.Random(seed)
    # Exclude all three retained settings, and whichever additional one is chosen.
    palette = [c for c in range(1, 10) if c not in (*TESTED_SETTINGS, border_color)]
    grids = []
    for i in range(4):
        bh, bw = ((4, 6), (6, 4), (5, 5), (6, 7))[i]
        top, left = rng.randrange(3), rng.randrange(3)
        height, width = top + bh + rng.randrange(3), left + bw + rng.randrange(3)
        bottom, right = top + bh - 1, left + bw - 1
        grid = [[0] * width for _ in range(height)]
        colors = rng.sample(palette, 3)
        # Nonzero opposite corners fix the global bounding box. The other two
        # corners remain zero, so every demonstration identifies the fill color.
        grid[top][left] = colors[0]
        grid[bottom][right] = colors[1]
        grid[top + 1][left + 1] = colors[2]
        # Vary existing perimeter sources and interior content, preserving colors.
        grid[top][left + 2] = colors[1]
        grid[bottom - 1][right] = colors[2]
        if i % 2:
            grid[bottom - 1][left + 1] = colors[0]
        grids.append(grid)
    return grids


def public_challenge(episode):
    return {'train': episode['pairs'][:3],
            'test': [{'input': pair['input']} for pair in episode['pairs'][3:]]}


def make_episode(bridge, *, seed, border_color=None, root=None):
    if border_color is None:
        border_color = random.Random(seed).randint(1, 9)
    validate_color(border_color)
    root = find_root(__file__) if root is None else root
    source = materialize(border_color, root=root)
    pairs = [{'input': grid, 'output': execute(bridge, source, grid)}
             for grid in inputs_for_episode(seed, border_color)]
    refutations = {}
    for rival in range(1, 10):
        if rival != border_color:
            rival_source = materialize(rival, root=root)
            refutations[str(rival)] = [i for i, pair in enumerate(pairs[:3])
                                      if execute(bridge, rival_source, pair['input']) != pair['output']]
    return {'border_color': border_color, 'seed': seed, 'racket': source,
            'racket_sha256': sha(source), 'pairs': pairs,
            'rival_refuting_demo_indices': refutations,
            'production_verdict': 'pass' if all(refutations.values()) else 'ambiguous',
            'query_rotation_verdict': 'unknown: ordered three-demo/last-query prototype only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=104729)
    args = parser.parse_args()
    root = find_root(__file__)
    args.out.mkdir(parents=True, exist_ok=True)
    episodes = []
    with RacketBridge(startup_timeout=120) as bridge:
        for color in TESTED_SETTINGS:
            episode = make_episode(bridge, seed=args.seed, border_color=color, root=root)
            (args.out / f'border-{color}.rkt').write_text(episode['racket'])
            (args.out / f'public-{color}.json').write_text(json.dumps(public_challenge(episode), indent=2) + '\n')
            episodes.append(episode)
        canonical_default = materialize(DEFAULT, root=root) == canonical_source(root)
        assert canonical_default
        assert all(ep['production_verdict'] == 'pass' for ep in episodes)
        assert all(ep['pairs'][0]['input'] == episodes[0]['pairs'][0]['input'] for ep in episodes)
    source = Path(__file__).resolve()
    ledger = canonical_path(root)
    record = {
        'status': 'proposed prototype; no production integration or approval',
        'parameter': {'name': 'border_color', 'allowed': list(range(1, 10)), 'default': DEFAULT,
                      'chosen_once_per_episode': True, 'retained_settings': list(TESTED_SETTINGS)},
        'source_hashes': {'prototype.py': sha(source.read_bytes()),
                          'canonical_program': sha(canonical_source(root)),
                          'canonical_ledger': sha(ledger.read_bytes())},
        'canonical_default_exact_text': canonical_default,
        'actual_payload_command': {'cwd': '.', 'argv': [sys.executable, *sys.argv], 'exit_code': 0},
        'wrapper_recipe_from_WORK': ['python3', 'run_with_racket.py', '../.venv/bin/python',
                                     'generators/a5bda33d14a0/workspace/parametric/prototype.py',
                                     '--out', '../checks/parametric', '--seed', str(args.seed)],
        'counts': {'episodes': len(episodes), 'demonstrations': 9, 'queries': 3,
                   'chosen_rule_pair_executions': 12, 'rival_demo_executions': 72,
                   'refuted_setting_episode_pairs': 24},
        'limits': ['One fixed seed; settings 8,3,6 retained as complete episodes.',
                   'Three ordered demonstrations and one final query per episode.',
                   'Rivals are the other eight allowed fill colors only.',
                   'No arbitrary query-rotation or other-semantic-rival census.',
                   'All-zero and degenerate boxes checked separately by focused tests.',
                   'Source palette excludes retained settings and selected color; this is a prototype input constraint.'],
        'episodes': episodes,
    }
    (args.out / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'status': record['status'], 'counts': record['counts'],
                      'source_hashes': record['source_hashes']}))


if __name__ == '__main__':
    main()
