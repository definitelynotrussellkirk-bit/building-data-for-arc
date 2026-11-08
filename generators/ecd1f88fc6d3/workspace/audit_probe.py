"""Findings-only probes of the packet's two immutable audit targets.

Requires the full packet's native checkout; never edits audit generators.
Execute with run_with_racket.py and keep the resulting JSON under checks/.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from probe_distribution import ROOT, RUNTIME, CANON

AUDITS = ('cdc2954e8f80', '7bba59d92716')


def global_color_rectangle(grid):
    """Wrong: merge all instances of a color across different columns."""
    out = [row[:] for row in grid]
    for color in range(1, 10):
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if len(cells) >= 2:
            for r in range(min(r for r,c in cells), max(r for r,c in cells)+1):
                for c in range(min(c for r,c in cells), max(c for r,c in cells)+1):
                    out[r][c] = color
    return out


def vertical_runs(grid):
    """Wrong: mark length-five column runs even inside branched components."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] != 1:
                r += 1
                continue
            start = r
            while r < h and grid[r][c] == 1:
                r += 1
            if r-start == 5:
                out[start+2][c] = 2
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not (ROOT/'shared/runtime').is_dir():
        parser.error('this findings probe needs the full native packet, not a single-task runtime')
    scripts = types.ModuleType('scripts')
    scripts.__path__ = [str(ROOT/'shared/tools')]
    sys.modules.setdefault('scripts', scripts)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    with CANON.open() as handle:
        rows = {d['task_id']: d for line in handle if (d := json.loads(line)).get('task_id') in AUDITS}
    reports = {}
    with RacketBridge(timeout=20, max_calls_before_restart=48) as bridge:
        for tid, rival in zip(AUDITS, (global_color_rectangle, vertical_runs)):
            source = ROOT/'generators'/tid/'generator.py'
            spec = importlib.util.spec_from_file_location('audit_'+tid, source)
            gen = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gen)
            row = rows[tid]
            rule = wrap_rule(row['program_solution'])
            def oracle(grid):
                literal = "'("+' '.join('('+' '.join(map(str,r))+')' for r in grid)+')'
                return bridge.eval_text(f'({rule} {literal})')
            pairs = list(row['train'])
            test = row.get('test')
            pairs += [test] if isinstance(test, dict) else list(test or [])
            rep = {'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'canonical_train_rival_matches': [rival(p['input']) == p['output'] for p in row['train']],
                'canonical_all_racket_matches': [oracle(p['input']) == p['output'] for p in pairs],
                'default_draws': 60, 'default_racket_rival_agreements': 0, 'default_selfcheck_failures': 0}
            for band in ('easy', 'medium', 'hard'):
                for seed in range(20):
                    g = gen.generate(seed, seed % 6, difficulty=band)
                    rep['default_racket_rival_agreements'] += oracle(g) == rival(g)
                    rep['default_selfcheck_failures'] += bool(gen.self_check(g))
            base = gen.generate(0, 0)
            overrides = ({'palette_size': 1, 'n_distinct_colors': 1, 'palette_kind':'warm'}
                         if tid == AUDITS[0] else {'n_lines': 1, 'palette_size': 1})
            override_grid = gen.generate(0, 0, **overrides)
            rep['ignored_overrides'] = {'seed':0, 'sample_index':0, 'overrides': overrides,
                'output_equals_default': override_grid == base, 'input': override_grid,
                'nonzero_palette': sorted({v for r in override_grid for v in r if v})}
            try:
                unknown = gen.generate(0, 0, invented_axis=True)
                rep['unknown_override_rejected'] = False
                rep['unknown_override_equals_default'] = unknown == base
            except Exception as exc:
                rep['unknown_override_rejected'] = True
                rep['unknown_override_error'] = str(exc)
            if tid == AUDITS[0]:
                witness = [[0]*7 for _ in range(7)]
                for r,c in ((1,1),(3,1),(3,5),(5,5)):
                    witness[r][c] = 2
                misplaced = [[0]*7 for _ in range(7)]
                misplaced[1][1] = misplaced[5][5] = 2
                rep['selfcheck_false_negative'] = {'input': misplaced,
                    'errors':gen.self_check(misplaced), 'racket_is_identity': oracle(misplaced) == misplaced}
                rep['never_emits_reason'] = 'Ordinary generation assigns globally distinct colors to columns.'
            else:
                witness = [[0]*10 for _ in range(8)]
                for r in range(1,6):
                    witness[r][2] = witness[r][7] = 1
                witness[3][3] = 1
                rep['never_emits_reason'] = 'Only separated vertical color-1 lines are sampled; no attached arms.'
            intended = oracle(witness)
            wrong = rival(witness)
            rep['counterexample'] = {'input': witness, 'racket_output': intended,
                'rival_output': wrong, 'rival_refuted': intended != wrong,
                'generator_selfcheck_errors': gen.self_check(witness)}
            reports[tid] = rep
    output = {'schema':'two-target-adversarial-audit-v1', 'targets':reports}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({tid:{k:v for k,v in rep.items() if k not in
        ('counterexample','ignored_overrides','selfcheck_false_negative')} for tid,rep in reports.items()}, indent=2))
    return 0 if all(all(r['canonical_all_racket_matches']) and r['counterexample']['rival_refuted']
                    for r in reports.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
