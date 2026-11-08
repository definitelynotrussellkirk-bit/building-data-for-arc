"""Focused exact-override audit; reads selected sources, writes only audit evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT.parent / 'checks/audit/7071285d78ce'
SOURCE = ROOT / 'generators/7071285d78ce/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
canonical_path = ROOT / 'shared/data/canonical/puzzles.jsonl'
canonical = next(json.loads(line) for line in canonical_path.read_text().splitlines()
                 if json.loads(line)['task_id'] == '7071285d78ce')
rule = canonical['program_solution']
cases = []
for overrides in ({}, {'n_distinct_colors': 2}, {'grid_h': 8}, {'n_blobs': 4}):
    case = {'seed': 0, 'sample_index': 0, 'difficulty': None, 'overrides': overrides}
    try:
        grid = generator.generate(0, 0, **overrides)
        case.update(status='returned', input=grid,
                    dimensions=[len(grid), len(grid[0])],
                    foreground_colors=sorted({v for row in grid for v in row if v}),
                    self_check=generator.self_check(grid))
    except Exception as exc:
        case.update(status='raised', exception_type=type(exc).__name__, error=str(exc))
    cases.append(case)
grid = cases[1]['input']
(OUT / 'input.json').write_text(json.dumps(grid) + '\n')
from puzzle_generators.helpers.selfcheck import components_cells, bbox
rival = [[0 for _ in row] for row in grid]
for cells in components_cells(grid, same_color=True):
    r1, c1, _, _ = bbox(cells)
    for r, c in cells:
        rival[r1+c-c1][c1+r-r1] = grid[r][c]
(OUT / 'rival.json').write_text(json.dumps(rival) + '\n')
report = {
    'task_id': '7071285d78ce',
    'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'canonical_rule_hash': hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12],
    'canonical_rule_sha256': hashlib.sha256(rule.encode()).hexdigest(),
    'canonical_record_path': 'repo/shared/data/canonical/puzzles.jsonl',
    'cases': cases,
    'ignored_override_output_identical_to_default': cases[0]['input'] == cases[1]['input'],
    'rival_name': 'independent local transpose mirror; sanity check, not an alleged shortcut',
    'rival_output_path': 'checks/audit/7071285d78ce/rival.json',
    'interpretation': 'n_distinct_colors=2 is AXES-valid and realizable with two distinct-color blobs, but silently returns three colors. grid_h=8 and n_blobs=4 are declared AXES-valid yet rejected. No semantic mismatch is claimed.',
}
(OUT / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'cases'}))
print(json.dumps([{k: v for k, v in case.items() if k != 'input'} for case in cases]))
