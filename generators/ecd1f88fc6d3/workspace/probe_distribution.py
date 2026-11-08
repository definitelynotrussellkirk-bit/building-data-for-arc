"""Reproduce structural diversity and code-blind shortcut support before/after.

Run from either the native checkout or a materialized standalone runtime.
Use --generator PATH to compare a frozen predecessor; no source is modified.
--racket verifies public examples and saved counterexamples against authority.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

TASK = 'ecd1f88fc6d3'
HERE = Path(__file__).resolve()
ROOT = next((p for p in HERE.parents if (p/'shared/runtime').is_dir()), None)
if ROOT is None:
    ROOT = next(p for p in HERE.parents if (p/'puzzle_generators').is_dir())
    RUNTIME = ROOT
    SOURCE = ROOT/'puzzle_generators/per_puzzle'/TASK/'generator.py'
    CANON = ROOT/'data/canonical/puzzles.jsonl'
else:
    RUNTIME = ROOT/'shared/runtime'
    SOURCE = ROOT/'generators'/TASK/'generator.py'
    CANON = ROOT/'shared/data/canonical/puzzles.jsonl'
sys.path.insert(0, str(RUNTIME))


def geometry_only(grid):
    h, w = len(grid), len(grid[0])
    out = [[0]*w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (1, 2, 3, 4):
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                sr, sc = r-dr, c-dc
                if 0 <= sr < h and 0 <= sc < w and grid[sr][sc] >= 5:
                    rr, cc = sr, sc
                    while 0 <= rr < h and 0 <= cc < w:
                        out[rr][cc] = grid[sr][sc]
                        rr, cc = rr+dr, cc+dc
    return out


def normalized(grid):
    return tuple(tuple(5 if v >= 5 else v for v in row) for row in grid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generator', type=Path, default=SOURCE)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=80)
    parser.add_argument('--racket', action='store_true')
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds must be positive')
    spec = importlib.util.spec_from_file_location('review_subject', args.generator)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    with CANON.open() as handle:
        row = next(d for line in handle if (d := json.loads(line)).get('task_id') == TASK)
    canonical = row['train'] + ([row['test']] if isinstance(row['test'], dict) else row['test'])
    report = {'schema': 'directed-ray-shortcut-probe-v1', 'task_id': TASK,
              'generator_sha256': hashlib.sha256(args.generator.read_bytes()).hexdigest(),
              'version': gen.VERSION, 'seeds': args.seeds,
              'canonical_geometry_agreements': sum(geometry_only(p['input']) == p['output'] for p in canonical),
              'canonical_pairs': len(canonical), 'profiles': {}, 'bands': {}, 'counterexamples': []}
    for profile in gen.SCHEDULE_PROFILES:
        grids = [gen.generate(s, 2, grid_h=7, grid_w=7, scene_profile=profile) for s in range(args.seeds)]
        report['profiles'][profile] = {'draws': len(grids),
            'normalized_layouts': len({normalized(g) for g in grids}),
            'geometry_agreements': sum(geometry_only(g) == gen.rule_mirror(g) for g in grids)}
        for seed, grid in enumerate(grids):
            expected, rival = gen.rule_mirror(grid), geometry_only(grid)
            if expected != rival:
                report['counterexamples'].append({'seed': seed, 'sample_index': 2,
                    'overrides': {'grid_h': 7, 'grid_w': 7, 'scene_profile': profile},
                    'input': grid, 'python_mirror_output': expected, 'rival_output': rival})
                break
    for band in ('easy', 'medium', 'hard'):
        grids = [gen.generate(seed, index, difficulty=band) for seed in range(10) for index in range(12)]
        report['bands'][band] = {'draws': len(grids),
            'normalized_layouts': len({normalized(g) for g in grids}),
            'geometry_agreements': sum(geometry_only(g) == gen.rule_mirror(g) for g in grids)}
    if args.racket:
        # Native source stores the runtime's `scripts` package in shared/tools.
        # Bind that package locally, rather than borrowing another checkout.
        if RUNTIME != ROOT and "scripts" not in sys.modules:
            scripts = types.ModuleType("scripts")
            scripts.__path__ = [str(ROOT / "shared/tools")]
            sys.modules["scripts"] = scripts
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        program = wrap_rule(row['program_solution'])
        with RacketBridge(timeout=20) as bridge:
            def evaluate(grid):
                literal = "'(" + ' '.join('('+' '.join(map(str,r))+')' for r in grid)+')'
                return bridge.eval_text(f'({program} {literal})')
            report['racket_canonical_matches'] = [evaluate(p['input']) == p['output'] for p in canonical]
            for example in report['counterexamples']:
                output = evaluate(example['input'])
                example['racket_output'] = output
                example['racket_matches_mirror'] = output == example['python_mirror_output']
                example['racket_refutes_rival'] = output != example['rival_output']
            report['racket_checks_passed'] = all(report['racket_canonical_matches']) and all(
                e['racket_matches_mirror'] and e['racket_refutes_rival'] for e in report['counterexamples'])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'counterexamples'}, indent=2))
    return 0 if report.get('racket_checks_passed', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
