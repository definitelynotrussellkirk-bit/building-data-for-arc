#!/usr/bin/env python3
"""Independent, source-hashed teacher/shortcut census; no model is trained.

From repo: python generators/f9dd4cf0f344/workspace/quality_probe.py --out ../checks/probe.json
Optional --racket verifies every sampled label with the unchanged canonical rule.
The Python oracle and deliberately wrong rules here are diagnostic, never labels
for exported training data. Reports keep a first counterexample per rival/band.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
TASK = 'f9dd4cf0f344'
CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def load_generator(path=HOME / 'generator.py'):
    spec = importlib.util.spec_from_file_location('reviewed_generator', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def oracle(grid):
    """Independent implementation: use a set, not the generator's _fires."""
    out = [row[:] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            colors = {grid[r+dr][c+dc] for dr, dc in CARD}
            if grid[r][c] == 0 and len(colors) == 1 and 0 not in colors:
                out[r][c] = colors.pop()
    return out


def rival(grid, name):
    out = oracle(grid)  # mutants deliberately make one specified extra edit
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = [grid[r+dr][c+dc] for dr, dc in CARD]
            counts = Counter(arms)
            k, n = counts.most_common(1)[0]
            if name == 'enclosed_majority' and grid[r][c] == 0 and 0 not in arms and n >= 3:
                out[r][c] = k
            elif name == 'overwrite_occupied' and 0 not in arms and len(counts) == 1:
                out[r][c] = k
            elif name == 'three_arms' and grid[r][c] == 0 and k != 0 and n >= 3:
                out[r][c] = k
            elif name == 'diagonals_also' and grid[r][c] == 0:
                ds = {grid[r+dr][c+dc] for dr, dc in DIAG}
                if len(ds) == 1 and 0 not in ds:
                    out[r][c] = ds.pop()
    return out


RIVALS = ('enclosed_majority', 'overwrite_occupied', 'three_arms', 'diagonals_also')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--generator', type=Path, default=HOME/'generator.py')
    ap.add_argument('--count', type=int, default=256, help='seeds per band, 0..count-1; sample_index=seed')
    ap.add_argument('--racket', action='store_true')
    args = ap.parse_args()
    if args.count <= 0:
        ap.error('--count must be positive')
    mod = load_generator(args.generator)
    report = {'schema':'plus-quality-probe-v1', 'task_id':TASK,
              'source_sha256':hashlib.sha256(args.generator.read_bytes()).hexdigest(),
              'seeds':f'0..{args.count-1}', 'sample_index':'seed', 'bands':{},
              'racket_checked':0, 'racket_mismatches':[], 'failures':[],
              'scope':'sampled input quality and known rivals, not model learning or approval'}
    bridge = None
    runtime_dir = None
    if args.racket:
        # The shared rule wrapper imports legacy scripts.* modules. Use the
        # supported portable runtime instead of fabricating aliases or relying
        # on an unrelated checkout's PYTHONPATH.
        sys.path.insert(0, str(ROOT/'src'))
        from arcpuzzles import Catalog
        from arcpuzzles.runtime import prepare_runtime
        runtime_dir = tempfile.TemporaryDirectory(prefix='plus-quality-runtime-')
        runtime_path = Path(runtime_dir.name)
        manifest = prepare_runtime(Catalog(ROOT), runtime_path, TASK)
        report['runtime_generator_sha256'] = next(
            row['sha256'] for row in manifest['files']
            if row['library_path'] == f'generators/{TASK}/generator.py')
        sys.path.insert(0, str(runtime_path))
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        source = next(json.loads(s)['program_solution'] for s in
                      (ROOT/'shared/data/canonical/puzzles.jsonl').open()
                      if json.loads(s).get('task_id') == TASK)
        report['rule_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        bridge = RacketBridge(prelude_path=str(runtime_path/'arc_repl/racket_prelude/arc-prelude.rkt'))
        bridge.eval_text(f'(define quality_rule {wrap_rule(source)})')
    try:
        for band in ('easy', 'medium', 'hard'):
            stats = {'requested':args.count, 'generated':0, 'unique_inputs':0,
                     'identity':0, 'rival_exact_matches':dict.fromkeys(RIVALS,0),
                     'first_counterexamples':{}, 'shape_counts':{}, 'fill_count_counts':{}}
            seen, shapes, fills = set(), Counter(), Counter()
            for seed in range(args.count):
                try:
                    g = mod.generate(seed, seed, difficulty=band)
                    expected = oracle(g)
                    if bridge:
                        bridge.define_grid('quality_input', g)
                        actual = bridge.eval_text('(quality_rule quality_input)')
                        report['racket_checked'] += 1
                        if actual != expected:
                            report['racket_mismatches'].append({'band':band,'seed':seed,'input':g,'expected':expected,'actual':actual})
                    stats['generated'] += 1
                    seen.add(json.dumps(g,separators=(',',':')))
                    shapes[f'{len(g)}x{len(g[0])}'] += 1
                    fills[sum(a != b for ra,rb in zip(g,expected) for a,b in zip(ra,rb))] += 1
                    stats['identity'] += (g == expected)
                    for name in RIVALS:
                        pred = rival(g, name)
                        stats['rival_exact_matches'][name] += (pred == expected)
                        if pred != expected and name not in stats['first_counterexamples']:
                            stats['first_counterexamples'][name] = {'seed':seed,'sample_index':seed,'input':g,'expected':expected,'rival_output':pred}
                except Exception as exc:
                    report['failures'].append({'band':band,'seed':seed,'error':repr(exc)})
            stats['unique_inputs'] = len(seen)
            stats['shape_counts'], stats['fill_count_counts'] = dict(sorted(shapes.items())), dict(sorted(fills.items()))
            report['bands'][band] = stats
    finally:
        if bridge:
            bridge.close()
        if runtime_dir:
            runtime_dir.cleanup()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'bands'}))
    for band,s in report['bands'].items():
        print(band, {k:v for k,v in s.items() if k not in ('first_counterexamples','shape_counts','fill_count_counts')})
    return 1 if report['failures'] or report['racket_mismatches'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
