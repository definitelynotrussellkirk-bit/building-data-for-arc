"""Portable, input-only corpus for independent public-Racket cross-checking.

Run from the packet root with run_with_racket.py; see workspace/README.md.
This is an authoring probe: never import it during a visible-only solve.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

TASK = 'ba29d14676d1'


def row_run_mirror(grid):
    """Independent oracle: reverse each maximal non-divider substring of a row."""
    result = []
    for row in grid:
        out, start = list(row), 0
        for stop in range(len(row) + 1):
            if stop == len(row) or row[stop] == 9:
                out[start:stop] = row[start:stop][::-1]
                start = stop + 1
        result.append(out)
    return result


def make_corpus(gen, canonical):
    cases = []
    for p in canonical:
        cases.append(dict(kind='canonical', split=p['split'], pair_index=p['pair_index'],
                          input=p['input'], expected=p['output']))
    names = ('tile_rows', 'tile_cols', 'tile_h', 'tile_w', 'foreground')
    for values in itertools.product((1, 3), (2, 5), (2, 5), (2, 5), (1, 8)):
        axes = dict(zip(names, values))
        grid = gen.generate(103, 2, **axes)
        cases.append(dict(kind='joint_axis_corner', seed=103, sample_index=2,
                          overrides=axes, input=grid, expected=row_run_mirror(grid)))
    for n in range(64 - len(cases)):
        band = ('easy', 'medium', 'hard')[n % 3]
        grid = gen.generate(314159, n, difficulty=band)
        cases.append(dict(kind='default', seed=314159, sample_index=n, difficulty=band,
                          overrides={}, input=grid, expected=row_run_mirror(grid)))
    return dict(schema='tile-reflection-probe-v1', task_id=TASK,
                canonical_shortcut_fit={name: all(fn(copy.deepcopy(p['input'])) == p['output']
                                                  for p in canonical)
                                        for name, fn in gen.CANONICAL_SHORTCUTS.items()},
                rival_refutations={name: [i for i, c in enumerate(cases)
                                          if fn(copy.deepcopy(c['input'])) != c['expected']]
                                   for name, fn in gen.LESSON_COMPETITORS.items()},
                cases=cases,
                limitation='Python-oracle expectations are not reference measurements until public apply is checked.')


def main():
    from reviewer_support import canonical_pairs, find_root
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output directory exists; retain each run under a fresh name')
    root = find_root(__file__)
    source = next(p for p in (root/'generators'/TASK/'generator.py',
                              root/'puzzle_generators'/'per_puzzle'/TASK/'generator.py') if p.is_file())
    spec = importlib.util.spec_from_file_location('probe_generator', source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    result = make_corpus(gen, canonical_pairs(TASK, root=root, labeled_only=True))
    result['generator_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    result['generator_version'] = gen.VERSION
    result['declared_rule_hash'] = gen.RULE_HASH
    args.out.mkdir(parents=True)
    (args.out/'probe.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.out/'inputs.json').write_text(json.dumps({'inputs': [c['input'] for c in result['cases']]}) + '\n')
    print(json.dumps({'cases': len(result['cases']), 'source': result['generator_sha256'],
                      'output': str(args.out)}))


if __name__ == '__main__':
    main()
