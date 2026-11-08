"""Bounded production-control/Racket parity probe; no generator edits."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.runner import wrap_rule

TASK = 'fd588326c845'
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
gen, source, source_hash = load_selected_generator(TASK, root=ROOT)
rows = [json.loads(line) for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if line.strip()]
rules = {row['program_solution'] for row in rows if row.get('task_id') == TASK}
assert len(rules) == 1, 'ambiguous canonical rule'
rule = next(iter(rules))

def digest(value):
    return hashlib.sha256(value).hexdigest()

def literal(grid):
    return "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'

checks = []
with RacketBridge() as bridge:
    for scale_h, scale_w in ((6, 1), (1, 6)):
        for seed in (0, 1, 17, 83):
            requested = dict(key_size=4, scale_h=scale_h, scale_w=scale_w, palette_size=4)
            sample_index = seed * 17 + 97
            grid = gen.generate(seed, sample_index, difficulty='hard', **requested)
            snapshot = [row[:] for row in grid]
            observed = gen.observe_overrides(grid)
            errors = gen.self_check(grid)
            actual = bridge.eval_text(f'({wrap_rule(rule)} {literal(grid)})')
            expected = gen.rule_mirror(grid)
            # Derive each label locally from the clockwise source-cell relation,
            # independent of generator scene analysis and Python rule mirror.
            key_cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,8)]
            cyan_cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 8]
            kr, kc = min(r for r,c in key_cells), min(c for r,c in key_cells)
            cr, cc = min(r for r,c in cyan_cells), min(c for r,c in cyan_cells)
            direct = [row[:] for row in grid]
            for r,c in cyan_cells:
                direct[r][c] = grid[kr + 3 - (c-cc)//scale_w][kc + (r-cr)//scale_h]
            passed = not errors and observed == requested and actual == expected == direct and grid == snapshot
            checks.append(dict(seed=seed, sample_index=sample_index, difficulty='hard', requested=requested,
                               observed=observed, self_check_errors=errors, shape=[len(grid),len(grid[0])],
                               passed=passed, input=grid, racket_output=actual,
                               python_mirror_equal=actual == expected, direct_label_equal=actual == direct,
                               input_unchanged=grid == snapshot))
            print(json.dumps({k:v for k,v in checks[-1].items() if k not in ('input','racket_output')}, sort_keys=True))
report = dict(schema='bounded-generator-probe-v1', task_id=TASK,
              scope='Eight lawful maximum-anisotropy production-control cases; no broad distribution/teaching claim',
              source_path=str(source.relative_to(ROOT)), source_sha256=source_hash,
              rule_sha256=digest(rule.encode()), normalized_rule_sha256=digest(' '.join(rule.split()).encode()),
              probe_sha256=digest(Path(__file__).read_bytes()),
              helper_hashes={str(path.relative_to(ROOT)):digest(path.read_bytes()) for path in
                             (ROOT/'shared/runtime/reviewer_support.py',ROOT/'shared/runtime/puzzle_generators/runner.py',ROOT/'shared/runtime/arc_repl/racket_bridge.py')},
              cases=checks, passed=all(row['passed'] for row in checks), case_count=len(checks))
(HERE/'result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(dict(passed=report['passed'],case_count=len(checks),source_sha256=source_hash,rule_sha256=report['rule_sha256']),sort_keys=True))
sys.exit(0 if report['passed'] else 1)
