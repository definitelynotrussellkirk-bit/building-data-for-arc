#!/usr/bin/env python3
"""Count-preservation and coverage census, with source hashes and witnesses.

Can measure a baseline generator path without replacing current selected code.
The cell-count metric does not trust generator.self_check or helper functions.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--generator', type=Path, required=True)
    p.add_argument('--seeds', type=int, default=200)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.seeds < 1 or args.out.exists():
        p.error('positive seeds and a new output path are required')
    sys.path.insert(0, str(args.root.resolve()/'shared/runtime'))
    spec = importlib.util.spec_from_file_location('distribution_target', args.generator)
    gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
    report = {'generator_sha256': hashlib.sha256(args.generator.read_bytes()).hexdigest(),
              'seed_range': [0, args.seeds-1], 'sample_index': 0, 'groups': {}}
    groups = [(band, band, {}) for band in ('easy', 'medium', 'hard')]
    groups += [('forced5_four', 'easy', {'canvas_size': 5, 'n_corners': 4}),
               ('repeat_four', 'medium', {'n_corners': 4, 'palette_size': 1})]
    for name, band, overrides in groups:
        counts, sizes, uniq, failures, witnesses = Counter(), Counter(), set(), [], {}
        flags = Counter()
        for seed in range(args.seeds):
            try:
                grid = gen.generate(seed, 0, difficulty=band, **overrides)
                colors = Counter(v for row in grid for v in row)
                bg, n_bg = colors.most_common(1)[0]
                foreground = sum(colors.values()) - n_bg
                counts[str(foreground//3)] += 1
                sizes[str(len(grid))] += 1
                uniq.add(json.dumps(grid, separators=(',', ':')))
                edge = any(v != bg and (r in (0, len(grid)-1) or c in (0, len(grid)-1))
                           for r, row in enumerate(grid) for c, v in enumerate(row))
                values = {'edge': edge, 'foreground_zero': bg != 0 and 0 in colors,
                          'background_zero': bg == 0,
                          'repeated_foreground_color': any(v > 3 for c, v in colors.items() if c != bg),
                          'validator_rejects': bool(gen.self_check(grid)),
                          'count_mismatch': 'n_corners' in overrides and foreground != 3*overrides['n_corners']}
                for key, truth in values.items():
                    if truth:
                        flags[key] += 1
                        witnesses.setdefault(key, {'seed': seed, 'sample_index': 0,
                                                  'difficulty': band, 'overrides': overrides, 'input': grid})
            except Exception as exc:
                failures.append({'seed': seed, 'error': f'{type(exc).__name__}: {exc}'})
        report['groups'][name] = {'attempts': args.seeds, 'successful_draws': args.seeds-len(failures),
            'unique_inputs': len(uniq), 'difficulty': band, 'overrides': overrides,
            'l_count_by_foreground_divided_by_3': counts, 'sizes': sizes, 'flags': flags,
            'exceptions': failures, 'first_witness_per_flag': witnesses}
    report['command'] = {'cwd': str(Path.cwd()), 'argv': [sys.executable]+sys.argv}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    for name, group in report['groups'].items():
        print(name, group['successful_draws'], dict(group['flags']))


if __name__ == '__main__':
    main()
